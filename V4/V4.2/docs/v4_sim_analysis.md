# v4 sim analysis → v4.2

Nov 19, 2026. I ran the v4 sim (`V4/sim/v4_motor_sim.html`) headlessly through a full 25 yd pull with `tools/sim_report.js`. I tested candidate fixes the same way and kept the ones that helped as **v4.2**.

All numbers are from the sim. Its tarp load is an estimate: wet 25 yd × 6-lane cover, about 315 lb, sliding friction 0.5. The motor curves are straight lines from the listed stall torque to an assumed 50 rpm no-load speed.

## What v4 does in the sim

| | v4 result |
|---|---|
| Full pull (21.5 m of rope) | **7 min 29 s**, finishes without tripping |
| Rope speed | 8.5–10.4 ft/min while running, slowing to 5.7 ft/min in the last metre |
| Peak rope tension | 303 lbf, in the last metre (rope angle 57° below level) |
| Peak motor current | **21.8 A** against a 25 A trip (87 %) |
| Peak motor torque | 18.8 N·m of 32 N·m stall (59 %) |
| Rope on the spool | 4 layers; working radius grows from 35 mm to 54 mm (+55 %) |
| Spool pushed into its slots | up to 220 lbf forward and 224 lbf down at the end |
| Latch pin load | **0 for the whole pull** |
| Battery used | about 13 Wh per pull (≈ 15 pulls from the 20 Ah battery) |
| Rope contact | rides on the front pulley for the entire pull |
| Parts cost | $1,135.10 (mechanical $676.39, electrical $458.71) |

## Pros

- **It works end to end.** The full 25 yd pull completes without an overload trip, and the rope-in limit stops it at the end.
- **One person, hands-free.** The spool stores all the rope, so nobody has to tail the loose end like on v3. The operator just holds IN on the pendant.
- **The spool seats itself.** The pinion sits straight forward of the big gear, so the gear force pushes the spool **down** and the rope pulls it **forward**, both into the slots. The latch pins carry no load at any point in the sim. They only stop the spool bouncing out.
- **Holds by itself.** The worm gearbox is self-locking, so letting go of the button anywhere holds the tarp, with no ratchet or pawl.
- **Can't over-pull.** At 4:1 the motor's 32 N·m stall works out to about 500 lbf on the last layer, the design rating. The 25 A trip stops it at about 340 lbf, well before that.
- **Low, steady rope line.** The rope stays on the front pulley the whole time and runs level about 50 mm above the platform, like v2 and v3.
- **Easy to transport.** Pull two pins, flip two latches, and the spool lifts out with its gear and rope, about 6 kg (13 lb) with the full rope. The CAD sweep confirms it lifts straight out without hitting anything.
- **Easy mesh alignment.** Off the frame, the spool spins freely on its bushings, so you turn it a few degrees by hand to line up the teeth as you drop it in.
- **Low energy.** About 13 Wh per pull, so a full charge lasts many pulls.
- **Built for wet use.** The motor is a sealed automotive wiper motor.

## Cons

- **Slow.** At 7.5 minutes per pull it's much slower than v3 with a drill (2–3 minutes).
- **Thin overload margin at the end.** Current peaks at 87 % of the trip in the last metre. A tarp only about 12 % heavier or stickier than the estimate would trip it just before it's in place.
- **Torque need grows when the load is highest.** With 4 rope layers, the working radius is 55 % larger at the end of the pull, right when the tarp is heaviest.
- **Last-metre tension spike.** Tension climbs from about 155 to 303 lbf in the final metre as the rope angle steepens to 57°. Every version has this, because the pulley sits at deck height. Lowering the pulley would help, but the rope would then hit the front lip: the most it could drop is about 30 mm, which cut the peak by less than 3 %.
- **Exposed gear mesh.** The pinion/gear nip is right where your hands go when you lift the spool.
- **Oversized battery.** A 20 Ah battery for 13 Wh per pull is extra cost and weight.
- **Pinion hangs on the motor shaft.** The pinion is cantilevered on the wiper motor's output shaft, with up to about 230 lbf of side load at the end of a pull. The motor's side-load rating is unknown.
- **Cost.** $1,135, more than four times v3's drill build, though less than half of v2's motor build.

## Improvements → v4.2

I tried several candidate changes in the sim and kept the combination that helped most:

| Candidate | Pull time | Peak current / trip | Kept? |
|---|---|---|---|
| v4 as built | 7:29 | 21.8 / 25 A (87 %) | baseline |
| 55 N·m motor, 30 A trip | 6:53 | 17.1 / 30 A | yes |
| + 8 in spool (3 layers) | 7:19 | 15.7 / 30 A | yes |
| + 36T gear (3:1) | **5:40** | **19.2 / 30 A (64 %)** | **yes = v4.2** |
| 55 N·m + 8 in + 42T gear | 6:29 | 16.8 / 30 A | no (slower) |
| 55 N·m + 8 in + 2 in core | 8:16 | 15.0 / 30 A | no (slower) |
| Front pulley 30 mm lower | 7:29 | 21.1 / 25 A | no (under 3 % better) |

What changed in v4.2:

1. **Motor: 32 N·m → 55 N·m** (same Autotex J3 family, +$38). The motor peaks at 39 % of stall instead of 59 %.
2. **Spool: 6 in → 8 in between flanges.** The rope fits in 3 layers, so the last-layer radius drops from 54 to 48 mm (12 % less torque at the end). The base plate grows from 15 to 17 in wide.
3. **Big gear: 48T → 36T (3:1).** The stronger motor turns this into speed: 11.4–13.9 ft/min.
4. **Trip: 25 A → 30 A.** That's about 470 lbf on the last layer, still under the 500 lbf rating. Peak current is now 64 % of the trip instead of 87 %.
5. **Gear guard.** Clear polycarbonate over the pinion side of the mesh. It stays forward of the big gear's outline, so the spool still lifts straight out (checked in the CAD).
6. **Battery: 20 Ah → 12 Ah.** About 9 Wh per pull gives roughly 13 pulls per charge, at less cost and weight.

### v4.2 in the sim

| | v4 | v4.2 |
|---|---|---|
| Full pull | 7:29 | **5:40** |
| Rope speed | 8.5–10.4 ft/min | 11.4–13.9 ft/min |
| Peak current / trip | 21.8 / 25 A (87 %) | 19.2 / 30 A (64 %) |
| Peak motor torque / stall | 18.8 / 32 N·m (59 %) | 21.3 / 55 N·m (39 %) |
| Rope layers, end radius | 4, 54 mm | 3, 48 mm |
| Battery per pull | 13 Wh | 9.3 Wh |
| Spool assembly mass (CAD, 2 layers of rope) | 5.5 kg | 4.3 kg |
| Parts cost | $1,135.10 | $1,156.26 |

## Still open (not fixed in v4.2)

- **Pinion support.** Check the wiper motor's output-shaft side-load rating. v4.2's smaller 36T gear actually raises the end-of-pull pinion force from about 230 to about 270 lbf. If the rating is too low, put the pinion on its own short shaft with a bearing on each side and couple it to the motor.
- **Motor speed under load.** The sim assumes both motors run 50 rpm with no load. Measure the real motor on a bench (rpm and amps at a known torque) and put the numbers into the `motor` settings in `v4_2_mechanism.js`.
- **Real tarp load.** The tarp weight is still an estimate. Pull the real tarp with a luggage scale on the rope to set the trip current properly.
- **Last-metre spike.** It's geometry, not the winch. If it trips in practice, place the stopper ball so the motor stops about 1 m early, and finish the last metre by hand.

## How to repeat this

```
node tools/sim_report.js V4/sim/v4_mechanism.js WinchV4 motor
node tools/sim_report.js V4/V4.2/sim/v4_2_mechanism.js WinchV4_2 motor "" V4/sim/v4_mechanism.js
node tools/sim_report.js V4/sim/v4_mechanism.js WinchV4 motor '{"gear":{"teeth":42}}'   # try your own change
```
