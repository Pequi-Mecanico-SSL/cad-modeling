"""Headless PNG rendering of build123d shapes with pyvista."""

from pathlib import Path

import numpy as np
import pyvista as pv
from build123d import Compound, Shape
from vtkmodules.vtkCommonCore import vtkLogger

# Silences the X server warning; VTK falls back to offscreen rendering on its own
vtkLogger.SetStderrVerbosity(vtkLogger.VERBOSITY_ERROR)

PALETTE = ["#8fa9c7", "#d9a066", "#9cc38f", "#c78fb4", "#c7c38f", "#8fc7c3"]

# (label, camera direction from focal point, view-up); robot front is +X
VIEWS = [
    ("iso", (1, -1, 0.8), (0, 0, 1)),
    ("top (+X right)", (0, 0, 1), (0, 1, 0)),
    ("front (from +X)", (1, 0, 0), (0, 0, 1)),
    ("side (from -Y)", (0, -1, 0), (0, 0, 1)),
]


def _leaves(shape: Shape) -> list[Shape]:
    if isinstance(shape, Compound) and shape.children:
        return [leaf for child in shape.children for leaf in _leaves(child)]
    return [shape]


def _to_polydata(shape: Shape, tolerance: float) -> pv.PolyData:
    verts, tris = shape.tessellate(tolerance, 0.2)
    points = np.array([(v.X, v.Y, v.Z) for v in verts])
    faces = np.hstack([[3, *t] for t in tris]) if tris else np.empty(0, dtype=int)
    return pv.PolyData(points, faces)


def render_views(shape: Shape, path: Path, title: str = "", size: int = 700) -> None:
    """Render a 2x2 grid (iso/top/front/side) to a PNG. Compound children get distinct colors."""
    bb = shape.bounding_box()
    tolerance = max(bb.diagonal / 2000, 0.01)
    meshes = []
    for i, leaf in enumerate(_leaves(shape)):
        mesh = _to_polydata(leaf, tolerance)
        if mesh.n_points == 0:
            continue
        color = PALETTE[i % len(PALETTE)]
        if getattr(leaf, "color", None) is not None:
            color = tuple(leaf.color)[:3]
        meshes.append((mesh, color))

    center = np.array([bb.center().X, bb.center().Y, bb.center().Z])
    pl = pv.Plotter(shape=(2, 2), off_screen=True, window_size=(2 * size, 2 * size))
    for idx, (label, direction, up) in enumerate(VIEWS):
        pl.subplot(idx // 2, idx % 2)
        pl.set_background("white")
        for mesh, color in meshes:
            pl.add_mesh(mesh, color=color, smooth_shading=False, specular=0.2)
            pl.add_mesh(mesh.extract_feature_edges(25), color="black", line_width=1.5)
        pl.add_text(f"{title}  {label}" if idx == 0 else label, font_size=10, color="black")
        pl.add_axes(line_width=2, labels_off=False)
        d = np.array(direction, dtype=float)
        pl.camera.focal_point = center
        pl.camera.position = center + d / np.linalg.norm(d) * bb.diagonal * 3
        pl.camera.up = up
        pl.camera.parallel_projection = True
        pl.reset_camera()
        pl.camera.zoom(1.1)
    pl.screenshot(str(path))
    pl.close()
