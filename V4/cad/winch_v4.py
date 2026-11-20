"""
v4: geared 12 V motor + detachable rope spool ("nooked pulley").

Drive train (motor -> small gear -> big gear -> spool):
  * 12 V worm (wiper-style) gearmotor bolted to the outside of the near side plate.
    Its output shaft passes through the plate and carries a 12T module-3 pinion.
  * The pinion drives a 48T module-3 gear (4:1) that is bolted to the spool's near flange
    by the same four tie rods that clamp the spool together.
  * The worm gearbox is self-locking, so the spool holds the tarp when the motor stops.

Spool ("nooked pulley"):
  * 2.5 in OD x 1/4 in wall 6061 tube core, two 6 in dia x 1/4 in 6061 flanges, 6 in between
    flanges. Holds the whole rope (about 22 m in 4 layers of 1/4 in rope).
  * The NOOK: a keyhole notch in the far flange. Push the rope's stopper knot through the
    big hole and slide the rope into the narrow slot: the knot can't pull back through.
  * Spins on two flanged bronze bushings on a 3/4 in 316 dead axle.

Detachable for transport:
  * The axle ends drop into open-top slots in two 1/4 in 6061 side plates.
  * A swing latch on each side plate closes over the axle and is locked by a 3/8 in
    ball-lock pin. Pull both pins, flip the latches up, lift the spool (gear and rope included).
  * The pinion sits straight FORWARD of the spool, so the gear force pushes the spool
    DOWN into its slots, and the rope pulls it FORWARD into the slot's front wall.
    The latches carry no load in normal use: they only stop the spool from bouncing out.

Mount: v3's bolt-together angle mount (rear angle hooks the block's back edge, front angle
hooks the lip and carries an eye bolt + pulley block that turns the rope down to the water).

All dims in mm. X+ = toward water, platform front face X=0, top Z=0, Y+ = away from the gear side.
build(params) takes overrides so V4.2 can reuse this file (see V4/V4.2/cad/winch_v4_2.py).
"""
import math
import copy
import cadquery as cq

IN = 25.4
T = 0.25 * IN
LEG = 2 * IN
XR = -520
LATCH_PIVOT, LATCH_PIN = -62, -30   # latch pivot and ball-lock pin sit BEHIND the axle, clear of the motor
GAP = 10          # spool-to-side-plate clearance (tie-rod nylocs sit in it)
Z_DECK = -450

DEFAULTS = {
    "name": "PoolCover_Winch_v4",
    "spool": {"x": -400, "z": 98, "core_r": 31.75, "rope_d": 6.35, "between": 6 * IN, "flange_r": 76.2, "layers_shown": 2},
    "gear": {"teeth": 48, "pinion": 12, "module": 3, "face": 30},
    "motor_name": "Wiper_Worm_Gearmotor_12V_32Nm",
    "guard": False,
    "battery_name": "Battery_12V_20Ah_LiFePO4",
}


def merge(a, b):
    o = copy.deepcopy(a)
    for k, v in (b or {}).items():
        o[k] = merge(o.get(k, {}), v) if isinstance(v, dict) else v
    return o


# ---------------- primitives ----------------
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def ycyl(d, y0, y1, x, z):
    return cq.Workplane("XZ", origin=(0, y1, 0)).center(x, z).circle(d / 2).extrude(y1 - y0)


def xcyl(d, x0, x1, y, z):
    return cq.Workplane("YZ", origin=(x0, 0, 0)).center(y, z).circle(d / 2).extrude(x1 - x0)


def zcyl(d, z0, z1, x, y):
    return cq.Workplane("XY", origin=(0, 0, z0)).center(x, y).circle(d / 2).extrude(z1 - z0)


def yprism(pts, y0, y1):
    """Extrude an XZ polygon between y0 and y1."""
    return cq.Workplane("XZ", origin=(0, y1, 0)).polyline(pts).close().extrude(y1 - y0)


def seg(p0, p1, r):
    p0, p1 = cq.Vector(*p0), cq.Vector(*p1)
    return cq.Solid.makeCylinder(r, (p1 - p0).Length, p0, (p1 - p0).normalized())


def gear_profile(cx, cz, rp, n, phase=0.0):
    """Same simplified trapezoid-tooth outline the sim draws (module = 2*rp/n)."""
    m = 2 * rp / n
    ro, rr, p = rp + m, rp - 1.25 * m, 2 * math.pi / n
    pts = []
    for i in range(n):
        a = phase + i * p
        for r, da in ((rr, -0.30), (ro, -0.13), (ro, 0.13), (rr, 0.30)):
            pts.append((cx + r * math.cos(a + da * p), cz + r * math.sin(a + da * p)))
    return pts


def angle(x_face, outward, y0, y1):
    """2x2x1/4 angle: horizontal leg on top of the platform, vertical leg down a face."""
    if outward > 0:
        return box(x_face - LEG + T, x_face + T, y0, y1, 0, T).union(box(x_face, x_face + T, y0, y1, -LEG + T, T))
    return box(x_face - T, x_face + LEG - T, y0, y1, 0, T).union(box(x_face - T, x_face, y0, y1, -LEG + T, T))


# ---------------- model ----------------
def geometry(P):
    S, G = P["spool"], P["gear"]
    g = {}
    g["RG"] = G["module"] * G["teeth"] / 2
    g["RP"] = G["module"] * G["pinion"] / 2
    g["PIN"] = (S["x"] + g["RG"] + g["RP"], S["z"])
    W = S["between"]
    g["yFL"] = (-W / 2 - T, -W / 2)                       # near (gear-side) flange
    g["yFR"] = (W / 2, W / 2 + T)                         # far flange (has the nook)
    g["yG"] = (g["yFL"][0] - G["face"], g["yFL"][0])      # big gear, bolted on the near flange
    g["yPL"] = (g["yG"][0] - GAP - T, g["yG"][0] - GAP)   # near side plate (GAP leaves room for the tie-rod nuts)
    g["yPR"] = (g["yFR"][1] + GAP, g["yFR"][1] + GAP + T) # far side plate
    half = max(-g["yPL"][0], g["yPR"][1]) + LEG + 5
    g["BW"] = math.ceil(2 * half / IN) * IN               # base plate width, rounded up to whole inches
    g["PLATE_TOP"] = 2 * T
    g["SP"] = (S["x"] - 90, g["PIN"][0] + 45, S["z"] + 42)   # side plate x0, x1, top
    g["SLOT_W"] = 0.75 * IN + 0.6
    g["LIMIT_X"] = g["SP"][1] + 22
    return g


def side_plate(P, g, y0, y1, pinion_hole):
    S = P["spool"]
    x0, x1, top = g["SP"]
    pz = g["PLATE_TOP"]
    pts = [(x0, pz), (x1, pz), (x1, top - 18), (x1 - 18, top), (x0 + 18, top), (x0, top - 18)]
    p = yprism(pts, y0, y1)
    w = g["SLOT_W"]
    p = p.cut(box(S["x"] - w / 2, S["x"] + w / 2, y0 - 1, y1 + 1, S["z"], top + 1)).cut(ycyl(w, y0 - 1, y1 + 1, S["x"], S["z"]))
    p = p.cut(ycyl(6.6, y0 - 1, y1 + 1, S["x"] + LATCH_PIVOT, S["z"] + 17.5))   # latch pivot
    p = p.cut(ycyl(9.9, y0 - 1, y1 + 1, S["x"] + LATCH_PIN, S["z"] + 17.5))     # ball-lock pin
    for bx in (x0 + 30, x0 + 30 + 2.5 * IN):                               # foot bolts
        p = p.cut(ycyl(8.2, y0 - 1, y1 + 1, bx, pz + 30))
    if pinion_hole:
        p = p.cut(ycyl(30, y0 - 1, y1 + 1, *g["PIN"]))
        for i in range(3):
            a = math.pi / 2 + i * 2 * math.pi / 3
            p = p.cut(ycyl(8.2, y0 - 1, y1 + 1, g["PIN"][0] + 46 * math.cos(a), g["PIN"][1] + 46 * math.sin(a)))
    return p


def foot(g, y_plate_outer, outward):
    x0 = g["SP"][0] + 10
    x1 = x0 + 4 * IN
    pz = g["PLATE_TOP"]
    if outward < 0:
        return box(x0, x1, y_plate_outer - LEG + T, y_plate_outer, pz, pz + T).union(box(x0, x1, y_plate_outer - T, y_plate_outer, pz, pz + LEG))
    return box(x0, x1, y_plate_outer, y_plate_outer + LEG - T, pz, pz + T).union(box(x0, x1, y_plate_outer, y_plate_outer + T, pz, pz + LEG))


def spool_parts(P, g):
    S, G = P["spool"], P["gear"]
    sx, sz, cr, fr = S["x"], S["z"], S["core_r"], S["flange_r"]
    yFL, yFR, yG = g["yFL"], g["yFR"], g["yG"]
    tie_pos = [(sx + 21 * math.cos(a), sz + 21 * math.sin(a)) for a in (math.pi / 4 + i * math.pi / 2 for i in range(4))]

    core = ycyl(2 * cr, yFL[1], yFR[0], sx, sz).cut(ycyl(2 * cr - 2 * T, yFL[1] - 1, yFR[0] + 1, sx, sz))

    def flange(y0, y1, nook):
        f = ycyl(2 * fr, y0, y1, sx, sz).cut(ycyl(25.6, y0 - 1, y1 + 1, sx, sz))
        for tx, tz in tie_pos:
            f = f.cut(ycyl(6.8, y0 - 1, y1 + 1, tx, tz))
        if nook:   # keyhole: 15 mm knot hole + 7 mm rope slot running outward
            a = math.radians(135)
            kx, kz = sx + (cr + 12) * math.cos(a), sz + (cr + 12) * math.sin(a)
            f = f.cut(ycyl(15, y0 - 1, y1 + 1, kx, kz))
            ex, ez = sx + (cr + 26) * math.cos(a), sz + (cr + 26) * math.sin(a)
            for k in range(1, 8):                 # row of 7 mm cuts = the narrow rope slot

                fx, fz = kx + (ex - kx) * k / 7, kz + (ez - kz) * k / 7
                f = f.cut(ycyl(7, y0 - 1, y1 + 1, fx, fz))
        return f

    flange_l = flange(*yFL, nook=False)
    flange_r = flange(*yFR, nook=True)

    gear = yprism(gear_profile(sx, sz, g["RG"], G["teeth"]), *yG).cut(ycyl(34, yG[0] - 1, yG[1] + 1, sx, sz))
    for tx, tz in tie_pos:
        gear = gear.cut(ycyl(6.8, yG[0] - 1, yG[1] + 1, tx, tz))
    for i in range(6):   # lightening holes
        a = i * math.pi / 3
        gear = gear.cut(ycyl(16, yG[0] - 1, yG[1] + 1, sx + 0.62 * g["RG"] * math.cos(a), sz + 0.62 * g["RG"] * math.sin(a)))

    ties = None
    for tx, tz in tie_pos:
        t = ycyl(6.35, yG[0] - 8, yFR[1] + 8, tx, tz)   # 8 mm stick-out < GAP
        t = t.union(ycyl(11, yG[0] - 7, yG[0], tx, tz)).union(ycyl(11, yFR[1], yFR[1] + 7, tx, tz))   # nylocs
        ties = t if ties is None else ties.union(t)

    bush = None
    for (y0, y1), out in ((yFL, -1), (yFR, 1)):
        b = ycyl(25.4, y0, y1, sx, sz).cut(ycyl(19.2, y0 - 1, y1 + 1, sx, sz))
        fl_y = (y1, y1 + 2) if out > 0 else (y0 - 2, y0)
        b = b.union(ycyl(29, *fl_y, sx, sz).cut(ycyl(19.2, fl_y[0] - 1, fl_y[1] + 1, sx, sz)))
        bush = b if bush is None else bush.union(b)

    axle = ycyl(0.75 * IN, g["yPL"][0] - 12, g["yPR"][1] + 12, sx, sz)

    n = P["spool"]["layers_shown"]
    pack = ycyl(2 * (cr + n * S["rope_d"]), yFL[1] + 0.5, yFR[0] - 0.5, sx, sz).cut(ycyl(2 * cr, yFL[1], yFR[0], sx, sz))
    return {"Spool_Core_Tube_6061_2.5in": core, "Spool_Flange_GearSide_6061": flange_l, "Spool_Flange_Nook_6061": flange_r,
            "Big_Gear_%dT_m%d_Steel" % (G["teeth"], G["module"]): gear, "Spool_Tie_Rods_0.25in_316": ties,
            "Spool_Bronze_Bushings_0.75in": bush, "Spool_Dead_Axle_0.75in_316": axle, "Rope_on_Spool": pack}


def latches(P, g):
    S = P["spool"]
    out = None
    for (y0, y1), side in ((g["yPL"], -1), (g["yPR"], 1)):
        ly = (y0 - T, y0) if side < 0 else (y1, y1 + T)
        bar = box(S["x"] - 70, S["x"] + 14, ly[0], ly[1], S["z"] + 10.5, S["z"] + 24.5)   # front end closes over the axle
        bar = bar.cut(ycyl(6.6, ly[0] - 1, ly[1] + 1, S["x"] + LATCH_PIVOT, S["z"] + 17.5))
        bar = bar.cut(ycyl(9.9, ly[0] - 1, ly[1] + 1, S["x"] + LATCH_PIN, S["z"] + 17.5))
        out = bar if out is None else out.union(bar)
    return out


def latch_pins(P, g):
    S = P["spool"]
    pins = None
    for (y0, y1), side in ((g["yPL"], -1), (g["yPR"], 1)):
        if side < 0:
            ya, yb = y0 - T - 14, y1 + 6
            ring_y = ya
        else:
            ya, yb = y0 - 6, y1 + T + 14
            ring_y = yb
        p = ycyl(9.5, ya, yb, S["x"] + LATCH_PIN, S["z"] + 17.5)
        ring = cq.Workplane("XZ", origin=(0, ring_y + 2, 0)).center(S["x"] + LATCH_PIN, S["z"] + 36).circle(12).circle(9).extrude(4)
        piv = ycyl(6.35, ya + 4, yb - 4, S["x"] + LATCH_PIVOT, S["z"] + 17.5)
        u = p.union(ring).union(piv)
        pins = u if pins is None else pins.union(u)
    return pins


def motor(P, g):
    px, pz = g["PIN"]
    y_out = g["yPL"][0]
    gb = ycyl(104, y_out - 45, y_out, px, pz)
    for i in range(3):
        a = math.pi / 2 + i * 2 * math.pi / 3
        gb = gb.union(ycyl(16, y_out - 45, y_out, px + 46 * math.cos(a), pz + 46 * math.sin(a)))
    can = zcyl(56, pz + 40, pz + 190, px, y_out - 31).union(zcyl(44, pz + 190, pz + 204, px, y_out - 31))
    shaft = ycyl(16, y_out - 2, g["yG"][1], px, pz)
    pin = yprism(gear_profile(px, pz, g["RP"], P["gear"]["pinion"], math.pi / P["gear"]["pinion"]), *g["yG"]).cut(ycyl(12, g["yG"][0] - 1, g["yG"][1] + 1, px, pz))
    return gb.union(can), shaft, pin


def guard(P, g):
    """1/8 in polycarbonate guard over the pinion side of the gear mesh, bolted to the motor-side plate.
    It stays forward of the big gear's outline so the spool still lifts straight out."""
    S = P["spool"]
    y0, y1 = g["yG"][0] - 1, g["yG"][1] - 0.5
    x0 = S["x"] + g["RG"] + P["gear"]["module"] + 2          # just forward of the big gear's tip circle
    x1 = g["PIN"][0] + g["RP"] + 14
    top = S["z"] + g["RP"] + 16
    roof = box(x0, x1, y0, y1, top, top + 3.2)
    front = box(x1, x1 + 3.2, y0, y1, g["PLATE_TOP"] + 4, top + 3.2)
    return roof.union(front)


def front_and_mount(g):
    rear = angle(XR, -1, -4 * IN, 4 * IN)
    bw = g["BW"]
    plate = box(XR - T, XR - T + 12 * IN, -bw / 2, bw / 2, T, 2 * T)
    for bx in (XR + 0.8 * IN, XR + 11 * IN):
        for by in (-3 * IN, 3 * IN):
            plate = plate.cut(cq.Workplane("XY", origin=(0, 0, -1)).center(bx, by).circle(4.2).extrude(30))
    front = angle(0, +1, -4 * IN, 4 * IN)
    EYE_Z = -0.6 * IN
    eyebolt = xcyl(9.5, -5, 1.6 * IN, 0, EYE_Z).union(
        cq.Workplane("XZ", origin=(0, 5, 0)).center(1.6 * IN + 12, EYE_Z).circle(14).circle(8).extrude(10))
    BLK_X, SHV_Z = 1.6 * IN + 26, EYE_Z + 26
    sheave = ycyl(2.0 * IN, -6, 6, BLK_X + 8, SHV_Z + 10)
    cheeks = ycyl(2.3 * IN, -9, -7, BLK_X + 8, SHV_Z + 10).union(ycyl(2.3 * IN, 7, 9, BLK_X + 8, SHV_Z + 10))
    blk_eye = cq.Workplane("XZ", origin=(0, 4, 0)).center(1.6 * IN + 20, EYE_Z + 4).circle(9).circle(5).extrude(8)
    return rear, plate, front, eyebolt, blk_eye.union(cheeks), sheave, (BLK_X + 8, SHV_Z + 10, 1.0 * IN + 3.2)


def limit_switch(g):
    lx, pz = g["LIMIT_X"], g["PLATE_TOP"]
    body = box(lx - 32, lx + 4, -15, 15, pz, pz + 26)
    lever = box(lx - 9, lx - 3, -4, 4, pz + 18, pz + 34).union(ycyl(12, -8, 8, lx, pz + 34))
    return body, lever


def reed_sensor(P, g):
    S = P["spool"]
    y_out = g["yPR"][1]
    return box(S["x"] + LATCH_PIN - 8, S["x"] + LATCH_PIN + 8, y_out, y_out + 8, S["z"] + 26, S["z"] + 40)


def controls():
    b = box(-1080, -840, -100, 100, Z_DECK, Z_DECK + 190)
    lid = box(-1083, -837, -103, 103, Z_DECK + 190, Z_DECK + 202)
    estop = zcyl(40, Z_DECK + 202, Z_DECK + 222, -890, 40)
    key = zcyl(24, Z_DECK + 202, Z_DECK + 212, -1030, -50)
    pend = box(-800, -740, -60, 50, Z_DECK, Z_DECK + 40)
    pbtn = zcyl(18, Z_DECK + 40, Z_DECK + 46, -782, -30).union(zcyl(18, Z_DECK + 40, Z_DECK + 46, -782, 5))
    pstop = zcyl(22, Z_DECK + 40, Z_DECK + 52, -758, 30)
    return b.union(lid), key, estop, pend, pbtn, pstop


def rope(P, g, sheave):
    S = P["spool"]
    r_pack = S["core_r"] + S["rope_d"] * P["spool"]["layers_shown"]
    sx_, sz_, rs = sheave
    p0 = (S["x"], 0, S["z"] - r_pack + S["rope_d"] / 2)
    p1 = (sx_, 0, sz_ + rs)
    p2 = (sx_ + rs, 0, sz_)
    d = (math.cos(math.radians(-60)), 0, math.sin(math.radians(-60)))
    p3 = tuple(p2[i] + 400 * d[i] for i in range(3))
    ball_x = g["LIMIT_X"] + 120
    u = (ball_x - p0[0]) / (p1[0] - p0[0])
    ball = cq.Solid.makeSphere(15, cq.Vector(ball_x, 0, p0[2] + u * (p1[2] - p0[2])))
    return [seg(p0, p1, 3.2), seg(p2, p3, 3.2)], ball


def build(overrides=None, spool_lifted=False):
    P = merge(DEFAULTS, overrides)
    g = geometry(P)
    a = cq.Assembly(name=P["name"] + ("_SpoolRemoved" if spool_lifted else ""))
    AL = cq.Color(0.72, 0.74, 0.77); SS = cq.Color(0.85, 0.85, 0.88); BLU = cq.Color(0.10, 0.35, 0.80)
    STL = cq.Color(0.55, 0.57, 0.60); BRZ = cq.Color(0.80, 0.62, 0.25); ROPE = cq.Color(0.95, 0.55, 0.05)
    GHOST = cq.Color(0.9, 0.9, 0.9, 0.35); MOT = cq.Color(0.17, 0.19, 0.22); YEL = cq.Color(0.95, 0.80, 0.10)
    RED = cq.Color(0.85, 0.10, 0.10); GRN = cq.Color(0.10, 0.65, 0.20); RUB = cq.Color(0.05, 0.05, 0.05)
    CLR = cq.Color(0.75, 0.88, 1.0, 0.35); SENS = cq.Color(0.16, 0.49, 0.88)

    a.add(box(-520, 0, -260, 260, -40, 0), name="REF_StartingBlock_Platform", color=GHOST)
    rear, plate, front, eyebolt, block, sheave, shv = front_and_mount(g)
    a.add(rear, name="Rear_Hook_Angle_2x2x0.25_8in", color=BLU)
    a.add(plate, name="Base_Plate_6061_0.25x%dx12in" % round(g["BW"] / IN), color=AL)
    a.add(front, name="Front_Hook_Angle_2x2x0.25_8in", color=BLU)
    a.add(eyebolt, name="Eye_Bolt_3_8in_SS", color=SS)
    a.add(block, name="Pulley_Block_SS_550lb", color=SS)
    a.add(sheave, name="Pulley_Sheave", color=cq.Color(0.2, 0.2, 0.2))

    a.add(side_plate(P, g, *g["yPL"], True), name="Side_Plate_Motor_Side_6061", color=AL)
    a.add(side_plate(P, g, *g["yPR"], False), name="Side_Plate_Far_6061", color=AL)
    a.add(foot(g, g["yPL"][0], -1).union(foot(g, g["yPR"][1], 1)), name="Side_Plate_Feet_Angle_2x2x0.25_6in", color=BLU)
    S = P["spool"]
    lat, pins = latches(P, g), latch_pins(P, g)
    if spool_lifted:   # pins pulled out sideways, latches swung up about their pivots
        piv = (S["x"] + LATCH_PIVOT, S["z"] + 17.5)
        lat = lat.rotate((piv[0], 0, piv[1]), (piv[0], 1, piv[1]), -100)
        pins = pins.translate((0, 0, 60))
    a.add(lat, name="Swing_Latches_6061", color=BLU)
    a.add(pins, name="Ball_Lock_Pins_3_8in_SS", color=SS)
    a.add(reed_sensor(P, g), name="Spool_Latched_Reed_Sensor", color=SENS)

    body, shaft, pinion = motor(P, g)
    a.add(body, name=P["motor_name"], color=MOT)
    a.add(shaft, name="Motor_Output_Shaft", color=SS)
    a.add(pinion, name="Pinion_%dT_m%d_Steel" % (P["gear"]["pinion"], P["gear"]["module"]), color=SS)
    if P["guard"]:
        a.add(guard(P, g), name="Gear_Guard_Polycarbonate", color=CLR)

    lift = (0, 0, 260) if spool_lifted else (0, 0, 0)
    for nm, part in spool_parts(P, g).items():
        col = ROPE if nm.startswith("Rope") else BRZ if "Bronze" in nm else STL if "Gear" in nm else SS if ("316" in nm) else AL
        if spool_lifted and nm.startswith("Rope"):
            nm = "Rope_stored_on_Spool"
        a.add(part.translate(lift), name=nm, color=col)

    lb, lv = limit_switch(g)
    a.add(lb, name="Limit_Switch_RopeIn_IP67", color=YEL)
    a.add(lv, name="Limit_Switch_Lever", color=SS)
    if not spool_lifted:
        segs, ball = rope(P, g, shv)
        a.add(cq.Workplane().add(cq.Compound.makeCompound(segs)), name="Rope_quarter_inch_polyester", color=ROPE)
        a.add(cq.Workplane().add(ball), name="Rope_Stopper_Ball", color=RED)

    cb, key, estop, pend, pbtn, pstop = controls()
    a.add(cb, name="Battery_Controller_Box_IP67", color=YEL)
    a.add(key, name="Key_Switch", color=RUB)
    a.add(estop, name="EStop_Box", color=RED)
    a.add(pend, name="Pendant_IP67", color=YEL)
    a.add(pbtn, name="Pendant_IN_OUT_Buttons", color=GRN)
    a.add(pstop, name="Pendant_EStop", color=RED)
    px, pz = g["PIN"]
    yc = g["yPL"][0] - 31
    cab = [seg((-870, 0, Z_DECK + 202), (-640, 0, 40), 4), seg((-640, 0, 40), (XR + 20, yc, 40), 4),
           seg((XR + 20, yc, 40), (px - 60, yc, pz + 215), 4), seg((px - 60, yc, pz + 215), (px, yc, pz + 215), 4)]
    a.add(cq.Workplane().add(cq.Compound.makeCompound(cab)), name="Motor_Cable", color=RUB)
    return a, P, g


def export(a, stem, outdir="out"):
    import os
    os.makedirs(outdir, exist_ok=True)
    a.save(f"{outdir}/{stem}.step")
    parts = [c for c in a.children if not c.name.startswith("REF_")]
    comp = cq.Compound.makeCompound([v for c in parts for v in c.obj.vals()])
    cq.exporters.export(cq.Workplane().add(comp), f"{outdir}/{stem}.stl", tolerance=0.3, angularTolerance=0.3)


if __name__ == "__main__":
    a, P, g = build()
    export(a, "Pool_Cover_Winch_v4_Motor")
    a2, _, _ = build(spool_lifted=True)
    export(a2, "Pool_Cover_Winch_v4_SpoolRemoved")
    print("ok", len(a.children), "parts; base plate", round(g["BW"] / IN), "in wide")
