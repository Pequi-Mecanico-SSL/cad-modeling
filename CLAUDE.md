# SSL robot CAD (build123d)

Parametric, code-only CAD for the Pequi SSL robot, using [build123d](https://build123d.readthedocs.io/) (OpenCASCADE B-rep).

## Layout

- `sslcad/`: shared helpers
  - `build(shape, name, export=True)` prints bbox, volume and per-child volumes, renders `out/<name>/<name>.png`
    and, with `export`, writes `.step`/`.stl` (vendor models pass `export=False`)
  - `load_step(name)` loads (and caches) a vendor model from `imports/`
  - `instance(shape, loc)` places a copy that shares geometry with `shape`
  - `check_robot_envelope(shape)` fails if anything is outside the 180 mm × 150 mm robot cylinder
- `parts/`: parts we design and 3D print. Parameters are module-level constants, plus a function that returns the `Part`
- `components/`: models of bought/existing hardware to design the frame around, each in its own natural frame
  (documented in the module docstring) with its key dimensions as constants.
  Mark each value's source: `# STEP` (measured on the vendor model), `# datasheet`, `# drawing`, `# measured` (calipers),
  `# photo` (estimated from photos) or `# assumed`
- `assemblies/`: combine parts into a `Compound` with labeled, colored children, then run the checks
- `imports/`: third-party STEP models
  - `imports/mechanics/`: git submodule of [Pequi-Mecanico-SSL/mechanics](https://github.com/Pequi-Mecanico-SSL/mechanics),
    the team's reviewed vendor models (`components/`) and reference drawings (`references/`, some only candidates)
- `reference/<component>/`: our photos (with a ruler) and datasheets used to model components
- `out/`: generated, never edit by hand

## Components

| Module | Source | Qty |
| --- | --- | ---: |
| `power_distribution` | modeled from photos and caliper measurements | 1 |
| `drive_motor` | Nanotec DF45L024048-A STEP + datasheet | 4 |
| `omni_wheel` | GTF Robots 50 mm v4 STEP | 4 |
| `esc` | ST B-G431B-ESC1 STEP; `esc(with_stlink=False)` removes the detachable strip | 4 |
| `raspberry_pi` | Raspberry Pi 4B STEP + dimension drawing | 1 |
| `can_hat` | Waveshare RS485 CAN HAT STEP; `pi_stack()` mounts it on the Pi | 1 |
| `imu` | Pololu MinIMU-9 v5 STEP | 1 |
| `kicker_board` | ZJUNlict Booster Board 2019 KiCad/STEP conversion + photos; tall parts (caps, rocker) as envelopes | 1 |
| `solenoid` | SOLETEC 018 drawing (kicker candidate) | 1 |

## Conventions

- Units in mm. Robot frame: floor at Z=0, robot centered on the Z axis, **front = +X**.
- Model each part in its own natural frame and position it in the assembly with `Pos(...) * Rot(...) * part`,
  or `instance(part, Pos(...) * Rot(...))` for vendor models.
- Derive dimensions from other parts' constants (`from parts import base_plate as bp; bp.WHEEL_DIAMETER`) instead of copying numbers.
- Every part/assembly script asserts validity (`part.is_valid`, solid count) and runs the relevant checks before `build`.
  Component scripts also assert their bbox against the datasheet/drawing constants, which catches a wrong frame.

## Commands

```sh
git submodule update --init         # after cloning, fetch imports/mechanics
uv run parts/base_plate.py          # build one part
uv run components/esc.py            # build one component
uv run assemblies/robot.py          # build + envelope/interference checks
uv run python -m ocp_viewer         # live 3D viewer at http://127.0.0.1:3939
uv run assemblies/robot.py --show   # also push the result to the viewer
```

## Verifying changes

After each change, run the script and read `out/<name>/<name>.png` (2×2 grid: iso, top, front, side).
Prefer numeric checks (bbox, volume, `(a & b).volume` for interference, `check_robot_envelope`) over judging the images alone.
Booleans against a whole vendor model are slow (tens of seconds); intersect only the relevant child when possible.

## build123d gotchas

- Operations are lowercase functions (`extrude`, `fillet`, `revolve`, `loft`, `sweep`); objects are classes (`Box`, `Circle`, `Rectangle`, `Hole`).
- Fillet 2D sketch corners before cutting circular holes into the sketch; a circle's seam vertex can't be filleted.
- `Hole` drills along -Z from its location, so place the locations on the top face.
- A bounding box does not bound radial extent (e.g. wheel rims); use booleans against an envelope solid.
- Assembly children are stored relative to their parent: `loc * assembly` moves only the root, so a child's own
  shape is not in global coordinates. Attaching children to a `Compound` rebuilds its geometry and resets its location.
- `loc * shape` deep-copies all the geometry, and for an assembly child also the whole tree it belongs to
  (gigabytes for a vendor board). Use `instance(shape, loc)`, and never re-parent the children of a cached `load_step` result.
- An intersection with nothing in common returns `None`.
