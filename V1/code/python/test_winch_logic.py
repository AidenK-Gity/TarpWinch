"""
Tests for winch_logic.py. Runs on a normal computer, no Pico needed:
    python -m unittest test_winch_logic.py      (from this folder)
"""
import unittest
import config as C
from winch_logic import WinchLogic, Inputs, IDLE, RUN_IN, RUN_OUT, STOPPING, FAULT


class Rig:
    """Steps the logic in 5 ms ticks with a given input, like main.py does."""

    def __init__(self, cfg=C, boot=(False, False)):
        self.t = 0
        self.L = WinchLogic(cfg, 0, buttons_at_boot=boot)
        self.out = None

    def run(self, ms, **kw):
        kw.setdefault("latched", True if cfg_has_latch(self.L.c) else None)
        kw.setdefault("volts", self.L.c.VBATT_MIN + 1.5)       # a healthy battery for this build
        inp = Inputs(**kw)
        for _ in range(int(ms / 5)):
            self.t += 5
            self.out = self.L.step(inp, self.t)
        return self.out


def cfg_has_latch(c):
    return getattr(c, "HAS_LATCH_SENSOR", False)


class TestWinchLogic(unittest.TestCase):
    def test_hold_to_run_and_ramp(self):
        r = Rig()
        o = r.run(250, btn_in=True)
        self.assertEqual(r.L.state, RUN_IN)
        self.assertEqual(o.dir, 1)
        self.assertGreater(o.duty, 0.2)
        self.assertLess(o.duty, 0.6)                 # still ramping
        o = r.run(500, btn_in=True)
        self.assertAlmostEqual(o.duty, C.DUTY_MAX_IN)
        self.assertTrue(o.buzzer)                     # warning tone while moving

    def test_release_stops_quickly(self):
        r = Rig()
        r.run(1000, btn_in=True)
        r.run(30)
        self.assertEqual(r.L.state, STOPPING)
        o = r.run(C.RAMP_DOWN_MS + 20)
        self.assertEqual(r.L.state, IDLE)
        self.assertEqual(o.duty, 0)

    def test_direction_change_stops(self):
        """C++ bug: sliding straight from IN to OUT kept winding IN. Now it stops."""
        r = Rig()
        r.run(1000, btn_in=True)
        r.run(50, btn_out=True)
        self.assertIn(r.L.state, (STOPPING, IDLE))
        self.assertTrue(any("direction change" in e for e in r.L.events))
        r.run(C.RAMP_DOWN_MS + C.REVERSE_DWELL_MS + 50, btn_out=True)
        self.assertEqual(r.L.state, RUN_OUT)          # then goes the new way after the dwell

    def test_both_buttons_stop(self):
        r = Rig()
        r.run(1000, btn_in=True)
        r.run(50, btn_in=True, btn_out=True)
        self.assertIn(r.L.state, (STOPPING, IDLE))

    def test_limit_blocks_and_stops_in_only(self):
        r = Rig()
        r.run(500, btn_in=True, limit_hit=True)
        self.assertEqual(r.L.state, IDLE)             # fully wound: IN refused
        r.run(600)
        r.run(500, btn_out=True, limit_hit=True)
        self.assertEqual(r.L.state, RUN_OUT)          # OUT still allowed
        r = Rig()
        r.run(1000, btn_in=True)
        o = r.run(10, btn_in=True, limit_hit=True)
        self.assertEqual(r.L.state, IDLE)
        self.assertEqual(o.duty, 0)

    def test_overcurrent_trips_after_delay_and_latches(self):
        r = Rig()
        r.run(1000, btn_in=True, amps=5)
        r.run(C.TRIP_MS - 50, btn_in=True, amps=C.TRIP_AMPS + 3)
        self.assertEqual(r.L.state, RUN_IN)           # short spike tolerated
        r.run(200, btn_in=True, amps=C.TRIP_AMPS + 3)
        self.assertEqual(r.L.state, FAULT)
        r.run(500, btn_in=True)
        self.assertEqual(r.L.state, FAULT)            # stays latched while a button is held
        r.run(C.FAULT_CLEAR_MS + 50)
        self.assertEqual(r.L.state, IDLE)

    def test_inrush_ignored_during_ramp(self):
        r = Rig()
        r.run(C.RAMP_MS - 20, btn_in=True, amps=C.TRIP_AMPS * 2)
        self.assertEqual(r.L.state, RUN_IN)

    def test_low_battery_refuses(self):
        r = Rig()
        r.run(100, btn_in=True, volts=C.VBATT_MIN - 0.5)
        self.assertEqual(r.L.state, FAULT)
        self.assertIn("battery", r.L.fault_msg)

    def test_button_held_at_boot_faults(self):
        r = Rig(boot=(True, False))
        self.assertEqual(r.L.state, FAULT)

    def test_watchdog(self):
        r = Rig()
        r.run(C.MAX_RUN_MS + 100, btn_in=True)
        self.assertEqual(r.L.state, FAULT)

    @unittest.skipUnless(cfg_has_latch(C), "no spool latch sensor in this build")
    def test_spool_not_latched_refuses(self):
        r = Rig()
        r.run(300, btn_in=True, latched=False)
        self.assertEqual(r.L.state, IDLE)
        self.assertEqual(sum("not latched" in e for e in r.L.events), 1)   # logged once per press, not every tick

    @unittest.skipUnless(cfg_has_latch(C), "no spool latch sensor in this build")
    def test_latch_opening_while_running_faults(self):
        r = Rig()
        r.run(1000, btn_in=True)
        o = r.run(10, btn_in=True, latched=False)
        self.assertEqual(r.L.state, FAULT)
        self.assertEqual(o.duty, 0)


if __name__ == "__main__":
    unittest.main()
