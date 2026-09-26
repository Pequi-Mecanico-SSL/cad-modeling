"""Robot assembly: base plate plus placeholder wheels, with envelope and interference checks.

Frame: floor at Z=0, robot centered on the Z axis, front along +X.
"""

from itertools import combinations

from build123d import Color, Compound, Cylinder, Part, Pos, Rot

from parts import base_plate as bp
from sslcad import build, check_robot_envelope

PLATE_Z = 8.0  # bottom of the base plate above the floor


def wheel_placeholder() -> Part:
    # Swap for the vendor model once available, e.g. load_step("omni_wheel_50")
    return Cylinder(bp.WHEEL_DIAMETER / 2, bp.WHEEL_WIDTH)


def robot() -> Compound:
    plate = Pos(Z=PLATE_Z) * bp.base_plate()
    plate.label, plate.color = "base_plate", Color(0.55, 0.6, 0.68)

    wheels = []
    for i, angle in enumerate(bp.WHEEL_ANGLES):
        # Axis along the radial direction, touching the floor
        wheel = (
            Rot(Z=angle)
            * Pos(X=bp.WHEEL_CENTER_RADIUS, Z=bp.WHEEL_DIAMETER / 2)
            * Rot(Y=90)
            * wheel_placeholder()
        )
        wheel.label, wheel.color = f"wheel_{i}", Color(0.25, 0.25, 0.25)
        wheels.append(wheel)

    return Compound(label="robot", children=[plate, *wheels])


def check_interference(assembly: Compound, tol: float = 1e-3) -> None:
    for a, b in combinations(assembly.children, 2):
        overlap = (a & b).volume
        if overlap > tol:
            raise ValueError(f"{a.label} and {b.label} overlap by {overlap:.2f} mm^3")


if __name__ == "__main__":
    assembly = robot()
    check_robot_envelope(assembly)
    check_interference(assembly)
    build(assembly, "robot")
