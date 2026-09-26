"""Waveshare RS485 CAN HAT, from the team's vendor STEP (board revision still to be checked).

Frame: PCB bottom at Z=0, component side up, origin at the PCB center, female GPIO header on the -Y edge (underneath).
ON_PI places it on components.raspberry_pi; only its two header-side holes line up with the Pi's.
"""

from build123d import Compound, Pos, Rot

from components import raspberry_pi as rp
from sslcad import build, instance, load_step

STEP = "mechanics/components/waveshare-rs485-can-hat"

PCB_SIZE = (65.0, 30.0)  # STEP
PCB_THICKNESS = 1.6  # STEP
MOUNT_HOLE_DIAMETER = 3.0  # STEP
MOUNT_HOLES = [(x, y) for x in (-29.0, 29.0) for y in (-11.5, 11.5)]  # STEP, 3.5 mm from the edges
HEADER_CENTER = (0.0, -11.5)  # STEP, 3.5 mm from the -Y edge
FEMALE_HEADER_HEIGHT = 8.5  # STEP, body below the PCB

STEP_TO_FRAME = Pos(-PCB_SIZE[0] / 2, -PCB_SIZE[1] / 2, PCB_THICKNESS)

# Female header seated on the Pi header's plastic base
STANDOFF = rp.HEADER_BASE_HEIGHT + FEMALE_HEADER_HEIGHT  # Pi PCB top to HAT PCB bottom
ON_PI = Pos(
    rp.HEADER_CENTER[0] + HEADER_CENTER[0],
    rp.HEADER_CENTER[1] + HEADER_CENTER[1],
    rp.PCB_THICKNESS + STANDOFF,
) * Rot(Z=180)


def can_hat() -> Compound:
    hat = instance(load_step(STEP), STEP_TO_FRAME)
    hat.label = "can_hat"
    return hat


def pi_stack() -> Compound:
    """Raspberry Pi with the CAN HAT on top, in the Pi's frame."""
    hat = instance(can_hat(), ON_PI)
    return Compound(label="pi_stack", children=[rp.raspberry_pi(), hat])


if __name__ == "__main__":
    hat = can_hat()
    assert hat.is_valid
    bb = hat.bounding_box()
    assert abs(bb.min.Z + FEMALE_HEADER_HEIGHT) < 0.01

    holes_on_pi = [(ON_PI * Pos(x, y)).position for x, y in MOUNT_HOLES]
    shared = [h for h in holes_on_pi if any(abs(h.X - x) < 0.01 and abs(h.Y - y) < 0.01 for x, y in rp.MOUNT_HOLES)]
    assert len(shared) == 2, f"expected 2 shared mounting holes, got {shared}"

    build(hat, "can_hat", export=False)
    build(pi_stack(), "pi_stack", export=False)
