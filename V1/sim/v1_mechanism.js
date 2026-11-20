/*
  v1 mechanism for the tarp winch sim.
  Front-lip C-clamp held by screw friction, over-wound UHMW drum, 12T -> 48T spur stage,
  fairlead sheave at the front. Styles: 'crank' (hand crank + ratchet/pawl) and
  'motor' (24 V worm gearmotor, pendant hold-to-run, rope-in limit switch + stopper ball).
  Layout follows the v1 design notes and winch_motor.py; winch.py is not in the repo, so a few
  frame dimensions are approximated.
*/
window.WinchV1 = (function () {
  'use strict';
  const { LBF, unit, fmt, ropeZAt, clamp } = WinchSim;
  const D = { x: -150, z: 115 };                 // drum axis
  const PIN = { x: -90, z: 182 };                // pinion / input shaft (90 mm centres, 4:1)
  const S = { x: 45, z: 75, r: 40 };             // fairlead sheave, 80 mm
  const KEEPER = { x: 45, z: 157 };
  const PHI = Math.atan2(PIN.z - D.z, PIN.x - D.x);
  const MESH = 5 * PHI + Math.PI + Math.PI / 12;  // pinion phase so the teeth interleave
  const PAWL_PIVOT = { x: -215, z: 70 };

  const AL = 'rgba(178,184,193,0.55)', AL_E = '#7f8790', BLUE = '#1f5fd0', BLUE_E = '#0f3a8a';
  const RUB = '#1b1b1b', SS = '#d9dce2', SS_E = '#7c828c', POM = '#2a2a2a', RED = '#d81b1b';
  const YEL = '#f2cc19', GRN = '#21b04a', MOT = '#3a3f47';

  function frontClamp(g) {
    g.rect(-255, 0, 0, 3, RUB);
    g.poly([[-260, 15], [14, 15], [14, -100], [-150, -100], [-150, -85], [0, -85], [0, 3], [-260, 3]], BLUE, BLUE_E, 1);
    for (const x of [-120, -60]) {
      g.rect(x - 7, -138, x + 7, -48, SS, SS_E, 1);
      g.rect(x - 16, -48, x + 16, -40, RUB);
      g.rect(x - 38, -146, x + 38, -136, SS, SS_E, 1);
    }
  }

  function sidePlate(g) {
    g.poly([[-245, 15], [70, 15], [100, 45], [100, 140], [62, 182], [-60, 262], [-205, 262], [-245, 215]], AL, AL_E, 1);
    for (const p of [[-222, 40], [-222, 235], [75, 40]]) g.circle(p[0], p[1], 10, '#c9ccd2', SS_E, 1);
  }

  function sheave(g, st) {
    g.circle(S.x, S.z, 40, POM, '#555', 1);
    g.circle(S.x, S.z, 34, null, '#4a4a4a', g.W(2, 1));
    g.spokes(S.x, S.z, 9, 31, 5, st.shAng, '#777', g.W(5, 1));
    g.circle(S.x, S.z, 8, SS, SS_E, 1);
    g.circle(KEEPER.x, KEEPER.z, 6, SS, SS_E, 1);
  }

  function gears(g, st) {
    g.circle(D.x, D.z, 80, null, 'rgba(70,70,70,.7)', g.W(2.5, 1));            // near flange (see-through)
    g.gear(D.x, D.z, 72, 48, st.dAng, 'rgba(204,158,64,0.28)', 'rgba(140,100,30,0.9)', 1);
    g.gear(PIN.x, PIN.z, 18, 12, st.pinAng + MESH, '#cfd3da', SS_E, 1);
    g.circle(PIN.x, PIN.z, 10, '#e8eaee', SS_E, 1);
  }

  function ratchetPawl(g, st) {
    const p = 2 * Math.PI / 20;
    g.ratchet(D.x, D.z, 27, 36, 20, st.dAng, +1, '#c3c7ce', SS_E);
    g.circle(D.x, D.z, 12.5, SS, SS_E, 1);
    const frac = ((st.dAng / p) % 1 + 1) % 1;
    const tipR = 27 + 9 * frac + 2;
    const a = -125 * Math.PI / 180;
    const tip = g.pt(D.x, D.z, tipR, a);
    g.line(PAWL_PIVOT.x, PAWL_PIVOT.z, tip[0], tip[1], RED, g.W(9, 2));
    g.circle(PAWL_PIVOT.x, PAWL_PIVOT.z, 6, SS, SS_E, 1);
  }

  function crank(g, st) {
    const k = g.pt(PIN.x, PIN.z, 200, st.pinAng);
    g.line(PIN.x, PIN.z, k[0], k[1], '#c7cbd2', g.W(16, 2));
    g.line(PIN.x, PIN.z, k[0], k[1], '#e9ebef', g.W(8, 1));
    g.circle(k[0], k[1], 18, RUB, '#000', 1);
    g.circle(PIN.x, PIN.z, 12, SS, SS_E, 1);
  }

  function motorBack(g, st) {
    // IP67 battery/controller box + pendant on the platform behind the winch
    g.rect(-410, 0, -300, 190, 'rgba(242,204,25,0.55)', '#9c8410', 1);
    g.rect(-413, 190, -297, 202, 'rgba(242,204,25,0.7)', '#9c8410', 1);
    g.circle(-355, 214, 18, RED, '#7a0d0d', 1);
    g.rect(-260, 0, -200, 40, YEL, '#9c8410', 1);
    g.circle(-245, 46, 8, st.running ? '#5dff7e' : GRN, '#0b5a20', 1);
    g.circle(-218, 50, 10, RED, '#7a0d0d', 1);
    g.polyline([[-300, 110], [-255, 230], [-200, 230]], RUB, g.W(8, 1.2));
    g.polyline([[-300, 60], [-260, 40]], RUB, g.W(6, 1));
  }

  function motorFront(g, st) {
    // outrigger plate, worm gearbox on the input shaft, motor can running back along -X
    g.poly([[PIN.x - 45, 45], [PIN.x + 130, 130], [PIN.x + 130, 175], [PIN.x + 80, 255], [PIN.x - 55, 255], [PIN.x - 80, 215]], 'rgba(178,184,193,0.30)', AL_E, 1);
    g.rect(PIN.x - 55, PIN.z - 45, PIN.x + 55, PIN.z + 45, 'rgba(115,120,128,0.55)', '#4d5259', 1.2);
    g.rect(PIN.x - 250, PIN.z - 72, PIN.x - 60, PIN.z + 28, 'rgba(58,63,71,0.6)', '#1f2328', 1.2);
    g.rect(PIN.x - 270, PIN.z - 64, PIN.x - 250, PIN.z + 20, 'rgba(58,63,71,0.7)', '#1f2328', 1);
    for (let i = 1; i < 8; i++) { const x = PIN.x - 250 + i * 22; g.line(x, PIN.z - 70, x, PIN.z + 26, 'rgba(20,22,26,.5)', 1); }
    g.circle(PIN.x, PIN.z, 10, '#e8eaee', SS_E, 1);
    // spinning indicator on the output shaft
    if (st.running) {
      const a0 = st.pinAng;
      for (let i = 0; i < 3; i++) { const p = g.pt(PIN.x, PIN.z, 30, a0 + i * 2.094); g.circle(p[0], p[1], 4, '#5dff7e'); }
    }
  }

  function limitSwitch(g, st) {
    const lx = 0, ropeZ = ropeZAt(st.geom, lx);
    const near = st.ball && st.ball.onPath ? clamp(1 - st.ballDist / 45, 0, 1) : 0;
    const lift = st.tripped ? 1 : near;
    const rz = ropeZ + 12 + lift * 18;
    g.rect(-25, 172, 25, 198, YEL, st.tripped ? RED : '#9c8410', st.tripped ? 3 : 1);
    g.line(15, 172, lx, rz, SS, g.W(5, 1.2));
    g.circle(lx, rz, 6, SS, SS_E, 1);
    if (st.tripped) g.text(0, 205, 'LIMIT', { color: '#fff', bg: RED, size: 11, bold: true, align: 'center', dy: -10 });
  }

  function config(style) {
    const isCrank = style === 'crank';
    return {
      title: isCrank ? 'Tarp Winch v1 — Hand Crank' : 'Tarp Winch v1 — 24 V Motor',
      subtitle: 'Front-lip C-clamp (screw friction) · over-wound drum · 12T→48T spur stage · 80 mm fairlead sheave' +
        (isCrank ? ' · ratchet + pawl' : ' · worm gearmotor, hold-to-run pendant, rope-in limit switch'),
      ratingLbf: 500, ratingWhat: 'drum + gears',
      ratio: 4, eff: 0.9,
      drum: { kind: 'spool', x: D.x, z: D.z, coreR: 45, ropeD: 6, perLayer: 16, flangeR: 80, reserve: 500 },
      wind: 'over',
      sheave: S, sheaveName: 'sheave',
      keeper: { x: KEEPER.x, z: KEEPER.z, r: 9 },   // 12 mm bar + rope radius
      drive: isCrank
        ? { kind: 'crank', armR: 200, rpm0: 42, fMax: 400, rampT: 1.0 }
        : { kind: 'motor', rpm0: 62, droop: 0.15, i0: 2, kI: 0.35, tripA: 18, rampT: 0.5, volts: 25.6 },
      driveName: isCrank ? 'Hand crank' : 'Gearmotor (24 V)',
      limit: isCrank ? null : { x: 0 },
      cam: { cx: isCrank ? -60 : -110, cz: 40, w: isCrank ? 820 : 900 },
      phaseText: isCrank
        ? ['Ready: operator takes the crank', 'Cranking: tarp coming across', '', 'Tarp in place: ratchet + pawl holding', '']
        : ['Ready: press and hold IN on the pendant', 'IN held: motor winding', '', 'Stopper ball tripped the limit switch: motor stopped, worm holds', 'Overcurrent trip (18 A)'],
      footnote: 'v1 clamp is held only by screw friction; see Mount loads.',

      drawBack(g, st) {
        if (!isCrank) motorBack(g, st);
        sidePlate(g);
        frontClamp(g);
        g.circle(D.x, D.z, 80, '#3a3a3a', '#555', 1);       // far flange
        g.circle(D.x, D.z, 45, '#262626');                   // core
        sheave(g, st);
      },
      drawFront(g, st) {
        gears(g, st);
        if (isCrank) { ratchetPawl(g, st); crank(g, st); }
        else { g.circle(D.x, D.z, 12.5, SS, SS_E, 1); motorFront(g, st); limitSwitch(g, st); }
      },
      drawForces(g, st) {
        const Th = st.Th;
        g.arrow(-60, -92, 1, 0, g.forceLen(Th), '#ff8c42', 'rope drags clamp toward water ' + fmt(Th) + ' lbf');
        for (const x of [-120, -60]) g.arrow(x, -146, 0, 1, g.forceLen(Th), '#ff5b5b', null, true);
        g.text(-90, -146, 'screws must squeeze ≈ ' + fmt(2 * Th) + ' lbf (friction only)', { dy: g.forceLen(Th) + 14, align: 'center', color: '#ff8080', bg: 'rgba(15,18,24,.85)', size: 11, bold: true });
      },
      labels(st) {
        const L = [
          [D.x - 60, D.z + 40, 'UHMW drum (rope over-wound)', -80, -150],
          [S.x + 25, S.z - 25, 'fairlead sheave 80 mm', 90, 40],
          [KEEPER.x, KEEPER.z, 'rope keeper bar', 90, -30],
          [-200, -92, 'front C-clamp (opens toward deck)', -60, 40],
          [-60, -120, 'M16 clamp screws', 80, 30],
          [D.x + 50, D.z - 50, '48T bronze gear (see-through)', 40, 120],
          [PIN.x + 14, PIN.z + 10, '12T pinion', 90, -60],
          [-240, 220, 'side plate', -60, -30],
        ];
        if (isCrank) {
          L.push([PAWL_PIVOT.x, PAWL_PIVOT.z, 'ratchet + pawl', -70, 60]);
          const k = [PIN.x + 200 * Math.cos(st.pinAng), PIN.z + 200 * Math.sin(st.pinAng)];
          L.push([k[0], k[1], 'crank handle (200 mm)', -70, -40]);
        } else {
          L.push([PIN.x, PIN.z + 40, 'worm gearbox', 80, -90]);
          L.push([PIN.x - 160, PIN.z - 22, '24 V motor', -40, -110]);
          L.push([0, 185, 'rope-in limit switch', 70, -70]);
          L.push([-355, 100, 'battery + controller box', -50, 120]);
          L.push([-230, 20, 'pendant', 0, 70]);
        }
        return L;
      },
      readouts(st) {
        return [
          ['Pull on winch (toward water)', fmt(st.Th) + ' lbf'],
          ['Clamp screw force needed', '≈ ' + fmt(2 * st.Th) + ' lbf', 'warn'],
          ['Held by', 'friction only (μ ≈ 0.5)'],
          ['Tipping moment (115 mm line)', fmt(st.T * LBF * 0.115) + ' N·m'],
        ];
      },
    };
  }
  return { config };
})();
