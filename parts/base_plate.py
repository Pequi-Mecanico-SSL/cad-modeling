"""Example chassis base plate: round plate with a front dribbler flat, four wheel slots and mounting holes.

Frame: plate centered on the Z axis, bottom face at Z=0, robot front along +X.
Dimensions are placeholders; replace them with the real design values.
"""

import math

from build123d import (
    BuildPart,
    BuildSketch,
    Circle,
    Locations,
    Mode,
    Part,
    Pos,
    Rectangle,
    Rot,
    extrude,
    fillet,
)

from sslcad import ROBOT_MAX_DIAMETER, build

# Plate
PLATE_DIAMETER = ROBOT_MAX_DIAMETER - 2  # margin so the shell can sit outside the plate
THICKNESS = 3.0
FRONT_FLAT_WIDTH = 76.0  # chord width of the dribbler opening
CORNER_RADIUS = 2.0

# Wheels (50 mm omni wheels)
WHEEL_ANGLES = (60.0, 135.0, -135.0, -60.0)  # degrees from +X
WHEEL_DIAMETER = 50.0
WHEEL_WIDTH = 12.0
# Outer rim corners of the wheel touch the plate circle
WHEEL_CENTER_RADIUS = math.sqrt((PLATE_DIAMETER / 2) ** 2 - (WHEEL_DIAMETER / 2) ** 2) - WHEEL_WIDTH / 2
WHEEL_CLEARANCE = 2.0

# Holes
M3_CLEARANCE = 3.4
MOTOR_MOUNT_SPACING = 30.0  # tangential distance between a motor bracket's two holes
MOTOR_MOUNT_INSET = 8.0  # radial distance from the wheel slot to the bracket holes
STANDOFF_SQUARE = 50.0  # side of the square of central standoff holes

R = PLATE_DIAMETER / 2
SLOT_INNER_RADIUS = WHEEL_CENTER_RADIUS - WHEEL_WIDTH / 2 - WHEEL_CLEARANCE


def _polar(radius: float, angle_deg: float, tangential: float = 0.0) -> tuple[float, float]:
    a = math.radians(angle_deg)
    return (
        radius * math.cos(a) - tangential * math.sin(a),
        radius * math.sin(a) + tangential * math.cos(a),
    )


def hole_positions() -> list[tuple[float, float]]:
    mount_r = SLOT_INNER_RADIUS - MOTOR_MOUNT_INSET
    motor = [
        _polar(mount_r, a, t)
        for a in WHEEL_ANGLES
        for t in (-MOTOR_MOUNT_SPACING / 2, MOTOR_MOUNT_SPACING / 2)
    ]
    s = STANDOFF_SQUARE / 2
    standoffs = [(x, y) for x in (-s, s) for y in (-s, s)]
    return motor + standoffs


def base_plate() -> Part:
    front_flat_x = math.sqrt(R**2 - (FRONT_FLAT_WIDTH / 2) ** 2)
    slot_len = R - SLOT_INNER_RADIUS + 5  # radial, runs past the rim
    slot_width = WHEEL_DIAMETER + 2 * WHEEL_CLEARANCE  # tangential

    with BuildPart() as plate:
        with BuildSketch() as outline:
            Circle(R)
            with Locations((front_flat_x + R, 0)):
                Rectangle(2 * R, 2 * R, mode=Mode.SUBTRACT)
            for angle in WHEEL_ANGLES:
                with Locations(Rot(Z=angle) * Pos(X=SLOT_INNER_RADIUS + slot_len / 2)):
                    Rectangle(slot_len, slot_width, mode=Mode.SUBTRACT)
            fillet(outline.vertices(), CORNER_RADIUS)
            with Locations(*hole_positions()):
                Circle(M3_CLEARANCE / 2, mode=Mode.SUBTRACT)
        extrude(amount=THICKNESS)
    return plate.part


if __name__ == "__main__":
    part = base_plate()
    part.label = "base_plate"
    assert part.is_valid
    assert len(part.solids()) == 1
    build(part, "base_plate")
