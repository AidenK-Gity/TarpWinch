/*
  v3 (budget) mechanism for the tarp winch sim, dimensions from winch_v3.py.
  2x2x1/4 in aluminum angle hooks the REAR edge, 1/4 in plate on top carries an off-the-shelf
  3,500 lb hand trailer winch used as a CAPSTAN (4 wraps, tail held by hand, rope not stored).
  A second angle hooks the FRONT lip; an eye bolt carries a pulley block that turns the rope down.
  Styles: 'hand' (winch crank) and 'drill' (18 V cordless drill on the input shaft via a socket).
*/
window.WinchV3 = (function () {
  'use strict';
  const { LBF, fmt, IN } = WinchSim;
  const T = 0.25 * IN, LEG = 2 * IN, XR = -520;
  const WX = XR + 3.5 * IN, DRUM_Z = 2 * T + 2.6 * IN;
  const PIN = { x: WX - 1.5 * IN, z: DRUM_Z + 1.1 * IN };
  const GEAR_R = 37.7, PIN_R = 9.5;                 // 48T / 12T so the CAD centre distance meshes at 4:1
  const ARM = Math.hypot(4, 8) * IN;                // crank arm from winch_v3.py
  const EYE_Z = -0.6 * IN;
  const SHEAVE = { x: 1.6 * IN + 26 + 8, z: EYE_Z + 26 + 10, r: 1.0 * IN + 3.2 };
  const HAND = { x: -780, z: 20 }, PILE = { x: -930, z: WinchSim.Z_DECK + 4 };
  const MU_CAP = 0.15, WRAPS = 4;
  const PHI = Math.atan2(PIN.z - DRUM_Z, PIN.x - WX);
  const MESH = 5 * PHI + Math.PI + Math.PI / 12;

  const AL = '#c4c9d0', AL_E = '#7f8790', BLUE = '#1f5fd0', BLUE_E = '#0f3a8a';
  const SS = '#d9dce2', SS_E = '#7c828c', WIN = '#262b33', RUB = '#151515';

  function angleRear(g) {
    g.poly([[XR - T, -LEG + T], [XR, -LEG + T], [XR, 0], [XR + LEG - T, 0], [XR + LEG - T, T], [XR - T, T]], BLUE, BLUE_E, 1);
  }
  function angleFront(g) {
    g.poly([[-LEG + T, 0], [0, 0], [0, -LEG + T], [T, -LEG + T], [T, T], [-LEG + T, T]], BLUE, BLUE_E, 1);
  }
  function plate(g) {
    g.rect(XR - T, T, XR - T + 12 * IN, 2 * T, AL, AL_E, 1);
    for (const bx of [XR + 0.8 * IN, XR + 11 * IN]) g.rect(bx - 4, -2, bx + 4, 2 * T + 6, SS, SS_E, 1);
  }
  function winchBack(g) {
    g.rect(WX - 2.2 * IN, 2 * T, WX + 2.4 * IN, 2 * T + 0.15 * IN, WIN);                           // base
    g.poly([[WX - 2.2 * IN, 2 * T], [WX + 1.6 * IN, 2 * T], [WX + 1.6 * IN, DRUM_Z + 0.9 * IN],
      [WX + 0.6 * IN, DRUM_Z + 1.4 * IN], [WX - 2.2 * IN, DRUM_Z + 1.4 * IN]], 'rgba(38,43,51,0.92)', '#111', 1);  // far frame
    for (const p of [[WX - 1.8 * IN, 0], [WX + 2.0 * IN, 0]]) g.rect(p[0] - 4.5, -T - 4, p[0] + 4.5, 2 * T + 0.15 * IN + 8, SS, SS_E, 1);
    g.circle(WX, DRUM_Z, 1.5 * IN, '#3b4048', '#111', 1);        // far flange
    g.circle(WX, DRUM_Z, 0.75 * IN, '#aeb3ba');                   // drum core
  }
  function winchFront(g, st) {
    g.poly([[WX - 2.2 * IN, 2 * T], [WX + 1.6 * IN, 2 * T], [WX + 1.6 * IN, DRUM_Z + 0.9 * IN],
      [WX + 0.6 * IN, DRUM_Z + 1.4 * IN], [WX - 2.2 * IN, DRUM_Z + 1.4 * IN]], 'rgba(38,43,51,0.18)', '#111', 1.2);  // near frame, see-through
    g.circle(WX, DRUM_Z, 1.5 * IN, null, 'rgba(40,40,40,.8)', g.W(2, 1));
    g.gear(WX, DRUM_Z, GEAR_R, 48, st.dAng, 'rgba(200,204,210,0.30)', 'rgba(90,95,104,0.95)', 1);
    g.gear(PIN.x, PIN.z, PIN_R, 12, st.pinAng + MESH, '#cfd3da', SS_E, 1);
    g.circle(WX, DRUM_Z, 6, SS, SS_E, 1);
    // anti-reverse pawl clicking on the big gear
    const p = 2 * Math.PI / 48, frac = ((-st.dAng / p) % 1 + 1) % 1;
    const tip = g.pt(WX, DRUM_Z, GEAR_R - 1 + 2.5 * frac, Math.PI / 2 - 0.25);
    const piv = [WX + 0.9 * IN, DRUM_Z + 1.7 * IN];
    g.line(piv[0], piv[1], tip[0], tip[1], '#d81b1b', g.W(6, 1.5));
    g.circle(piv[0], piv[1], 4, SS, SS_E, 1);
  }
  function pulleyBlock(g, st, back) {
    if (back) {
      g.rect(-12, EYE_Z - 10, -5, EYE_Z + 10, SS, SS_E, 1);                        // nut behind the leg
      g.rect(-5, EYE_Z - 4.75, 1.6 * IN, EYE_Z + 4.75, SS, SS_E, 1);               // 3/8 eye bolt
      g.ring(1.6 * IN + 12, EYE_Z, 8, 14, SS);
      g.circle(1.6 * IN + 12, EYE_Z, 14, null, SS_E, 1);
      g.ring(1.6 * IN + 20, EYE_Z + 4, 5, 9, '#b9bec6');
      g.poly([[1.6 * IN + 14, EYE_Z + 8], [1.6 * IN + 26, EYE_Z + 2], [SHEAVE.x + 14, SHEAVE.z - 6], [SHEAVE.x - 6, SHEAVE.z + 8]], 'rgba(185,190,198,0.9)', SS_E, 1);
      g.circle(SHEAVE.x, SHEAVE.z, 1.15 * IN, '#b9bec6', SS_E, 1);                  // far cheek
      g.circle(SHEAVE.x, SHEAVE.z, 1.0 * IN, '#333', '#111', 1);                     // sheave
      g.circle(SHEAVE.x, SHEAVE.z, 0.8 * IN, null, '#555', g.W(1.5, 1));
      g.spokes(SHEAVE.x, SHEAVE.z, 5, 19, 4, st.shAng, '#888', g.W(4, 1));
    } else {
      g.circle(SHEAVE.x, SHEAVE.z, 1.15 * IN, 'rgba(185,190,198,0.18)', SS_E, 1.2); // near cheek, see-through
      g.circle(SHEAVE.x, SHEAVE.z, 5, SS, SS_E, 1);
    }
  }
  function handCrank(g, st) {
    const k = g.pt(PIN.x, PIN.z, ARM, st.pinAng);
    g.line(PIN.x, PIN.z, k[0], k[1], '#c7cbd2', g.W(10, 2));
    g.circle(k[0], k[1], 0.5 * IN, RUB, '#000', 1);
    g.circle(PIN.x, PIN.z, 0.3 * IN, SS, SS_E, 1);
  }
  function drill(g, st) {
    const x = PIN.x, z = PIN.z;
    g.rect(x - 0.7 * IN, z - 5.5 * IN, x + 0.7 * IN, z - 0.8 * IN, 'rgba(134,184,23,0.55)', '#4d6b0e', 1);   // grip
    g.rect(x - 1.6 * IN, z - 7.3 * IN, x + 1.6 * IN, z - 5.5 * IN, 'rgba(25,25,25,0.75)', '#000', 1);      // battery
    g.circle(x, z, 1.1 * IN, 'rgba(134,184,23,0.55)', '#4d6b0e', 1.2);                                     // body (end view)
    g.circle(x, z, 0.8 * IN, 'rgba(30,30,30,0.6)', '#000', 1);                                             // chuck
    g.circle(x, z, 0.45 * IN, '#9a9da3', SS_E, 1);                                                          // socket adapter
    g.rect(x - 0.15 * IN, z - 1.6 * IN, x + 0.15 * IN, z - 1.0 * IN, st.running ? '#ff6b3d' : '#333');     // trigger
    if (st.running) for (let i = 0; i < 3; i++) { const p = g.pt(x, z, 0.62 * IN, st.pinAng + i * 2.094); g.circle(p[0], p[1], 2.6, '#b6ff3d'); }
    if (st.phase === 2) g.text(x, z - 7.3 * IN, 'CLUTCH SLIPPING', { dy: 16, align: 'center', color: '#fff', bg: '#d81b1b', size: 11, bold: true });
  }
  function hand(g) {
    g.polyline([[HAND.x - 160, HAND.z + 230], [HAND.x - 20, HAND.z + 25]], '#e0b08a', g.W(28, 3));
    g.circle(HAND.x, HAND.z, 26, '#e7b892', '#9c6d4a', 1);
  }

  function capstanHold(T) { return T / Math.exp(MU_CAP * WRAPS * 2 * Math.PI); }

  function config(style) {
    const isHand = style === 'hand';
    return {
      title: isHand ? 'Tarp Winch v3 — Budget, Hand Winch' : 'Tarp Winch v3 — Budget, Drill Motor',
      subtitle: '2×2×¼ in angle hooks the rear edge · 3,500 lb trailer winch used as a capstan (4 wraps, tail by hand) · front angle + eye bolt + pulley block' +
        (isHand ? '' : ' · 18 V drill on the input shaft'),
      ratingLbf: 300, ratingWhat: '¼ in pulley block',
      ratio: 4, eff: 0.85,
      drum: { kind: 'capstan', x: WX, z: DRUM_Z, coreR: 0.75 * IN, ropeD: 6.35, flangeR: 1.5 * IN, wraps: WRAPS },
      wind: 'under',
      sheave: SHEAVE, sheaveName: 'pulley',
      tail: { hand: HAND, pile: PILE },
      drive: isHand
        ? { kind: 'crank', armR: Math.round(ARM), rpm0: 60, fMax: 250, rampT: 1.0 }
        : { kind: 'drill', rpm0: 340, droop: 9, clutchNm: 12, rampT: 0.3 },
      driveName: isHand ? 'Winch handle' : 'Cordless drill (18 V)',
      limit: null,
      cam: { cx: -330, cz: 70, w: 960 },
      phaseText: isHand
        ? ['Ready: one hand on the winch handle, the other tailing', 'Cranking + tailing: tarp coming across', '', 'Tarp in place: winch pawl holds, tail cleated', '']
        : ['Ready: drill on the input shaft, other hand tailing', 'Trigger held: drill driving the winch', 'Drill clutch slipping: load too high', 'Tarp in place: trigger released, winch pawl holds', ''],
      footnote: 'Pulley block drawn at its CAD position (fixed). A capstan holds no rope: the tail piles up behind the block.',

      drawBack(g, st) {
        hand(g);
        angleRear(g);
        plate(g);
        winchBack(g);
        angleFront(g);
        pulleyBlock(g, st, true);
      },
      drawFront(g, st) {
        winchFront(g, st);
        if (isHand) handCrank(g, st); else drill(g, st);
        pulleyBlock(g, st, false);
        g.circle(HAND.x, HAND.z, 26, 'rgba(231,184,146,0.85)', '#9c6d4a', 1);
      },
      drawForces(g, st) {
        const Th = st.Th, hold = capstanHold(st.T);
        g.arrow(WX, DRUM_Z - 45, 1, 0, g.forceLen(Th), '#ff8c42', 'rope pulls winch toward water ' + fmt(Th) + ' lbf');
        g.arrow(XR - T, -25, 1, 0, g.forceLen(Th), '#4cd07d', 'rear edge pushes back ' + fmt(Th) + ' lbf (bearing)', true);
        g.arrow(HAND.x - 30, HAND.z, -1, 0, 40, '#7fd3ff', 'tail hold ' + fmt(hold, 1) + ' lbf');
      },
      labels(st) {
        const L = [
          [WX, DRUM_Z + 0.9 * IN, '3,500 lb trailer winch (strap removed)', 40, -150],
          [WX + 20, DRUM_Z - 22, 'capstan: 4 wraps', 70, 110],
          [XR - T, -30, 'rear angle 2×2×¼ in hooks the back edge', -30, 80],
          [XR + 200, 2 * T, '¼ in winch plate', 10, 120],
          [-20, 3, 'front angle hooks the lip', -40, 110],
          [1.6 * IN + 12, EYE_Z, '⅜ in eye bolt', 60, 80],
          [SHEAVE.x + 20, SHEAVE.z + 18, 'pulley block', 60, -70],
          [HAND.x, HAND.z, 'operator tails the rope', -20, -90],
          [PILE.x, PILE.z + 20, 'tail piles on the deck', 20, -60],
        ];
        if (isHand) {
          const k = [PIN.x + ARM * Math.cos(st.pinAng), PIN.z + ARM * Math.sin(st.pinAng)];
          L.push([k[0], k[1], 'winch handle', Math.cos(st.pinAng) > 0 ? 60 : -60, -30]);
        } else {
          L.push([PIN.x + 0.8 * IN, PIN.z, 'drill + socket on the input shaft', -60, -130]);
          L.push([PIN.x, PIN.z - 6.4 * IN, 'drill battery', -70, 30]);
        }
        return L;
      },
      readouts(st) {
        const gm = st.geom;
        const Rx = st.T * (gm.toTarp.x + gm.toDrum.x), Rz = st.T * (gm.toTarp.z + gm.toDrum.z);
        return [
          ['Pull on winch (toward water)', fmt(st.Th) + ' lbf'],
          ['Rear angle bearing', fmt(st.Th) + ' lbf', 'good'],
          ['Front angle pushed down', fmt(Math.max(0, -Rz)) + ' lbf'],
          ['Front angle pushed back', fmt(Math.max(0, -Rx)) + ' lbf'],
          ['Tail hold force (μ 0.15, 4 wraps)', fmt(capstanHold(st.T), 1) + ' lbf'],
          ['Tail paid out behind block', fmt(st.s / 1000, 1) + ' m'],
        ];
      },
    };
  }
  return { config };
})();
