"""
Tarp winch controller: Raspberry Pi Pico running MicroPython.

Copy main.py, config.py and winch_logic.py onto the Pico (Thonny: File > Save as > Raspberry
Pi Pico). It starts by itself at power-up. All decisions are made in winch_logic.py; this file
only reads the pins and drives the outputs.

Hardware safety does NOT depend on this code: the key switch, both E-stops and fuse F2 drop
contactor K1, which cuts power to the motor driver and to this board.
"""
from machine import Pin, PWM, ADC
import time
import config as C
from winch_logic import WinchLogic, Inputs

pwm = PWM(Pin(C.PIN_PWM))
pwm.freq(C.PWM_FREQ)
pwm.duty_u16(0)
dir_pin = Pin(C.PIN_DIR, Pin.OUT, value=0)
btn_in = Pin(C.PIN_BTN_IN, Pin.IN, Pin.PULL_UP)
btn_out = Pin(C.PIN_BTN_OUT, Pin.IN, Pin.PULL_UP)
limit = Pin(C.PIN_LIMIT, Pin.IN, Pin.PULL_UP)
latch = Pin(C.PIN_LATCH, Pin.IN, Pin.PULL_UP) if C.HAS_LATCH_SENSOR else None
led = Pin(C.PIN_LED, Pin.OUT, value=0)
buzzer = Pin(C.PIN_BUZZER, Pin.OUT, value=0)
adc_i = ADC(C.PIN_ISENSE)
adc_v = ADC(C.PIN_VBATT)


def volts(adc, n=8):
    s = 0
    for _ in range(n):
        s += adc.read_u16()
    return s / n * C.ADC_VREF / 65535


# current-sensor zero, measured with the motor stopped
time.sleep_ms(200)
acs_zero = sum(volts(adc_i) for _ in range(64)) / 64


def amps():
    return abs(volts(adc_i) - acs_zero) / C.ACS_V_PER_A


def batt():
    return volts(adc_v) * C.VBATT_DIV


# monotonic millisecond counter (time.ticks_ms() wraps; this does not)
_last = time.ticks_ms()
_now = 0


def now_ms():
    global _last, _now
    t = time.ticks_ms()
    _now += time.ticks_diff(t, _last)
    _last = t
    return _now


logic = WinchLogic(C, now_ms(), buttons_at_boot=(btn_in.value() == 0, btn_out.value() == 0))
print(C.NAME, "ready. ACS zero %.3f V, battery %.1f V" % (acs_zero, batt()))
last_log = 0

while True:
    t = now_ms()
    inp = Inputs(
        btn_in=btn_in.value() == 0,
        btn_out=btn_out.value() == 0,
        limit_hit=limit.value() == 1,
        latched=(latch.value() == 0) if latch else None,
        amps=amps(),
        volts=batt(),
    )
    out = logic.step(inp, t)
    if out.dir != 0:
        dir_pin.value(C.DIR_IN_LEVEL if out.dir > 0 else 1 - C.DIR_IN_LEVEL)
    pwm.duty_u16(int(out.duty * 65535))
    led.value(1 if out.led else 0)
    buzzer.value(1 if out.buzzer else 0)

    for e in logic.events:
        print(e)
    logic.events.clear()
    if out.dir != 0 and t - last_log > C.LOG_MS:
        last_log = t
        print("%s %.1f A  %.1f V  duty %.2f" % ("IN " if out.dir > 0 else "OUT", inp.amps, inp.volts, out.duty))
    time.sleep_ms(5)
