"""
Draws the v4 / v4.2 wiring diagram as an SVG (same look as V1/electrical/Motor_Wiring_Diagram.svg).
Usage:  python tools/make_wiring.py v4      -> V4/electrical/V4_Wiring_Diagram.svg
        python tools/make_wiring.py v4.2    -> V4/V4.2/electrical/V4_2_Wiring_Diagram.svg

Main power runs are drawn as wires. Signal wires end in named tags: every tag with the same
name is one connection (for example, every "GND" tag joins the ground bus).
"""
import os
import sys
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VARIANTS = {
    "v4": {
        "out": "V4/electrical/V4_Wiring_Diagram.svg",
        "title": "Tarp Winch v4: Wiring Diagram (12 V DC, battery powered)",
        "battery": ["12 V LiFePO4 (12.8 V nom.)", "20 Ah, built-in BMS", "≥ 40 A continuous", "≈ 256 Wh"],
        "motor": ["M1 WORM GEARMOTOR", "12 V wiper-style, 32 N·m", "≈ 50 rpm no load", "self-locking worm", "drives 12T pinion → 48T gear"],
        "f1": "40 A", "trip": 25, "code": "V4/code (main.py)",
        "sizing": ["MOTOR SIZING (from the sim)", "Design pull: 500 lbf (2.2 kN)", "Spool torque at 500 lbf, 4th layer: 120 N·m",
                   "÷ 4:1 gears ÷ 0.93 → 32 N·m = motor stall", "  so the motor can't pull past ~500 lbf",
                   "Sim peak (est. tarp): 303 lbf, 21.8 A", "Trip 25 A ≈ 340 lbf on the last layer",
                   "Full 25 yd pull: 7.5 min, 9–10 ft/min", "≈ 13 Wh per pull → ≈ 15 pulls per charge"],
    },
    "v4.2": {
        "out": "V4/V4.2/electrical/V4_2_Wiring_Diagram.svg",
        "title": "Tarp Winch v4.2: Wiring Diagram (12 V DC, battery powered)",
        "battery": ["12 V LiFePO4 (12.8 V nom.)", "12 Ah, built-in BMS", "≥ 50 A continuous", "≈ 154 Wh"],
        "motor": ["M1 WORM GEARMOTOR", "12 V wiper-style, 55 N·m", "≈ 50 rpm no load", "self-locking worm", "drives 12T pinion → 36T gear"],
        "f1": "50 A", "trip": 30, "code": "V4/V4.2/code (main.py)",
        "sizing": ["MOTOR SIZING (from the sim)", "Design pull: 500 lbf (2.2 kN)", "Spool torque at 500 lbf, 3rd layer: 106 N·m",
                   "÷ 3:1 gears ÷ 0.93 → 38 N·m (motor stall 55)", "Trip 30 A ≈ 470 lbf on the last layer",
                   "Sim peak (est. tarp): 303 lbf, 19.2 A", "  (64 % of the trip; v4 was 87 %)",
                   "Full 25 yd pull: 5.7 min, 11–14 ft/min", "≈ 9 Wh per pull → ≈ 13 pulls per charge"],
    },
}

C_POS, C_GND, C_MP, C_MN, C_LOOP, C_SIG, C_PEND = "#d00000", "#222", "#e85d04", "#1d4ed8", "#7b2cbf", "#2a9d8f", "#4d7c0f"


class SVG:
    def __init__(self, w, h):
        self.w, self.h, self.items = w, h, []

    def add(self, s):
        self.items.append(s)

    def text(self, x, y, s, cls="p", anchor=None, fill=None, extra=""):
        a = ' text-anchor="%s"' % anchor if anchor else ""
        f = ' fill="%s"' % fill if fill else ""
        self.add('<text x="%g" y="%g" class="%s"%s%s%s>%s</text>' % (x, y, cls, a, f, extra, escape(s)))

    def rect(self, x, y, w, h, fill="#fff", stroke="#333", sw=2, rx=8, dash=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.add('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" stroke="%s" stroke-width="%g"%s/>' % (x, y, w, h, rx, fill, stroke, sw, d))

    def wire(self, pts, color, sw=2.2, dash=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.add('<polyline points="%s" fill="none" stroke="%s" stroke-width="%g" stroke-linejoin="round"%s/>' % (
            " ".join("%g,%g" % p for p in pts), color, sw, d))

    def dot(self, x, y, color):
        self.add('<circle cx="%g" cy="%g" r="4.5" fill="%s"/>' % (x, y, color))

    def term(self, x, y, label=None, side="r"):
        self.add('<circle cx="%g" cy="%g" r="4.5" fill="#fff" stroke="#333" stroke-width="2"/>' % (x, y))
        if label:
            if side == "r":
                self.text(x + 9, y + 4, label, anchor="start")
            elif side == "l":
                self.text(x - 9, y + 4, label, anchor="end")
            elif side == "u":
                self.text(x, y - 9, label, anchor="middle")
            else:
                self.text(x, y + 17, label, anchor="middle")

    def comp(self, x, y, w, h, title, lines, fill="#f6f7f9"):
        self.rect(x, y, w, h, fill=fill)
        self.text(x + w / 2, y + 22, title, cls="t")
        for i, l in enumerate(lines):
            self.text(x + w / 2, y + 41 + 15 * i, l, cls="s")

    def tag(self, x, y, name, color, direction="r", length=34):
        """Stub wire from a terminal ending in a named tag."""
        dx = {"r": 1, "l": -1, "u": 0, "d": 0}[direction]
        dy = {"r": 0, "l": 0, "u": -1, "d": 1}[direction]
        ex, ey = x + dx * length, y + dy * length
        self.wire([(x, y), (ex, ey)], color, 1.8)
        tw = 7.2 * len(name) + 12
        if direction == "r":
            bx, by = ex, ey - 9
        elif direction == "l":
            bx, by = ex - tw, ey - 9
        elif direction == "u":
            bx, by = ex - tw / 2, ey - 18
        else:
            bx, by = ex - tw / 2, ey
        self.add('<rect x="%g" y="%g" width="%g" height="18" rx="9" fill="#fff" stroke="%s" stroke-width="1.6"/>' % (bx, by, tw, color))
        self.text(bx + tw / 2, by + 13, name, cls="g", anchor="middle", fill=color)

    def save(self, path):
        css = (".t{font-size:15px;font-weight:700;text-anchor:middle;fill:#111}.s{font-size:12px;text-anchor:middle;fill:#444}"
               ".p{font-size:11.5px;fill:#111}.w{font-size:11.5px;font-weight:700}.h{font-size:24px;font-weight:700;fill:#111}"
               ".n{font-size:13px;fill:#222}.g{font-size:11px;font-weight:700}")
        body = "\n".join(self.items)
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Helvetica, Arial, sans-serif">\n'
               '<style>%s</style>\n<rect width="%d" height="%d" fill="#fff"/>\n%s\n</svg>\n') % (self.w, self.h, self.w, self.h, css, self.w, self.h, body)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)


def draw(v):
    s = SVG(1900, 1360)
    s.text(20, 38, v["title"], cls="h")
    s.text(20, 62, "All power at the pool is extra-low-voltage DC from a battery. No mains wiring at the starting block. Charge away from the water.", cls="n")
    s.rect(20, 85, 1390, 865, fill="none", stroke="#b8a000", sw=2.5, rx=14, dash="10 6")
    s.text(470, 104, "IP67 BATTERY / CONTROLLER BOX (yellow box in the CAD, on the deck). Every cable leaves through an IP68 gland.", cls="w", fill="#8a7800")

    # ---------- power row ----------
    s.comp(60, 140, 200, 150, "BT1 BATTERY", v["battery"], fill="#fff4e0")
    s.term(260, 200); s.text(260, 191, "+", anchor="middle")
    s.term(260, 250); s.text(260, 267, "−", anchor="middle")
    s.comp(320, 175, 120, 50, "F1  " + v["f1"], ["MIDI fuse"])
    s.term(320, 200); s.term(440, 200)
    s.comp(520, 140, 200, 140, "K1 MAIN CONTACTOR", ["100 A cont.-duty, 12 V coil", "normally open: closes only", "while the safety loop is made"], fill="#eef4ff")
    s.term(520, 200, "A1"); s.term(720, 200, "A2", "l")
    s.term(580, 280); s.term(680, 280)
    s.text(580, 272, "coil +", anchor="middle"); s.text(680, 272, "coil −", anchor="middle")
    s.comp(860, 140, 220, 200, "U4 MOTOR DRIVER", ["Cytron MD30C, 30 A cont.", "5–30 V, brushed DC", "PWM + DIR inputs (3.3 V ok)"], fill="#eefaf0")
    s.term(860, 200, "B+"); s.term(860, 300, "B−")
    s.term(1080, 200, "M+", "l"); s.term(1080, 300, "M−", "l")
    s.term(920, 340); s.term(970, 340); s.term(1020, 340)
    s.text(920, 332, "PWM", anchor="middle"); s.text(970, 332, "DIR", anchor="middle"); s.text(1020, 332, "GND", anchor="middle")
    s.comp(1130, 160, 140, 70, "U3 ACS758-050B", ["current sensor"], fill="#f3eefc")
    s.term(1130, 200); s.term(1270, 200)
    s.text(1138, 222, "IP+", anchor="start"); s.text(1262, 222, "IP−", anchor="end")
    s.term(1160, 160); s.term(1200, 160); s.term(1240, 160)
    s.comp(1460, 140, 300, 190, v["motor"][0], v["motor"][1:], fill="#eceff3")
    s.term(1460, 200, "+"); s.term(1460, 300, "−")

    s.wire([(260, 200), (320, 200)], C_POS, 4)
    s.wire([(440, 200), (520, 200)], C_POS, 4)
    s.dot(480, 200, C_POS)
    s.wire([(720, 200), (860, 200)], C_POS, 4)
    s.dot(780, 200, C_POS)
    s.text(470, 192, "10 AWG", cls="p", anchor="middle")
    s.wire([(1080, 200), (1130, 200)], C_MP, 4)
    s.wire([(1270, 200), (1460, 200)], C_MP, 4)
    s.wire([(1080, 300), (1460, 300)], C_MN, 4)
    s.text(1350, 192, "M+", anchor="middle"); s.text(1350, 292, "M−", anchor="middle")
    s.text(1430, 345, "2 × 10 AWG outdoor motor cable, 3 m", cls="p", anchor="middle")
    # ground bus
    s.wire([(260, 250), (290, 250), (290, 410), (1300, 410)], C_GND, 4)
    s.wire([(860, 300), (800, 300), (800, 410)], C_GND, 4)
    s.dot(800, 410, C_GND)
    s.text(300, 404, "GND bus (10 AWG)", anchor="start")
    # contactor coil, flyback diode, bulk cap
    s.tag(580, 280, "K1 COIL+", C_LOOP, "d", 30)
    s.wire([(680, 280), (680, 410)], C_GND, 1.8); s.dot(680, 410, C_GND)
    s.add('<polygon points="622,318 638,318 630,330" fill="#fff" stroke="#333" stroke-width="1.6"/>')
    s.wire([(622, 332), (638, 332)], "#333", 1.8)
    s.wire([(630, 280), (630, 318)], "#333", 1.4); s.wire([(630, 332), (630, 345), (680, 345)], "#333", 1.4)
    s.text(632, 362, "D1 1N5408", anchor="middle")
    s.wire([(780, 200), (780, 245)], C_POS, 1.8)
    s.wire([(768, 245), (792, 245)], "#333", 2.4); s.wire([(768, 253), (792, 253)], "#333", 2.4)
    s.wire([(780, 253), (780, 300), (800, 300)], C_GND, 1.8)
    s.text(790, 232, "C1", anchor="start"); s.text(790, 274, "1000 µF", anchor="start")
    # taps
    s.tag(480, 200, "+12V F1", C_POS, "u", 40)
    s.tag(780, 200, "+12V SW", C_POS, "u", 40)
    s.tag(920, 340, "PWM", C_SIG, "d", 24); s.tag(970, 340, "DIR", C_SIG, "d", 24); s.tag(1020, 340, "GND", C_GND, "d", 24)
    s.tag(1160, 160, "+5V", C_MP, "u", 20); s.tag(1200, 160, "GND", C_GND, "u", 40); s.tag(1240, 160, "I-SENSE 5V", C_SIG, "u", 20)

    # ---------- logic row ----------
    X0 = 150
    s.comp(X0, 460, 200, 110, "U2 BUCK 12→5 V", ["3 A, input 8–40 V", "feeds the Pico + sensor"])
    s.term(X0, 500); s.term(X0, 540); s.term(X0 + 200, 500)
    s.text(X0 + 10, 504, "VIN", anchor="start"); s.text(X0 + 10, 544, "GND", anchor="start"); s.text(X0 + 190, 504, "5 V", anchor="end")
    s.tag(X0, 500, "+12V SW", C_POS, "l", 20); s.tag(X0, 540, "GND", C_GND, "l", 20); s.tag(X0 + 200, 500, "+5V", C_MP, "r", 20)

    s.comp(X0, 620, 200, 100, "R1 / R2 DIVIDER", ["100 kΩ / 22 kΩ", "14.6 V → 2.6 V at GP27"])
    s.term(X0, 660); s.term(X0, 700); s.term(X0 + 200, 680)
    s.tag(X0, 660, "+12V SW", C_POS, "l", 20); s.tag(X0, 700, "GND", C_GND, "l", 20); s.tag(X0 + 200, 680, "V-SENSE", C_SIG, "r", 20)

    s.comp(X0, 770, 200, 100, "R3 / R4 DIVIDER", ["10 kΩ / 20 kΩ", "ACS 0–5 V → 0–3.3 V"])
    s.term(X0, 810); s.term(X0, 850); s.term(X0 + 200, 830)
    s.tag(X0, 810, "I-SENSE 5V", C_SIG, "l", 20); s.tag(X0, 850, "GND", C_GND, "l", 20); s.tag(X0 + 200, 830, "I-SENSE", C_SIG, "r", 20)

    PX = 530
    s.comp(PX, 450, 280, 440, "U1 RASPBERRY PI PICO", ["controller, MicroPython", v["code"], "3.3 V logic"], fill="#e9f7ef")
    left = [(500, "VSYS", "+5V", C_MP), (540, "GND", "GND", C_GND), (600, "GP27 ADC1", "V-SENSE", C_SIG),
            (640, "GP26 ADC0", "I-SENSE", C_SIG), (720, "GP15", "BUZZ", C_SIG), (760, "GP14", "LED", C_PEND)]
    right = [(500, "GP16 PWM", "PWM", C_SIG), (540, "GP17 DIR", "DIR", C_SIG), (620, "GP2", "BTN IN", C_PEND),
             (660, "GP3", "BTN OUT", C_PEND), (720, "GP4", "LIMIT", C_SIG), (780, "GP5", "LATCH", C_SIG)]
    for y, pin, net, col in left:
        s.term(PX, y, pin, "r"); s.tag(PX, y, net, col, "l", 26)
    for y, pin, net, col in right:
        s.term(PX + 280, y, pin, "l"); s.tag(PX + 280, y, net, col, "r", 26)
    s.text(PX + 140, 870, "inputs use internal pull-ups", cls="s", anchor="middle")

    BX = 1010
    s.comp(BX, 460, 220, 130, "BZ1 BUZZER + Q1", ["5 V buzzer, IP65", "Q1 2N2222 low-side", "1 kΩ base resistor"])
    s.term(BX, 510); s.term(BX, 550); s.term(BX + 220, 510)
    s.text(BX + 10, 514, "base", anchor="start"); s.text(BX + 10, 554, "emitter", anchor="start"); s.text(BX + 210, 514, "BZ +", anchor="end")
    s.tag(BX, 510, "BUZZ", C_SIG, "l", 20); s.tag(BX, 550, "GND", C_GND, "l", 20); s.tag(BX + 220, 510, "+5V", C_MP, "r", 20)

    # safety loop
    s.text(1010, 630, "Safety loop (purple): K1's coil only gets power", cls="w", fill=C_LOOP)
    s.text(1010, 646, "while every item in it is closed", cls="w", fill=C_LOOP)
    chain = [(1010, "F2  3 A", ["control fuse"]), (1115, "S1 KEY", ["removable key"]), (1220, "S2 E-STOP", ["box, N.C."])]
    for x, t, l in chain:
        s.comp(x, 660, 90, 60, t, l)
        s.term(x, 690); s.term(x + 90, 690)
    s.tag(1010, 690, "+12V F1", C_POS, "l", 20)
    s.wire([(1100, 690), (1115, 690)], C_LOOP, 2.4, "7 4")
    s.wire([(1205, 690), (1220, 690)], C_LOOP, 2.4, "7 4")
    s.tag(1310, 690, "ESTOP OUT", C_LOOP, "d", 40)
    s.dot(1120, 770, C_LOOP)
    s.tag(1120, 770, "ESTOP RET", C_LOOP, "l", 20)
    s.tag(1120, 770, "K1 COIL+", C_LOOP, "r", 20)
    s.text(1120, 798, "pendant E-stop return feeds K1 coil +", cls="s", anchor="middle")

    s.comp(1010, 830, 300, 90, "J1 CHARGE INLET", ["IP67, wired straight to the battery", "with its own 15 A fuse (charge only)"])

    # ---------- outside the box ----------
    s.text(1440, 400, "OUTSIDE THE BOX", cls="w", fill="#555")
    s.comp(1460, 420, 300, 230, "PENDANT", ["IP67, 6-core cable, 5 m", "hold-to-run: let go = stop"], fill="#fff8d6")
    pend = [(500, "IN (green, N.O.)", "BTN IN", C_PEND), (535, "OUT (black, N.O.)", "BTN OUT", C_PEND), (570, "COM", "GND", C_GND),
            (605, "LED + (220 Ω)", "LED", C_PEND)]
    for y, lab, net, col in pend:
        s.term(1460, y, lab, "r"); s.tag(1460, y, net, col, "l", 30)
    s.term(1760, 520); s.term(1760, 600)
    s.text(1750, 524, "E-stop in", anchor="end"); s.text(1750, 604, "E-stop out", anchor="end")
    s.text(1610, 640, "S4 E-STOP: N.C., in series with S2", cls="s", anchor="middle")
    s.tag(1760, 520, "ESTOP OUT", C_LOOP, "r", 20); s.tag(1760, 600, "ESTOP RET", C_LOOP, "r", 20)

    s.comp(1460, 690, 300, 100, "S3 ROPE-IN LIMIT", ["IP67 roller lever on the base plate", "N.C.: opens when the stopper ball", "on the rope arrives"])
    s.term(1460, 720, "C", "r"); s.term(1460, 760, "NC", "r")
    s.tag(1460, 720, "GND", C_GND, "l", 30); s.tag(1460, 760, "LIMIT", C_SIG, "l", 30)

    s.comp(1460, 810, 300, 100, "S5 SPOOL-LATCHED SENSOR", ["IP67 reed switch on the side plate,", "magnet in the ball-lock pin handle:", "closed only while the pin is in"], fill="#e8f1fd")
    s.term(1460, 845, "", "r"); s.term(1460, 880, "", "r")
    s.tag(1460, 845, "GND", C_GND, "l", 30); s.tag(1460, 880, "LATCH", C_SIG, "l", 30)

    # ---------- legend / notes / sizing ----------
    s.rect(20, 975, 290, 360, fill="#fafafa", stroke="#bbb", sw=1.5, rx=10)
    s.text(38, 1001, "Legend", cls="t", extra=' style="text-anchor:start"')
    leg = [(C_POS, "+12 V power", 4, None), (C_GND, "Ground / battery −", 4, None), (C_MP, "Motor + / +5 V", 4, None),
           (C_MN, "Motor − lead", 4, None), (C_LOOP, "E-stop safety loop (18 AWG)", 2.4, "7 4"), (C_SIG, "Logic signals (22 AWG)", 1.8, None),
           (C_PEND, "Pendant buttons / LED", 1.8, None)]
    for i, (c, t, w_, d) in enumerate(leg):
        y = 1029 + i * 28
        s.wire([(38, y), (88, y)], c, w_, d)
        s.text(100, y + 4, t, cls="n")
    s.text(38, 1231, "Rounded tags with the same name", cls="p")
    s.text(38, 1249, "are the same wire. Dots = joined.", cls="p")
    s.text(38, 1267, "Lines that cross without a dot", cls="p")
    s.text(38, 1285, "are not connected.", cls="p")

    notes = [
        "1. Key S1, both E-stops (box S2, pendant S4) and fuse F2 form one series loop that powers K1's coil. Open any of them",
        "    and K1 drops out: the motor driver and the Pico lose power at the same moment.",
        "2. Hold-to-run: the motor turns only while IN or OUT is held. The code ramps up over 0.5 s and stops when released.",
        "3. Overload: above %d A for 0.3 s it stops and beeps, so a snagged tarp can't rip the winch off the block." % v["trip"],
        "4. S3 is normally closed, so a broken wire reads as 'limit reached' and winding IN is blocked (fails safe).",
        "    Crimp the stopper ball on the rope about 1 m before the tarp's tow bar.",
        "5. S5 only closes while the ball-lock pin holds the spool's latch shut. Open or broken = the motor will not start.",
        "6. Below 12.0 V the controller won't start. Recharge with a 14.6 V LiFePO4 charger, key OFF, away from the pool.",
        "7. Mount F1 within 18 cm of battery +. D1 goes across the K1 coil; C1 sits right at the driver's power input.",
        "8. The worm gearbox is self-locking: when power drops, the spool holds the tarp where it is.",
    ]
    s.text(330, 1001, "How it works", cls="t", extra=' style="text-anchor:start"')
    for i, n in enumerate(notes):
        s.text(330, 1027 + 24 * i, n, cls="n")

    s.rect(1440, 975, 340, 360, fill="#eef7ff", stroke="#9cc", sw=1, rx=10)
    for i, l in enumerate(v["sizing"]):
        s.text(1458, 1003 + 30 * i, l, cls="n", extra=' style="font-weight:%d"' % (700 if i == 0 else 400))
    return s


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else "v4"
    v = VARIANTS[key]
    path = os.path.join(ROOT, v["out"])
    draw(v).save(path)
    print("wrote", path)
