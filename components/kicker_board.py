"""ZJUNlict Booster Board 2019 (kicker charger), from the team's KiCad conversion in
imports/mechanics/references/kicker-board (see its README for the conversion notes), plus photos in reference/kicker_board.

Frame: PCB bottom at Z=0, component side up, origin at the center of the smallest circle enclosing the outline,
+Y toward the straight edge.
The conversion only has 3D models for L2, the XT60 and C19/C20; the tall parts (the two 200 V capacitors, soldered
upright into the CAP_IN connector footprints J1/J2, and the rocker switch) are added as envelopes from measurements and photos.
"""

import math

from build123d import Align, Axis, Box, Color, Compound, Cylinder, Plane, Pos, Rot, extrude

from sslcad import build, instance, load_step

STEP_BARE = "mechanics/references/kicker-board/zjunlict-booster-board-bare"
STEP_PARTIAL = "mechanics/references/kicker-board/zjunlict-booster-board-partial"
STEP_THICKNESS = 0.41116  # Altium's default 2-layer stackup, carried into the KiCad conversion
STEP_ORIGIN = (144.16, -89.25)  # enclosing circle center in the STEP frame


def _from_step(x: float, y: float) -> tuple[float, float]:
    return (x - STEP_ORIGIN[0], y - STEP_ORIGIN[1])


PCB_THICKNESS = 1.6  # measured
PCB_SIZE = (147.71, 129.09)  # STEP
OUTLINE_CIRCLE = 172.12  # STEP, smallest circle enclosing the outline
MOUNT_HOLE_DIAMETER = 3.5  # STEP
MOUNT_HOLES = [  # STEP; the pairs at the sides are plated, the pair on the straight edge is not
    _from_step(x, y)
    for x, y in [(74.28, -75.26), (213.09, -75.36), (77.84, -113.36), (209.54, -113.23), (129.18, -43.42), (159.18, -43.42)]
]

# 200 V 330 uF capacitors, upright on the J1/J2 pad midpoints
CAP_CENTERS = [_from_step(175.15, -122.96), _from_step(112.86, -121.89)]  # STEP
CAP_DIAMETER = 18.3  # measured
CAP_HEIGHT = 38.6  # measured, above the PCB top

# Rocker switch S1: stands on two spade terminals in the S1 holes, its body along the slanted edge next to them
# and sticking out past it
ROCKER_EDGE = ((75.197, -133.299), (112.127, -154.487))  # STEP, slanted outline edge
ROCKER_ALONG_EDGE = 34.0  # photo, body center distance from the edge's first point
ROCKER_OVERHANG = 10.0  # measured, past the edge
ROCKER_SIZE = (21.0, 15.0)  # photo, along and across the edge
ROCKER_HEIGHT = 15.0  # photo, above the PCB top

LABELS = {  # embedded model name -> reference designator
    "BC40324D60C2162098A4822548A51554": "L2",
    "4AC53AD4C5CF69C6F659C2ED0629CD60": "xt60",
    "6101E91A8FF9ED33B7338B80FA883BC6": "C19_C20",
}


def _step_parts() -> list:
    """Modeled parts, moved onto the real PCB thickness."""
    parts = []
    for child in load_step(STEP_PARTIAL).children:
        if child.label.endswith("_PCB"):
            continue
        label = LABELS[child.label.rsplit("_", 1)[-1]]
        if label == "C19_C20":
            label = "C19" if child.bounding_box().center().X < 80 else "C20"
        if label == "xt60":
            # The footprint is on the bottom layer, but the connector is soldered on the component side
            part = Pos(Z=PCB_THICKNESS) * instance(child).mirror(Plane.XY)
            part.color = Color(0.9, 0.75, 0.3)
        elif child.bounding_box().min.Z > STEP_THICKNESS / 2:
            part = instance(child, Pos(Z=PCB_THICKNESS - STEP_THICKNESS))
        else:
            part = instance(child)
        part.label = label
        parts.append(instance(part, Pos(-STEP_ORIGIN[0], -STEP_ORIGIN[1])))
    return parts


def _rocker_edge_angle() -> float:
    (x0, y0), (x1, y1) = ROCKER_EDGE
    return math.atan2(y1 - y0, x1 - x0)


def _rocker_center() -> tuple[float, float]:
    """Body center: ROCKER_ALONG_EDGE along the edge, then outward so the outer face overhangs by ROCKER_OVERHANG."""
    a = _rocker_edge_angle()
    out = ROCKER_OVERHANG - ROCKER_SIZE[1] / 2
    x0, y0 = ROCKER_EDGE[0]
    x = x0 + ROCKER_ALONG_EDGE * math.cos(a) + out * math.sin(a)
    y = y0 + ROCKER_ALONG_EDGE * math.sin(a) - out * math.cos(a)
    return _from_step(x, y)


def kicker_board() -> Compound:
    bottom = load_step(STEP_BARE).faces().sort_by(Axis.Z)[0]
    pcb = Pos(-STEP_ORIGIN[0], -STEP_ORIGIN[1]) * extrude(bottom, amount=PCB_THICKNESS, dir=(0, 0, 1))
    pcb.label, pcb.color = "pcb", Color(0.15, 0.3, 0.2)
    children = [pcb, *_step_parts()]

    for i, (x, y) in enumerate(CAP_CENTERS):
        cap = Pos(x, y, PCB_THICKNESS) * Cylinder(CAP_DIAMETER / 2, CAP_HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MIN))
        cap.label, cap.color = f"cap_{i}", Color(0.12, 0.12, 0.14)
        children.append(cap)

    rocker = Pos(*_rocker_center(), PCB_THICKNESS) * Rot(Z=math.degrees(_rocker_edge_angle())) * Box(
        *ROCKER_SIZE, ROCKER_HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    rocker.label, rocker.color = "rocker_switch", Color(0.2, 0.2, 0.2)
    children.append(rocker)

    return Compound(label="kicker_board", children=children)


if __name__ == "__main__":
    board = kicker_board()
    assert board.is_valid
    assert len(board.children) == 1 + 4 + 2 + 1
    pcb = board.children[0]
    pcb_bb = pcb.bounding_box()
    assert abs(pcb_bb.size.X - PCB_SIZE[0]) < 0.01 and abs(pcb_bb.size.Y - PCB_SIZE[1]) < 0.01
    assert abs(pcb_bb.size.Z - PCB_THICKNESS) < 1e-6
    assert abs(board.bounding_box().max.Z - (PCB_THICKNESS + CAP_HEIGHT)) < 1e-6
    rocker = next(c for c in board.children if c.label == "rocker_switch")
    a = _rocker_edge_angle()
    edge_x, edge_y = _from_step(*ROCKER_EDGE[0])
    overhang = max((v.X - edge_x) * math.sin(a) - (v.Y - edge_y) * math.cos(a) for v in rocker.vertices())
    assert abs(overhang - ROCKER_OVERHANG) < 1e-6
    for x, y in MOUNT_HOLES:
        probe = Pos(x, y) * Cylinder(MOUNT_HOLE_DIAMETER / 2 - 0.05, PCB_THICKNESS, align=(Align.CENTER, Align.CENTER, Align.MIN))
        assert (clash := pcb & probe) is None or clash.volume < 1e-3, f"mounting hole at ({x:.2f}, {y:.2f}) is not clear"
    xt60 = next(c for c in board.children if c.label == "xt60")
    assert xt60.bounding_box().max.Z > PCB_THICKNESS + 5, "the XT60 body must sit on the component side"
    build(board, "kicker_board", export=False)
