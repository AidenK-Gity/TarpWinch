# Tarp Winch

A winch that sits on a pool's **starting block** and pulls a pool cover (tarp) across a 25-yard pool. The tarp's tow rope runs over a pulley at the front of the block and back to the winch, which reels it in.

The design has gone through several versions. Each one lives in its own folder with its 3D model, a simulation you can watch, a parts list with prices and, for motorized versions, a wiring diagram and controller code.

## Which version is which

| Version | In one sentence | Powered by | Parts cost | Full pull (sim) |
|---|---|---|---|---|
| [V1](V1/) | First design: a custom geared drum clamped to the front lip of the block | hand crank or 24 V motor (the crank CAD file is not in the repo) | not priced | about 4–5 min |
| [V2](V2/) | Same drum, but it hooks the *back* edge of the block, so the rope can't pull it off | hand crank or 24 V motor | about $1,472 crank / $2,421 motor | about 4–5 min |
| [V3](V3/) | Budget version: an off-the-shelf boat-trailer winch on two pieces of aluminum angle | hand crank or a cordless drill | $187 hand / $262 drill | 11 min hand / 2–3 min drill |
| [V4](V4/) | Motor → small gear → big gear → a rope spool that **lifts out** for transport | 12 V motor | about $1,135 | 7.5 min |
| [V4.2](V4/V4.2/) | V4 improved using what its simulation showed: stronger motor, wider spool, 3:1 gears | 12 V motor | about $1,156 | 5.7 min |

**Picking one:** V3 is the cheapest by far, but someone has to hold the loose end of the rope while it winds. V4.2 is the newest: one person holds a button and the rope stores itself on the spool.

## Getting started (no software needed)

| I want to... | Open this | How |
|---|---|---|
| **Watch it work** | any `sim/*.html` file, e.g. [V4/V4.2/sim/v4_2_motor_sim.html](V4/V4.2/sim/v4_2_motor_sim.html) | Double-click it. It opens in your web browser. Space = play/pause, drag to move, scroll to zoom, H = help. |
| **See the 3D model** | any `cad/*.step` or `cad/*.stl` file | Drag it into a free viewer such as [3dviewer.net](https://3dviewer.net) or FreeCAD. STEP keeps the part names and colors. |
| **See what it costs** | `docs/*Supplies and Costs.xlsx` in each version | Opens in Excel or Google Sheets. The totals are at the top. "Quoted" prices came from a real listing; "Estimate" means nobody checked yet. |
| **Read how to build it** | `docs/*Build Guide.pdf` (V3, V4) | Any PDF reader. |
| **See the wiring** | `electrical/*.svg` (V1, V4, V4.2) | Double-click; it opens in your browser. Tags with the same name are the same wire. |
| **Understand why v4.2 changed** | [V4/V4.2/docs/v4_sim_analysis.md](V4/V4.2/docs/v4_sim_analysis.md) | Pros, cons and the improvements, with numbers from the sim. |

### What to look for in a sim

- **The orange rope** has dark marks that move with it, and the gears and pulley have spokes, so you can see everything turn.
- **The right-hand panel** shows the live numbers. Rope tension turns orange and then red as it nears the rating. Motor current turns orange as it nears the trip point.
- **Colored arrows** are forces. Green means the block is pushing back on the mount (good: the mount is bearing on the block, not relying on friction).
- **The top buttons** jump between a close-up of the winch, the whole pool and the tarp edge.

## Every version folder has the same layout

```
Vx/
  cad/          3D model files (.step, .stl) and the Python script that makes them
  sim/          the browser simulation (.html) and its mechanism file (.js)
  code/         controller software (motorized versions)
  electrical/   wiring diagram (motorized versions)
  docs/         parts list + costs (.xlsx), build guide, notes
```

Not every version has every folder. V2 and V3 have no electronics, and V1's parts list was never made.

Shared things live at the top:

| Folder / file | What it is |
|---|---|
| `sim_common/` | The simulation engine all the sims share (pool, tarp, rope physics, controls) |
| `tools/` | Scripts that regenerate the v4 wiring diagrams, budgets and PDFs, and run sims without a browser |
| `DESIGN_NOTES.md` | The engineering decisions behind every version, all in one place |

## For people who want to change things

### Controller code (Python)

The motorized versions run on a **Raspberry Pi Pico** using **MicroPython**. Each `code/` folder has:

- `winch_logic.py`: all the rules (hold-to-run, overload trip, limit switch, spool latch). It has no hardware code, so you can test it on any computer.
- `config.py`: pin numbers and settings (trip current, battery cutoff and so on). Change numbers here.
- `main.py`: connects the logic to the Pico's pins.
- `test_winch_logic.py`: tests. Run `python -m unittest test_winch_logic.py` inside the folder.

To put it on a Pico:

1. Install MicroPython (hold BOOTSEL while plugging in, then drag on the `.uf2` from micropython.org).
2. Open Thonny.
3. Save the three non-test `.py` files onto the Pico.

V1's original Arduino C++ is kept next to its Python port; [V1/code/README.md](V1/code/README.md) explains the differences and a bug the port fixes.

### Simulations

The sims are plain HTML + JavaScript with no build step. A version's look and dimensions are in its `sim/*_mechanism.js`. Headless runs use Node.js:

```
node tools/sim_report.js V4/sim/v4_mechanism.js WinchV4 motor        # numbers for a full pull
node tools/sim_smoke.js  V4/sim/v4_mechanism.js WinchV4 motor        # check every frame draws
node tools/sim_report.js V4/sim/v4_mechanism.js WinchV4 motor '{"gear":{"teeth":42}}'   # try a change
```

### CAD

The models are generated by Python scripts using [CadQuery](https://cadquery.readthedocs.io), installed with `pip install cadquery`. Run the script inside its `cad/` folder:

- `python winch_v4.py` writes the v4 STEP/STL files.
- `V4/V4.2/cad/winch_v4_2.py` reuses the v4 script with different settings.

The V1 and V2 scripts import a base `winch.py` that isn't in this repo, so their STEP/STL files can be viewed but not regenerated.

### Budgets, wiring diagrams, PDFs (v4 and v4.2)

These are generated, so edit the script, not the file:

- `python tools/make_budget.py` rebuilds both `.xlsx` files (needs `pip install openpyxl`).
- `python tools/make_wiring.py v4` (or `v4.2`) redraws the wiring diagram.
- `python tools/md_to_pdf.py <file.md>` prints a Markdown doc to PDF with Chrome (needs `pip install markdown`).

## Safety, for every version

Use the winch only with the pool closed to swimmers, and stand to the side of the rope line. Keep a backup strap from the winch to the block's post. Starting blocks aren't rated for this kind of load by default, so check yours with its maker. Charge batteries away from the water.
