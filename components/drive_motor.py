"""Nanotec DF45L024048-A flat BLDC drive motor (one per wheel), from the team's vendor STEP.

Frame: shaft along +Z, origin on the axis at the flange front face, body toward -Z, connector PCB tab toward -Y.
Dimensions come from reference/drive_motor/DF45L024048-A2-datasheet.pdf (the cable variant; same flange and body)
and match the STEP.
"""

import math

from build123d import Compound, Pos

from sslcad import build, instance, load_step

STEP = "mechanics/components/nanotec-df45l024048-a"
STEP_FLANGE_FACE_Z = 4.0  # flange front face in the vendor model's frame

FLANGE_DIAMETER = 43.2  # datasheet
FLANGE_THICKNESS = 4.0  # datasheet
BODY_DIAMETER = 42.8  # datasheet, max
BODY_LENGTH = 27.0  # datasheet, flange front face to back of the rotor bell
PILOT_DIAMETER = 16.0  # datasheet, centering boss on the flange face
PILOT_HEIGHT = 3.2  # datasheet
SHAFT_DIAMETER = 4.0  # datasheet
SHAFT_LENGTH = 20.6  # datasheet, from the flange front face
MOUNT_HOLE_CIRCLE = 22.0  # datasheet, 3x M3 depth 3 min
MOUNT_HOLE_ANGLES = (90.0, 210.0, 330.0)  # degrees from +X; the first one is opposite the connector tab
MOUNT_HOLE_DEPTH = 3.0
TAB_EXTENT = 40.5  # STEP, connector PCB reach toward -Y from the axis


def mount_holes() -> list[tuple[float, float]]:
    r = MOUNT_HOLE_CIRCLE / 2
    return [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in MOUNT_HOLE_ANGLES]


def drive_motor() -> Compound:
    motor = instance(load_step(STEP), Pos(Z=-STEP_FLANGE_FACE_Z))
    motor.label = "drive_motor"
    return motor


if __name__ == "__main__":
    motor = drive_motor()
    assert motor.is_valid
    bb = motor.bounding_box()
    assert abs(bb.min.Z + BODY_LENGTH) < 0.05 and abs(bb.max.Z - SHAFT_LENGTH) < 0.05
    assert abs(bb.size.X - FLANGE_DIAMETER) < 0.05 and abs(bb.min.Y + TAB_EXTENT) < 0.05
    build(motor, "drive_motor", export=False)
