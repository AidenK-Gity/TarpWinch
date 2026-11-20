/*
  v4 mechanism for the tarp winch sim, dimensions from V4/cad/winch_v4.py.

  Drive train: 12 V worm (wiper-style) gearmotor -> 12T pinion -> 48T gear -> rope spool.
  The 48T gear is bolted to the spool's near flange, so motor -> small gear -> big gear -> spool.
  The spool is a "nooked" pulley: a flanged reel that stores the whole rope, with a keyhole
  notch (the nook) in the far flange that catches the rope's stopper knot. It drops into
  open-top slots in two side plates and is held by swing latches + ball-lock pins, so it
  lifts out for transport.

  Mount is the v3 one: 2x2x1/4 in angle hooks the block's REAR edge under a base plate,
  second angle hooks the FRONT lip with an eye bolt + pulley block that turns the rope down.

  config(style, P): style is 'motor'; P overrides the default parameters (V4.2 uses this).
*/
window.WinchV4 = (function () {
  'use strict';
  const { fmt, IN, Z_DECK, ropeZAt, clamp } = WinchSim;

  const DEFAULTS = {
    version: 'v4',
    title: 'Tarp Winch v4 — Geared Motor + Detachable Spool',
    // spool ("nooked pulley"): 2.5 in OD aluminum tube core, 6 in between 6 in dia flanges
    spool: { x: -400, z: 98, coreR: 31.75, ropeD: 6.35, between: 6 * IN, flangeR: 76.2, reserve: 700 },
    // gears: module 3 spur, pinion forward of the spool so mesh force pushes the spool DOWN into its slots
    gear: { teeth: 48, pinion: 12, module: 3, eff: 0.93 },
    // motor: 12 V worm gearmotor, linear torque-speed line from no-load rpm to stall torque
    motor: { name: '12 V worm motor (32 N·m)', rpm0: 50, stallNm: 32, i0: 3, stallA: 35, tripA: 25, volts: 12.8, rampT: 0.5 },
    ratingLbf: 500, ratingWhat: 'spool, gears + ¼ in rope at 4:1 safety',
    pulley: { name: 'pulley block', wll: 550, dropZ: 0 },
    guard: false,
  };

  function merge(a, b) {
    const o = Array.isArray(a) ? a.slice() : Object.assign({}, a);
    for (const k in b || {}) o[k] = (b[k] && typeof b[k] === 'object' && !Array.isArray(b[k])) ? merge(a[k] || {}, b[k]) : b[k];
    return o;
  }

  const AL = '#c4c9d0', AL_E = '#7f8790', BLUE = '#1f5fd0', BLUE_E = '#0f3a8a';
  const SS = '#d9dce2', SS_E = '#7c828c', STEEL = 'rgba(160,166,176,0.30)', STEEL_E = 'rgba(70,76,86,0.95)';
  const RUB = '#151515', YEL = '#f2cc19', RED = '#d81b1b', GRN = '#21b04a', MOT = '#2b3038';

  function config(style, overrides) {
    const P = merge(DEFAULTS, overrides);
    const T = 0.25 * IN, LEG = 2 * IN, XR = -520;
    const S = P.spool, G = P.gear, M = P.motor;
    const ratio = G.teeth / G.pinion;
    const RG = G.module * G.teeth / 2, RP = G.module * G.pinion / 2;     // pitch radii (mm)
    const CD = RG + RP;                                                    // centre distance
    const PIN = { x: S.x + CD, z: S.z };                                   // pinion straight forward of the spool
    const PHI = Math.atan2(PIN.z - S.z, PIN.x - S.x);
    const MESH = (1 + ratio) * PHI + Math.PI + Math.PI / G.pinion;
    const perLayer = Math.floor(S.between / S.ropeD);
    const PLATE_TOP = 2 * T;                                               // base plate top (z)
    const SP = { x0: S.x - 90, x1: PIN.x + 45, top: S.z + 42 };            // side plate outline
    const SLOT_W = 0.75 * IN + 0.6;
    const EYE_Z = -0.6 * IN + P.pulley.dropZ;
    const SHEAVE = { x: 1.6 * IN + 26 + 8, z: EYE_Z + 26 + 10, r: 1.0 * IN + 3.2 };
    const LIMIT_X = SP.x1 + 22;
    const BOX = { x0: -1080, x1: -840, z0: Z_DECK, z1: Z_DECK + 190 };
    const PEND = { x: -770, z: Z_DECK };

    function sidePlatePts() {
      const pts = [[SP.x0, PLATE_TOP], [SP.x1, PLATE_TOP], [SP.x1, SP.top - 18], [SP.x1 - 18, SP.top], [S.x + SLOT_W / 2, SP.top]];
      for (let i = 0; i <= 12; i++) { const a = -i * Math.PI / 12; pts.push([S.x + SLOT_W / 2 * Math.cos(a), S.z + SLOT_W / 2 * Math.sin(a)]); }
      pts.push([S.x - SLOT_W / 2, SP.top], [SP.x0 + 18, SP.top], [SP.x0, SP.top - 18]);
      return pts;
    }

    // ---------- mount (same as v3, longer base plate) ----------
    function angleRear(g) { g.poly([[XR - T, -LEG + T], [XR, -LEG + T], [XR, 0], [XR + LEG - T, 0], [XR + LEG - T, T], [XR - T, T]], BLUE, BLUE_E, 1); }
    function angleFront(g) { g.poly([[-LEG + T, 0], [0, 0], [0, -LEG + T], [T, -LEG + T], [T, T], [-LEG + T, T]], BLUE, BLUE_E, 1); }
    function basePlate(g) {
      g.rect(XR - T, T, XR - T + 12 * IN, 2 * T, AL, AL_E, 1);
      for (const bx of [XR + 0.8 * IN, XR + 11 * IN]) g.rect(bx - 4, -2, bx + 4, 2 * T + 6, SS, SS_E, 1);
    }
    function pulleyBlock(g, st, back) {
      if (back) {
        if (P.pulley.dropZ < 0) g.rect(T, EYE_Z - 14, T + 6, -LEG + T, BLUE, BLUE_E, 1);       // drop plate down the front face
        g.rect(-12, EYE_Z - 10, -5, EYE_Z + 10, SS, SS_E, 1);
        g.rect(-5, EYE_Z - 4.75, 1.6 * IN, EYE_Z + 4.75, SS, SS_E, 1);
        g.ring(1.6 * IN + 12, EYE_Z, 8, 14, SS);
        g.circle(1.6 * IN + 12, EYE_Z, 14, null, SS_E, 1);
        g.poly([[1.6 * IN + 14, EYE_Z + 8], [1.6 * IN + 26, EYE_Z + 2], [SHEAVE.x + 14, SHEAVE.z - 6], [SHEAVE.x - 6, SHEAVE.z + 8]], 'rgba(185,190,198,0.9)', SS_E, 1);
        g.circle(SHEAVE.x, SHEAVE.z, 1.15 * IN, '#b9bec6', SS_E, 1);
        g.circle(SHEAVE.x, SHEAVE.z, 1.0 * IN, '#333', '#111', 1);
        g.circle(SHEAVE.x, SHEAVE.z, 0.8 * IN, null, '#555', g.W(1.5, 1));
        g.spokes(SHEAVE.x, SHEAVE.z, 5, 19, 4, st.shAng, '#888', g.W(4, 1));
      } else {
        g.circle(SHEAVE.x, SHEAVE.z, 1.15 * IN, 'rgba(185,190,198,0.18)', SS_E, 1.2);
        g.circle(SHEAVE.x, SHEAVE.z, 5, SS, SS_E, 1);
      }
    }

    // ---------- winch ----------
    function farSide(g) {
      g.poly(sidePlatePts(), 'rgba(178,184,193,0.95)', AL_E, 1);                          // far side plate
      g.rect(SP.x0 + 10, PLATE_TOP, SP.x0 + 10 + 4 * IN, PLATE_TOP + LEG, 'rgba(31,95,208,0.85)', BLUE_E, 1);  // far foot angle
      g.circle(S.x, S.z, S.flangeR, '#3b4048', '#111', 1);                                 // far flange
      g.circle(S.x, S.z, S.coreR, '#aeb3ba');                                              // core tube
      // the nook: keyhole notch in the far flange that catches the rope's stopper knot
      const a = Math.PI * 0.75, k = g.pt(S.x, S.z, S.coreR + 9, a);
      g.circle(k[0], k[1], 6, '#1a1d22', '#000', 1);
    }
    function gearPinion(g, st) {
      g.circle(S.x, S.z, S.flangeR, null, 'rgba(40,40,40,.8)', g.W(2, 1));                  // near flange outline
      g.gear(S.x, S.z, RG, G.teeth, st.dAng, STEEL, STEEL_E, 1);
      for (let i = 0; i < 4; i++) { const p = g.pt(S.x, S.z, 50, st.dAng + Math.PI / 4 + i * Math.PI / 2); g.circle(p[0], p[1], 4, SS, SS_E, 1); }
      g.gear(PIN.x, PIN.z, RP, G.pinion, st.pinAng + MESH, '#cfd3da', SS_E, 1);
      g.circle(PIN.x, PIN.z, 6, SS, SS_E, 1);
      g.circle(S.x, S.z, 9.5, SS, SS_E, 1);                                                 // dead axle
    }
    function nearSide(g, st) {
      g.poly(sidePlatePts(), 'rgba(178,184,193,0.22)', AL_E, 1.2);                          // near side plate, see-through
      g.rect(SP.x0 + 10, PLATE_TOP, SP.x0 + 10 + 4 * IN, PLATE_TOP + LEG, 'rgba(31,95,208,0.18)', BLUE_E, 1);
      // swing latch + ball-lock pin over the axle
      // latch pivot and ball-lock pin sit behind the axle (clear of the motor); the front end closes over the axle
      const lz = S.z + 10.5;
      g.rect(S.x - 70, lz, S.x + 14, lz + 14, 'rgba(31,95,208,0.9)', BLUE_E, 1);
      g.circle(S.x - 62, lz + 7, 4, SS, SS_E, 1);
      g.circle(S.x - 30, lz + 7, 5, SS, SS_E, 1);
      g.ring(S.x - 30, lz + 26, 6, 10, '#c9ccd2');
      g.rect(S.x - 36, lz + 14, S.x - 24, lz + 22, '#2a7de1');                             // spool-latched reed sensor
      if (P.guard) {                                                                         // pinion-side mesh guard (clear of the gear so the spool lifts out)
        const gx0 = S.x + RG + G.module + 2, gx1 = PIN.x + RP + 14, gtop = S.z + RP + 16;
        g.poly([[gx0, gtop], [gx1, gtop], [gx1, PLATE_TOP + 4], [gx1 + 3, PLATE_TOP + 4], [gx1 + 3, gtop + 3], [gx0, gtop + 3]], 'rgba(200,230,255,0.35)', 'rgba(90,140,190,0.95)', 1.5);
      }
    }
    function motor(g, st) {
      const x = PIN.x, z = PIN.z;
      g.circle(x, z, 52, 'rgba(58,63,71,0.55)', '#1f2328', 1.2);                           // worm gearbox housing
      for (let i = 0; i < 3; i++) { const p = g.pt(x, z, 46, Math.PI / 2 + i * 2.094); g.circle(p[0], p[1], 4, SS, SS_E, 1); }
      g.rect(x - 28, z + 40, x + 28, z + 190, 'rgba(43,48,56,0.62)', '#111', 1.2);         // motor can
      g.rect(x - 22, z + 190, x + 22, z + 204, 'rgba(43,48,56,0.75)', '#111', 1);
      for (let i = 1; i < 7; i++) g.line(x - 27, z + 40 + i * 21, x + 27, z + 40 + i * 21, 'rgba(15,17,20,.45)', 1);
      g.circle(x, z, 7, '#e8eaee', SS_E, 1);
      if (st.running) for (let i = 0; i < 3; i++) { const p = g.pt(x, z, 30, st.pinAng + i * 2.094); g.circle(p[0], p[1], 3.5, '#5dff7e'); }
    }
    function limitSwitch(g, st) {
      const lx = LIMIT_X, ropeZ = ropeZAt(st.geom, lx);
      const near = st.ball && st.ball.onPath ? clamp(1 - st.ballDist / 45, 0, 1) : 0;
      const dip = st.tripped ? 1 : near;
      const rz = Math.min(ropeZ - 11, 45) - dip * 9;
      g.rect(lx - 32, PLATE_TOP, lx + 4, PLATE_TOP + 26, YEL, st.tripped ? RED : '#9c8410', st.tripped ? 3 : 1);
      g.line(lx - 6, PLATE_TOP + 20, lx, rz, SS, g.W(5, 1.2));
      g.circle(lx, rz, 6, SS, SS_E, 1);
      if (st.tripped) g.text(lx, PLATE_TOP + 30, 'LIMIT', { color: '#fff', bg: RED, size: 11, bold: true, align: 'center', dy: -34 });
    }
    function controls(g, st) {
      g.rect(BOX.x0, BOX.z0, BOX.x1, BOX.z1, 'rgba(242,204,25,0.85)', '#9c8410', 1);
      g.rect(BOX.x0 - 3, BOX.z1, BOX.x1 + 3, BOX.z1 + 12, 'rgba(242,204,25,0.95)', '#9c8410', 1);
      g.circle(BOX.x1 - 50, BOX.z1 + 26, 18, RED, '#7a0d0d', 1);
      g.rect(BOX.x0 + 40, BOX.z1 + 12, BOX.x0 + 64, BOX.z1 + 22, RUB);
      g.rect(PEND.x - 30, PEND.z, PEND.x + 30, PEND.z + 40, 'rgba(242,204,25,0.95)', '#9c8410', 1);
      g.circle(PEND.x - 12, PEND.z + 46, 8, st.running ? '#5dff7e' : GRN, '#0b5a20', 1);
      g.circle(PEND.x + 14, PEND.z + 50, 10, RED, '#7a0d0d', 1);
      g.polyline([[BOX.x1, BOX.z0 + 60], [PEND.x - 30, PEND.z + 20]], RUB, g.W(4, 1));
      // motor cable: box -> over the block's back edge -> motor
      g.polyline([[BOX.x1 - 30, BOX.z1 + 12], [-640, 290], [PIN.x - 60, 330], [PIN.x, PIN.z + 204]], 'rgba(20,20,20,.75)', g.W(6, 1.2));
    }

    function slotLoads(st) {
      const gm = st.geom, r = st.drum.r, Ft = st.T * r / RG;           // tangential gear force on the spool, lbf
      const Fx = -st.T * gm.toDrum.x - Math.tan(20 * Math.PI / 180) * Ft;
      const Fz = -st.T * gm.toDrum.z - Ft;
      return { Fx, Fz, Ft };
    }

    const isMotor = true;
    return {
      title: P.title,
      subtitle: 'Motor → 12T pinion → 48T gear → rope spool (stores the rope) · spool lifts out of open slots for transport · v3 angle mount + front pulley block'
        .replace('12T', G.pinion + 'T').replace('48T', G.teeth + 'T') + (P.subtitleExtra || ''),
      ratingLbf: P.ratingLbf, ratingWhat: P.ratingWhat,
      ratio, eff: G.eff,
      drum: { kind: 'spool', x: S.x, z: S.z, coreR: S.coreR, ropeD: S.ropeD, perLayer, flangeR: S.flangeR, reserve: S.reserve },
      wind: 'under',
      sheave: SHEAVE, sheaveName: 'pulley',
      drive: { kind: 'motor', rpm0: M.rpm0, droop: M.rpm0 / M.stallNm, i0: M.i0, kI: (M.stallA - M.i0) / M.stallNm, tripA: M.tripA, rampT: M.rampT, volts: M.volts },
      driveName: M.name,
      limit: { x: LIMIT_X },
      cam: { cx: -300, cz: 60, w: 900 },
      phaseText: ['Ready: spool latched, press and hold IN on the pendant', 'IN held: motor winding rope onto the spool', '',
        'Stopper ball tripped the rope-in limit: motor stopped, worm holds the tarp', 'Overcurrent trip (' + M.tripA + ' A): tarp snagged or motor overloaded'],
      footnote: 'The worm gearbox is self-locking, so the spool holds when the motor stops. ' + (P.footExtra || ''),
      params: P,

      drawBack(g, st) {
        controls(g, st);
        angleRear(g);
        basePlate(g);
        farSide(g);
        angleFront(g);
        pulleyBlock(g, st, true);
      },
      drawFront(g, st) {
        gearPinion(g, st);
        nearSide(g, st);
        motor(g, st);
        limitSwitch(g, st);
        pulleyBlock(g, st, false);
      },
      drawForces(g, st) {
        const L = slotLoads(st);
        g.arrow(S.x, S.z - S.flangeR - 20, 1, 0, g.forceLen(st.Th), '#ff8c42', 'rope pulls winch toward water ' + fmt(st.Th) + ' lbf');
        g.arrow(XR - T, -25, 1, 0, g.forceLen(st.Th), '#4cd07d', 'rear edge pushes back ' + fmt(st.Th) + ' lbf (bearing)', true);
        g.arrow(S.x + RG, S.z, 0, -1, g.forceLen(L.Ft), '#7fd3ff', 'pinion pushes gear down ' + fmt(L.Ft) + ' lbf');
      },
      labels(st) {
        return [
          [S.x - 30, S.z + 50, 'rope spool (lifts out)', -60, -150],
          [S.x + RG * 0.7, S.z - RG * 0.7, G.teeth + 'T gear bolted to spool (see-through)', 60, 130],
          [PIN.x + RP, PIN.z, G.pinion + 'T pinion', 90, 20],
          [PIN.x, PIN.z + 150, M.name, 70, -60],
          [S.x - 30, S.z + 36, 'swing latch + ball-lock pin', -40, -110],
          [S.x - 66, S.z + 30, 'the nook: keyhole holds the rope knot', -90, -20],
          [SP.x0 + 40, PLATE_TOP + 40, 'side plates with open-top slots', -60, 70],
          [XR - T, -30, 'rear angle hooks the back edge', -30, 80],
          [LIMIT_X - 14, PLATE_TOP + 10, 'rope-in limit switch', 110, -25],
          [-20, 3, 'front angle hooks the lip', -40, 120],
          [SHEAVE.x + 20, SHEAVE.z + 18, P.pulley.name, 60, -70],
        ];
      },
      readouts(st) {
        const gm = st.geom, L = slotLoads(st);
        const Rx = st.T * (gm.toTarp.x + gm.toDrum.x), Rz = st.T * (gm.toTarp.z + gm.toDrum.z);
        return [
          ['Pull on winch (toward water)', fmt(st.Th) + ' lbf'],
          ['Rear angle bearing', fmt(st.Th) + ' lbf', 'good'],
          ['Front angle pushed down', fmt(Math.max(0, -Rz)) + ' lbf'],
          ['Pinion force on 48T gear'.replace('48', G.teeth), fmt(L.Ft) + ' lbf'],
          ['Spool pushed into slots (fwd / down)', fmt(L.Fx) + ' / ' + fmt(-L.Fz) + ' lbf', 'good'],
          ['Latch pin load', L.Fz > 0 ? fmt(L.Fz) + ' lbf' : '0 (load seats the spool)', L.Fz > 0 ? 'warn' : 'good'],
          ['Rope left on spool to wind', fmt(Math.max(0, (st.drum.wound - S.reserve)) / 1000, 1) + ' m'],
        ];
      },
    };
  }
  return { config, DEFAULTS };
})();
