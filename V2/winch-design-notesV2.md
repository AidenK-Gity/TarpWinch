# Tarp Winch: design notes

## Versions
| Version | Mount | Drive | Parts cost | Files |
|---|---|---|---|---|
| v1 crank | C-clamp over the FRONT lip, held by screw friction | hand crank, 4:1 gears, ratchet + pawl | — | Pool_Cover_Winch.step/.stl, winch.py |
| v1 motor | same | 24 V worm gearmotor, Arduino control | — | Pool_Cover_Winch_MOTORIZED.step/.stl, winch_motor.py, Motor_Wiring_Diagram.svg, winch_controller.ino |
| v2 crank / v2 motor | C-clamp on the REAR edge + roller saddle on the front lip | same as v1 | about $1,472 / $2,421 | Pool_Cover_Winch_v2_RearClamp_CRANK/MOTORIZED.step/.stl, winch_v2.py; v2 assembly manual doc |
| **v3 hand / v3 drill motor** (current, budget) | 2×2×1/4 in aluminum angle hooks the REAR edge (winch on a 1/4 in plate); second angle hooks the FRONT lip with an eye bolt + pulley block | off-the-shelf 3,500 lb hand trailer winch used as a capstan (4 wraps, tail by hand); drill version drives the winch input shaft with an 18 V cordless drill | $186.66 / $261.63 | Pool_Cover_Winch_v3_Budget.step/.stl, Pool_Cover_Winch_v3_DrillMotor.step/.stl, winch_v3.py; v3 budget build guide doc; "v3 Budget" tab of the supplies sheet |

## v3 decisions (budget: hand under $200, motor under $500)
- Custom gearbox, stainless shafts, bearings and the 24 V electronics were dropped: they cannot fit the budget.
- The winch is used as a capstan so a 25 yd pull doesn't depend on drum capacity (trailer winch straps are only 20–33 ft).
- Motor = cordless drill: hold-to-run trigger, clutch acts as a torque limiter, no wiring at the pool. Torque needed at the input is about 4 N·m at 160 lbf.
- Rating about 300 lbf, limited by the 1/4 in pulley block. Rope: 1/4 in double braid polyester, about 2,000 lb break.
- Estimated speed: hand about 7 ft/min (about 11 min for 25 yd); drill at 300 rpm about 30 ft/min (2–3 min). Assumes a 4:1 winch.

## v1/v2 drivetrain (kept for reference)
- Drum: 90 mm core, 160 mm flanges, 98 mm wide; holds about 23 m of 6 mm Dyneema (25 yd pool)
- Gears: 12T → 48T, module 3 (4:1). Shafts: 316 SS. Sealed stainless bearings.
- Rated rope pull: 500 lbf (2.2 kN). Estimated real tarp pull: about 160 lbf (wet 25 yd × 6-lane cover, about 315 lb, μ≈0.5).
- Motor: 24 V brushed with worm gearbox, ≥350 W, about 55 rpm, ≥45 N·m. Trip at 18 A.

## Why the rear-edge mount (v2 and v3)
- v1 relied on friction: the rope pulled the clamp off the lip, so the screws needed about 1,000 lbf of clamp force to hold 500 lbf.
- Rear-edge mount: the rope drives the hook into the platform's rear edge and presses the mount's front down. Nothing relies on friction.
- The front piece is pushed down and back into the lip by the rope (up to about 430 lbf down and 250 lbf back at a 60° rope angle and 500 lbf). It needs no screws.
- The pulling force is set by the winch, not the mount.

## Open items
- The real tarp weight and size are not confirmed (the sizing uses an estimate).
- The starting block's anchor rating is not confirmed. A backup strap to the block post is recommended.
- v3: check the drill socket adapter fits the specific winch's input shaft before buying.
- v1/v2 firmware has only been syntax-checked, not compiled on real hardware.
