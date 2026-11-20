"""
Builds the v4 and v4.2 supplies-and-costs workbooks (same layout as the v2/v3 sheets).
Usage: python tools/make_budget.py     (needs openpyxl)
"""
import datetime
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKED = datetime.datetime(2026, 11, 19)
SECTIONS = ["Mount", "Spool", "Drive", "Electrical"]

ZORO_PIN = "https://www.zoro.com/i/G1815130/"
SPEEDY_ANGLE = "https://speedymetals.com/p-2198-2-x-2-angle-6061-t6-aluminum-extruded.aspx"
ROPE = "https://ebay.com/str/blueoxrope"
SAILRITE = "https://www.sailrite.com/Single-Block-with-Shackle-1-Stainless-Steel"
WATTCYCLE = "https://www.wattcycle.com/products/wattcycle-12v-20ah-lifepo4-battery"
MD30C = "https://uk.robotshop.com/products/cytron-30a-5-30v-single-brushed-dc-motor-driver"
J3_32 = "https://www.zoro.com/autotex-wiper-motor-j3-series-12v-32nm-torque-d101/i/G6125826/"
J3_55 = "https://www.zoro.com/autotex-wiper-motor-j3-series-12v-55nm-torque-g138/i/G6125808/"
GEAR60 = "https://www.123bearing.com/power-transmission/rack-spur-gear/spur-gear/3-60-x"

# (item, section, qty, unit, price, spec, where, link, notes)
V4 = [
    ("6061 aluminum angle, 2 x 2 x 1/4 in, 36 in", "Mount", 1, 31.22, "Quoted", "Cut into the rear hook (8 in), front hook (8 in) and two side-plate feet (4 in each)", "Speedy Metals", SPEEDY_ANGLE, "Same stock as v3. 8 in left over."),
    ("6061 aluminum plate, 1/4 in, 15 x 12 in", "Mount", 1, 40.00, "Estimate", "Base plate: carries both side plates", "", None, "A scrap piece from the robotics shop works."),
    ("Stainless pulley block for 1/4 in rope, 550 lb WLL", "Mount", 1, 35.00, "Estimate", "Single block with swivel shackle, 1/4–5/16 in line, 2,200 lb break", "Sailrite", SAILRITE, "v3's 300 lb block is too light for v4's 500 lbf rating."),
    ("Stainless hardware", "Mount", 1, 25.00, "Estimate", "3/8 in eye bolt, 5/16 and 1/4 in bolts, nyloc nuts, washers", "", None, None),
    ("Rubber pads", "Mount", 1, 8.00, "Estimate", "Self-adhesive neoprene strip, 1/8 in", "", None, "Under both hooks and the base plate."),
    ("Backup strap", "Mount", 1, 10.00, "Estimate", "1 in ratchet strap", "", None, "From the base plate around the block post."),
    ("Stainless snap hook", "Mount", 1, 8.00, "Estimate", "For the tarp's tow bar", "", None, None),
    ("6061 round tube, 2.5 in OD x 1/4 in wall, 12 in", "Spool", 1, 25.00, "Estimate", "Spool core, cut to 6 in", "Speedy Metals", None, "Half is left as a spare."),
    ("Laser-cut 1/4 in 6061 parts (one set)", "Spool", 1, 85.00, "Estimate", "2 spool flanges (one with the rope nook), 2 side plates with slots, 2 swing latches", "SendCutSend", None, "Upload DXFs exported from winch_v4.py for an exact quote."),
    ("316 stainless round rod, 3/4 in x 12 in", "Spool", 1, 30.00, "Estimate", "Spool dead axle, cut to about 10 in", "", None, None),
    ("Flanged bronze bushing, 3/4 in ID x 1 in OD", "Spool", 2, 6.00, "Estimate", "Pressed into each flange; the spool spins on these", "", None, None),
    ("316 threaded rod 1/4-20 x 12 in + nylocs", "Spool", 1, 12.00, "Estimate", "Four tie rods clamp gear + flanges + core together", "", None, None),
    ("Ball-lock pin, 3/8 in, 304 stainless, pull ring", "Spool", 2, 13.19, "Quoted", "2-1/2 in grip (LBH-SS3127)", "Zoro", ZORO_PIN, "Pull both to lift the spool out. Another Zoro page lists the same part at $14.59."),
    ("Rope, 1/4 in x 100 ft double braid polyester", "Spool", 1, 34.95, "Quoted", "Blue Ox Rope, about 2,000 lb break", "eBay store", ROPE, "4:1 safety factor at 500 lbf."),
    ("Stopper ball, 30 mm", "Spool", 1, 5.00, "Estimate", "Trips the rope-in limit switch", "", None, None),
    ("12 V wiper worm gearmotor, 32 N·m", "Drive", 1, 156.99, "Quoted", "Autotex J3 series D101, self-locking worm", "Zoro", J3_32, "Built for wet use. Check the output shaft size before ordering the pinion."),
    ("Spur gear, 48 teeth, module 3", "Drive", 1, 66.85, "Quoted", "Steel, 3-48-X (144 mm pitch dia)", "123Bearing", None, "Price from the v2 sheet. Bolted to the spool flange."),
    ("Spur pinion, 12 teeth, module 3", "Drive", 1, 40.00, "Estimate", "Steel, module 3, 12T", "", None, None),
    ("Pinion hub / adapter to the motor shaft", "Drive", 1, 25.00, "Estimate", "Bore + key or set screw to suit the motor output", "", None, "Free if your school or FRC shop can make it."),
    ("Battery, 12 V 20 Ah LiFePO4", "Electrical", 1, 69.99, "Quoted", "WattCycle, built-in BMS", "WattCycle", WATTCYCLE, "About 15 full pulls per charge (sim: 13 Wh per pull)."),
    ("LiFePO4 charger, 14.6 V", "Electrical", 1, 30.00, "Estimate", "4–5 A", "", None, "Charge away from the pool."),
    ("Motor driver, Cytron MD30C", "Electrical", 1, 45.00, "Estimate", "30 A continuous, 5–30 V, PWM + DIR", "RobotShop", MD30C, "Listed at £31.32 on RobotShop UK; US price not checked."),
    ("Raspberry Pi Pico", "Electrical", 1, 5.00, "Estimate", "RP2040, runs the MicroPython controller", "", None, None),
    ("Current sensor module", "Electrical", 1, 8.72, "Quoted", "ACS758LCB-050B, 50 A bidirectional", "Walmart", None, "Price from the v2 sheet."),
    ("Buck converter 12 V to 5 V", "Electrical", 1, 8.00, "Estimate", "3 A, 8–40 V input", "", None, None),
    ("Main contactor, 12 V coil, 100 A continuous duty", "Electrical", 1, 30.00, "Estimate", "K1", "", None, None),
    ("Fuses + holders", "Electrical", 1, 25.00, "Estimate", "F1 40 A MIDI, F2 3 A, 15 A charge fuse", "", None, None),
    ("Hold-to-run pendant with E-stop", "Electrical", 1, 45.00, "Estimate", "Rainproof 2-button + mushroom E-stop, 6-core cable 5 m", "", None, None),
    ("Box E-stop + key switch", "Electrical", 1, 27.00, "Estimate", "22 mm twist-release mushroom (N.C.) + removable-key switch", "", None, None),
    ("Rope-in limit switch", "Electrical", 1, 18.00, "Estimate", "IP67 roller-lever switch, N.C. contact", "", None, None),
    ("Spool-latched sensor", "Electrical", 1, 8.00, "Estimate", "IP67 reed switch + magnet (magnet goes in the ball-lock pin handle)", "", None, None),
    ("Small parts", "Electrical", 1, 12.00, "Estimate", "Buzzer, LED, 2N2222, 1N5408, 1000 µF cap, 100k/22k/10k/20k/1k/220 ohm resistors", "", None, None),
    ("Enclosure, IP67", "Electrical", 1, 40.00, "Estimate", "About 10 x 8 x 6 in", "", None, None),
    ("Wire, terminals, heat shrink, glands", "Electrical", 1, 57.00, "Estimate", "10 AWG red/black, 18/22 AWG, ring terminals, 6 IP68 glands", "", None, None),
    ("Motor cable + charge inlet", "Electrical", 1, 30.00, "Estimate", "2 x 10 AWG outdoor cable 3 m; IP67 2-pin charge inlet", "", None, None),
]


def v42_items():
    out = []
    for it in V4:
        it = list(it)
        name = it[0]
        if name.startswith("6061 aluminum plate"):
            it[0], it[3], it[5] = "6061 aluminum plate, 1/4 in, 17 x 12 in", 45.00, "Base plate: carries both side plates (wider for the 8 in spool)"
        elif name.startswith("6061 round tube"):
            it[5], it[8] = "Spool core, cut to 8 in", "v4.2: 8 in between flanges, so the rope fits in 3 layers instead of 4."
        elif name.startswith("12 V wiper worm gearmotor"):
            it[0], it[3], it[5], it[7] = "12 V wiper worm gearmotor, 55 N·m", 194.99, "Autotex J3 series G138, self-locking worm", J3_55
            it[8] = "v4.2: up from 32 N·m. Sim peak uses 39 % of stall (v4: 59 %)."
        elif name.startswith("Spur gear, 48"):
            it[0], it[3], it[4], it[5], it[6] = "Spur gear, 36 teeth, module 3", 55.00, "Estimate", "Steel, module 3, 36T (108 mm pitch dia)", "123Bearing"
            it[8] = "v4.2: 3:1 instead of 4:1, faster with the stronger motor. (The 60T is $88.56 at 123Bearing, for comparison.)"
            it[7] = None
        elif name.startswith("Battery"):
            it[0], it[3], it[4], it[5], it[7] = "Battery, 12 V 12 Ah LiFePO4", 45.00, "Estimate", "Built-in BMS, ≥ 50 A continuous", None
            it[8] = "v4.2: about 13 pulls per charge (sim: 9 Wh per pull). The 20 Ah was much bigger than needed."
        elif name.startswith("Fuses"):
            it[5] = "F1 50 A MIDI, F2 3 A, 15 A charge fuse"
        out.append(tuple(it))
    idx = next(i for i, x in enumerate(out) if x[0].startswith("Pinion hub"))
    out.insert(idx + 1, ("Gear guard", "Drive", 1, 15.00, "Estimate", "1/8 in clear polycarbonate, bent over the gear mesh", "", None, "v4.2: covers the pinion/gear mesh where hands go when lifting the spool."))
    return out


def build(path, sheet_title, label, items, compare):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title
    bold = Font(bold=True)
    money = '$#,##0.00'
    first = 10
    ws["A1"], ws["B1"] = label + " mechanical parts", '=SUMIFS(E%d:E1048576,B%d:B1048576,"<>Electrical")' % (first, first)
    ws["A2"], ws["B2"] = label + " electrical parts", '=SUMIFS(E%d:E1048576,B%d:B1048576,"Electrical")' % (first, first)
    ws["A3"], ws["B3"] = label + " build total", "=B1+B2"
    ws["A4"], ws["B4"] = "Compare", compare
    ws["A5"], ws["B5"] = "Prices checked", CHECKED
    ws["A6"], ws["B6"] = "Note", "Prices exclude tax and shipping. Estimate = no live listing checked; get a quote before ordering."
    for c in ("A1", "A2", "A3", "B1", "B2", "B3"):
        ws[c].font = bold
    for c in ("B1", "B2", "B3"):
        ws[c].number_format = money
    ws["B5"].number_format = "yyyy-mm-dd"
    hdr = ["Item", "Section", "Qty", "Unit cost ($)", "Line total ($)", "Price", "Spec", "Where to buy", "Notes"]
    for i, h in enumerate(hdr, 1):
        c = ws.cell(first - 1, i, h)
        c.fill = PatternFill("solid", fgColor="FFF3F3F3")
        c.font = bold
    for r, (item, sec, qty, unit, price, spec, where, link, notes) in enumerate(items, first):
        ws.cell(r, 1, item)
        ws.cell(r, 2, sec)
        ws.cell(r, 3, qty)
        ws.cell(r, 4, unit).number_format = money
        ws.cell(r, 5, "=C%d*D%d" % (r, r)).number_format = money
        ws.cell(r, 6, price)
        ws.cell(r, 7, spec)
        w = ws.cell(r, 8, where or None)
        if link:
            w.hyperlink = link
            w.style = "Hyperlink"
        ws.cell(r, 9, notes)
    last = first + len(items) - 1
    for col, wd in zip("ABCDEFGHI", (46, 12, 5, 13, 13, 10, 58, 16, 60)):
        ws.column_dimensions[col].width = wd
    for row in ws.iter_rows(min_row=first, max_row=last):
        for c in row:
            c.alignment = Alignment(vertical="top", wrap_text=c.column in (1, 7, 9))
    ws.freeze_panes = "A%d" % first

    dd = wb.create_sheet("Dropdown options")
    dd["A1"], dd["A2"] = "Quoted", "Estimate"
    for i, s in enumerate(SECTIONS, 1):
        dd.cell(i, 2, s)
    v1 = DataValidation(type="list", formula1="'Dropdown options'!$A$1:$A$2", allow_blank=True)
    v2 = DataValidation(type="list", formula1="'Dropdown options'!$B$1:$B$%d" % len(SECTIONS), allow_blank=True)
    ws.add_data_validation(v1)
    ws.add_data_validation(v2)
    v1.add("F%d:F%d" % (first, last))
    v2.add("B%d:B%d" % (first, last))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wb.save(path)
    mech = sum(q * u for (_, s, q, u, *_) in items if s != "Electrical")
    elec = sum(q * u for (_, s, q, u, *_) in items if s == "Electrical")
    print("%s: mechanical $%.2f, electrical $%.2f, total $%.2f -> %s" % (label, mech, elec, mech + elec, path))


if __name__ == "__main__":
    build(os.path.join(ROOT, "V4", "docs", "Pool Cover Winch v4 Supplies and Costs.xlsx"), "v4 Supplies", "v4", V4,
          "v3 drill build $261.63; v2 motor build about $2,421")
    build(os.path.join(ROOT, "V4", "V4.2", "docs", "Pool Cover Winch v4.2 Supplies and Costs.xlsx"), "v4.2 Supplies", "v4.2", v42_items(),
          "v4 build (see V4/docs); changed rows say 'v4.2:' in Notes")
