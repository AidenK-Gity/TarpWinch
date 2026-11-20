"""
Tarp winch controller logic: the "brain", with no hardware in it.

The same file runs on the Raspberry Pi Pico (MicroPython, called from main.py) and on a
normal computer (CPython, called from test_winch_logic.py), so every rule below can be
tested without a winch.

Python port of V1/code/winch_controller/winch_controller.ino, plus fixes:
  * Direction change while running now stops the motor. (The C++ kept winding IN if the
    operator slid straight from IN to OUT between two loop passes.)
  * No blocking delays: stop ramps, fault beeps and debouncing are all time-based.
  * Optional "spool latched" sensor (v4): the motor will not start, and stops with a fault,
    if the detachable spool's latch pin is not in.

Call step(inp, now_ms) about every 5 ms. now_ms must keep counting up (main.py makes a
counter that does not wrap). It returns an Outputs object: motor direction, duty 0..1,
buzzer on/off and LED on/off.
"""

IDLE, RUN_IN, RUN_OUT, STOPPING, FAULT = "IDLE", "RUN_IN", "RUN_OUT", "STOPPING", "FAULT"


class Inputs:
    """One snapshot of every sensor. latched=None means the build has no latch sensor."""

    def __init__(self, btn_in=False, btn_out=False, limit_hit=False, latched=None, amps=0.0, volts=13.0):
        self.btn_in = btn_in
        self.btn_out = btn_out
        self.limit_hit = limit_hit
        self.latched = latched
        self.amps = amps
        self.volts = volts


class Outputs:
    def __init__(self):
        self.dir = 0          # +1 = wind IN, -1 = pay OUT, 0 = stopped
        self.duty = 0.0       # 0..1 PWM duty to the motor driver
        self.buzzer = False
        self.led = False

    def __repr__(self):
        return "Outputs(dir=%d, duty=%.2f, buzzer=%s, led=%s)" % (self.dir, self.duty, self.buzzer, self.led)


class Debounce:
    """A button only changes state after it has read the same for `ms` milliseconds."""

    def __init__(self, ms):
        self.ms = ms
        self.state = False
        self._raw = False
        self._since = 0

    def update(self, raw, now):
        if raw != self._raw:
            self._raw = raw
            self._since = now
        elif raw != self.state and now - self._since >= self.ms:
            self.state = raw
        return self.state


class WinchLogic:
    def __init__(self, cfg, now_ms=0, buttons_at_boot=(False, False)):
        self.c = cfg
        self.state = IDLE
        self.fault_msg = ""
        self.dir = 0
        self.duty = 0.0
        self.run_start = 0
        self.over_since = None
        self.stopped_at = -10 ** 9
        self.last_dir = 0
        self.released_at = None
        self.beep_until = 0
        self.beep_pattern = None      # (start, on_ms, off_ms, count)
        self._prev_want = 0
        self.events = []              # human-readable log lines, main.py prints and clears them
        self.db_in = Debounce(cfg.DEBOUNCE_MS)
        self.db_out = Debounce(cfg.DEBOUNCE_MS)
        self.db_in.state, self.db_out.state = buttons_at_boot
        if buttons_at_boot[0] or buttons_at_boot[1]:
            self._fault("button held at power-up", now_ms)
        else:
            self._beep(now_ms, 100)

    # ---------------- helpers ----------------
    def _log(self, msg):
        self.events.append(msg)

    def _beep(self, now, ms):
        self.beep_until = max(self.beep_until, now + ms)

    def _fault(self, why, now):
        self.state = FAULT
        self.fault_msg = why
        self.dir, self.duty = 0, 0.0
        self.stopped_at = now
        self.released_at = None
        self.beep_pattern = (now, 150, 100, 3)
        self._log("FAULT: " + why)

    def _begin_stop(self, now):
        if self.state in (RUN_IN, RUN_OUT):
            self.state = STOPPING
            self._stop_t0 = now
            self._stop_duty0 = self.duty

    def _buzzer(self, now):
        if self.state in (RUN_IN, RUN_OUT):
            return True                                   # continuous warning tone while moving
        if now < self.beep_until:
            return True
        if self.beep_pattern:
            t0, on, off, n = self.beep_pattern
            k, r = divmod(now - t0, on + off)
            if k < n:
                return r < on
            self.beep_pattern = None
        return False

    # ---------------- main step ----------------
    def step(self, inp, now):
        c = self.c
        b_in = self.db_in.update(inp.btn_in, now)
        b_out = self.db_out.update(inp.btn_out, now)
        out = Outputs()

        if self.state == FAULT:
            # latched: clears after both buttons have been released for FAULT_CLEAR_MS
            if not b_in and not b_out:
                if self.released_at is None:
                    self.released_at = now
                if now - self.released_at >= c.FAULT_CLEAR_MS:
                    self.state = IDLE
                    self._log("fault cleared")
            else:
                self.released_at = None
            out.led = (now // 150) % 2 == 1
            out.buzzer = self._buzzer(now)
            return out

        if self.state == STOPPING:
            f = 1.0 - (now - self._stop_t0) / float(c.RAMP_DOWN_MS)
            if f <= 0:
                self.state, self.duty, self.dir = IDLE, 0.0, 0
                self.stopped_at = now
            else:
                self.duty = self._stop_duty0 * f
            out.dir, out.duty = self.dir, self.duty
            out.led = True
            out.buzzer = self._buzzer(now)
            return out

        want = 1 if (b_in and not b_out) else -1 if (b_out and not b_in) else 0
        edge = want != self._prev_want            # True only on the pass where the request changed
        self._prev_want = want
        running = self.state in (RUN_IN, RUN_OUT)

        # spool latch (v4): never move with the spool unlatched
        if inp.latched is False and running:
            self._fault("spool latch opened while running", now)
            return self._out_fault(now)

        if running:
            cur = 1 if self.state == RUN_IN else -1
            if want != cur:                       # released, both pressed, or direction change
                if want == -cur:
                    self._log("direction change while running: stopping")
                self._begin_stop(now)
                return self.step_outputs(now)
        elif want != 0 and self.state == IDLE:
            if want == 1 and inp.limit_hit:
                if edge:
                    self._beep(now, 80)           # already fully wound in
                return self._idle_out(now, inp)
            if inp.latched is False:
                if edge:
                    self._beep(now, 300)
                    self._log("refused: spool not latched")
                return self._idle_out(now, inp)
            if inp.volts < c.VBATT_MIN:
                self._fault("battery low - charge it", now)
                return self._out_fault(now)
            if want != self.last_dir and now - self.stopped_at < c.REVERSE_DWELL_MS:
                return self._idle_out(now, inp)
            self.state = RUN_IN if want == 1 else RUN_OUT
            self.last_dir = want
            self.dir = want
            self.run_start = now
            self.over_since = None
            self._log("start " + self.state)
        else:
            return self._idle_out(now, inp)

        # ---- running ----
        t = now - self.run_start
        dmax = c.DUTY_MAX_IN if self.state == RUN_IN else c.DUTY_MAX_OUT
        self.duty = dmax if t >= c.RAMP_MS else dmax * t / float(c.RAMP_MS)

        if self.state == RUN_IN and inp.limit_hit:
            self._log("rope-in limit reached")
            self.state, self.duty, self.dir = IDLE, 0.0, 0     # hard stop at the limit
            self.stopped_at = now
            self._beep(now, 400)
            return self._idle_out(now, inp)

        if t > c.RAMP_MS:                                       # ignore inrush during soft start
            if inp.amps > c.TRIP_AMPS:
                if self.over_since is None:
                    self.over_since = now
                if now - self.over_since > c.TRIP_MS:
                    self._fault("overload %.1f A - tarp snagged?" % inp.amps, now)
                    return self._out_fault(now)
            else:
                self.over_since = None
        if t > c.MAX_RUN_MS:
            self._fault("run time exceeded", now)
            return self._out_fault(now)

        return self.step_outputs(now)

    def step_outputs(self, now):
        out = Outputs()
        out.dir, out.duty = self.dir, self.duty
        out.led = True
        out.buzzer = self._buzzer(now)
        return out

    def _idle_out(self, now, inp):
        out = Outputs()
        out.led = ((now // 500) % 2 == 1) if inp.limit_hit else True   # slow blink = rope fully in
        if inp.latched is False:
            out.led = (now // 1000) % 2 == 1                            # very slow blink = spool not latched
        out.buzzer = self._buzzer(now)
        return out

    def _out_fault(self, now):
        out = Outputs()
        out.led = True
        out.buzzer = self._buzzer(now)
        return out
