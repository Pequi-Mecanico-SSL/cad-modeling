"""GTF Robots 50 mm omni wheel v4, from the team's vendor STEP.

Frame: axis along Z, origin at the wheel center on the mid-plane of the roller ring, hub boss toward -Z.
The brand/revision still has to be checked against the real wheel. The kinematics code uses an effective
radius of 24.5 mm; keep that calibration independent of this model.
"""

import math

from build123d import Align, Compound, Cylinder, Pos

from sslcad import build, instance, load_step

STEP = "mechanics/components/gtf-omniwheel-50mm-v4"
STEP_CENTER = (50.0, 40.0)  # wheel axis in the vendor model's frame
STEP_BORE_DIAMETER = 8.0  # STEP

OUTER_RADIUS = 24.25  # STEP, over the rollers
ROLLER_DIAMETER = 6.5  # STEP, sets the tread width
DISC_THICKNESS = 4.0  # STEP, the two side plates holding the rollers
BORE_DIAMETER = 4.0  # measured, fits the motor shaft directly
BORE_TOP = 4.0  # STEP, the bore runs from the hub end up to here
HUB_LENGTH = 8.0  # STEP, boss reach toward -Z from the mid-plane
TOP_REACH = 4.25  # STEP, highest point toward +Z from the mid-plane


def omni_wheel() -> Compound:
    raw = load_step(STEP)
    # The real wheel has a smaller bore than the STEP; fill the difference
    bore_length = BORE_TOP + HUB_LENGTH
    sleeve = Cylinder(STEP_BORE_DIAMETER / 2, bore_length, align=(Align.CENTER, Align.CENTER, Align.MIN)) - Cylinder(
        BORE_DIAMETER / 2, bore_length, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    sleeve = Pos(*STEP_CENTER, -HUB_LENGTH) * sleeve
    wheel = instance(Compound([*raw.solids(), *sleeve.solids()]), Pos(-STEP_CENTER[0], -STEP_CENTER[1]))
    wheel.label = "omni_wheel"
    return wheel


if __name__ == "__main__":
    wheel = omni_wheel()
    assert wheel.is_valid
    bb = wheel.bounding_box()
    assert abs(bb.max.Y - OUTER_RADIUS) < 0.05 and abs(bb.min.Y + OUTER_RADIUS) < 0.05
    assert abs(bb.min.Z + HUB_LENGTH) < 0.05 and abs(bb.max.Z - TOP_REACH) < 0.05
    shaft = Pos(Z=-HUB_LENGTH) * Cylinder(BORE_DIAMETER / 2 - 0.05, HUB_LENGTH + BORE_TOP, align=(Align.CENTER, Align.CENTER, Align.MIN))
    assert (clash := wheel & shaft) is None or clash.volume < 1e-3, "the bore must be clear"
    snug = Pos(Z=-HUB_LENGTH) * Cylinder(BORE_DIAMETER / 2 + 0.05, HUB_LENGTH + BORE_TOP, align=(Align.CENTER, Align.CENTER, Align.MIN))
    wall = math.pi * ((BORE_DIAMETER / 2 + 0.05) ** 2 - (BORE_DIAMETER / 2) ** 2) * (HUB_LENGTH + BORE_TOP)
    assert abs((wheel & snug).volume - wall) < 0.01 * wall, f"the bore must be {BORE_DIAMETER} mm"
    build(wheel, "omni_wheel", export=False)
