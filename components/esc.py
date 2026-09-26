"""ST B-G431B-ESC1 motor controller (one per motor), from the team's vendor STEP.

Frame: PCB bottom at Z=0, component side up, origin at the center of the ESC section.
The detachable ST-LINK strip (USB, potentiometer, button) is on the -X side and the motor phase pads on the +Y edge.
The board has no mounting holes.
"""

from build123d import Align, Box, Compound, Pos

from sslcad import build, instance, load_step

STEP = "mechanics/components/st-b-g431b-esc1"

PCB_THICKNESS = 1.56  # STEP
ESC_SIZE = (17.75, 41.0)  # STEP, without the ST-LINK strip
STLINK_WIDTH = 12.25  # STEP, detachable strip on the -X side
BREAK_GAP = 1.0  # STEP, slotted gap between the strip and the ESC

STEP_ESC_MIN_X = STLINK_WIDTH + BREAK_GAP
STEP_BREAK_X = STLINK_WIDTH + BREAK_GAP / 2
STEP_TO_FRAME = Pos(-(STEP_ESC_MIN_X + ESC_SIZE[0] / 2), -ESC_SIZE[1] / 2, PCB_THICKNESS)


def esc(with_stlink: bool = True) -> Compound:
    raw = load_step(STEP)
    if with_stlink:
        shape = instance(raw, STEP_TO_FRAME)
    else:
        keep = Pos(X=STEP_BREAK_X) * Box(100, 100, 100, align=(Align.MIN, Align.CENTER, Align.CENTER))
        children = []
        for child in raw.children:
            if child.bounding_box().max.X < STEP_BREAK_X:
                continue
            part = instance(child)
            if part.bounding_box().min.X < STEP_BREAK_X:
                part = part & keep
                part.label, part.color = child.label, child.leaves[0].color
            children.append(part)
        shape = instance(Compound(children=children), STEP_TO_FRAME)
    shape.label = "esc"
    return shape


if __name__ == "__main__":
    for with_stlink in (True, False):
        e = esc(with_stlink)
        assert e.is_valid
        bb = e.bounding_box()
        print(f"with_stlink={with_stlink}: {bb.size.X:.2f} x {bb.size.Y:.2f}, Z {bb.min.Z:.2f}..{bb.max.Z:.2f}")
    # The cut runs through the middle of the break gap
    assert abs(bb.max.X - ESC_SIZE[0] / 2) < 0.01 and abs(bb.min.X + ESC_SIZE[0] / 2 + BREAK_GAP / 2) < 0.01
    build(esc(), "esc", export=False)
    build(esc(with_stlink=False), "esc_without_stlink", export=False)
