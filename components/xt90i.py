"""XT90I connector (two power contacts plus two signal pins), from the vendor drawing in reference/xt90i, without the rubber boot.

Frame: mating axis along Z, origin on the axis at the housing's rear face, mating face toward +Z and the solder cups toward -Z.
The power contacts lie along X; the cups are half cylinders with their flat faces on the Y=0 plane and their solid half toward +Y.
The drawing only gives the section along the contacts; the thickness and the cups are estimated from the product photos.
ON_ESC mounts it on components.esc, with the cups' flat faces soldered onto the battery pads.
"""

from build123d import Align, Box, Color, Compound, Cylinder, Pos, RectangleRounded, Rot, extrude

from components import esc as e
from sslcad import build, instance

HOUSING_HEIGHT = 22.56  # drawing, along the contacts
HOUSING_THICKNESS = 11.7  # assumed, the male shroud's walls equal on all sides
CORNER_RADIUS = 1.5  # photo

FEMALE_LENGTH = 29.7  # drawing, cup ends to mating face
FEMALE_HOUSING_LENGTH = 25.2  # drawing
FEMALE_SKIRT_LENGTH = 11.7  # drawing, full-section rear part; the rest goes into the male shroud
FEMALE_INSERT = (19.3, 8.4)  # drawing
FEMALE_CONTACT_SPACING = 10.9  # drawing

MALE_LENGTH = 30.7  # drawing, cup ends to mating face
MALE_CAVITY = (19.6, 8.7)  # drawing
MALE_CONTACT_SPACING = 11.0  # drawing
MALE_PIN_DIAMETER = 4.5  # assumed, XT90 bullet

CUP_LENGTH = FEMALE_LENGTH - FEMALE_HOUSING_LENGTH
CUP_DIAMETER = 5.0  # photo
MALE_HOUSING_LENGTH = MALE_LENGTH - CUP_LENGTH
MALE_CAVITY_DEPTH = FEMALE_HOUSING_LENGTH - FEMALE_SKIRT_LENGTH

# The ESC is the load, so it gets the male side
ON_ESC = Pos(0, -e.ESC_SIZE[1] / 2, e.PCB_THICKNESS) * Rot(X=90)


def _block(size: tuple[float, float], length: float, radius: float = CORNER_RADIUS):
    return extrude(RectangleRounded(*size, radius), length)


def xt90i(male: bool = True) -> Compound:
    if male:
        housing = _block((HOUSING_HEIGHT, HOUSING_THICKNESS), MALE_HOUSING_LENGTH)
        housing -= Pos(Z=MALE_HOUSING_LENGTH - MALE_CAVITY_DEPTH) * _block(MALE_CAVITY, MALE_CAVITY_DEPTH, 1.0)
        spacing = MALE_CONTACT_SPACING
    else:
        housing = _block((HOUSING_HEIGHT, HOUSING_THICKNESS), FEMALE_SKIRT_LENGTH)
        housing += Pos(Z=FEMALE_SKIRT_LENGTH) * _block(FEMALE_INSERT, FEMALE_HOUSING_LENGTH - FEMALE_SKIRT_LENGTH, 1.0)
        spacing = FEMALE_CONTACT_SPACING
    housing.label, housing.color = "housing", Color(0.95, 0.75, 0.1)

    half = Cylinder(CUP_DIAMETER / 2, CUP_LENGTH, align=(Align.CENTER, Align.CENTER, Align.MAX)) & Box(
        CUP_DIAMETER, CUP_DIAMETER / 2, CUP_LENGTH, align=(Align.CENTER, Align.MIN, Align.MAX)
    )
    contacts = []
    for x in (-spacing / 2, spacing / 2):
        contact = Pos(X=x) * half
        if male:
            pin_base = MALE_HOUSING_LENGTH - MALE_CAVITY_DEPTH
            contact += Pos(x, 0, pin_base) * Cylinder(
                MALE_PIN_DIAMETER / 2, MALE_CAVITY_DEPTH - 1, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )
        contacts.append(contact)
    contact = contacts[0] + contacts[1]
    contact.label, contact.color = "contacts", Color(0.85, 0.65, 0.25)
    return Compound(label="xt90i_male" if male else "xt90i_female", children=[housing, contact])


def esc_with_xt90i(with_stlink: bool = True) -> Compound:
    """ESC with its male XT90I, in the ESC's frame."""
    return Compound(label="esc_with_xt90i", children=[e.esc(with_stlink), instance(xt90i(), ON_ESC)])


if __name__ == "__main__":
    for male, length in ((True, MALE_LENGTH), (False, FEMALE_LENGTH)):
        c = xt90i(male)
        assert all(child.is_valid for child in c.children)
        bb = c.bounding_box()
        assert abs(bb.size.Z - length) < 1e-6 and abs(bb.size.X - HOUSING_HEIGHT) < 1e-6
        build(c, c.label, export=False)

    connector = instance(xt90i(), ON_ESC)
    cups = connector.children[1]
    for x, y in e.POWER_PADS:
        pad = Pos(x, y, e.PCB_THICKNESS) * Box(*e.POWER_PAD_SIZE, 0.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
        assert (overlap := instance(cups, connector.location) & pad) is not None and overlap.volume > 0.1, f"no cup on the pad at {x}"
    board = e.esc()
    for part in board.children:
        placed = instance(part, board.location)
        for child in connector.children:
            clash = instance(child, connector.location) & placed
            assert clash is None or clash.volume < 1e-3, f"{child.label} hits {part.label}"
    build(esc_with_xt90i(), "esc_with_xt90i", export=False)
