# Tarp Winch: design notes

## Versions

| Version | Mount | Drive | Parts cost | Files |
|---|---|---|---|---|
| v1 motor | C-clamp over the FRONT lip, held by screw friction | 24 V worm gearmotor, 4:1 gears, Arduino control | — | `V1/cad/` (Pool_Cover_Winch_MOTORIZED.step/.stl, winch_motor.py), `V1/electrical/Motor_Wiring_Diagram.svg`, `V1/code/` (C++ original + Python port) |
| v2 crank / v2 motor | C-clamp on the REAR edge + roller saddle on the front lip | same as v1 | about $1,472 / $2,421 | `V2/cad/` (…v2_RearClamp_CRANK/MOTORIZED.step/.stl, winch_v2.py), `V2/docs/` (supplies sheet, v2-era notes) |
| v3 hand / v3 drill | 2×2×1/4 in angle hooks the REAR edge (winch on a 1/4 in plate); second angle hooks the FRONT lip with an eye bolt + pulley block | off-the-shelf 3,500 lb hand trailer winch used as a capstan (4 wraps, tail by hand); drill version drives the input shaft with an 18 V drill | $186.66 / $261.63 | `V3/cad/`, `V3/docs/` (build guide PDF, supplies sheet) |
| v4 motor | v3's angle mount (wider base plate) + side plates with open-top slots | 12 V wiper worm gearmotor → 12T pinion → 48T gear bolted to a detachable rope spool | $1,135.10 | `V4/cad/` (winch_v4.py, …v4_Motor / …v4_SpoolRemoved .step/.stl), `V4/sim/`, `V4/code/`, `V4/electrical/`, `V4/docs/` |
| **v4.2 motor** (current) | same as v4, 17 in base plate | 55 N·m motor → 12T → 36T (3:1) → 8 in spool; mesh guard | $1,156.26 | `V4/V4.2/` (same subfolders); changes explained in `V4/V4.2/docs/v4_sim_analysis.md` |

## v4 decisions (geared motor + detachable spool)

- **Drive train, as requested:** motor → small gear → big gear → spool. The big gear is bolted to the spool's flange by the same four tie rods that clamp the spool together, so the axle carries no torque. That lets it be a dead (non-turning) axle.
- **Spool = the "nooked pulley":** a 2.5 in aluminum tube between 6 in flanges. A keyhole notch (the nook) in one flange catches the rope's stopper knot. It stores the whole 22 m of rope, so nobody tails the rope as on v3.
- **Detachable:** the axle drops into open-top slots in two side plates, held by swing latches and 3/8 in ball-lock pins.
  - The pinion sits straight **forward** of the spool, so the gear force pushes the spool **down** into the slots. The rope pulls it **forward** into the slots' front walls.
  - In the sim the latch pins carry zero load for the whole pull. The CAD sweep confirms the spool lifts straight out.
- **Motor:** small hobby worm gearmotors only make about 2–3 N·m, which is far too little.
  - An automotive wiper motor (Autotex J3, 32 N·m, $156.99) is self-locking, made for wet use, and at 4:1 stalls at about the 500 lbf rating on the last rope layer.
- **12 V instead of 24 V:** the battery costs $70 instead of $360. The sim's whole pull uses about 13 Wh.
- **Controller:** a Raspberry Pi Pico running MicroPython instead of an Arduino Nano. It's cheaper ($5), testable on a PC, and adds a spool-latched interlock.
- **Rating 500 lbf** on the spool, gears and 1/4 in rope (4:1 rope safety). The front pulley block is upgraded to 550 lb WLL (v3's was 300 lb).

## v4.2 changes (from the v4 sim)

- Pull time 7:29 → 5:40, and peak current 87 % → 64 % of the trip. Details and the candidates that were rejected are in `V4/V4.2/docs/v4_sim_analysis.md`.
- 55 N·m motor, 8 in spool (3 layers instead of 4), 36T gear (3:1), 30 A trip, 12 Ah battery, polycarbonate mesh guard on the pinion side.

## v3 decisions (budget: hand under $200, motor under $500)

- The custom gearbox, stainless shafts, bearings and the 24 V electronics were dropped: they can't fit the budget.
- The winch is used as a capstan, so a 25 yd pull doesn't depend on drum capacity (trailer winch straps are only 20–33 ft).
- The motor is a cordless drill: hold-to-run trigger, the clutch acts as a torque limiter, and there's no wiring at the pool. It needs about 4 N·m at the input at 160 lbf.
- Rated about 300 lbf, limited by the 1/4 in pulley block. Rope: 1/4 in double braid polyester, about 2,000 lb break.
- Estimated speed: about 7 ft/min by hand (about 11 min for 25 yd), and about 30 ft/min with a drill at 300 rpm (2–3 min). Assumes a 4:1 winch.

## v1/v2 drivetrain (kept for reference)

- Drum: 90 mm core, 160 mm flanges, 98 mm wide. Holds about 23 m of 6 mm Dyneema (25 yd pool).
- Gears: 12T → 48T, module 3 (4:1). Shafts: 316 SS. Sealed stainless bearings.
- Rated rope pull: 500 lbf (2.2 kN). Estimated real tarp pull: about 160 lbf (wet 25 yd × 6-lane cover, about 315 lb, μ≈0.5).
- Motor: 24 V brushed with worm gearbox, ≥350 W, about 55 rpm, ≥45 N·m. Trips at 18 A.

## Why the rear-edge mount (v2, v3, v4)

- v1 relied on friction: the rope pulled the clamp off the lip, so the screws needed about 1,000 lbf of clamp force to hold 500 lbf.
- Rear-edge mount: the rope drives the hook into the platform's rear edge and presses the mount's front down. Nothing relies on friction.
- The front piece is pushed down and back into the lip by the rope (up to about 430 lbf down and 250 lbf back at a 60° rope angle and 500 lbf). It needs no screws.
- The pulling force is set by the winch, not the mount.

## Open items

- The real tarp weight and size aren't confirmed; the sizing uses an estimate. Weigh the pull with a luggage scale before setting trip currents.
- The starting block's anchor rating isn't confirmed. A backup strap to the block post is recommended.
- v3: check the drill socket adapter fits the specific winch's input shaft before buying.
- v4/v4.2:
  - Check the wiper motor's output shaft (size, and side-load rating for the pinion) before ordering the pinion.
  - Bench-measure the motor's speed and current under load.
- The v3 build guide PDF still says the supplies list is on the "v3 Budget tab of the v2 sheet". That tab is now its own file: `V3/docs/Pool Cover Winch v3 Supplies and Costs.xlsx`.
- v1 C++ firmware was only syntax-checked. The Python logic (v1 port, v4, v4.2) passes its unit tests on a PC but hasn't run on a Pico yet.
