"""RoboCup SSL robot size rules. Units are mm, robot centered on the Z axis with the floor at Z=0."""

from build123d import Align, Cylinder, Shape

ROBOT_MAX_DIAMETER = 180.0
ROBOT_MAX_HEIGHT = 150.0


def check_robot_envelope(shape: Shape, tol: float = 1e-3) -> None:
    """Raise if any material lies outside the 180 mm x 150 mm robot cylinder."""
    envelope = Cylinder(
        ROBOT_MAX_DIAMETER / 2, ROBOT_MAX_HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    outside = shape - envelope
    if outside.volume > tol:
        bb = outside.bounding_box()
        raise ValueError(
            f"{outside.volume:.2f} mm^3 outside the robot envelope, "
            f"between ({bb.min.X:.1f}, {bb.min.Y:.1f}, {bb.min.Z:.1f}) "
            f"and ({bb.max.X:.1f}, {bb.max.Y:.1f}, {bb.max.Z:.1f})"
        )
