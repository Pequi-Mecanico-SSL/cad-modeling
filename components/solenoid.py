"""SOLETEC 018 solenoid, the kicker's, from imports/mechanics/references/candidates/soletec-018-solenoid-dimensions.pdf.

Frame: plunger axis along Z, origin on the axis at the frame face the plunger exits from, plunger toward -Z.
The U-frame back (mounting face) faces -X and the coil side +X.
The drawing shows the energized (retracted) position; the stroke is not given. The drawing is not to scale,
so values marked "drawing, scaled" are estimated from it.
"""

from build123d import Align, Box, Color, Compound, Cylinder, Pos, RegularPolygon, Rot, extrude

from sslcad import build

BODY_SIZE = (22.0, 15.0, 33.0)  # drawing; X back-to-coil, Y, Z along the axis
AXIS_FROM_BACK = 12.0  # drawing
MOUNT_HOLES = [(4.0, 26.5), (-4.0, 6.5)]  # drawing, (Y, Z) on the back face; 2x M3, diagonal
MOUNT_HOLE_DEPTH = 3.0  # assumed
MOUNT_TAP_DIAMETER = 2.5

TOTAL_LENGTH = 59.5  # drawing, ±1.0, rear rod end to plunger tip
PLUNGER_DIAMETER = 7.9  # drawing
PLUNGER_REACH = 14.5  # drawing, ±0.5, frame face to plunger tip
CLEVIS_SLOT = (3.0, 10.0)  # drawing, width x depth, through along X
CLEVIS_PIN_DIAMETER = 2.0  # drawing, cross hole along Y
CLEVIS_PIN_FROM_TIP = 4.0  # drawing
SPRING_DIAMETER = 14.0  # drawing, scaled; return spring plus retaining washer
SPRING_LENGTH = 9.0  # drawing, scaled
ROD_DIAMETER = 3.0  # drawing, M3 rear rod
ROD_REACH = TOTAL_LENGTH - BODY_SIZE[2] - PLUNGER_REACH
NUT_WIDTH = 5.5  # M3 nut across flats
NUT_THICKNESS = 2.4


def _down(radius: float, length: float) -> Cylinder:
    return Cylinder(radius, length, align=(Align.CENTER, Align.CENTER, Align.MAX))


def _up(radius: float, length: float) -> Cylinder:
    return Cylinder(radius, length, align=(Align.CENTER, Align.CENTER, Align.MIN))


def solenoid() -> Compound:
    body = Pos(X=-AXIS_FROM_BACK) * Box(*BODY_SIZE, align=(Align.MIN, Align.CENTER, Align.MIN))
    for y, z in MOUNT_HOLES:
        body -= Pos(-AXIS_FROM_BACK, y, z) * Rot(Y=90) * _up(MOUNT_TAP_DIAMETER / 2, MOUNT_HOLE_DEPTH)

    tip_z = -PLUNGER_REACH
    plunger = _down(PLUNGER_DIAMETER / 2, PLUNGER_REACH)
    plunger -= Pos(Z=tip_z) * Box(PLUNGER_DIAMETER, CLEVIS_SLOT[0], CLEVIS_SLOT[1], align=(Align.CENTER, Align.CENTER, Align.MIN))
    plunger -= Pos(Z=tip_z + CLEVIS_PIN_FROM_TIP) * Rot(X=90) * Cylinder(CLEVIS_PIN_DIAMETER / 2, PLUNGER_DIAMETER)

    spring = _down(SPRING_DIAMETER / 2, SPRING_LENGTH) - _down(PLUNGER_DIAMETER / 2, SPRING_LENGTH)

    top = BODY_SIZE[2]
    rod = Pos(Z=top) * _up(ROD_DIAMETER / 2, ROD_REACH)
    nut = extrude(RegularPolygon(NUT_WIDTH / 2, 6, major_radius=False), NUT_THICKNESS)
    rod += Pos(Z=top + ROD_REACH - 1 - NUT_THICKNESS) * nut

    children = []
    for part, label, color in (
        (body, "body", Color(0.35, 0.35, 0.38)),
        (plunger, "plunger", Color(0.75, 0.75, 0.78)),
        (spring, "spring", Color(0.55, 0.5, 0.4)),
        (rod, "rear_rod", Color(0.75, 0.75, 0.78)),
    ):
        part.label, part.color = label, color
        children.append(part)
    return Compound(label="solenoid", children=children)


if __name__ == "__main__":
    s = solenoid()
    assert all(c.is_valid for c in s.children)
    bb = s.bounding_box()
    assert abs(bb.size.Z - TOTAL_LENGTH) < 0.01
    assert abs(bb.size.X - BODY_SIZE[0]) < 0.01 and abs(bb.size.Y - BODY_SIZE[1]) < 0.01
    build(s, "solenoid")
