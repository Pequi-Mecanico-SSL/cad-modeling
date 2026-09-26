"""Pololu MinIMU-9 v5 (LSM6DS33 + LIS3MDL), from the team's vendor STEP.

Frame: PCB bottom at Z=0, component side up, origin at the PCB center, pin row along the -X edge.
"""

from build123d import Compound, Pos

from sslcad import build, instance, load_step

STEP = "mechanics/components/pololu-minimu-9-v5"

PCB_SIZE = (20.32, 12.7)  # STEP, 0.8 x 0.5 in
PCB_THICKNESS = 1.02  # STEP
MOUNT_HOLE = (7.62, 3.81)  # STEP
MOUNT_HOLE_DIAMETER = 2.18  # STEP, for #2 or M2 screws
PIN_ROW_X = -8.89  # STEP, 5 pins at 2.54 mm pitch plus one inboard

STEP_TO_FRAME = Pos(-PCB_SIZE[0] / 2, -PCB_SIZE[1] / 2)


def imu() -> Compound:
    part = instance(load_step(STEP), STEP_TO_FRAME)
    part.label = "imu"
    return part


if __name__ == "__main__":
    part = imu()
    assert part.is_valid
    bb = part.bounding_box()
    assert abs(bb.size.X - PCB_SIZE[0]) < 0.01 and abs(bb.min.Z) < 0.01
    build(part, "imu", export=False)
