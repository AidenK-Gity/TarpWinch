"""
MOTORIZED version of the starting-block pool-cover winch (separate design).
Reuses the clamp, frame, drum, 4:1 spur stage and fairlead from winch.py, and replaces:
  - hand crank        -> 24 V DC worm gearmotor (>=350 W, ~55 rpm, >=45 N*m rated)
  - ratchet + pawl     -> removed (worm gearbox is self-locking; firmware holds/brakes)
Adds:
  - outrigger plate + standoffs that carry the gearmotor off the right side plate
  - rope-in limit switch at the fairlead (stopper ball on the rope trips it)
  - IP67 battery/controller box and hold-to-run pendant (reference placement)
All dims mm, same coordinate system as winch.py.
"""
import math
import cadquery as cq
import winch as w
from winch import box, ycyl, zcyl

# gearbox / motor
Y_OUTRIG = (106, 114)                 # outrigger plate Y span
GB_X0, GB_X1 = -95, 15                # worm gearbox body
GB_Y0, GB_Y1 = 120, 200
GB_Z0, GB_Z1 = w.PIN_Z - 45, w.PIN_Z + 45
MOTOR_D, MOTOR_L = 100, 190
MOTOR_AX_Y, MOTOR_AX_Z = 168, w.PIN_Z - 22   # worm axis offset below the output shaft
OUT_STANDOFFS = [(60, 150), (-120, 60), (-120, 180)]


def outrigger_plate():
    y0, y1 = Y_OUTRIG
    prof = [(-135, 45), (-100, 45), (75, 130), (75, 175), (25, 255), (-110, 255), (-135, 215)]
    p = cq.Workplane("XZ", origin=(0, y1, 0)).polyline(prof).close().extrude(y1 - y0)
    p = p.cut(ycyl(42, y0 - 1, y1 + 1, w.PIN_X, w.PIN_Z))      # bearing seat for output shaft
    for sx, sz in OUT_STANDOFFS:
        p = p.cut(ycyl(10.5, y0 - 1, y1 + 1, sx, sz))
    p = p.cut(ycyl(30, y0 - 1, y1 + 1, -60, 110))             # lightening / drain
    return p


def outrigger_standoffs():
    s = None
    y0 = w.SP_IN + w.SP_T
    for sx, sz in OUT_STANDOFFS:
        t = ycyl(20, y0, Y_OUTRIG[0], sx, sz).cut(ycyl(10.5, y0 - 1, Y_OUTRIG[0] + 1, sx, sz))
        s = t if s is None else s.union(t)
    return s


def gearmotor():
    gb = box(GB_X0, GB_X1, GB_Y0, GB_Y1, GB_Z0, GB_Z1)
    flange = box(GB_X0 - 5, GB_X1 + 5, Y_OUTRIG[1], GB_Y0, GB_Z0 - 5, GB_Z1 + 5)
    gb = gb.union(flange).cut(ycyl(20, Y_OUTRIG[1] - 1, GB_Y0 + 11, w.PIN_X, w.PIN_Z))
    # motor can runs back toward the deck along -X
    can = (cq.Workplane("YZ", origin=(GB_X0 - 5 - MOTOR_L, 0, 0)).center(MOTOR_AX_Y, MOTOR_AX_Z)
           .circle(MOTOR_D / 2).extrude(MOTOR_L))
    endcap = (cq.Workplane("YZ", origin=(GB_X0 - 5 - MOTOR_L - 20, 0, 0)).center(MOTOR_AX_Y, MOTOR_AX_Z)
              .circle(MOTOR_D / 2 - 8).extrude(20))
    gland = (cq.Workplane("XY", origin=(0, 0, MOTOR_AX_Z + MOTOR_D / 2 - 5))
             .center(GB_X0 - 40, MOTOR_AX_Y).circle(10).extrude(25))
    return gb, can.union(endcap).union(gland)


def output_shaft():
    return ycyl(20, w.SP_IN - 2, GB_Y0 + 10, w.PIN_X, w.PIN_Z)


def limit_switch():
    """IP67 roller-lever limit switch on the inside of the R plate, just behind the sheave.
    A stopper ball crimped on the rope (near the tarp end) pushes the lever -> motor stops."""
    sx, sz = 85, 148
    body = box(sx - 25, sx + 25, w.SP_IN - 30, w.SP_IN, sz - 12, sz + 14)
    # lever arm reaches across to the rope centreline; roller rides ~15 mm above the rope
    lever = box(sx - 3, sx + 3, 4, w.SP_IN - 30, sz - 4, sz + 2)
    drop = box(sx - 3, sx + 3, 4, 10, sz - 18, sz - 4)
    roller = ycyl(12, -6, 14, sx, sz - 18)
    lever = lever.union(drop)
    return body, lever.union(roller)


def control_box():
    """IP67 battery + controller box sitting behind the winch (can also sit on the deck)."""
    x0, x1, y0, y1, z0, z1 = -410, -300, -230, -20, 0, 190
    b = box(x0, x1, y0, y1, z0, z1)
    lid = box(x0 - 3, x1 + 3, y0 - 3, y1 + 3, z1, z1 + 12)
    estop_base = zcyl(44, z1 + 12, z1 + 30, (x0 + x1) / 2, y1 - 45)
    estop = zcyl(40, z1 + 30, z1 + 48, (x0 + x1) / 2, y1 - 45)
    key = zcyl(24, z1 + 12, z1 + 22, (x0 + x1) / 2, y0 + 50)
    glands = None
    for zz in (60, 110):
        g = (cq.Workplane("YZ", origin=(x1, 0, 0)).center(-60, zz).circle(9).extrude(18))
        glands = g if glands is None else glands.union(g)
    return b.union(lid), estop_base.union(key).union(glands), estop


def pendant():
    """Hold-to-run pendant hanging from its cable (IP67), shown resting on the platform."""
    x, y = -230, -170
    body = box(x - 30, x + 30, y - 110, y, 0, 40)
    btns = zcyl(18, 40, 46, x, y - 30).union(zcyl(18, 40, 46, x, y - 65))
    stop = zcyl(22, 40, 52, x, y - 95)
    return body, btns, stop


def cables():
    """Simplified cable runs: control box -> motor, control box -> pendant."""
    c1p0 = cq.Vector(-300, -60, 110)
    c1p1 = cq.Vector(GB_X0 - 40, MOTOR_AX_Y, MOTOR_AX_Z + MOTOR_D / 2 + 20)
    c1 = cq.Solid.makeCylinder(5, (c1p1 - c1p0).Length, c1p0, (c1p1 - c1p0).normalized())
    c2p0 = cq.Vector(-300, -120, 60)
    c2p1 = cq.Vector(-230, -170, 20)
    c2 = cq.Solid.makeCylinder(4, (c2p1 - c2p0).Length, c2p0, (c2p1 - c2p0).normalized())
    return cq.Workplane().add(c1).union(cq.Workplane().add(c2))


def build():
    a = cq.Assembly(name="StartingBlock_PoolCover_Winch_MOTORIZED")
    AL = cq.Color(0.70, 0.72, 0.75)
    SS = cq.Color(0.85, 0.85, 0.88)
    BR = cq.Color(0.80, 0.62, 0.25)
    POM = cq.Color(0.15, 0.15, 0.15)
    RUB = cq.Color(0.05, 0.05, 0.05)
    BLUE = cq.Color(0.10, 0.35, 0.80)
    ROPE = cq.Color(0.95, 0.55, 0.05)
    GHOST = cq.Color(0.9, 0.9, 0.9, 0.35)
    MOT = cq.Color(0.20, 0.22, 0.25)
    YEL = cq.Color(0.95, 0.80, 0.10)
    RED = cq.Color(0.85, 0.10, 0.10)
    GRN = cq.Color(0.10, 0.65, 0.20)
    GRY = cq.Color(0.45, 0.47, 0.50)

    a.add(w.platform_ghost(), name="REF_StartingBlock_Platform_40mm", color=GHOST)
    a.add(w.clamp(), name="Clamp_Body_6061T6_HardAnodized", color=BLUE)
    a.add(w.rubber_pad_top(), name="Neoprene_Liner", color=RUB)
    for i, yy in enumerate((-45, 45)):
        pad, scr = w.clamp_screw(yy)
        a.add(pad, name=f"Swivel_Pad_{i+1}_Rubber", color=RUB)
        a.add(scr, name=f"Clamp_Screw_M16_316SS_{i+1}", color=SS)
    a.add(w.side_plate(*w.Y_PLATE_R, False), name="Side_Plate_R_6061T6", color=AL)
    a.add(w.side_plate(*w.Y_PLATE_L, False), name="Side_Plate_L_6061T6", color=AL)
    a.add(w.standoffs(), name="Standoffs_316SS", color=SS)
    a.add(w.angle_brackets(), name="Mount_Brackets_6061T6", color=AL)
    a.add(w.drum(), name="Rope_Drum_UHMW", color=POM)
    a.add(w.drum_shaft(), name="Drum_Shaft_25mm_316SS", color=SS)
    a.add(w.bearings(), name="Flange_Bearings_SS_2RS", color=SS)
    g, y_out = w.gear_big()
    a.add(g, name="Gear_48T_m3_Bronze", color=BR)
    a.add(w.gear_pinion(y_out), name="Pinion_12T_m3_316SS", color=SS)
    a.add(output_shaft(), name="Gearmotor_Output_Shaft_20mm_316SS", color=SS)
    a.add(outrigger_plate(), name="Motor_Outrigger_Plate_6061T6", color=AL)
    a.add(outrigger_standoffs(), name="Outrigger_Standoffs_316SS", color=SS)
    gb, mot = gearmotor()
    a.add(gb, name="Worm_Gearbox_IP65", color=GRY)
    a.add(mot, name="Motor_24VDC_350W_IP65", color=MOT)
    s, axle, spacers, keeper = w.sheave()
    a.add(s, name="Fairlead_Sheave_80mm_UHMW", color=POM)
    a.add(axle, name="Sheave_Axle_16mm_316SS", color=SS)
    a.add(spacers, name="Sheave_Spacers", color=SS)
    a.add(keeper, name="Rope_Keeper_Bar_316SS", color=SS)
    lb, lv = limit_switch()
    a.add(lb, name="Limit_Switch_RopeIn_IP67", color=YEL)
    a.add(lv, name="Limit_Switch_Lever", color=SS)
    a.add(w.rope(), name="Rope_6mm_Dyneema", color=ROPE)
    cb, cbx, estop = control_box()
    a.add(cb, name="Battery_Controller_Box_IP67", color=YEL)
    a.add(cbx, name="Box_KeySwitch_Glands", color=RUB)
    a.add(estop, name="EStop_Mushroom", color=RED)
    pb, pbtn, pstop = pendant()
    a.add(pb, name="Pendant_IP67", color=YEL)
    a.add(pbtn, name="Pendant_IN_OUT_Buttons", color=GRN)
    a.add(pstop, name="Pendant_EStop", color=RED)
    a.add(cables(), name="Cables", color=RUB)
    return a


if __name__ == "__main__":
    a = build()
    a.save("out/Pool_Cover_Winch_MOTORIZED.step")
    parts = [c for c in a.children if not c.name.startswith("REF_")]
    comp = cq.Compound.makeCompound([v for c in parts for v in c.obj.vals()])
    cq.exporters.export(cq.Workplane().add(comp), "out/Pool_Cover_Winch_MOTORIZED.stl",
                        tolerance=0.3, angularTolerance=0.3)
    print("ok", len(a.children), "parts")
