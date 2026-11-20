"""
v1 settings for the Python port: same numbers as winch_controller.ino.
Hardware: V1/electrical/Motor_Wiring_Diagram.svg with a Pico in place of the Nano (see V1/code/README.md).
Change numbers here, not in winch_logic.py.
"""
NAME = "Tarp Winch v1 (Python port)"

# ---------------- pins (GPxx numbers on the Pico) ----------------
PIN_PWM = 16        # -> MDDS30 PWM (PWM independent mode)
PIN_DIR = 17        # -> MDDS30 DIR
PIN_BTN_IN = 2      # pendant IN  (N.O. to GND, internal pull-up)
PIN_BTN_OUT = 3     # pendant OUT (N.O. to GND, internal pull-up)
PIN_LIMIT = 4       # rope-in limit, N.C. to GND: HIGH = limit reached OR wire broken (fails safe)
PIN_LATCH = 5       # not used in v1
PIN_LED = 14        # pendant status LED (via 220 ohm)
PIN_BUZZER = 15     # -> 2N2222 base (1k) -> 5 V buzzer
PIN_ISENSE = 26     # ADC0: ACS758 output through a 10k/20k divider
PIN_VBATT = 27      # ADC1: battery through a 100k/22k divider
HAS_LATCH_SENSOR = False            # v1 has no detachable spool

# ---------------- analog scaling ----------------
ADC_VREF = 3.3
ACS_V_PER_A = 0.040 * 20.0 / 30.0   # ACS758LCB-050B is 40 mV/A at 5 V; the 10k/20k divider scales by 2/3
VBATT_DIV = (100.0 + 10.0) / 10.0   # 29.2 V full charge -> 2.65 V. v1 used 15k for the 5 V Nano: change R2 to 10k

# ---------------- tuning ----------------
PWM_FREQ = 16000                    # Hz
TRIP_AMPS = 18.0                    # about 500 lbf rope pull with the v1 gear train (same as the C++)
TRIP_MS = 300                       # must exceed TRIP_AMPS this long to trip
VBATT_MIN = 22.0                    # 24 V LiFePO4 (8S) under load (same as the C++)
DUTY_MAX_IN = 1.0                   # full speed winding in
DUTY_MAX_OUT = 200 / 255.0          # same as the C++ PWM_MAX_OUT
RAMP_MS = 500                       # soft start 0 -> max
RAMP_DOWN_MS = 100                  # soft stop (spares the worm gear)
REVERSE_DWELL_MS = 400              # stopped this long before changing direction
MAX_RUN_MS = 8 * 60 * 1000          # same as the C++
DEBOUNCE_MS = 10
FAULT_CLEAR_MS = 2000               # fault clears after both buttons are released this long
DIR_IN_LEVEL = 1                    # flip to 0 if the drum turns the wrong way when you press IN
LOG_MS = 500
