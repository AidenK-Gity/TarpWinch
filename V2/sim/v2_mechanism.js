/*
  v2 mechanism for the tarp winch sim (from winch_v2.py and the design notes).
  Rear C-clamp on the block's BACK edge (opens toward the water, bears on the edge),
  winch frame on top of it, UNDER-wound drum (rope leaves the bottom, runs ~60 mm above the
  platform) to an 80 mm roller saddle hooked on the FRONT lip. No screws on the saddle.
  Styles: 'crank' (hand crank, mirrored ratchet/pawl) and 'motor' (24 V worm gearmotor,
  pendant, rope-in limit switch on the saddle + stopper ball).
*/
window.WinchV2 = (function () {
  'use strict';
  const { LBF, fmt, ropeZAt, clamp, hyp } = WinchSim;
  const DX = -290;                                  // winch group sits over the rear clamp
  const D = { x: -150 + DX, z: 115 };
  const PIN = { x: -90 + DX, z: 182 };
  const ROLLER = { x: 58, z: 15, r: 38 };           // 80 mm roller, rope sits in the groove
  const KEEPER = { x: 58, z: 15 + 40 + 42 };        // 37 mm gap: the 30 mm stopper ball passes under
  const SAD_CHEEK = [[-60, 10], [15, 10], [15, -40], [95, -15], [95, 40], [75, 108], [35, 108], [-60, 30]];
  const PHI = Math.atan2(PIN.z - D.z, PIN.x - D.x);
  const MESH = 5 * PHI + Math.PI + Math.PI / 12;
  const PAWL_PIVOT = { x: D.x + 65, z: D.z - 45 };  // mirrored about the drum for under-wind

  const AL = 'rgba(178,184,193,0.55)', AL_E = '#7f8790', BLUE = '#1f5fd0', BLUE_E = '#0f3a8a';
  const RUB = '#1b1b1b', SS = '#d9dce2', SS_E = '#7c828c', POM = '#2a2a2a', RED = '#d81b1b';
  const YEL = '#f2cc19', GRN = '#21b04a';

  const mx = x => -520 - x;   // mirror the v1 clamp onto the rear edge

  function rearClamp(g) {
    g.rect(mx(-255), 0, mx(0), 3, RUB);
    g.poly([[-260, 15], [mx(14), 15], [mx(14), -100], [mx(-150), -100], [mx(-150), -85], [mx(0), -85], [mx(0), 3], [-260, 3]].map(p => [p[0], p[1]]), BLUE, BLUE_E, 1);
    for (const x of [mx(-120), mx(-60)]) {
      g.rect(x - 7, -138, x + 7, -48, SS, SS_E, 1);
      g.rect(x - 16, -48, x + 16, -40, RUB);
      g.rect(x - 38, -146, x + 38, -136, SS, SS_E, 1);
    }
  }

  function sidePlate(g) {
    // v1 side plate moved back and trimmed (no front sheave)
    g.poly([[-245 + DX, 15], [70 + DX, 15], [70 + DX, 140], [62 + DX, 182], [-60 + DX, 262], [-205 + DX, 262], [-245 + DX, 215]], AL, AL_E, 1);
    for (const p of [[-222, 40], [-222, 235], [45, 40]]) g.circle(p[0] + DX, p[1], 10, '#c9ccd2', SS_E, 1);
  }

  function saddleBack(g, st) {
    g.rect(-148, -3, 0, 0, RUB);
    g.rect(0, -43, 3, -3, RUB);
    g.poly(SAD_CHEEK, 'rgba(31,95,208,0.95)', BLUE_E, 1);          // far cheek
    g.rect(-150, 0, 0, 10, BLUE, BLUE_E, 1);
    g.rect(3, -50, 15, 10, BLUE, BLUE_E, 1);
    for (const x of [-120, -80]) g.rect(x, 1, x + 12, 9, '#0f3a8a');
    // roller
    g.circle(ROLLER.x, ROLLER.z, 40, POM, '#555', 1);
    g.circle(ROLLER.x, ROLLER.z, 34, null, '#4a4a4a', g.W(2, 1));
    g.spokes(ROLLER.x, ROLLER.z, 9, 31, 5, st.shAng, '#777', g.W(5, 1));
    g.circle(ROLLER.x, ROLLER.z, 8, SS, SS_E, 1);
    g.circle(KEEPER.x, KEEPER.z, 5, SS, SS_E, 1);
  }
  function saddleFront(g) {
    g.poly(SAD_CHEEK, 'rgba(31,95,208,0.22)', BLUE_E, 1.2);         // near cheek, see-through
    g.circle(ROLLER.x, ROLLER.z, 8, SS, SS_E, 1);
    g.circle(KEEPER.x, KEEPER.z, 5, SS, SS_E, 1);
  }

  function gears(g, st) {
    g.circle(D.x, D.z, 80, null, 'rgba(70,70,70,.7)', g.W(2.5, 1));
    g.gear(D.x, D.z, 72, 48, st.dAng, 'rgba(204,158,64,0.28)', 'rgba(140,100,30,0.9)', 1);
    g.gear(PIN.x, PIN.z, 18, 12, st.pinAng + MESH, '#cfd3da', SS_E, 1);
    g.circle(PIN.x, PIN.z, 10, '#e8eaee', SS_E, 1);
  }

  function ratchetPawl(g, st) {
    const p = 2 * Math.PI / 20;
    g.ratchet(D.x, D.z, 27, 36, 20, st.dAng, -1, '#c3c7ce', SS_E);
    g.circle(D.x, D.z, 12.5, SS, SS_E, 1);
    const frac = ((-st.dAng / p) % 1 + 1) % 1;
    const tipR = 27 + 9 * frac + 2;
    const a = -55 * Math.PI / 180;
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
    // battery/controller box and pendant moved forward onto the platform (winch_v2.py build_motor)
    g.rect(-300, 0, -190, 190, 'rgba(242,204,25,0.45)', '#9c8410', 1);
    g.rect(-303, 190, -187, 202, 'rgba(242,204,25,0.6)', '#9c8410', 1);
    g.circle(-245, 214, 18, RED, '#7a0d0d', 1);
    g.rect(-140, 0, -80, 40, 'rgba(242,204,25,0.85)', '#9c8410', 1);
    g.circle(-125, 46, 8, st.running ? '#5dff7e' : GRN, '#0b5a20', 1);
    g.circle(-98, 50, 10, RED, '#7a0d0d', 1);
    g.polyline([[-300, 150], [PIN.x - 130, PIN.z + 28]], 'rgba(20,20,20,.6)', g.W(5, 1));
    g.polyline([[-190, 25], [-60, 25], [-60, 20]], RUB, g.W(4, 1));
  }

  function motorFront(g, st) {
    g.poly([[PIN.x - 45, 45], [PIN.x + 130, 130], [PIN.x + 130, 175], [PIN.x + 80, 255], [PIN.x - 55, 255], [PIN.x - 80, 215]], 'rgba(178,184,193,0.30)', AL_E, 1);
    g.rect(PIN.x - 55, PIN.z - 45, PIN.x + 55, PIN.z + 45, 'rgba(115,120,128,0.55)', '#4d5259', 1.2);
    g.rect(PIN.x - 250, PIN.z - 72, PIN.x - 60, PIN.z + 28, 'rgba(58,63,71,0.6)', '#1f2328', 1.2);
    g.rect(PIN.x - 270, PIN.z - 64, PIN.x - 250, PIN.z + 20, 'rgba(58,63,71,0.7)', '#1f2328', 1);
    for (let i = 1; i < 8; i++) { const x = PIN.x - 250 + i * 22; g.line(x, PIN.z - 70, x, PIN.z + 26, 'rgba(20,22,26,.5)', 1); }
    g.circle(PIN.x, PIN.z, 10, '#e8eaee', SS_E, 1);
    if (st.running) {
      for (let i = 0; i < 3; i++) { const p = g.pt(PIN.x, PIN.z, 30, st.pinAng + i * 2.094); g.circle(p[0], p[1], 4, '#5dff7e'); }
    }
  }

  function limitSwitch(g, st) {
    // on the saddle: lever roller sits just under the rope; the stopper ball deflects it
    const lx = -50, ropeZ = ropeZAt(st.geom, lx);
    const near = st.ball && st.ball.onPath ? clamp(1 - st.ballDist / 45, 0, 1) : 0;
    const dip = st.tripped ? 1 : near;
    const rz = Math.min(ropeZ - 12, 40) - dip * 10;
    g.rect(-70, 10, -30, 38, YEL, st.tripped ? RED : '#9c8410', st.tripped ? 3 : 1);
    g.line(-36, 30, lx, rz, SS, g.W(5, 1.2));
    g.circle(lx, rz, 6, SS, SS_E, 1);
    if (st.tripped) g.text(-50, 38, 'LIMIT', { color: '#fff', bg: RED, size: 11, bold: true, align: 'center', dy: -30 });
  }

  function config(style) {
    const isCrank = style === 'crank';
    return {
      title: isCrank ? 'Tarp Winch v2 — Rear Clamp, Hand Crank' : 'Tarp Winch v2 — Rear Clamp, 24 V Motor',
      subtitle: 'Rear-edge C-clamp (bearing, no friction) · under-wound drum, rope ~60 mm above platform · 80 mm roller saddle on the front lip' +
        (isCrank ? ' · mirrored ratchet' : ' · worm gearmotor, pendant, limit switch on the saddle'),
      ratingLbf: 500, ratingWhat: 'drum + gears',
      ratio: 4, eff: 0.9,
      drum: { kind: 'spool', x: D.x, z: D.z, coreR: 45, ropeD: 6, perLayer: 16, flangeR: 80, reserve: 500 },
      wind: 'under',
      sheave: ROLLER, sheaveName: 'roller',
      drive: isCrank
        ? { kind: 'crank', armR: 200, rpm0: 42, fMax: 400, rampT: 1.0 }
        : { kind: 'motor', rpm0: 62, droop: 0.15, i0: 2, kI: 0.35, tripA: 18, rampT: 0.5, volts: 25.6 },
      driveName: isCrank ? 'Hand crank' : 'Gearmotor (24 V)',
      limit: isCrank ? null : { x: -50 },
      cam: { cx: -235, cz: 70, w: 860 },
      phaseText: isCrank
        ? ['Ready: operator takes the crank', 'Cranking: tarp coming across', '', 'Tarp in place: ratchet + pawl holding', '']
        : ['Ready: press and hold IN on the pendant', 'IN held: motor winding', '', 'Stopper ball tripped the limit switch on the saddle: motor stopped', 'Overcurrent trip (18 A)'],
      footnote: 'Under-winding reverses the drum, so the ratchet is mirrored' + (isCrank ? '.' : ' (and DIR_IN_LEVEL may need flipping in the firmware).'),

      drawBack(g, st) {
        if (!isCrank) motorBack(g, st);
        sidePlate(g);
        rearClamp(g);
        g.circle(D.x, D.z, 80, '#3a3a3a', '#555', 1);
        g.circle(D.x, D.z, 45, '#262626');
        saddleBack(g, st);
      },
      drawFront(g, st) {
        gears(g, st);
        if (isCrank) { ratchetPawl(g, st); crank(g, st); }
        else { g.circle(D.x, D.z, 12.5, SS, SS_E, 1); motorFront(g, st); limitSwitch(g, st); }
        saddleFront(g);
      },
      drawForces(g, st, f) {
        const Th = st.Th;
        g.arrow(D.x, D.z - 60, 1, 0, g.forceLen(Th), '#ff8c42', 'rope pulls winch toward water ' + fmt(Th) + ' lbf');
        g.arrow(-520, -60, 1, 0, g.forceLen(Th), '#4cd07d', 'rear edge pushes back ' + fmt(Th) + ' lbf (bearing)', true);
      },
      labels(st) {
        const L = [
          [D.x - 60, D.z + 40, 'UHMW drum (rope under-wound)', -60, -150],
          [mx(14), -60, 'rear C-clamp (opens toward water)', -40, 70],
          [mx(-120), -120, 'M16 clamp screws', -60, 30],
          [D.x + 50, D.z - 50, '48T gear (see-through)', 110, 150],
          [PIN.x + 14, PIN.z + 10, '12T pinion', 90, -60],
          [ROLLER.x + 30, ROLLER.z - 25, 'roller 80 mm', 80, 40],
          [KEEPER.x, KEEPER.z, 'keeper bar (ball passes under)', 70, -40],
          [-100, 5, 'roller saddle (no screws)', 20, 110],
          [8, -45, 'hook plate bears on front face', 70, 60],
        ];
        if (isCrank) {
          L.push([PAWL_PIVOT.x, PAWL_PIVOT.z, 'mirrored ratchet + pawl', 60, 90]);
        } else {
          L.push([PIN.x, PIN.z + 40, 'worm gearbox', 80, -90]);
          L.push([PIN.x - 160, PIN.z - 22, '24 V motor', -40, -110]);
          L.push([-50, 24, 'rope-in limit switch', -60, 90]);
          L.push([-245, 100, 'battery + controller box', -10, -170]);
        }
        return L;
      },
      readouts(st) {
        const gm = st.geom;
        const Rx = st.T * (gm.toTarp.x + gm.toDrum.x), Rz = st.T * (gm.toTarp.z + gm.toDrum.z);
        return [
          ['Pull on winch (toward water)', fmt(st.Th) + ' lbf'],
          ['Rear edge bearing', fmt(st.Th) + ' lbf', 'good'],
          ['Held by', 'bearing on the edge (no friction)'],
          ['Saddle pushed down', fmt(Math.max(0, -Rz)) + ' lbf'],
          ['Saddle pushed back', fmt(Math.max(0, -Rx)) + ' lbf'],
          ['Tipping moment (~60 mm line)', fmt(st.T * LBF * 0.06) + ' N·m'],
        ];
      },
    };
  }
  return { config };
})();
