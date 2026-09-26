"""Export, render and import helpers."""

import sys
from functools import cache
from pathlib import Path

from build123d import Compound, Shape, export_step, export_stl, import_step

from sslcad.render import render_views

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "out"
IMPORTS_DIR = ROOT / "imports"


@cache
def load_step(name: str) -> Shape:
    """Load a vendor/third-party STEP file from imports/ (extension optional).

    Cached and shared between callers: place copies with `loc * shape` instead of mutating the result.
    """
    path = IMPORTS_DIR / name
    if not path.suffix:
        path = path.with_suffix(".step")
    return import_step(path)


def build(shape: Shape, name: str, render: bool = True, export: bool = True) -> Path:
    """Print a geometry summary and write out/<name>/<name>.png, plus .step/.stl when `export` is set.

    Vendor models pass export=False: their STEP already exists and their fine STL is huge.
    Pass --show on the command line to also send the shape to a running ocp_vscode viewer.
    """
    out = OUT_DIR / name
    out.mkdir(parents=True, exist_ok=True)

    bb = shape.bounding_box()
    print(f"[{name}]")
    print(f"  bbox min  ({bb.min.X:.2f}, {bb.min.Y:.2f}, {bb.min.Z:.2f})")
    print(f"  bbox max  ({bb.max.X:.2f}, {bb.max.Y:.2f}, {bb.max.Z:.2f})")
    print(f"  size      {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm")
    print(f"  volume    {shape.volume:.1f} mm^3")
    solids = shape.solids()
    print(f"  solids {len(solids)}  faces {len(shape.faces())}  edges {len(shape.edges())}")
    if isinstance(shape, Compound) and shape.children:
        for child in shape.children:
            print(f"    - {child.label or '(unlabeled)'}: {child.volume:.1f} mm^3")
    print(f"  -> {out.relative_to(ROOT)}/", flush=True)

    # Render before the STL export: OCC keeps the finest mesh on the faces and would reuse it for the render
    if render:
        render_views(shape, out / f"{name}.png", title=name)
    if export:
        export_step(shape, out / f"{name}.step")
        export_stl(shape, out / f"{name}.stl", tolerance=0.01, angular_tolerance=0.1)

    if "--show" in sys.argv:
        from ocp_vscode import show

        show(shape)
    return out
