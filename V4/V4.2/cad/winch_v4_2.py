"""
v4.2 CAD: v4 (../../cad/winch_v4.py) with the changes picked from the v4 sim analysis
(see ../docs/v4_sim_analysis.md):
  * 8 in between spool flanges (was 6 in): the rope fits in 3 layers, so the last-layer
    radius drops from 54 to 48 mm and the torque needed at the end of the pull drops 12 %.
  * 36T big gear (was 48T): 3:1, faster, paired with the stronger motor below.
  * 12 V 55 N·m wiper gearmotor (was 32 N·m).
  * Clear polycarbonate guard over the gear mesh.
Everything else is v4. Run from this folder: python winch_v4_2.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "cad"))
import winch_v4 as w  # noqa: E402

IN = 25.4
V42 = {
    "name": "PoolCover_Winch_v4_2",
    "spool": {"between": 8 * IN},
    "gear": {"teeth": 36},
    "motor_name": "Wiper_Worm_Gearmotor_12V_55Nm",
    "guard": True,
}

if __name__ == "__main__":
    a, P, g = w.build(V42)
    w.export(a, "Pool_Cover_Winch_v4_2_Motor", ".")
    a2, _, _ = w.build(V42, spool_lifted=True)
    w.export(a2, "Pool_Cover_Winch_v4_2_SpoolRemoved", ".")
    print("ok", len(a.children), "parts; base plate", round(g["BW"] / IN), "in wide")
