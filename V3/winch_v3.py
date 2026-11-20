"""
v3 (budget, under $200): off-the-shelf hand trailer winch on a bolt-together aluminum mount.

Same mounting idea as v2, made from stock shapes:
  * REAR HOOK: one 8 in piece of 2 x 2 x 1/4 in 6061 angle drops over the block's BACK edge.
    A 1/4 in aluminum plate bolted on top carries the winch. Rope pull drives the angle's
    leg into the platform edge, and tips the plate's front end DOWN onto the block.
  * WINCH: a 3,500 lb hand trailer winch with its strap removed, used as a capstan:
    4 wraps of rope round the drum, loose end tailed by hand, so any rope length works.
  * FRONT: a second 8 in piece of the same angle hooks the FRONT lip. A stainless
    eye bolt through its front leg carries a single pulley block that turns the rope down.
All dims in mm. X+ = toward water, platform front face X=0, top Z=0.
"""
import math
import cadquery as cq

IN = 25.4
PLAT_D = 520
T = 0.25 * IN            # angle / plate thickness
LEG = 2 * IN
ANG_L = 8 * IN           # angle pieces are 8 in long (along Y)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def ycyl(d, y0, y1, x, z):
    return cq.Workplane("XZ", origin=(0, y1, 0)).center(x, z).circle(d / 2).extrude(y1 - y0)


def xcyl(d, x0, x1, y, z):
    return cq.Workplane("YZ", origin=(x0, 0, 0)).center(y, z).circle(d / 2).extrude(x1 - x0)


def angle(x_face, outward, y0, y1):
    """2x2x1/4 angle: horizontal leg on top of the platform, vertical leg down a face.
    x_face = face of the platform the leg hangs down; outward = +1 front face, -1 back face."""
    if outward > 0:
        horiz = box(x_face - LEG + T, x_face + T, y0, y1, 0, T)
        vert = box(x_face, x_face + T, y0, y1, -LEG + T, T)
    else:
        horiz = box(x_face - T, x_face + LEG - T, y0, y1, 0, T)
        vert = box(x_face - T, x_face, y0, y1, -LEG + T, T)
    return horiz.union(vert)


# ---- rear mount ----
XR = -PLAT_D
rear_angle = angle(XR, -1, -ANG_L / 2, ANG_L / 2)
plate = box(XR - T, XR - T + 12 * IN, -4 * IN, 4 * IN, T, 2 * T)
for (bx, by) in ((XR + 0.8 * IN, -3 * IN), (XR + 0.8 * IN, 3 * IN), (XR + 11 * IN, -3 * IN), (XR + 11 * IN, 3 * IN)):
    plate = plate.cut(cq.Workplane("XY", origin=(0, 0, -1)).center(bx, by).circle(4.2).extrude(30))

# ---- winch (simplified KFFKFF/AC-DK style 3,500 lb hand winch) ----
WX = XR + 3.5 * IN            # drum axis X
DRUM_Z = 2 * T + 2.6 * IN     # drum axis height
base = box(WX - 2.2 * IN, WX + 2.4 * IN, -1.9 * IN, 1.9 * IN, 2 * T, 2 * T + 0.15 * IN)
frame_l = box(WX - 2.2 * IN, WX + 1.6 * IN, -1.9 * IN, -1.75 * IN, 2 * T, DRUM_Z + 1.4 * IN)
frame_r = box(WX - 2.2 * IN, WX + 1.6 * IN, 1.75 * IN, 1.9 * IN, 2 * T, DRUM_Z + 1.4 * IN)
drum = ycyl(1.5 * IN, -1.75 * IN, 1.75 * IN, WX, DRUM_Z)
drum_fl = ycyl(3.0 * IN, -1.75 * IN, -1.6 * IN, WX, DRUM_Z).union(ycyl(3.0 * IN, 1.6 * IN, 1.75 * IN, WX, DRUM_Z))
gear = ycyl(3.6 * IN, 1.9 * IN, 2.1 * IN, WX, DRUM_Z)
pin_z = DRUM_Z + 1.1 * IN
pin_x = WX - 1.5 * IN
handle_shaft = ycyl(0.6 * IN, -1.9 * IN, 2.9 * IN, pin_x, pin_z)
pinion = ycyl(0.9 * IN, 1.9 * IN, 2.1 * IN, pin_x, pin_z)
arm = (cq.Workplane("XZ", origin=(0, 3.1 * IN, 0))
       .polyline([(pin_x - 6, pin_z), (pin_x + 6, pin_z), (pin_x - 4 * IN + 5, pin_z + 8 * IN), (pin_x - 4 * IN - 5, pin_z + 8 * IN)])
       .close().extrude(0.2 * IN))
knob = ycyl(1.0 * IN, 3.1 * IN, 7.1 * IN, pin_x - 4 * IN, pin_z + 8 * IN)
pawl = box(WX - 0.4 * IN, WX + 0.4 * IN, 2.1 * IN, 2.3 * IN, DRUM_Z + 1.9 * IN, DRUM_Z + 2.4 * IN)
winch_body = base.union(frame_l).union(frame_r).union(drum_fl).union(gear).union(pinion).union(pawl)
for (bx, by) in ((WX - 1.8 * IN, -1.5 * IN), (WX - 1.8 * IN, 1.5 * IN), (WX + 2.0 * IN, 0)):
    winch_body = winch_body.union(cq.Workplane("XY", origin=(0, 0, -T - 4)).center(bx, by).circle(4.5).extrude(2 * T + 0.15 * IN + 12))

# ---- front angle + eye bolt + pulley block ----
front_angle = angle(0, +1, -ANG_L / 2, ANG_L / 2)
EYE_Z = -0.6 * IN
eyebolt = xcyl(9.5, -5, 1.6 * IN, 0, EYE_Z)
eye = (cq.Workplane("XZ", origin=(0, 5, 0)).center(1.6 * IN + 12, EYE_Z)
       .circle(14).circle(8).extrude(10))
# block hangs from the eye; sheave plane = XZ (rope runs in X)
BLK_X = 1.6 * IN + 26
SHV_Z = EYE_Z + 26
sheave = ycyl(2.0 * IN, -6, 6, BLK_X + 8, SHV_Z + 10)
cheeks = ycyl(2.3 * IN, -9, -7, BLK_X + 8, SHV_Z + 10).union(ycyl(2.3 * IN, 7, 9, BLK_X + 8, SHV_Z + 10))
blk_eye = (cq.Workplane("XZ", origin=(0, 4, 0)).center(1.6 * IN + 20, EYE_Z + 4).circle(9).circle(5).extrude(8))

# ---- rope: 4 capstan wraps, run to pulley top, drop to water, tail behind ----
wraps = ycyl(1.5 * IN + 13, -1.0 * IN, 1.0 * IN, WX, DRUM_Z).cut(ycyl(1.5 * IN, -2 * IN, 2 * IN, WX, DRUM_Z))
rope_d = 6.35


def seg(p0, p1, r=rope_d / 2):
    p0, p1 = cq.Vector(*p0), cq.Vector(*p1)
    return cq.Solid.makeCylinder(r, (p1 - p0).Length, p0, (p1 - p0).normalized())


r_drum = 0.75 * IN + rope_d / 2
sheave_c = (BLK_X + 8, SHV_Z + 10)
r_sh = 1.0 * IN + rope_d / 2
# loaded side leaves the bottom of the drum (under-wound) to the top of the sheave
p_drum_bot = (WX, 0.5 * IN, DRUM_Z - r_drum)
p_sh_top = (sheave_c[0], 0.5 * IN, sheave_c[1] + r_sh)
p_sh_front = (sheave_c[0] + r_sh, 0.5 * IN, sheave_c[1])
drop_dir = (math.cos(math.radians(-60)), 0, math.sin(math.radians(-60)))
p_drop = tuple(p_sh_front[i] + 400 * drop_dir[i] for i in range(3))
# tail leaves the top of the drum toward the operator (behind the block)
p_tail0 = (WX, -0.5 * IN, DRUM_Z + r_drum)
p_tail1 = (XR - 250, -0.5 * IN, DRUM_Z - 60)
rope_parts = [seg(p_drum_bot, p_sh_top), seg(p_sh_front, p_drop), seg(p_tail0, p_tail1)]

platform = box(-PLAT_D, 0, -260, 260, -40, 0)


def build():
    a = cq.Assembly(name="PoolCover_Winch_v3_Budget")
    AL = cq.Color(0.72, 0.74, 0.77)
    SS = cq.Color(0.85, 0.85, 0.88)
    WIN = cq.Color(0.15, 0.17, 0.20)
    ROPE = cq.Color(0.95, 0.55, 0.05)
    GHOST = cq.Color(0.9, 0.9, 0.9, 0.35)
    BLU = cq.Color(0.10, 0.35, 0.80)
    a.add(platform, name="REF_StartingBlock_Platform", color=GHOST)
    a.add(rear_angle, name="Rear_Hook_Angle_2x2x0.25_8in", color=BLU)
    a.add(plate, name="Winch_Plate_6061_0.25x8x12in", color=AL)
    a.add(winch_body, name="Hand_Winch_3500lb_strap_removed", color=WIN)
    a.add(drum, name="Winch_Drum", color=SS)
    a.add(handle_shaft.union(arm), name="Winch_Crank", color=SS)
    a.add(knob, name="Winch_Handle_Grip", color=cq.Color(0.05, 0.05, 0.05))
    a.add(front_angle, name="Front_Hook_Angle_2x2x0.25_8in", color=BLU)
    a.add(eyebolt.union(eye), name="Eye_Bolt_3_8in_SS", color=SS)
    a.add(blk_eye.union(cheeks), name="Pulley_Block_SS", color=SS)
    a.add(sheave, name="Pulley_Sheave", color=cq.Color(0.2, 0.2, 0.2))
    a.add(wraps, name="Rope_4_capstan_wraps", color=ROPE)
    a.add(cq.Workplane().add(cq.Compound.makeCompound(rope_parts)), name="Rope_quarter_inch_polyester", color=ROPE)
    return a


if __name__ == "__main__":
    a = build()
    a.save("out/Pool_Cover_Winch_v3_Budget.step")
    parts = [c for c in a.children if not c.name.startswith("REF_")]
    comp = cq.Compound.makeCompound([v for c in parts for v in c.obj.vals()])
    cq.exporters.export(cq.Workplane().add(comp), "out/Pool_Cover_Winch_v3_Budget.stl", tolerance=0.3, angularTolerance=0.3)
    print("ok", len(a.children))


def build_drill():
    """v3 + cordless drill on the winch input shaft (crank arm removed)."""
    a = build()
    a = cq.Assembly(name="PoolCover_Winch_v3_DrillMotor")
    full = build()
    for c in full.children:
        if c.name in ("Winch_Crank", "Winch_Handle_Grip"):
            continue
        a.add(c.obj, name=c.name, color=c.color)
    shaft = ycyl(0.6 * IN, -1.9 * IN, 2.4 * IN, pin_x, pin_z)
    socket = ycyl(0.9 * IN, 2.3 * IN, 3.6 * IN, pin_x, pin_z)
    chuck = ycyl(1.6 * IN, 3.6 * IN, 4.8 * IN, pin_x, pin_z)
    body = ycyl(2.2 * IN, 4.8 * IN, 10.5 * IN, pin_x, pin_z)
    grip = box(pin_x - 0.7 * IN, pin_x + 0.7 * IN, 7.0 * IN, 8.6 * IN, pin_z - 5.5 * IN, pin_z - 0.8 * IN)
    batt = box(pin_x - 1.6 * IN, pin_x + 1.6 * IN, 6.4 * IN, 9.4 * IN, pin_z - 7.3 * IN, pin_z - 5.5 * IN)
    a.add(shaft, name="Winch_Input_Shaft", color=cq.Color(0.85, 0.85, 0.88))
    a.add(socket, name="Drill_Socket_Adapter", color=cq.Color(0.6, 0.6, 0.62))
    a.add(chuck.union(body).union(grip), name="Cordless_Drill_18V", color=cq.Color(0.55, 0.75, 0.10))
    a.add(batt, name="Drill_Battery", color=cq.Color(0.15, 0.15, 0.15))
    return a
