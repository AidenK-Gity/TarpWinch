"""
v4 settings: pins (Raspberry Pi Pico) and tuning. Matches V4/electrical/V4_Wiring_Diagram.svg.
Change numbers here, not in winch_logic.py.
"""
NAME = "Tarp Winch v4"

# ---------------- pins (GPxx numbers on the Pico) ----------------
PIN_PWM = 16        # -> MD30C PWM
PIN_DIR = 17        # -> MD30C DIR
PIN_BTN_IN = 2      # pendant IN  (N.O. to GND, internal pull-up)
PIN_BTN_OUT = 3     # pendant OUT (N.O. to GND, internal pull-up)
PIN_LIMIT = 4       # rope-in limit, N.C. to GND: HIGH = limit reached OR wire broken (fails safe)
PIN_LATCH = 5       # spool-latched reed, closes to GND when the ball-lock pin is in: HIGH = NOT latched
PIN_LED = 14        # pendant status LED (via 220 ohm)
PIN_BUZZER = 15     # -> 2N2222 base (1k) -> 5 V buzzer
PIN_ISENSE = 26     # ADC0: ACS758 output through a 10k/20k divider
PIN_VBATT = 27      # ADC1: battery through a 100k/22k divider
HAS_LATCH_SENSOR = True

# ---------------- analog scaling ----------------
ADC_VREF = 3.3
ACS_V_PER_A = 0.040 * 20.0 / 30.0   # ACS758LCB-050B is 40 mV/A at 5 V; the 10k/20k divider scales by 2/3
VBATT_DIV = (100.0 + 22.0) / 22.0   # 14.6 V full charge -> 2.63 V at the pin

# ---------------- tuning ----------------
PWM_FREQ = 16000                    # Hz, MD30C accepts up to 20 kHz
TRIP_AMPS = 25.0                    # sim peak is 21.8 A at the end of a full pull (about 300 lbf rope)
TRIP_MS = 300                       # must exceed TRIP_AMPS this long to trip
VBATT_MIN = 12.0                    # 12 V LiFePO4: refuse to start below this
DUTY_MAX_IN = 1.0                   # full speed winding in
DUTY_MAX_OUT = 0.8                  # pay out a little slower
RAMP_MS = 500                       # soft start 0 -> max
RAMP_DOWN_MS = 100                  # soft stop (spares the worm gear)
REVERSE_DWELL_MS = 400              # stopped this long before changing direction
MAX_RUN_MS = 12 * 60 * 1000         # watchdog: no single run longer than 12 min (sim full pull: 7.5 min)
DEBOUNCE_MS = 10
FAULT_CLEAR_MS = 2000               # fault clears after both buttons are released this long
DIR_IN_LEVEL = 1                    # flip to 0 if the spool turns the wrong way when you press IN
LOG_MS = 500
