"""
v2 MOUNT: clamp on the BACK edge of the starting block, roller saddle on the FRONT lip.

Why (load path):
  v1 hooked the front lip with the opening facing the deck, so the rope pulled the clamp
  OFF the block and only the screws' friction held it. v2 flips it:
    * The rear C-clamp opens toward the water. Rope tension drives its back wall straight into
      the platform's rear edge (metal-on-edge bearing, no friction needed).
    * The rope is UNDER-wound (leaves the bottom of the drum) and runs low and level across the
      platform to a roller saddle on the front lip, ~55 mm above the platform instead of ~115 mm.
    * At the roller the rope turns down to the water. The resultant on the saddle points DOWN
      and BACK, so it presses onto the platform and its hook plate bears on the front face.
      It needs no screws at all.
  Every reaction is compression/bearing into the block, and the pull line is half as high.

Builds two assemblies: hand-crank v2 and motorized v2.
Same coordinates as v1: X+ toward water, platform front face at X=0, top at Z=0.
"""
import math
import cadquery as cq
import winch as w
import winch_motor as m
from winch import box, ycyl, zcyl

PLAT_D = 520                 # platform depth front-to-back (any depth works: the two units are independent)
DX = -PLAT_D + 115           # shift that puts the winch frame on top of the rear clamp
ROLLER_X, ROLLER_Z, ROLLER_D = 58, 15, 80
KEEPER_Z = ROLLER_Z + ROLLER_D / 2 + 42   # 37 mm gap: rope can't jump off, 30 mm stopper ball passes
SAD_Y = 55                   # saddle half-width (outer face of cheeks)
CHEEK_T = 10

# ---------- colors ----------
AL = cq.Color(0.70, 0.72, 0.75); SS = cq.Color(0.85, 0.85, 0.88); BR = cq.Color(0.80, 0.62, 0.25)
POM = cq.Color(0.15, 0.15, 0.15); RUB = cq.Color(0.05, 0.05, 0.05); BLUE = cq.Color(0.10, 0.35, 0.80)
ROPE = cq.Color(0.95, 0.55, 0.05); GHOST = cq.Color(0.9, 0.9, 0.9, 0.35); MOT = cq.Color(0.20, 0.22, 0.25)
YEL = cq.Color(0.95, 0.80, 0.10); RED = cq.Color(0.85, 0.10, 0.10); GRN = cq.Color(0.10, 0.65, 0.20)
GRY = cq.Color(0.45, 0.47, 0.50); ORGB = cq.Color(0.95, 0.45, 0.05)


def mv(s, dx=DX, dy=0, dz=0):
    return s.translate((dx, dy, dz))


def mirror_x(s):
    """Mirror across the YZ plane (X -> -X)."""
    return s.mirror("YZ")


# ---------- reference platform (full depth) ----------
def platform(t=40):
    return box(-PLAT_D, 0, -260, 260, -t - 3, -3)


# ---------- rear clamp: v1 clamp flipped to face the water, moved to the rear edge ----------
def rear_clamp():
    return mv(mirror_x(w.clamp()), -PLAT_D)


def rear_liner():
    return mv(mirror_x(w.rubber_pad_top()), -PLAT_D)


def rear_screws():
    out = []
    for yy in (-45, 45):
        pad, scr = w.clamp_screw(yy)
        out.append((mv(mirror_x(pad), -PLAT_D), mv(mirror_x(scr), -PLAT_D)))
    return out


# ---------- winch frame (trimmed: no front sheave needed) ----------
def side_plate_v2(y0, y1, left):
    p = w.side_plate(y0, y1, left)
    return p.intersect(box(-200, 70, y0 - 1, y1 + 1, -50, 400))


# ---------- ratchet/pawl mirrored for under-wind (load now turns the drum the other way) ----------
def mirror_about_drum(s):
    return s.mirror("YZ", basePointVector=(w.DRUM_X, 0, 0))


# ---------- front roller saddle ----------
def saddle():
    base = box(-150, 0, -SAD_Y, SAD_Y, 0, 10)
    hook = box(3, 15, -SAD_Y, SAD_Y, -50, 10)                     # bears on the platform's front face
    cheek_prof = [(-60, 10), (15, 10), (15, -40), (95, -15), (95, 40), (75, 108), (35, 108), (-60, 30)]
    s = base.union(hook)
    for yo in (SAD_Y - CHEEK_T, -SAD_Y):
        c = (cq.Workplane("XZ", origin=(0, yo + CHEEK_T, 0)).polyline(cheek_prof).close().extrude(CHEEK_T))
        s = s.union(c)
    s = s.cut(ycyl(16.5, -SAD_Y - 1, SAD_Y + 1, ROLLER_X, ROLLER_Z))
    s = s.cut(ycyl(10.5, -SAD_Y - 1, SAD_Y + 1, ROLLER_X, KEEPER_Z))
    for xx in (-120, -80):                                         # drain slots
        s = s.cut(box(xx, xx + 12, -30, 30, -1, 11))
    return s


def saddle_pads():
    top = box(-148, 0, -SAD_Y + 2, SAD_Y - 2, -3, 0)
    face = box(0, 3, -SAD_Y + 2, SAD_Y - 2, -43, -3)
    return top.union(face)


def roller():
    half = SAD_Y - CHEEK_T - 3
    r = ycyl(ROLLER_D, -half, half, ROLLER_X, ROLLER_Z)
    groove = (cq.Workplane("XZ").center(ROLLER_D / 2 + 1, 0).circle(5.5)
              .revolve(360, (-(ROLLER_D / 2 + 1), 0, 0), (-(ROLLER_D / 2 + 1), 1, 0))
              .translate((ROLLER_X, 0, ROLLER_Z)))
    r = r.cut(groove).cut(ycyl(16.5, -half - 1, half + 1, ROLLER_X, ROLLER_Z))
    axle = ycyl(16, -SAD_Y - 6, SAD_Y + 6, ROLLER_X, ROLLER_Z)
    keeper = ycyl(10, -SAD_Y - 4, SAD_Y + 4, ROLLER_X, KEEPER_Z)
    return r, axle, keeper


def limit_switch_v2():
    """Rope-in limit on the saddle: lever roller sits just under the rope; the stopper ball lifts it."""
    body = box(-70, -30, 18, 45, 10, 38)
    arm = box(-53, -47, -6, 18, 30, 36)
    rol = ycyl(12, -8, 8, -50, 40)
    return body, arm.union(rol)


# ---------- rope (under-wound) ----------
def rope_v2():
    dz = w.DRUM_Z
    half = w.DRUM_LEN / 2 - w.FL_T
    band = (ycyl(w.DRUM_CORE_D + 24, -half, half, w.DRUM_X + DX, dz)
            .cut(ycyl(w.DRUM_CORE_D, -half - 1, half + 1, w.DRUM_X + DX, dz)))
    z_run = dz - w.DRUM_CORE_D / 2 - 12                               # leaves bottom of the wrap band
    p0 = cq.Vector(w.DRUM_X + DX, 0, z_run)
    top = ROLLER_Z + ROLLER_D / 2 - 4
    p1 = cq.Vector(ROLLER_X, 0, top)
    run = cq.Solid.makeCylinder(3, (p1 - p0).Length, p0, (p1 - p0).normalized())
    p2 = cq.Vector(ROLLER_X + ROLLER_D / 2 - 4, 0, ROLLER_Z)
    d = cq.Vector(math.cos(math.radians(-60)), 0, math.sin(math.radians(-60)))
    drop = cq.Solid.makeCylinder(3, 400, p2, d)
    return band.union(cq.Workplane().add(run)).union(cq.Workplane().add(drop))


def common(a):
    a.add(platform(), name="REF_StartingBlock_Platform_520x40", color=GHOST)
    a.add(rear_clamp(), name="Rear_Clamp_6061T6_HardAnodized", color=BLUE)
    a.add(rear_liner(), name="Rear_Clamp_Neoprene_Liner", color=RUB)
    for i, (pad, scr) in enumerate(rear_screws()):
        a.add(pad, name=f"Swivel_Pad_{i+1}_Rubber", color=RUB)
        a.add(scr, name=f"Clamp_Screw_M16_316SS_{i+1}", color=SS)
    a.add(mv(side_plate_v2(*w.Y_PLATE_R, False)), name="Side_Plate_R_6061T6", color=AL)
    a.add(mv(w.standoffs()), name="Standoffs_316SS", color=SS)
    a.add(mv(w.angle_brackets()), name="Mount_Brackets_6061T6", color=AL)
    a.add(mv(w.drum()), name="Rope_Drum_UHMW", color=POM)
    a.add(mv(w.drum_shaft()), name="Drum_Shaft_25mm_316SS", color=SS)
    g, y_out = w.gear_big()
    a.add(mv(g), name="Gear_48T_m3_Bronze", color=BR)
    a.add(mv(w.gear_pinion(y_out)), name="Pinion_12T_m3_316SS", color=SS)
    a.add(saddle(), name="Front_Roller_Saddle_6061T6", color=BLUE)
    a.add(saddle_pads(), name="Saddle_Neoprene_Pads", color=RUB)
    r, axle, keeper = roller()
    a.add(r, name="Front_Roller_80mm_UHMW", color=POM)
    a.add(axle, name="Roller_Axle_16mm_316SS", color=SS)
    a.add(keeper, name="Rope_Keeper_Bar_316SS", color=SS)
    a.add(rope_v2(), name="Rope_6mm_Dyneema_underwound", color=ROPE)
    return y_out


def build_crank():
    a = cq.Assembly(name="PoolCover_Winch_v2_RearClamp_CRANK")
    y_out = common(a)
    a.add(mv(side_plate_v2(*w.Y_PLATE_L, False).cut(
        ycyl(10.5, -100, 0, 2 * w.DRUM_X - w.PAWL_PIVOT[0], w.PAWL_PIVOT[1]))),
        name="Side_Plate_L_6061T6", color=AL)
    a.add(mv(w.pinion_shaft()), name="Pinion_Shaft_20mm_316SS", color=SS)
    a.add(mv(w.bearings()), name="Flange_Bearings_SS_2RS", color=SS)
    arm, knob = w.crank(y_out)
    a.add(mv(arm), name="Crank_Arm_200mm_316SS", color=SS)
    a.add(mv(knob), name="Crank_Knob_Rubber", color=RUB)
    rw, ry0, ry1 = w.ratchet()
    pw, pin = w.pawl(ry0, ry1)
    a.add(mv(mirror_about_drum(rw)), name="Ratchet_Wheel_20T_316SS", color=SS)
    a.add(mv(mirror_about_drum(pw)), name="Pawl_316SS", color=RED)
    a.add(mv(mirror_about_drum(pin)), name="Pawl_Pivot_Pin", color=SS)
    return a


def build_motor():
    a = cq.Assembly(name="PoolCover_Winch_v2_RearClamp_MOTORIZED")
    common(a)
    a.add(mv(side_plate_v2(*w.Y_PLATE_L, False)), name="Side_Plate_L_6061T6", color=AL)
    a.add(mv(w.bearings()), name="Flange_Bearings_SS_2RS", color=SS)
    a.add(mv(m.output_shaft()), name="Gearmotor_Output_Shaft_20mm_316SS", color=SS)
    a.add(mv(m.outrigger_plate()), name="Motor_Outrigger_Plate_6061T6", color=AL)
    a.add(mv(m.outrigger_standoffs()), name="Outrigger_Standoffs_316SS", color=SS)
    gb, mot = m.gearmotor()
    a.add(mv(gb), name="Worm_Gearbox_IP65", color=GRY)
    a.add(mv(mot), name="Motor_24VDC_350W_IP65", color=MOT)
    lb, lv = limit_switch_v2()
    a.add(lb, name="Limit_Switch_RopeIn_IP67", color=YEL)
    a.add(lv, name="Limit_Switch_Lever", color=SS)
    # control box + pendant beside the winch, on the platform
    cb, cbx, estop = m.control_box()
    sh = (110, -30, 0)
    a.add(cb.translate(sh), name="Battery_Controller_Box_IP67", color=YEL)
    a.add(cbx.translate(sh), name="Box_KeySwitch_Glands", color=RUB)
    a.add(estop.translate(sh), name="EStop_Mushroom", color=RED)
    pb, pbtn, pstop = m.pendant()
    ps = (120, 60, 0)
    a.add(pb.translate(ps), name="Pendant_IP67", color=YEL)
    a.add(pbtn.translate(ps), name="Pendant_IN_OUT_Buttons", color=GRN)
    a.add(pstop.translate(ps), name="Pendant_EStop", color=RED)
    # cables: box -> motor, box -> pendant, box -> limit switch (along platform edge)
    def cable(pts, r=5):
        sol = []
        for p0, p1 in zip(pts[:-1], pts[1:]):
            p0, p1 = cq.Vector(*p0), cq.Vector(*p1)
            sol.append(cq.Solid.makeCylinder(r, (p1 - p0).Length, p0, (p1 - p0).normalized()))
            sol.append(cq.Solid.makeSphere(r, p1))
        return sol
    gx = m.GB_X0 - 40 + DX
    c = (cable([(-245, -150, 202), (-245, -150, 300), (gx, m.MOTOR_AX_Y, 300), (gx, m.MOTOR_AX_Y, 258)])
         + (cable([(-190, -180, 60), (-160, -170, 20), (-142, -165, 20)], 4))
         + (cable([(-190, -100, 30), (-60, 0, 25), (-60, 18, 25)], 4)))
    a.add(cq.Workplane().add(cq.Compound.makeCompound(c)), name="Cables", color=RUB)
    return a


def export(a, stem):
    a.save(f"out/{stem}.step")
    parts = [c for c in a.children if not c.name.startswith("REF_")]
    comp = cq.Compound.makeCompound([v for c in parts for v in c.obj.vals()])
    cq.exporters.export(cq.Workplane().add(comp), f"out/{stem}.stl", tolerance=0.3, angularTolerance=0.3)


if __name__ == "__main__":
    export(build_crank(), "Pool_Cover_Winch_v2_RearClamp_CRANK")
    export(build_motor(), "Pool_Cover_Winch_v2_RearClamp_MOTORIZED")
    print("ok")
