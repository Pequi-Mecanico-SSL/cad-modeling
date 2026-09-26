"""Raspberry Pi 4 Model B, from the team's vendor STEP.

Frame: PCB bottom at Z=0, component side up, origin at the PCB center, laid out as in
imports/mechanics/references/raspberry-pi-4-model-b-dimensions.pdf: USB/Ethernet toward +X, GPIO header along +Y.
"""

from build123d import Align, Compound, Cylinder, Pos, Rot

from sslcad import build, instance, load_step

STEP = "mechanics/components/raspberry-pi-4-model-b"

PCB_SIZE = (85.0, 56.0)  # drawing
PCB_THICKNESS = 1.6  # STEP
CORNER_RADIUS = 3.0  # drawing
MOUNT_HOLE_DIAMETER = 2.7  # drawing, M2.5
MOUNT_PAD_DIAMETER = 6.0  # drawing, component-free ring for standoffs
HEADER_BASE_HEIGHT = 2.5  # STEP, plastic base of the GPIO header above the PCB top
HEADER_PIN_HEIGHT = 8.5  # drawing, above the PCB top
PORTS_OVERHANG = 4.0  # STEP, USB/Ethernet reach past the +X edge

# The vendor model lies in its XZ plane with the component side facing +Y
STEP_TO_FRAME = Pos(Z=PCB_THICKNESS / 2) * Rot(X=90)


def _from_corner(x: float, y: float) -> tuple[float, float]:
    """Drawing coordinates (from the lower-left PCB corner) to this frame."""
    return (x - PCB_SIZE[0] / 2, y - PCB_SIZE[1] / 2)


MOUNT_HOLES = [_from_corner(x, y) for x in (3.5, 61.5) for y in (3.5, 52.5)]  # drawing
HEADER_CENTER = _from_corner(32.5, 52.5)  # drawing, 2x20 GPIO


def raspberry_pi() -> Compound:
    pi = instance(load_step(STEP), STEP_TO_FRAME)
    pi.label = "raspberry_pi"
    return pi


if __name__ == "__main__":
    pi = raspberry_pi()
    assert pi.is_valid
    bb = pi.bounding_box()
    assert abs(bb.min.X + PCB_SIZE[0] / 2) < 0.01 and abs(bb.max.Y - PCB_SIZE[1] / 2) < 0.01
    assert abs(bb.max.X - PCB_SIZE[0] / 2 - PORTS_OVERHANG) < 0.5
    pcb = instance(next(c for c in load_step(STEP).children if c.label.startswith("PCB")), STEP_TO_FRAME)
    for x, y in MOUNT_HOLES:
        probe = Pos(x, y, 0) * Cylinder(MOUNT_HOLE_DIAMETER / 2 - 0.05, PCB_THICKNESS, align=(Align.CENTER, Align.CENTER, Align.MIN))
        assert (clash := pcb & probe) is None or clash.volume < 1e-3, f"mounting hole at ({x}, {y}) is not clear"
    build(pi, "raspberry_pi", export=False)
