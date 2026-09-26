"""Cheap placement of shapes that share geometry."""

from build123d import Compound, Location, Shape
from build123d.topology.shape_core import downcast


def instance(shape: Shape, loc: Location | None = None) -> Shape:
    """Copy of `shape`, optionally moved by `loc`, that shares its OCC geometry and keeps labels/colors.

    Prefer it over `loc * shape` for vendor models: that deep-copies all the geometry, and for a
    child of an assembly also the whole tree it belongs to.
    """
    if isinstance(shape, Compound) and shape.children:
        new = Compound(children=[instance(child) for child in shape.children])
        new.wrapped = shape.wrapped  # attaching children resets the root location
    else:
        new = shape.__class__(shape.wrapped)
    if loc is not None:
        new.wrapped = downcast(new.wrapped.Moved(loc.wrapped))
    new.label, new.color = shape.label, shape.color
    return new
