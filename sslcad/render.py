"""Headless PNG rendering of build123d shapes with pyvista."""

from pathlib import Path

import numpy as np
import pyvista as pv
from build123d import Color, Compound, Location, Shape
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


def _leaves(shape: Shape, parent: Location | None = None) -> list[tuple[Shape, Location | None, Color | None]]:
    """Leaf shapes with the location of their parent and their color.

    Assembly children are stored relative to their parent, so a leaf is in global coordinates only after
    applying that location.
    """
    if isinstance(shape, Compound) and shape.children:
        inner = shape.location if parent is None else parent * shape.location
        return [leaf for child in shape.children for leaf in _leaves(child, inner)]
    return [(shape, parent, shape.color)]


def _to_polydata(shape: Shape, tolerance: float, loc: Location | None) -> pv.PolyData:
    verts, tris = shape.tessellate(tolerance, 0.2)
    points = np.array([(v.X, v.Y, v.Z) for v in verts]).reshape(-1, 3)
    if loc is not None:
        t = loc.wrapped.Transformation()
        m = np.array([[t.Value(i, j) for j in range(1, 5)] for i in range(1, 4)])
        points = points @ m[:, :3].T + m[:, 3]
    faces = np.hstack([[3, *t] for t in tris]) if tris else np.empty(0, dtype=int)
    return pv.PolyData(points, faces)


def render_views(shape: Shape, path: Path, title: str = "", size: int = 700) -> None:
    """Render a 2x2 grid (iso/top/front/side) to a PNG. Compound children get distinct colors."""
    bb = shape.bounding_box()
    tolerance = max(bb.diagonal / 2000, 0.01)
    by_color: dict[tuple | str, list[pv.PolyData]] = {}
    for i, (leaf, loc, leaf_color) in enumerate(_leaves(shape)):
        mesh = _to_polydata(leaf, tolerance, loc)
        if mesh.n_points == 0:
            continue
        color = PALETTE[i % len(PALETTE)] if leaf_color is None else tuple(round(c, 3) for c in tuple(leaf_color)[:3])
        by_color.setdefault(color, []).append(mesh)
    # One mesh per color keeps assemblies with hundreds of vendor parts fast to draw
    meshes = [(pv.merge(group) if len(group) > 1 else group[0], color) for color, group in by_color.items()]

    center = np.array([bb.center().X, bb.center().Y, bb.center().Z])
    corners = np.array([(x, y, z) for x in (bb.min.X, bb.max.X) for y in (bb.min.Y, bb.max.Y) for z in (bb.min.Z, bb.max.Z)])
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
        d /= np.linalg.norm(d)
        pl.camera.focal_point = center
        pl.camera.position = center + d * bb.diagonal * 3
        pl.camera.up = up
        pl.camera.parallel_projection = True
        pl.reset_camera()
        # Fit the projected bounding box; VTK fits the bounding sphere, which crops long thin parts
        right = np.cross(up, d)
        right /= np.linalg.norm(right)
        true_up = np.cross(d, right)
        extent = corners - center
        half_width = np.abs(extent @ right).max()
        half_height = np.abs(extent @ true_up).max()
        pl.camera.parallel_scale = 1.1 * max(half_width, half_height)
    pl.screenshot(str(path))
    pl.close()
