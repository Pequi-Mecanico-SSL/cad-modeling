"""Power distribution board: 50x50 mm PCB, 8 female XT60 (2 per edge), 4 PTC fuses on the bottom side.

Frame: PCB centered on the Z axis, bottom face (fuse side) at Z=0, silkscreen side up.
+X/+Y match reference/power_distribution/top.jpg as seen (right/up); the rivet is on the +X side.
Values marked "photo" are estimated from the reference photos (~±0.5 mm); "measured" ones come from calipers.
"""

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Compound,
    Cylinder,
    Locations,
    Mode,
    Part,
    Pos,
    Rectangle,
    Rot,
    extrude,
    fillet,
)

from sslcad import build

# PCB
PCB_SIZE = 50.0  # photo
PCB_THICKNESS = 1.6  # measured
PCB_CORNER_RADIUS = 2.0  # photo
CENTER_HOLE_DIAMETER = 16.0  # photo
OUTER_HOLE_SPACING = 45.0  # photo, confirmed; square pattern
INNER_HOLE_SPACING = 35.0  # photo, confirmed; square pattern, plated
MOUNT_HOLE_DIAMETER = 3.0  # photo, confirmed
AUX_HOLE = (15.1, -12.3)  # photo, plated
AUX_HOLE_DIAMETER = 3.2  # photo
RIVET = (15.1, -4.3)  # photo
RIVET_HEAD_DIAMETER = 4.5  # photo
RIVET_HEAD_HEIGHT = 1.5  # assumed

# XT60 female, lying flat with the mating face pointing outward
XT60_PAIR_WIDTH = 31.5  # measured, both connectors of one edge side by side
XT60_WIDTH = XT60_PAIR_WIDTH / 2
XT60_HEIGHT = 7.9  # measured
XT60_PROTRUSION = 18.0  # photo, from PCB edge to mating face
XT60_PIN_SPACING = 7.2
XT60_CUP_DIAMETER = 4.5
XT60_CUP_LENGTH = 7.0  # photo, overlap onto the PCB pads
XT60_EDGE_OFFSETS = (-XT60_WIDTH / 2, XT60_WIDTH / 2)  # touching pair centered on each edge
XT60_AXIS_Z = XT60_HEIGHT / 2  # connector bottoms flush with the PCB bottom
XT60_MATING_CLEARANCE = 35.0  # male plug body plus cable bend radius

# PTC resettable fuses (XF250), discs lying on the bottom side; one corner has two stacked
FUSE_DIAMETER = 20.5  # photo
FUSE_DEPTHS = (4.1 - PCB_THICKNESS, 7.2 - PCB_THICKNESS)  # measured, lowest point of layer 1/2 below the PCB
FUSE_THICKNESS = 2.2  # photo
FUSE_OFFSET = 15.7  # photo, disc centers at (±, ±)
FUSE_STACK_CORNER = (1, -1)  # confirmed: the quadrant with AUX_HOLE


def _square(spacing: float) -> list[tuple[float, float]]:
    s = spacing / 2
    return [(x, y) for x in (-s, s) for y in (-s, s)]


def pcb() -> Part:
    with BuildPart() as part:
        with BuildSketch() as sk:
            Rectangle(PCB_SIZE, PCB_SIZE)
            fillet(sk.vertices(), PCB_CORNER_RADIUS)
            Circle(CENTER_HOLE_DIAMETER / 2, mode=Mode.SUBTRACT)
            with Locations(*_square(OUTER_HOLE_SPACING), *_square(INNER_HOLE_SPACING)):
                Circle(MOUNT_HOLE_DIAMETER / 2, mode=Mode.SUBTRACT)
            with Locations(AUX_HOLE):
                Circle(AUX_HOLE_DIAMETER / 2, mode=Mode.SUBTRACT)
        extrude(amount=PCB_THICKNESS)
        with Locations(Pos(*RIVET, PCB_THICKNESS)):
            Cylinder(RIVET_HEAD_DIAMETER / 2, RIVET_HEAD_HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return part.part


def xt60() -> Part:
    """Connector along +X: mating face at X=XT60_PROTRUSION, solder cups over X<0, pin axis at Z=0."""
    body = Box(XT60_PROTRUSION, XT60_WIDTH, XT60_HEIGHT, align=(Align.MIN, Align.CENTER, Align.CENTER))
    for y in (-XT60_PIN_SPACING / 2, XT60_PIN_SPACING / 2):
        body += Pos(-XT60_CUP_LENGTH, y, 0) * Rot(Y=90) * Cylinder(
            XT60_CUP_DIAMETER / 2, XT60_CUP_LENGTH, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
    return body


def _edge_placements():
    for angle in (0, 90, 180, 270):
        for offset in XT60_EDGE_OFFSETS:
            yield angle, Rot(Z=angle) * Pos(PCB_SIZE / 2, offset, XT60_AXIS_Z)


def mating_keepouts() -> list[Part]:
    """Space in front of each connector for the male plug and its cable."""
    box = Box(XT60_MATING_CLEARANCE, XT60_WIDTH, XT60_HEIGHT, align=(Align.MIN, Align.CENTER, Align.CENTER))
    return [loc * Pos(X=XT60_PROTRUSION) * box for _, loc in _edge_placements()]


def power_distribution() -> Compound:
    board = pcb()
    board.label, board.color = "pcb", Color(0.1, 0.2, 0.6)
    children = [board]

    for i, (_, loc) in enumerate(_edge_placements()):
        conn = loc * xt60()
        conn.label, conn.color = f"xt60_{i}", Color(0.9, 0.78, 0.45)
        children.append(conn)

    sx, sy = FUSE_STACK_CORNER
    discs = [(x, y, FUSE_DEPTHS[0]) for x, y in _square(2 * FUSE_OFFSET)]
    discs.append((sx * FUSE_OFFSET, sy * FUSE_OFFSET, FUSE_DEPTHS[1]))
    for i, (x, y, depth) in enumerate(discs):
        fuse = Pos(x, y, -depth) * Cylinder(
            FUSE_DIAMETER / 2, FUSE_THICKNESS, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        fuse.label, fuse.color = f"fuse_{i}", Color(0.85, 0.65, 0.2)
        children.append(fuse)

    return Compound(label="power_distribution", children=children)


if __name__ == "__main__":
    assembly = power_distribution()
    assert all(c.is_valid for c in assembly.children)
    assert len(assembly.children) == 1 + 8 + 5
    # Overall height measured as 13.3 mm; the per-layer fuse measurements add up to 0.2 mm more
    assert abs(assembly.bounding_box().size.Z - 13.3) < 0.3
    build(assembly, "power_distribution")
