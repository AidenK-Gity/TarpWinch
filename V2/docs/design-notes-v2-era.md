# Tarp Winch: design notes

## Versions
| Version | Mount | Drive | Files |
|---|---|---|---|
| v1 crank | C-clamp over the FRONT lip, held by screw friction | hand crank, 4:1 gears, ratchet + pawl | Pool_Cover_Winch.step/.stl, winch.py |
| v1 motor | same | 24 V worm gearmotor, Arduino control | Pool_Cover_Winch_MOTORIZED.step/.stl, winch_motor.py, Motor_Wiring_Diagram.svg, winch_controller.ino |
| **v2 crank / v2 motor** (current) | C-clamp on the REAR edge + roller saddle on the front lip | same as v1 | Pool_Cover_Winch_v2_RearClamp_CRANK/MOTORIZED.step/.stl, winch_v2.py (imports winch.py and winch_motor.py) |

## Shared drivetrain
- Drum: 90 mm core, 160 mm flanges, 98 mm wide; holds about 23 m of 6 mm Dyneema (25 yd pool)
- Gears: 12T → 48T, module 3 (4:1). Shafts: 316 SS. Sealed stainless bearings.
- Rated rope pull: 500 lbf (2.2 kN). Estimated real tarp pull: about 160 lbf (wet 25 yd × 6-lane cover, about 315 lb, μ≈0.5).
- Crank effort at 500 lbf: about 30–45 lbf on the 200 mm arm.
- Motor: 24 V brushed with worm gearbox, ≥350 W, about 55 rpm, ≥45 N·m (needs 41 N·m at 500 lbf on a full drum). Trip at 18 A.

## Why v2 (rear clamp)
- v1 relied on friction: the rope pulled the clamp off the lip, so the screws needed about 1,000 lbf of clamp force to hold 500 lbf.
- v2: the rope drives the rear clamp's back wall into the platform's rear edge (0.33 MPa bearing). Nothing relies on friction.
- The rope is under-wound and runs level about 60 mm above the platform (v1: about 115 mm), so the tipping moment on the clamp drops from about 300 to about 180 N·m (screw load about 1.4 kN).
- The front saddle is pushed down and back into the lip (up to about 430 lbf down and 250 lbf back as the tarp arrives at a 60° rope angle). It needs no screws.
- The pulling force itself is unchanged: that is set by the drum and gears. v2 gains holding strength and stability, not pull.
- Under-winding reverses the drum direction: the ratchet is mirrored in the v2 crank version, and the motor version may need DIR_IN_LEVEL flipped in the firmware.
- The roller keeper sits 37 mm above the roller so the 30 mm stopper ball passes under it and trips the limit switch on the saddle.

## Open items
- The real tarp weight and size are not confirmed (the sizing uses an estimate).
- The starting block's anchor rating is not confirmed. It is still the weak link, and a backup strap to the block post is recommended.
- The firmware has only been syntax-checked, not compiled on real hardware.
