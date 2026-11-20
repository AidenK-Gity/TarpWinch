# v1 controller code: C++ original and Python port

There are two versions of the same controller here:

| Folder | Language | Runs on | Status |
|---|---|---|---|
| `winch_controller/winch_controller.ino` | C++ (Arduino) | Arduino Nano | Original. Syntax-checked only, never run on hardware. |
| `python/` | Python (MicroPython) | Raspberry Pi Pico | Port of the original with the bugs below fixed. Logic is unit-tested on a PC. |

The `.ino` file is the only C++ in the repo. v4 and v4.2 use the Python version from the start.

## What the C++ does

`winch_controller.ino` is a single loop that runs a hold-to-run motor controller for the 24 V gearmotor:

- **Hold-to-run:** the motor turns only while the pendant's IN or OUT button is held. Letting go stops it.
- **Soft start/stop:** it ramps the PWM up over 0.5 s and back down when you stop, so the worm gear isn't shock-loaded.
- **Overload trip:** above 18 A for 0.3 s (about 500 lbf on the rope) it stops and latches a fault. It ignores the start-up current spike during the ramp.
- **Rope-in limit:** a normally-closed switch stops winding IN when the stopper ball arrives. A broken wire reads as "limit reached", so it fails safe.
- **Battery lockout:** it won't start below 22 V.
- **Direction-change wait:** it must be stopped for 0.4 s before it reverses.
- **Watchdog:** no single run longer than 8 minutes.
- **Faults:** a fault blinks the LED fast and beeps 3 times. It clears once both buttons have been released for 2 s.
- **Stuck button:** a button held at power-up is a fault.
- **Logging:** current and voltage go to the serial port every 0.5 s.

## Problems found in the C++

1. **Direction change while running (real bug).** If the loop sees OUT pressed while it's still running IN, it skips the "start" code and keeps driving IN. That's because `state` isn't `IDLE` and the running branch reuses `lastDir`. Sliding a thumb straight from IN to OUT could keep winding in. The Python port stops the motor instead (tested in `test_direction_change_stops`).
2. **Blocking delays.** `stopMotor()` blocks for up to 100 ms and `fault()` for 750 ms. `pressed()` also waits 3 ms per button on every pass. While blocked, nothing else is checked. The port uses time-based steps with no `delay()`.
3. **Board mismatch.** The file header says ATmega328P (Nano), but the v2 supplies sheet lists a Nano Every (ATmega4809). Both run the sketch, but they aren't the same board.
4. **Small one:** when a fault happens mid-run, `stoppedAt` isn't updated. That's because `fault()` sets `FAULT` before `stopMotor()` checks for a running state. It only affects the reverse-dwell timer.

## Can it be Python? Yes, but not on the Nano

An Arduino Nano is too small to run Python. The port runs MicroPython on a **Raspberry Pi Pico** (about $5, cheaper than the Nano). The Pico uses 3.3 V signals, so three wiring changes are needed against `../electrical/Motor_Wiring_Diagram.svg`:

| Change | Why |
|---|---|
| Battery divider R2: 15 kΩ → **10 kΩ** | 29.2 V must read under 3.3 V at the Pico (it gives 2.65 V) |
| Add a **10 kΩ / 20 kΩ divider** on the ACS758 output | The sensor still runs on 5 V, but its 0–5 V output must be scaled to under 3.3 V |
| Buzzer through a **2N2222 transistor** (1 kΩ base resistor) | A 3.3 V pin can't drive the 5 V buzzer directly |

The buck converter's 5 V feeds the Pico's VSYS pin. The MDDS30's PWM and DIR inputs accept 3.3 V logic. Pin numbers are in `python/config.py`.

## Python files

| File | What it is |
|---|---|
| `winch_logic.py` | All the rules (the "brain"). Has no hardware code, so it runs on a PC too. |
| `config.py` | Pins and numbers (trip current, battery limit, ramp times). Same values as the C++. |
| `main.py` | Reads the Pico's pins, calls the logic, drives the outputs. |
| `test_winch_logic.py` | 12 tests. Run `python -m unittest test_winch_logic.py` in this folder. |

To load it onto a Pico:

1. Install MicroPython on the Pico (hold BOOTSEL, plug in, drag the `.uf2` from micropython.org).
2. Open Thonny.
3. Save `main.py`, `config.py` and `winch_logic.py` to the Pico.

It starts by itself at power-up.
