# Pool Cover Winch v4 Build Guide

Nov 19, 2026

v4 is a motorized winch with a detachable rope spool. A 12 V motor turns a small gear, which turns a big gear bolted to the spool. The spool winds up and stores the whole rope, then lifts out for transport. Parts cost about $1,135.

## How v4 works

v4 keeps v3's bolt-together mount: aluminum angle hooks the block's back edge and front lip, so nothing relies on friction. The hand winch is replaced with a geared motor and a spool. CAD files: `cad/Pool_Cover_Winch_v4_Motor.step` (in use) and `cad/Pool_Cover_Winch_v4_SpoolRemoved.step` (spool lifted out).

**Drive.** A 12 V wiper-style worm gearmotor bolts to the outside of one side plate. Its shaft carries a 12-tooth pinion (the small gear), which drives a 48-tooth gear (the big gear), a 4:1 reduction. The worm gearbox is self-locking, so the spool holds the tarp whenever the motor stops.

**Spool (the "nooked pulley").** A 2.5 in aluminum tube between two 6 in aluminum flanges, clamped by four stainless tie rods that also hold the big gear on. It holds the whole rope in 4 layers. The far flange has the **nook**, a keyhole notch: push the rope's stopper knot through the big hole and slide the rope into the narrow slot, and the knot can't pull back through. The spool spins on two bronze bushings on a fixed 3/4 in stainless axle.

**Detachable.** The axle ends drop into open-top slots in two side plates. A swing latch on each plate closes over the axle and locks with a ball-lock pin. The rope pulls the spool forward and the gear pushes it down, both into the slots, so the latches carry no load in normal use. A magnetic sensor tells the controller whether the pin is in, and the motor won't run if it isn't.

**Front pulley.** Same as v3: a second piece of angle hooks the front lip, and an eye bolt carries a stainless pulley block. v4 uses a heavier one (550 lb working load) that turns the rope down to the water.

**Controls.** A battery box sits on the deck behind the block. Hold the pendant's IN button to wind; let go to stop. There's an E-stop on the box and on the pendant, plus a key switch. A rope-in limit switch stops the motor when a ball on the rope reaches it. A Raspberry Pi Pico runs the Python controller in `code/`.

## Supplies and cost

The full list with links is in `Pool Cover Winch v4 Supplies and Costs.xlsx` in this folder. Prices were checked 2026-11-19 and exclude tax and shipping.

| Group | Cost |
|---|---|
| Mount (angle, base plate, pulley block, hardware, pads, strap, snap hook) | $157.22 |
| Spool (tube, laser-cut parts, axle, bushings, tie rods, 2 ball-lock pins, rope, stopper ball) | $230.33 |
| Drive (32 N·m wiper motor, 48T gear, 12T pinion, pinion adapter) | $288.84 |
| Electrical (battery, charger, driver, Pico, sensors, contactor, pendant, E-stops, box, wiring) | $458.71 |
| **v4 total** | **$1,135.10** |

The motor ($156.99), battery ($69.99), 48T gear ($66.85) and ball-lock pins ($13.19 each) are quoted prices. Most other lines are estimates.

## Build steps

About a weekend: half of it waiting for laser-cut parts. You need a hacksaw, a drill, taps or nuts, and a file.

1. Order the laser-cut parts (2 spool flanges, 2 side plates, 2 latches) from DXFs exported from `cad/winch_v4.py`.
2. Cut the aluminum angle into two 8 in hooks and two 4 in side-plate feet. Cut the tube to 6 in and the axle to about 10 in. File every cut edge smooth.
3. **Mount:** bolt the rear hook angle under the base plate's back edge, as on v3. Fit the eye bolt to the front hook angle and clip on the pulley block.
4. **Side plates:** bolt each side plate to its foot, then bolt the feet to the base plate with the slots lined up. The plate with the big round hole is the motor side.
5. **Motor:** bolt the motor to the outside of the motor-side plate with its shaft through the round hole. Fit the pinion on the shaft (with the adapter if needed).
6. **Spool:** press a bronze bushing into each flange. Stack, in order: big gear, gear-side flange, tube, nook flange. Run the four tie rods through and tighten the nylocs evenly.
7. Slide the axle through the bushings. Check the spool spins freely by hand.
8. Fit the latches to the side plates with a shoulder bolt at the pivot. Glue the magnet into one ball-lock pin's handle, and mount the reed sensor where the handle sits when the pin is in.
9. Tie a stopper knot in one end of the rope and seat it in the nook. Tie a bowline with the snap hook in the other end. Crimp the stopper ball about 1 m back from the snap hook.
10. **Electrical:** wire the box exactly as `electrical/V4_Wiring_Diagram.svg` shows. Load `main.py`, `config.py` and `winch_logic.py` onto the Pico (see the README in the repo root).
11. **Bench test, spool out:** key on, press IN. It should refuse and beep, because the spool isn't latched. Drop the spool in, close both latches and pins, then press IN. If the spool winds the wrong way, set `DIR_IN_LEVEL = 0` in `config.py`.

## Using it

1. Set the frame on the block: rear angle over the back edge, front angle over the lip. Strap the base plate to the block's post.
2. **Pay out the rope.** Either hold OUT on the pendant, or take the spool out and walk it to the far end like a hose reel, letting it unwind. Then drop it back in.
3. To drop the spool in, line it over the slots and turn it a little by hand until the gear teeth mesh, then lower it. Close both latches and push in both ball-lock pins.
4. Clip the snap hook to the tarp's tow bar. Run the rope under the pulley block's sheave, over the pulley, and back to the bottom of the spool.
5. Key on and hold **IN**. The buzzer sounds while it moves. The motor stops on its own when the stopper ball reaches the limit switch.
6. To stop at any time, let go. The worm gearbox holds the tarp. Use an E-stop for anything unexpected.
7. **Transport:** key off, pull both pins, flip the latches up, and lift the spool out by its flanges. The frame and the battery box come off separately.

The sim's estimate for a full 25 yd pull is about 7.5 minutes at 9–10 ft/min, using about 13 Wh, so a charge lasts roughly 15 pulls.

## Limits and safety

- **Rating: 500 lbf on the rope**, set by the spool, gears and rope. The motor physically stalls at about that pull on the last layer. The controller trips at 25 A, about 340 lbf, so a snagged tarp stops it first.
- The sim's peak with the estimated tarp is about 300 lbf in the last metre. That's close to the 25 A trip; see `V4.2/docs/v4_sim_analysis.md` for the fix.
- Use it only with the pool closed to swimmers. Stand to the side of the rope line.
- Keep hands off the gears and spool while the key is on. Never lift the spool out with the key on.
- Keep the backup strap on, and check the starting block's load rating with its maker.
- Charge the battery away from the pool with the key off. Rinse the frame with fresh water after use, and grease the gears monthly.

## Sources

- Autotex J3 12 V 32 N·m wiper motor, Zoro
- Ball-lock pin 3/8 in, 304 stainless, Zoro
- WattCycle 12 V 20 Ah LiFePO4 battery
- Cytron MD30C motor driver, RobotShop
- Stainless single block with shackle, Sailrite
- 1/4 in double braid polyester rope, Blue Ox Rope
- 6061 angle 2 × 2 × 1/4 in, Speedy Metals
