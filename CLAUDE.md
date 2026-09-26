# SSL robot CAD (build123d)

Parametric, code-only CAD for the Pequi SSL robot, using [build123d](https://build123d.readthedocs.io/) (OpenCASCADE B-rep).

## Layout

- `sslcad/`: shared helpers
  - `build(shape, name)` writes `out/<name>/<name>.{step,stl,png}` and prints bbox, volume and per-child volumes
  - `load_step(name)` loads a vendor model from `imports/`
  - `check_robot_envelope(shape)` fails if anything is outside the 180 mm × 150 mm robot cylinder
- `parts/`: parts we design and 3D print. Parameters are module-level constants, plus a function that returns the `Part`
- `components/`: models of bought/existing hardware (boards, connectors, motors) to design the frame around.
  Dimensions estimated from photos are marked `# photo`, and guesses `# assumed`; replace them with caliper values when available
- `assemblies/`: combine parts into a `Compound` with labeled, colored children, then run the checks
- `imports/`: third-party STEP models (motors, wheels, connectors…)
- `reference/<component>/`: photos (with a ruler) and datasheets used to model components
- `out/`: generated, never edit by hand

## Conventions

- Units in mm. Robot frame: floor at Z=0, robot centered on the Z axis, **front = +X**.
- Model each part in its own natural frame and position it in the assembly with `Pos(...) * Rot(...) * part`.
- Derive dimensions from other parts' constants (`from parts import base_plate as bp; bp.WHEEL_DIAMETER`) instead of copying numbers.
- Every part/assembly script asserts validity (`part.is_valid`, solid count) and runs the relevant checks before `build`.

## Commands

```sh
uv run parts/base_plate.py          # build one part
uv run assemblies/robot.py          # build + envelope/interference checks
uv run python -m ocp_viewer         # live 3D viewer at http://127.0.0.1:3939
uv run assemblies/robot.py --show   # also push the result to the viewer
```

## Verifying changes

After each change, run the script and read `out/<name>/<name>.png` (2×2 grid: iso, top, front, side).
Prefer numeric checks (bbox, volume, `(a & b).volume` for interference, `check_robot_envelope`) over judging the images alone.

## build123d gotchas

- Operations are lowercase functions (`extrude`, `fillet`, `revolve`, `loft`, `sweep`); objects are classes (`Box`, `Circle`, `Rectangle`, `Hole`).
- Fillet 2D sketch corners before cutting circular holes into the sketch; a circle's seam vertex can't be filleted.
- `Hole` drills along -Z from its location, so place the locations on the top face.
- A bounding box does not bound radial extent (e.g. wheel rims); use booleans against an envelope solid.
