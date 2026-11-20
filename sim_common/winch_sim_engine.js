/*
  Tarp Winch visual simulator: shared engine.

  Side-elevation (X-Z) view in mm, same frame as the CAD scripts:
    X+ toward the water, starting-block platform front face at X = 0, platform top at Z = 0.

  The engine owns the pool, tarp, rope path, physics, time control, camera and HUD.
  Each version (V1/V2/V3) supplies a config with its geometry, drive and drawing code.

  Physics is pre-integrated once at load (fixed 10 ms step), so time can be scrubbed,
  reversed and sped up freely. Load model (from the design notes): wet 25 yd cover ~315 lb,
  sliding mu ~0.5 on the part that is on the water, plus a small base drag. The rope tension
  is the horizontal pull divided by cos(rope angle), so it climbs as the tarp nears the wall.
*/
(function () {
  'use strict';

  // ---------------- world constants (mm) ----------------
  const LBF = 4.448222;
  const POOL_L = 22860;            // 25 yd
  const Z_WATER = -750;            // water surface below the platform top
  const Z_DECK = -450;             // deck the block stands on
  const Z_FLOOR = -2750;
  const WALL_NEAR = -80;           // block front overhangs the near wall by 80 mm
  const X_STOP = 600;              // pull ends with the tarp edge 0.6 m from the block front
  const EDGE_Z = Z_WATER + 18;     // tarp leading-edge bar floats at the surface
  const X0 = POOL_L - 400;         // tarp edge start position (just off the far wall)
  const TARP_WET_LB = 315, MU_TARP = 0.5, BASE_DRAG_LB = 12;
  const TARP_TOTAL = POOL_L + 2200;
  const REEL = { x: POOL_L + 1150, z: Z_DECK + 700, core: 90, t: 3.2 };
  const START_DELAY = 1.0, REC = 0.05, DT = 0.01;
  const TOP_H = 50, TB_H = 56, PANEL_W = 310;
  const SPEEDS = [0.25, 0.5, 1, 2, 4, 8, 16, 32, 64];
  const NUM = ['s', 'dAng', 'shAng', 'T', 'v', 'rpmIn', 'tauIn', 'F', 'I', 'ramp'];

  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, f) => a + (b - a) * f;
  const hyp = Math.hypot;
  const fmt = (v, d = 0) => (isFinite(v) ? v.toFixed(d) : '-');
  function fmtTime(t) {
    t = Math.max(0, t);
    const m = Math.floor(t / 60), s = t - m * 60;
    return m + ':' + (s < 10 ? '0' : '') + s.toFixed(1);
  }

  // ---------------- geometry helpers ----------------
  // tangent from external point E to circle (C, r); returns the upper (or lower) tangent point
  function tangentPC(E, C, r, lower) {
    const dx = E.x - C.x, dz = E.z - C.z, d = hyp(dx, dz);
    const b = Math.atan2(dz, dx), a = Math.acos(clamp(r / d, -1, 1));
    const p1 = { x: C.x + r * Math.cos(b + a), z: C.z + r * Math.sin(b + a) };
    const p2 = { x: C.x + r * Math.cos(b - a), z: C.z + r * Math.sin(b - a) };
    return (p1.z > p2.z) !== !!lower ? p1 : p2;
  }
  // wrap angle to (-PI, PI]
  function wrapPI(a) { while (a <= -Math.PI) a += 2 * Math.PI; while (a > Math.PI) a -= 2 * Math.PI; return a; }
  // common tangents between two circles; pick the one matching pred(p1, p2)
  function tangentCC(c1, r1, c2, r2, pred) {
    const Dx = c1.x - c2.x, Dz = c1.z - c2.z, L = hyp(Dx, Dz), phi = Math.atan2(Dz, Dx);
    let best = null;
    for (const s1 of [1, -1]) for (const s2 of [1, -1]) {
      const R1 = r1 * s1, R2 = r2 * s2, k = (R1 - R2) / L;
      if (Math.abs(k) > 1) continue;
      const a = Math.acos(k);
      for (const sg of [1, -1]) {
        const al = phi + sg * a, nx = Math.cos(al), nz = Math.sin(al);
        const sol = { p1: { x: c1.x - R1 * nx, z: c1.z - R1 * nz }, p2: { x: c2.x - R2 * nx, z: c2.z - R2 * nz } };
        if (pred(sol.p1, sol.p2)) best = best || sol;
      }
    }
    return best || { p1: { x: c1.x, z: c1.z + r1 }, p2: { x: c2.x, z: c2.z + r2 } };
  }
  function unit(x, z) { const l = hyp(x, z) || 1; return { x: x / l, z: z / l }; }

  // ---------------- model ----------------
  function baseGeo(cfg) {
    const sh = cfg.sheave;
    const sxF = sh.x + sh.r, H = sh.z - EDGE_Z;
    const Lf0 = hyp(X0 - sxF, H);
    const sEnd = Lf0 - hyp(X_STOP - sxF, H);
    return { sxF, H, Lf0, sEnd };
  }
  function edgeX(geo, s) {
    const L = geo.Lf0 - s;
    return geo.sxF + Math.sqrt(Math.max(0, L * L - geo.H * geo.H));
  }
  function drumState(cfg, s) {
    const d = cfg.drum;
    if (d.kind === 'capstan') return { r: d.coreR + d.ropeD / 2, outer: d.coreR + d.ropeD, layer: 1, wound: 0 };
    let rem = d.reserve + s, k = 0;
    for (;;) {
      const rc = d.coreR + d.ropeD * (k + 0.5), per = d.perLayer * 2 * Math.PI * rc;
      if (rem <= per || k > 30) return { r: rc, outer: d.coreR + d.ropeD * (k + 1), layer: k + 1, wound: d.reserve + s, frac: rem / per };
      rem -= per; k++;
    }
  }
  function loadAt(geo, s) {
    const x = edgeX(geo, s);
    const ang = Math.atan2(geo.H, Math.max(1, x - geo.sxF));
    const onWater = clamp((POOL_L - 250 - x) / POOL_L, 0, 1);
    let Th = BASE_DRAG_LB + MU_TARP * TARP_WET_LB * onWater;
    Th *= 1 + 0.05 * Math.sin(x / 2700 * 2 * Math.PI) + 0.03 * Math.sin(x / 830 * 2 * Math.PI);
    return { x, ang, Th, T: Th / Math.cos(ang) };
  }

  function simulate(cfg) {
    const geo = baseGeo(cfg), d = cfg.drive, out = [];
    const sign = cfg.wind === 'over' ? 1 : -1;
    let t = 0, s = 0, dAng = 0, shAng = 0, ramp = 0, done = false, tDone = 0, fault = false, overT = 0, nextRec = 0, energy = 0;
    let onSheave = true;
    for (let it = 0; it < 2e6; it++) {
      if (it % 10 === 0) onSheave = ropeGeom(cfg, { x: edgeX(geo, s), drum: drumState(cfg, s) }).contact === 'sheave';
      const L = loadAt(geo, s);
      const r = drumState(cfg, s).r;
      const tauIn = L.T * LBF * (r / 1000) / cfg.ratio / cfg.eff;
      const running = !done && !fault && t >= START_DELAY;
      let rpmT = 0, F = 0, I = 0, slip = false;
      const pinAng = -cfg.ratio * dAng;
      if (d.kind === 'crank') {
        F = tauIn / (d.armR / 1000);
        rpmT = d.rpm0 * clamp(1 - F / d.fMax, 0.15, 1) * (1 + 0.12 * Math.sin(2 * pinAng));
      } else if (d.kind === 'motor') {
        rpmT = Math.max(0, d.rpm0 - d.droop * tauIn);
        I = d.i0 + d.kI * tauIn;
      } else if (d.kind === 'drill') {
        if (tauIn > d.clutchNm) { slip = true; rpmT = 0; } else rpmT = Math.max(0, d.rpm0 - d.droop * tauIn);
      }
      ramp = running ? Math.min(1, ramp + DT / d.rampT) : 0;   // ratchet / worm / pawl hold instantly
      if (!running) { F = 0; I = 0; }
      if (d.kind === 'motor' && running) {
        overT = I > d.tripA ? overT + DT : 0;
        if (overT > 0.3) fault = true;
      }
      const rpmIn = rpmT * ramp;
      const wIn = rpmIn * 2 * Math.PI / 60, wDrum = wIn / cfg.ratio, v = wDrum * r;  // v in mm/s
      energy += tauIn * wIn * DT;
      const phase = fault ? 4 : done ? 3 : slip && running ? 2 : t < START_DELAY ? 0 : 1;
      if (t >= nextRec - 1e-9) {
        out.push({ t, s, dAng, shAng, T: L.T, v, rpmIn, tauIn, F, I, ramp, phase, energy });
        nextRec += REC;
      }
      s += v * DT;
      dAng += sign * wDrum * DT;
      if (onSheave) shAng += v / cfg.sheave.r * DT;
      if (fault && !done) { done = true; tDone = t; }
      if (!done && s >= geo.sEnd) { s = geo.sEnd; done = true; tDone = t; }
      t += DT;
      if (done && t > tDone + 4) break;
      if (t > 7200) break;
    }
    const sim = { out, geo, tDone, duration: out[out.length - 1].t };
    // stopper ball: place it on the rope so it reaches the limit switch exactly at the end of the pull
    if (cfg.limit) {
      const st = { s: geo.sEnd, x: edgeX(geo, geo.sEnd), drum: drumState(cfg, geo.sEnd) };
      const gm = ropeGeom(cfg, st);
      sim.ballOffset = gm.cum[gm.iP2] + limitPoint(cfg, gm).u * hyp(gm.tl.p1.x - gm.tl.p2.x, gm.tl.p1.z - gm.tl.p2.z);
    }
    return sim;
  }

  // ---------------- rope path ----------------
  // Rope path from the tarp edge to the drum. The rope normally wraps over the top of the
  // redirect sheave/roller. If the line out to the tarp is flatter than the line in from the
  // drum, it lifts off the sheave: it then bears under the keeper bar (if any) or spans free.
  function ropeGeom(cfg, st) {
    const D = { x: cfg.drum.x, z: cfg.drum.z }, rd = st.drum.r, under = cfg.wind === 'under';
    const S = { x: cfg.sheave.x, z: cfg.sheave.z }, rs = cfg.sheave.r;
    const E = { x: st.x, z: EDGE_Z };
    const drumSide = p => (under ? p.z < D.z : p.z > D.z);
    let contact = null, tp, tl, a0 = 0, wrap = 0, sgn = 1;
    {
      const tpS = tangentPC(E, S, rs);
      const tlS = tangentCC(D, rd, S, rs, (p1, p2) => drumSide(p1) && p2.z > S.z);
      const aOut = Math.atan2(tpS.z - S.z, tpS.x - S.x), aIn = Math.atan2(tlS.p2.z - S.z, tlS.p2.x - S.x);
      const w = wrapPI(aIn - aOut);
      if (w >= 0) { contact = { C: S, r: rs, kind: 'sheave' }; tp = tpS; tl = tlS; a0 = aOut; wrap = w; sgn = 1; }
    }
    if (!contact && cfg.keeper) {
      const K = { x: cfg.keeper.x, z: cfg.keeper.z }, rk = cfg.keeper.r;
      const tpK = tangentPC(E, K, rk, true);
      const tlK = tangentCC(D, rd, K, rk, (p1, p2) => drumSide(p1) && p2.z < K.z);
      const bOut = Math.atan2(tpK.z - K.z, tpK.x - K.x), bIn = Math.atan2(tlK.p2.z - K.z, tlK.p2.x - K.x);
      const w = wrapPI(bOut - bIn);
      if (w >= 0) { contact = { C: K, r: rk, kind: 'keeper' }; tp = tpK; tl = tlK; a0 = bOut; wrap = w; sgn = -1; }
    }
    if (!contact) {
      const pd = tangentPC(E, D, rd, under);
      const u = (S.x - pd.x) / ((E.x - pd.x) || 1);
      const pm = { x: S.x, z: lerp(pd.z, E.z, u) };
      contact = { C: pm, r: 0, kind: 'none' }; tp = pm; tl = { p1: pd, p2: pm };
    }
    const C = contact.C, rc = contact.r;
    const pts = [[E.x, E.z], [tp.x, tp.z]];
    const n = Math.max(2, Math.ceil(wrap / 0.1));
    if (rc > 0) for (let i = 1; i < n; i++) { const a = a0 + sgn * wrap * i / n; pts.push([C.x + rc * Math.cos(a), C.z + rc * Math.sin(a)]); }
    pts.push([tl.p2.x, tl.p2.z]);
    const iP2 = pts.length - 1;
    pts.push([tl.p1.x, tl.p1.z]);
    const cum = [0];
    for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + hyp(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    return {
      E, tp, tl, S: C, rs: rc, contact: contact.kind, D, rd, pts, cum, iP2, total: cum[cum.length - 1],
      toTarp: unit(E.x - tp.x, E.z - tp.z), toDrum: unit(tl.p1.x - tl.p2.x, tl.p1.z - tl.p2.z),
    };
  }
  function walk(gm, d) {
    if (d <= 0) return { x: gm.pts[0][0], z: gm.pts[0][1], onPath: true };
    for (let i = 1; i < gm.pts.length; i++) {
      if (gm.cum[i] >= d) {
        const f = (d - gm.cum[i - 1]) / ((gm.cum[i] - gm.cum[i - 1]) || 1);
        return { x: lerp(gm.pts[i - 1][0], gm.pts[i][0], f), z: lerp(gm.pts[i - 1][1], gm.pts[i][1], f), onPath: true };
      }
    }
    const p = gm.pts[gm.pts.length - 1];
    return { x: p[0], z: p[1], onPath: false };
  }
  function limitPoint(cfg, gm) {
    const a = gm.tl.p2, b = gm.tl.p1;
    const u = clamp((cfg.limit.x - a.x) / ((b.x - a.x) || 1), 0, 1);
    return { u, x: lerp(a.x, b.x, u), z: lerp(a.z, b.z, u) };
  }
  function ropeZAt(gm, x) {
    const a = gm.tl.p2, b = gm.tl.p1;
    const u = clamp((x - a.x) / ((b.x - a.x) || 1), 0, 1);
    return lerp(a.z, b.z, u);
  }
  function tailGeom(cfg, st) {
    const D = { x: cfg.drum.x, z: cfg.drum.z }, hand = cfg.tail.hand, pile = cfg.tail.pile;
    const tt = tangentPC(hand, D, st.drum.r);
    const pts = [[tt.x, tt.z], [hand.x, hand.z]];
    for (let i = 1; i <= 12; i++) {
      const f = i / 12, mx = (hand.x + pile.x) / 2 - 120, mz = (hand.z + pile.z) / 2 - 40;
      pts.push([(1 - f) * (1 - f) * hand.x + 2 * f * (1 - f) * mx + f * f * pile.x,
                (1 - f) * (1 - f) * hand.z + 2 * f * (1 - f) * mz + f * f * pile.z]);
    }
    return { tt, pts };
  }

  // ---------------- app state ----------------
  const A = {
    cfg: null, sim: null, t: 0, playing: true, speedIdx: 5, reverse: false,
    cam: { cx: 0, cz: 0, scale: 1 }, follow: false, inset: true, forces: true, labels: true,
    W: 0, H: 0, dpr: 1, canvas: null, ctx: null, last: 0, drag: null, el: {},
  };

  function stateAt(t) {
    const cfg = A.cfg, sim = A.sim, o = sim.out;
    const fi = clamp(t / REC, 0, o.length - 1);
    const i = Math.min(Math.floor(fi), o.length - 2), f = clamp(fi - i, 0, 1);
    const a = o[i], b = o[i + 1] || a;
    const st = { t };
    for (const k of NUM) st[k] = lerp(a[k], b[k], f);
    st.energy = lerp(a.energy, b.energy, f);
    st.phase = (f < 0.5 ? a : b).phase;
    st.x = edgeX(sim.geo, st.s);
    st.drum = drumState(cfg, st.s);
    st.pinAng = -cfg.ratio * st.dAng;
    st.ropeAngDeg = Math.atan2(sim.geo.H, Math.max(1, st.x - sim.geo.sxF)) * 180 / Math.PI;
    st.Th = st.T * Math.cos(st.ropeAngDeg * Math.PI / 180);
    st.running = st.rpmIn > 0.3;
    st.geom = ropeGeom(cfg, st);
    if (cfg.limit) {
      st.ball = walk(st.geom, sim.ballOffset);
      st.limitPt = limitPoint(cfg, st.geom);
      st.ballDist = st.ball.onPath ? hyp(st.ball.x - st.limitPt.x, st.ball.z - st.limitPt.z) : 0;
      st.tripped = st.phase === 3;
    }
    if (cfg.tail) st.tail = tailGeom(cfg, st);
    st.done = st.phase >= 3;
    return st;
  }

  // ---------------- drawing helpers ----------------
  function makeG(ctx, view) {
    const sc = view.scale, ox = view.ox, oy = view.oy, cx = view.cx, cz = view.cz;
    const X = x => ox + (x - cx) * sc, Y = z => oy - (z - cz) * sc;
    const g = { ctx, sc, X, Y, view };
    g.W = (mm, min = 1) => Math.max(mm * sc, min);
    g.begin = pts => {
      ctx.beginPath();
      for (let i = 0; i < pts.length; i++) { const p = pts[i]; if (i) ctx.lineTo(X(p[0]), Y(p[1])); else ctx.moveTo(X(p[0]), Y(p[1])); }
    };
    g.fs = (fill, stroke, lw) => {
      if (fill) { ctx.fillStyle = fill; ctx.fill(); }
      if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw || 1; ctx.stroke(); }
    };
    g.poly = (pts, fill, stroke, lw) => { g.begin(pts); ctx.closePath(); g.fs(fill, stroke, lw); };
    g.polyline = (pts, stroke, lw, dash, off) => {
      g.begin(pts);
      ctx.setLineDash(dash || []); ctx.lineDashOffset = off || 0;
      ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.lineJoin = 'round'; ctx.lineCap = dash ? 'butt' : 'round';
      ctx.stroke(); ctx.setLineDash([]);
    };
    g.rect = (x0, z0, x1, z1, fill, stroke, lw) => g.poly([[x0, z0], [x1, z0], [x1, z1], [x0, z1]], fill, stroke, lw);
    g.circle = (x, z, r, fill, stroke, lw) => {
      ctx.beginPath(); ctx.arc(X(x), Y(z), Math.max(r * sc, 0.6), 0, Math.PI * 2); g.fs(fill, stroke, lw);
    };
    g.ring = (x, z, r0, r1, fill) => {
      ctx.beginPath();
      ctx.arc(X(x), Y(z), Math.max(r1 * sc, 0.6), 0, Math.PI * 2);
      ctx.moveTo(X(x) + Math.max(r0 * sc, 0.3), Y(z));
      ctx.arc(X(x), Y(z), Math.max(r0 * sc, 0.3), 0, Math.PI * 2, true);
      ctx.fillStyle = fill; ctx.fill('evenodd');
    };
    g.line = (x0, z0, x1, z1, stroke, lw) => g.polyline([[x0, z0], [x1, z1]], stroke, lw);
    g.pt = (x, z, r, a) => [x + r * Math.cos(a), z + r * Math.sin(a)];
    g.gear = (x, z, rp, n, ang, fill, stroke, lw) => {
      const m = 2 * rp / n, ro = rp + m, rr = rp - 1.25 * m, p = 2 * Math.PI / n, pts = [];
      for (let i = 0; i < n; i++) {
        const a = ang + i * p;
        pts.push(g.pt(x, z, rr, a - 0.30 * p), g.pt(x, z, ro, a - 0.13 * p), g.pt(x, z, ro, a + 0.13 * p), g.pt(x, z, rr, a + 0.30 * p));
      }
      g.poly(pts, fill, stroke, lw);
    };
    // sawtooth ratchet; dir = +1 free to turn CCW, -1 free to turn CW
    g.ratchet = (x, z, rRoot, rTip, n, ang, dir, fill, stroke) => {
      const p = 2 * Math.PI / n, pts = [];
      for (let i = 0; i < n; i++) {
        const a = ang + dir * i * p;
        pts.push(g.pt(x, z, rTip, a), g.pt(x, z, rRoot, a + dir * p * 0.97));
      }
      g.poly(pts, fill, stroke, 1);
    };
    g.spokes = (x, z, r0, r1, n, ang, stroke, lw) => {
      for (let i = 0; i < n; i++) {
        const a = ang + i * 2 * Math.PI / n, p0 = g.pt(x, z, r0, a), p1 = g.pt(x, z, r1, a);
        g.line(p0[0], p0[1], p1[0], p1[1], stroke, lw);
      }
    };
    g.textPx = (sx, sy, s, o = {}) => {
      ctx.font = (o.bold ? '600 ' : '') + (o.size || 12) + 'px system-ui, Segoe UI, Arial, sans-serif';
      ctx.textAlign = o.align || 'left'; ctx.textBaseline = 'middle';
      if (o.bg) {
        const w = ctx.measureText(s).width, h = (o.size || 12) + 6;
        const x0 = o.align === 'center' ? sx - w / 2 - 4 : o.align === 'right' ? sx - w - 4 : sx - 4;
        ctx.fillStyle = o.bg; ctx.beginPath(); ctx.roundRect(x0, sy - h / 2, w + 8, h, 4); ctx.fill();
        if (o.border) { ctx.strokeStyle = o.border; ctx.lineWidth = 1; ctx.stroke(); }
      }
      ctx.fillStyle = o.color || '#111'; ctx.fillText(s, sx, sy);
    };
    g.text = (x, z, s, o = {}) => g.textPx(X(x) + (o.dx || 0), Y(z) + (o.dy || 0), s, o);
    // callout: leader line from a world point to a text box offset in px
    g.callout = (x, z, s, dx, dy, color = '#e8edf5') => {
      const sx = X(x), sy = Y(z);
      ctx.strokeStyle = 'rgba(20,24,32,.75)'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(sx + dx, sy + dy); ctx.stroke();
      ctx.fillStyle = 'rgba(20,24,32,.85)'; ctx.beginPath(); ctx.arc(sx, sy, 2.2, 0, 7); ctx.fill();
      g.textPx(sx + dx + (dx < 0 ? -2 : 2), sy + dy, s, { align: dx < 0 ? 'right' : 'left', bg: 'rgba(20,24,32,.82)', color, size: 11 });
    };
    // force arrow: world anchor, world unit direction, length in px. push=true puts the head on the anchor.
    g.arrow = (x, z, ux, uz, len, color, label, push) => {
      const sx = X(x), sy = Y(z), dx = ux, dy = -uz;
      let x0, y0, x1, y1;
      if (push) { x1 = sx; y1 = sy; x0 = sx - dx * len; y0 = sy - dy * len; } else { x0 = sx; y0 = sy; x1 = sx + dx * len; y1 = sy + dy * len; }
      ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 3.2; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1 - dx * 9, y1 - dy * 9); ctx.stroke();
      const h = 12, w = 6.5;
      ctx.beginPath(); ctx.moveTo(x1, y1);
      ctx.lineTo(x1 - dx * h - dy * w, y1 - dy * h + dx * w); ctx.lineTo(x1 - dx * h + dy * w, y1 - dy * h - dx * w);
      ctx.closePath(); ctx.fill();
      if (label) {
        const lx = push ? x0 : x1, ly = push ? y0 : y1;
        const ax = push ? -dx : dx, ay = push ? -dy : dy;
        g.textPx(lx + ax * 8, ly + ay * 10, label, { align: ax < -0.3 ? 'right' : ax > 0.3 ? 'left' : 'center', bg: 'rgba(15,18,24,.85)', color, size: 11, bold: true });
      }
    };
    g.forceLen = lbf => clamp(Math.abs(lbf) * 0.32, 22, 210);
    return g;
  }

  // ---------------- scene ----------------
  function drawEnvironment(g, st) {
    const v = g.view, sc = g.sc;
    const xMin = v.cx - (v.ox - v.x) / sc - 100, xMax = v.cx + (v.x + v.w - v.ox) / sc + 100;
    // earth and decks
    g.rect(-9000, -9000, POOL_L + 9000, Z_DECK, '#5d554b');
    g.rect(-9000, Z_DECK - 160, WALL_NEAR, Z_DECK, '#cbc5b8');
    g.rect(POOL_L, Z_DECK - 160, POOL_L + 9000, Z_DECK, '#cbc5b8');
    // pool shell
    g.rect(WALL_NEAR, Z_WATER, POOL_L, Z_DECK, '#bcd9ea');
    const grd = g.ctx.createLinearGradient(0, g.Y(Z_WATER), 0, g.Y(Z_FLOOR));
    grd.addColorStop(0, '#2a8fc8'); grd.addColorStop(1, '#0d4f7a');
    g.rect(WALL_NEAR, Z_FLOOR, POOL_L, Z_WATER, grd);
    g.rect(WALL_NEAR - 200, Z_FLOOR - 200, POOL_L + 200, Z_FLOOR, '#e9f1f5');
    g.rect(WALL_NEAR - 200, Z_FLOOR, WALL_NEAR, Z_DECK - 160, '#e9f1f5');
    g.rect(POOL_L, Z_FLOOR, POOL_L + 200, Z_DECK - 160, '#e9f1f5');
    // coping
    g.rect(WALL_NEAR - 250, Z_DECK - 20, WALL_NEAR + 30, Z_DECK + 30, '#f1ede4', '#a59f92', 1);
    g.rect(POOL_L - 30, Z_DECK - 20, POOL_L + 250, Z_DECK + 30, '#f1ede4', '#a59f92', 1);
    // distance ticks on the floor (every 1 m, labelled every 5 m from the near wall)
    if (sc * 1000 > 6) {
      for (let m = 0; m <= 22; m++) {
        const x = WALL_NEAR + m * 1000;
        if (x < xMin || x > xMax) continue;
        const big = m % 5 === 0;
        g.line(x, Z_FLOOR, x, Z_FLOOR + (big ? 220 : 110), 'rgba(10,30,50,.55)', big ? 2 : 1);
        if (big && sc * 1000 > 14) g.text(x, Z_FLOOR + 300, m + ' m', { color: '#d6ecf8', size: 11, align: 'center' });
      }
    }
    // water surface line with small waves
    const step = Math.max(80, 6 / sc), pts = [];
    for (let x = Math.max(WALL_NEAR, xMin); x <= Math.min(POOL_L, xMax) + step; x += step) {
      const xx = Math.min(x, POOL_L);
      pts.push([xx, Z_WATER + 6 * Math.sin(xx / 260 + st.t * 2.2) + 3 * Math.sin(xx / 97 - st.t * 3.1)]);
    }
    if (pts.length > 1) g.polyline(pts, 'rgba(230,248,255,.85)', g.W(5, 1.2));
  }

  function drawBlock(g) {
    // starting block: pedestal + 520 mm deep platform
    g.poly([[-470, Z_DECK], [-170, Z_DECK], [-205, -40], [-430, -40]], '#8f99a4', '#6c757f', 1);
    g.rect(-500, Z_DECK, -140, Z_DECK + 25, '#76808b');
    g.rect(-520, -40, 0, 0, '#eef0f3', '#9aa1aa', 1);
    g.rect(-500, -6, -20, 0, '#4e5560');
    g.text(-260, -22, 'starting block', { color: '#6a727c', size: Math.max(9, Math.min(13, g.sc * 16)), align: 'center' });
  }

  function tarpGeom(st) {
    const C = { x: POOL_L + 40, z: Z_DECK + 32 };
    const Wp = { x: Math.max(st.x + 1, POOL_L - 250), z: EDGE_Z };
    let r = REEL.core + 60;
    let RB, Lout = 0;
    for (let i = 0; i < 3; i++) {
      RB = { x: REEL.x - r * 0.45, z: REEL.z - r * 0.89 };
      Lout = hyp(RB.x - C.x, RB.z - C.z) + hyp(C.x - Wp.x, C.z - Wp.z) + Math.max(0, Wp.x - st.x);
      r = Math.sqrt(REEL.core * REEL.core + Math.max(0, TARP_TOTAL - Lout) * REEL.t / Math.PI);
    }
    return { C, Wp, RB, r, Lout };
  }

  function drawTarp(g, st) {
    const tg = tarpGeom(st);
    // reel stand
    g.poly([[REEL.x - 260, Z_DECK], [REEL.x - 30, REEL.z], [REEL.x + 30, REEL.z], [REEL.x + 260, Z_DECK]], null, '#8a9099', g.W(30, 2));
    const pts = [[st.x, EDGE_Z], [tg.Wp.x, tg.Wp.z], [tg.C.x, tg.C.z], [tg.RB.x, tg.RB.z]];
    g.polyline(pts, '#2f6fd6', g.W(24, 3));
    // stripes anchored at the edge so they travel with the fabric
    const dpx = Math.max(500 * g.sc, 5), gpx = Math.max(1100 * g.sc, 9);
    g.polyline(pts, '#8fb8ff', g.W(14, 1.5), [dpx, gpx], 0);
    // roll on the reel
    g.circle(REEL.x, REEL.z, tg.r, '#2f6fd6', '#1d4a96', g.W(4, 1));
    const reelAng = -tg.Lout / 140;
    g.spokes(REEL.x, REEL.z, REEL.core * 0.3, tg.r * 0.95, 3, reelAng, '#8fb8ff', g.W(8, 1));
    g.circle(REEL.x, REEL.z, REEL.core * 0.35, '#c9ced6', '#555', 1);
    // leading-edge bar
    g.circle(st.x, EDGE_Z, 25, '#3a3f47', '#111', 1);
    if (g.view.main && g.sc < 1) {
      const togo = (st.x - X_STOP) / 1000;
      g.text(st.x, EDGE_Z, 'tarp edge  ' + (togo > 0.01 ? togo.toFixed(1) + ' m to go' : 'in place'),
        { dy: -26, align: 'center', color: '#fff', bg: 'rgba(20,40,90,.85)', size: 12, bold: true });
    }
  }

  function drawRope(g, st) {
    const cfg = A.cfg, gm = st.geom, d = cfg.drum, ctx = g.ctx;
    const ropeW = g.W(d.ropeD, 1.6);
    // rope on the drum
    if (d.kind === 'spool') {
      g.ring(d.x, d.z, d.coreR, st.drum.outer, '#f08a1c');
      for (let k = 1; k < st.drum.layer; k++) g.circle(d.x, d.z, d.coreR + d.ropeD * k, null, 'rgba(120,60,0,.55)', 1);
      g.spokes(d.x, d.z, d.coreR + 1, st.drum.outer - 0.5, 10, st.dAng, 'rgba(110,55,0,.8)', g.W(2, 1));
    } else {
      g.ring(d.x, d.z, d.coreR, d.coreR + d.ropeD, '#f08a1c');
      g.spokes(d.x, d.z, d.coreR + 0.5, d.coreR + d.ropeD - 0.5, 14, st.dAng, 'rgba(110,55,0,.85)', g.W(1.5, 1));
    }
    // main rope: drum -> sheave -> tarp edge. Dashes are anchored at the rope's tarp end, so they move with the rope.
    const dash = Math.max(30 * g.sc, 5);
    g.polyline(gm.pts, '#f5a524', ropeW);
    g.polyline(gm.pts, '#b75f00', ropeW, [dash, dash], 0);
    // tail (capstan versions): leaves the drum toward the operator's hand
    if (st.tail) {
      g.polyline(st.tail.pts, '#f5a524', ropeW);
      g.polyline(st.tail.pts, '#b75f00', ropeW, [dash, dash], -st.s * g.sc);
      const p = cfg.tail.pile, n = Math.min(9, 1 + Math.floor(st.s / 2500));
      for (let i = 0; i < n; i++) g.circle(p.x - 30 + (i % 3) * 30, p.z + 12 + Math.floor(i / 3) * 14, 26, null, '#d9861c', g.W(5, 1.2));
    }
    // rope end shackle at the tarp
    g.circle(gm.E.x, gm.E.z, 9, '#d0d4da', '#555', 1);
    // stopper ball
    if (st.ball && st.ball.onPath) {
      g.circle(st.ball.x, st.ball.z, 15, '#e63946', '#7a1018', g.W(2, 1));
      if (g.view.main && g.sc > 0.2) g.text(st.ball.x, st.ball.z, 'stopper ball', { dy: 24, align: 'center', color: '#ffd7da', size: 11, bg: 'rgba(60,10,15,.75)' });
    }
    ctx.lineCap = 'butt';
  }

  function drawCommonForces(g, st) {
    const gm = st.geom, T = st.T;
    // tension in the rope near the tarp
    const mid = { x: lerp(gm.tp.x, gm.E.x, Math.min(0.5, 600 / Math.max(600, gm.E.x - gm.tp.x))), z: 0 };
    mid.z = lerp(gm.tp.z, gm.E.z, (mid.x - gm.tp.x) / ((gm.E.x - gm.tp.x) || 1));
    g.arrow(mid.x, mid.z, gm.toTarp.x, gm.toTarp.z, g.forceLen(T), '#ffcf3f', 'rope ' + fmt(T) + ' lbf');
    // resultant on the redirect pulley
    const R = { x: T * (gm.toTarp.x + gm.toDrum.x), z: T * (gm.toTarp.z + gm.toDrum.z) };
    const Rm = hyp(R.x, R.z), u = unit(R.x, R.z);
    if (gm.contact !== 'none') {
      const name = gm.contact === 'keeper' ? 'rope riding on keeper bar' : A.cfg.sheaveName + ' load';
      g.arrow(gm.S.x, gm.S.z, u.x, u.z, g.forceLen(Rm), '#c58cff', name + ' ' + fmt(Rm) + ' lbf');
    }
    return { R, Rm };
  }

  function drawScene(view, st) {
    const ctx = A.ctx;
    ctx.save();
    ctx.beginPath(); ctx.rect(view.x, view.y, view.w, view.h); ctx.clip();
    const sky = ctx.createLinearGradient(0, view.y, 0, view.y + view.h);
    sky.addColorStop(0, '#9fcbe8'); sky.addColorStop(1, '#e4f1f8');
    ctx.fillStyle = sky; ctx.fillRect(view.x, view.y, view.w, view.h);
    const g = makeG(ctx, view);
    drawEnvironment(g, st);
    drawBlock(g);
    drawTarp(g, st);
    A.cfg.drawBack(g, st);
    drawRope(g, st);
    A.cfg.drawFront(g, st);
    if (A.forces && g.sc > 0.12) {
      const f = drawCommonForces(g, st);
      A.cfg.drawForces(g, st, f);
    }
    if (A.labels && view.main && g.sc > 0.6) {
      for (const L of A.cfg.labels(st)) g.callout(L[0], L[1], L[2], L[3], L[4]);
    }
    ctx.restore();
    return g;
  }

  function niceLen(px, sc) {
    const opts = [5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000];
    for (const o of opts) if (o * sc >= px) return o;
    return 10000;
  }

  function drawOverlays(mainView, st) {
    const ctx = A.ctx, W = A.W, H = A.H;
    // inset close-up of the winch (only when the main view is zoomed out)
    const c = A.cfg.cam;
    const iw = Math.min(400, W * 0.32), ih = Math.min(260, (H - TOP_H - TB_H) * 0.42);
    const insetScale = Math.min(iw / c.w, ih / (c.w * 0.62));
    const showInset = A.inset && mainView.scale < insetScale * 0.45;
    if (showInset) {
      const v = { x: 12, y: H - TB_H - 12 - ih, w: iw, h: ih, scale: insetScale, cx: c.cx, cz: c.cz, main: false };
      v.ox = v.x + v.w / 2; v.oy = v.y + v.h / 2;
      drawScene(v, st);
      ctx.strokeStyle = '#e6e9ef'; ctx.lineWidth = 2; ctx.strokeRect(v.x, v.y, v.w, v.h);
      ctx.fillStyle = 'rgba(14,17,22,.8)'; ctx.fillRect(v.x, v.y, 150, 20);
      ctx.fillStyle = '#e6e9ef'; ctx.font = '600 12px system-ui, Segoe UI, Arial'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
      ctx.fillText('Winch close-up (live)', v.x + 6, v.y + 10);
    }
    // scale bar
    const L = niceLen(90, mainView.scale), px = L * mainView.scale;
    const bx = showInset ? iw + 32 : 16, by = H - TB_H - 18;
    ctx.fillStyle = 'rgba(14,17,22,.75)'; ctx.fillRect(bx - 6, by - 18, px + 70, 26);
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(bx, by - 4); ctx.lineTo(bx, by); ctx.lineTo(bx + px, by); ctx.lineTo(bx + px, by - 4); ctx.stroke();
    ctx.fillStyle = '#fff'; ctx.font = '12px system-ui, Segoe UI, Arial'; ctx.textAlign = 'left';
    ctx.fillText(L >= 1000 ? L / 1000 + ' m' : L + ' mm', bx + px + 8, by - 3);
    // minimap strip
    const mm = minimapRect();
    const wx0 = -2500, wx1 = POOL_L + 3000, mx = x => mm.x + (x - wx0) / (wx1 - wx0) * mm.w;
    ctx.fillStyle = 'rgba(14,17,22,.82)'; ctx.fillRect(mm.x - 4, mm.y - 4, mm.w + 8, mm.h + 8);
    ctx.fillStyle = '#cbc5b8'; ctx.fillRect(mx(wx0), mm.y + mm.h - 5, mm.w, 5);
    ctx.fillStyle = '#2a8fc8'; ctx.fillRect(mx(WALL_NEAR), mm.y + 6, mx(POOL_L) - mx(WALL_NEAR), mm.h - 6);
    ctx.fillStyle = '#2f6fd6'; ctx.fillRect(mx(st.x), mm.y + 6, mx(POOL_L) - mx(st.x), 5);
    ctx.fillStyle = '#f5a524'; ctx.fillRect(mx(0), mm.y + 7, mx(st.x) - mx(0), 2);
    ctx.fillStyle = '#eef0f3'; ctx.fillRect(mx(-520), mm.y + 2, mx(0) - mx(-520) + 1, 5);
    ctx.fillStyle = '#ffcf3f'; ctx.fillRect(mx(st.x) - 1.5, mm.y, 3, mm.h);
    const vx0 = mainView.cx - (mainView.ox - mainView.x) / mainView.scale, vx1 = mainView.cx + (mainView.x + mainView.w - mainView.ox) / mainView.scale;
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5;
    ctx.strokeRect(clamp(mx(vx0), mm.x, mm.x + mm.w), mm.y - 2, Math.max(3, clamp(mx(vx1), mm.x, mm.x + mm.w) - clamp(mx(vx0), mm.x, mm.x + mm.w)), mm.h + 4);
    ctx.fillStyle = '#9aa4b2'; ctx.font = '11px system-ui, Segoe UI, Arial'; ctx.textAlign = 'right';
    ctx.fillText('pool map (click to jump)', mm.x + mm.w, mm.y + mm.h + 13);
  }
  function minimapRect() {
    return { x: 16, y: TOP_H + 10, w: Math.max(200, A.W - PANEL_W - 40), h: 18 };
  }

  // ---------------- HUD ----------------
  function bar(frac, color) {
    return '<div class="bar"><i style="width:' + clamp(frac * 100, 0, 100).toFixed(1) + '%;background:' + color + '"></i></div>';
  }
  function row(k, v, cls) { return '<div class="row"><span>' + k + '</span><span' + (cls ? ' class="' + cls + '"' : '') + '>' + v + '</span></div>'; }
  function updatePanel(st) {
    const c = A.cfg, d = c.drive, sim = A.sim;
    const travel = X0 - X_STOP, pulled = clamp(X0 - st.x, 0, travel);
    const pct = pulled / travel;
    const mMin = st.v / 1000 * 60;
    const tf = st.T / c.ratingLbf;
    const tCol = tf < 0.6 ? '#4cc26b' : tf < 0.9 ? '#f0b13b' : '#ff5b5b';
    let h = '';
    const statusTxt = c.phaseText[st.phase] || '';
    const sCls = st.phase === 3 ? 'good' : st.phase === 2 || st.phase === 4 ? 'bad' : '';
    h += '<div class="status ' + sCls + '">' + statusTxt + '</div>';
    h += '<h3>Tarp</h3>';
    h += row('Pulled', fmt(pulled / 1000, 2) + ' / ' + fmt(travel / 1000, 1) + ' m');
    h += bar(pct, '#2f6fd6');
    h += row('Edge to block', fmt(st.x / 1000, 2) + ' m');
    h += row('Rope speed', fmt(mMin * 3.28084, 1) + ' ft/min  (' + fmt(mMin, 2) + ' m/min)');
    h += row('Rope angle at ' + c.sheaveName, fmt(st.ropeAngDeg, 1) + '° below level');
    h += row('Rope bears on', st.geom.contact === 'sheave' ? c.sheaveName : st.geom.contact === 'keeper' ? 'keeper bar (lifted off ' + c.sheaveName + ')' : 'nothing (free span)',
      st.geom.contact === 'sheave' ? '' : 'warn');
    h += '<h3>Rope load</h3>';
    h += row('Rope tension', fmt(st.T) + ' lbf', tf > 1 ? 'bad' : tf > 0.9 ? 'warn' : '');
    h += bar(tf, tCol);
    h += row('Rating (' + c.ratingWhat + ')', c.ratingLbf + ' lbf');
    h += row('Horizontal drag on tarp', fmt(st.Th) + ' lbf');
    h += '<h3>Drum & gears</h3>';
    h += row('Drum speed', fmt(st.rpmIn / c.ratio, 1) + ' rpm');
    if (c.drum.kind === 'spool') {
      h += row('Rope on drum', fmt(st.drum.wound / 1000, 2) + ' m, layer ' + st.drum.layer);
      h += row('Working radius', fmt(st.drum.r, 0) + ' mm');
    } else {
      h += row('Capstan wraps', c.drum.wraps + ' (rope not stored)');
      h += row('Working radius', fmt(st.drum.r, 1) + ' mm');
    }
    h += row('Drum torque', fmt(st.T * LBF * st.drum.r / 1000, 1) + ' N·m');
    h += row('Gear ratio', c.ratio + ':1');
    h += '<h3>' + c.driveName + '</h3>';
    if (d.kind === 'crank') {
      h += row('Crank speed', fmt(st.rpmIn, 0) + ' rpm');
      h += row('Crank torque', fmt(st.tauIn, 1) + ' N·m');
      h += row('Hand force (' + d.armR + ' mm arm)', st.running ? fmt(st.F / LBF, 1) + ' lbf' : '0 (holding)');
    } else if (d.kind === 'motor') {
      h += row('Pendant', st.running ? 'IN held' : st.phase === 0 ? 'idle' : 'released');
      h += row('Output speed', fmt(st.rpmIn, 1) + ' rpm');
      h += row('Output torque', fmt(st.running ? st.tauIn : 0, 1) + ' N·m');
      h += row('Motor current', fmt(st.I, 1) + ' A', st.I > d.tripA * 0.85 ? 'warn' : '');
      h += bar(st.I / d.tripA, st.I > d.tripA * 0.85 ? '#f0b13b' : '#4cc26b');
      h += row('Trip setting', d.tripA + ' A');
      h += row('Power', fmt(st.I * d.volts, 0) + ' W @ ' + d.volts + ' V');
      h += row('Energy used', fmt(st.energy / 3600, 1) + ' Wh');
    } else if (d.kind === 'drill') {
      h += row('Trigger', st.running ? 'held' : st.phase === 0 ? 'ready' : 'released');
      h += row('Drill speed', fmt(st.rpmIn, 0) + ' rpm');
      h += row('Torque at chuck', fmt(st.tauIn, 1) + ' N·m');
      h += bar(st.tauIn / d.clutchNm, st.tauIn > d.clutchNm * 0.85 ? '#f0b13b' : '#4cc26b');
      h += row('Clutch slips at', d.clutchNm + ' N·m');
      h += row('Energy used', fmt(st.energy / 3600, 1) + ' Wh');
    }
    const extra = c.readouts(st);
    if (extra.length) {
      h += '<h3>Mount loads</h3>';
      for (const r of extra) h += row(r[0], r[1], r[2]);
    }
    h += '<div class="note">Full pull: ' + fmtTime(sim.tDone - START_DELAY) + ' (sim). ' + c.footnote + '</div>';
    A.el.panel.innerHTML = h;
  }

  // ---------------- camera ----------------
  function mainView() {
    const W = A.W, H = A.H;
    const v = { x: 0, y: TOP_H, w: W, h: H - TOP_H - TB_H, scale: A.cam.scale, cx: A.cam.cx, cz: A.cam.cz, main: true };
    v.ox = (W - PANEL_W) / 2; v.oy = TOP_H + (H - TOP_H - TB_H) / 2 + 12;
    return v;
  }
  function setCam(which) {
    const vw = A.W - PANEL_W - 20, vh = A.H - TOP_H - TB_H - 40;
    A.follow = false;
    if (which === 'winch') {
      const c = A.cfg.cam;
      A.cam.scale = Math.min(vw / c.w, vh / (c.w * 0.62)); A.cam.cx = c.cx; A.cam.cz = c.cz;
    } else if (which === 'pool') {
      A.cam.scale = vw / (POOL_L + 3500); A.cam.cx = POOL_L / 2 + 300; A.cam.cz = -900;
    } else if (which === 'block') {
      A.cam.scale = Math.min(vw / 2600, vh / 1700); A.cam.cx = 450; A.cam.cz = -400;
    } else if (which === 'edge') {
      const st = stateAt(A.t);
      A.cam.scale = Math.min(vw / 3200, vh / 2000); A.cam.cx = st.x; A.cam.cz = Z_WATER + 300;
    } else if (which === 'follow') {
      setCam('edge'); A.follow = true;
    }
    syncButtons();
  }
  function zoomAt(sx, sy, factor) {
    const v = mainView();
    const wx = v.cx + (sx - v.ox) / v.scale, wz = v.cz - (sy - v.oy) / v.scale;
    const ns = clamp(A.cam.scale * factor, 0.004, 25);
    A.cam.scale = ns;
    A.cam.cx = wx - (sx - v.ox) / ns;
    A.cam.cz = wz + (sy - v.oy) / ns;
  }

  // ---------------- DOM ----------------
  function el(tag, attrs, html) {
    const e = document.createElement(tag);
    for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (html != null) e.innerHTML = html;
    return e;
  }
  function buildDom() {
    const c = A.cfg;
    document.title = c.title + ' — Tarp Winch Sim';
    const canvas = el('canvas', { id: 'view' });
    document.body.appendChild(canvas);
    A.canvas = canvas; A.ctx = canvas.getContext('2d');

    const top = el('div', { id: 'topbar' });
    top.innerHTML =
      '<div class="titles"><h1>' + c.title + '</h1><div class="sub">' + c.subtitle + '</div></div>' +
      '<div class="btns">' +
      '<button data-cam="winch" title="1">Winch</button>' +
      '<button data-cam="block" title="2">Block + water</button>' +
      '<button data-cam="pool" title="3">Whole pool</button>' +
      '<button data-cam="edge" title="4">Tarp edge</button>' +
      '<button data-tg="follow" title="F">Follow tarp</button>' +
      '<button data-tg="forces" title="G">Forces</button>' +
      '<button data-tg="labels" title="L">Labels</button>' +
      '<button data-tg="inset" title="I">Inset</button>' +
      '<button data-tg="help" title="H">?</button></div>';
    document.body.appendChild(top);

    const panel = el('div', { id: 'panel' });
    document.body.appendChild(panel);

    const tb = el('div', { id: 'timebar' });
    tb.innerHTML =
      '<button id="bStart" title="Home">⏮</button>' +
      '<button id="bBack" title="←">◀ 5s</button>' +
      '<button id="bPlay" title="Space" style="min-width:64px">Pause</button>' +
      '<button id="bFwd" title="→">5s ▶</button>' +
      '<button id="bEnd" title="End">⏭</button>' +
      '<input id="slider" type="range" min="0" max="1000" step="0.01" value="0">' +
      '<span id="clock"></span>' +
      '<label>Speed <select id="speed">' + SPEEDS.map((s, i) => '<option value="' + i + '">×' + s + '</option>').join('') + '</select></label>' +
      '<label title="R"><input id="rev" type="checkbox"> Reverse</label>';
    document.body.appendChild(tb);

    const help = el('div', { id: 'help', hidden: '' });
    help.innerHTML = '<h2>Controls</h2><table>' +
      '<tr><td>Drag</td><td>pan the view</td></tr>' +
      '<tr><td>Mouse wheel</td><td>zoom at the cursor</td></tr>' +
      '<tr><td>Pool map strip</td><td>click to jump along the pool</td></tr>' +
      '<tr><td>Space</td><td>play / pause</td></tr>' +
      '<tr><td>← / →</td><td>step 5 s of sim time (Shift: 0.5 s)</td></tr>' +
      '<tr><td>Home / End</td><td>jump to start / end</td></tr>' +
      '<tr><td>+ / −</td><td>faster / slower</td></tr>' +
      '<tr><td>R</td><td>run time in reverse</td></tr>' +
      '<tr><td>1 2 3 4</td><td>winch / block + water / whole pool / tarp edge</td></tr>' +
      '<tr><td>F G L I</td><td>follow tarp, forces, labels, inset</td></tr>' +
      '</table><p style="color:#9aa4b2">Side elevation, cutaway: the near drum flange and the big gear are drawn see-through so the rope and teeth stay visible. ' +
      'The orange rope has dark marks that travel with it; the pulley and drum have spokes so you can see them turn.</p>' +
      '<p style="text-align:right;margin:0"><button id="bHelpClose">Close</button></p>';
    document.body.appendChild(help);

    A.el = {
      panel, slider: tb.querySelector('#slider'), clock: tb.querySelector('#clock'), play: tb.querySelector('#bPlay'),
      speed: tb.querySelector('#speed'), rev: tb.querySelector('#rev'), help, top,
    };
    A.el.slider.max = A.sim.duration;
    A.el.speed.value = A.speedIdx;

    top.addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      if (b.dataset.cam) setCam(b.dataset.cam);
      if (b.dataset.tg) toggle(b.dataset.tg);
    });
    tb.querySelector('#bStart').onclick = () => seek(0);
    tb.querySelector('#bEnd').onclick = () => seek(A.sim.duration);
    tb.querySelector('#bBack').onclick = () => seek(A.t - 5);
    tb.querySelector('#bFwd').onclick = () => seek(A.t + 5);
    A.el.play.onclick = () => setPlaying(!A.playing);
    A.el.slider.oninput = () => { A.t = +A.el.slider.value; };
    A.el.speed.onchange = () => { A.speedIdx = +A.el.speed.value; };
    A.el.rev.onchange = () => { A.reverse = A.el.rev.checked; if (A.reverse && A.t <= 0) A.reverse = false; };
    help.querySelector('#bHelpClose').onclick = () => toggle('help');

    canvas.addEventListener('pointerdown', e => {
      const mm = minimapRect();
      if (e.clientY >= mm.y - 4 && e.clientY <= mm.y + mm.h + 4 && e.clientX >= mm.x && e.clientX <= mm.x + mm.w) {
        const wx0 = -2500, wx1 = POOL_L + 3000;
        A.cam.cx = wx0 + (e.clientX - mm.x) / mm.w * (wx1 - wx0);
        A.follow = false; syncButtons();
        return;
      }
      A.drag = { x: e.clientX, y: e.clientY };
      canvas.setPointerCapture(e.pointerId); canvas.classList.add('dragging');
    });
    canvas.addEventListener('pointermove', e => {
      if (!A.drag) return;
      A.cam.cx -= (e.clientX - A.drag.x) / A.cam.scale;
      A.cam.cz += (e.clientY - A.drag.y) / A.cam.scale;
      A.drag = { x: e.clientX, y: e.clientY };
      if (A.follow) { A.follow = false; syncButtons(); }
    });
    const endDrag = () => { A.drag = null; canvas.classList.remove('dragging'); };
    canvas.addEventListener('pointerup', endDrag);
    canvas.addEventListener('pointercancel', endDrag);
    canvas.addEventListener('wheel', e => { e.preventDefault(); zoomAt(e.clientX, e.clientY, Math.exp(-e.deltaY * 0.0015)); }, { passive: false });
    canvas.addEventListener('dblclick', e => zoomAt(e.clientX, e.clientY, 2));

    window.addEventListener('keydown', e => {
      if (e.target.tagName === 'SELECT' || e.target.tagName === 'INPUT' && e.target.type !== 'range' && e.target.type !== 'checkbox') return;
      const k = e.key;
      if (k === ' ') { setPlaying(!A.playing); e.preventDefault(); }
      else if (k === 'ArrowRight') { seek(A.t + (e.shiftKey ? 0.5 : 5)); e.preventDefault(); }
      else if (k === 'ArrowLeft') { seek(A.t - (e.shiftKey ? 0.5 : 5)); e.preventDefault(); }
      else if (k === 'Home') seek(0);
      else if (k === 'End') seek(A.sim.duration);
      else if (k === '+' || k === '=') { A.speedIdx = Math.min(SPEEDS.length - 1, A.speedIdx + 1); A.el.speed.value = A.speedIdx; }
      else if (k === '-' || k === '_') { A.speedIdx = Math.max(0, A.speedIdx - 1); A.el.speed.value = A.speedIdx; }
      else if (k === 'r' || k === 'R') { A.reverse = !A.reverse; A.el.rev.checked = A.reverse; if (A.reverse) setPlaying(true); }
      else if (k === '1') setCam('winch');
      else if (k === '2') setCam('block');
      else if (k === '3') setCam('pool');
      else if (k === '4') setCam('edge');
      else if (k === 'f' || k === 'F') toggle('follow');
      else if (k === 'g' || k === 'G') toggle('forces');
      else if (k === 'l' || k === 'L') toggle('labels');
      else if (k === 'i' || k === 'I') toggle('inset');
      else if (k === 'h' || k === 'H' || k === '?') toggle('help');
      else if (k === 'Escape') { A.el.help.hidden = true; syncButtons(); }
    });
    window.addEventListener('resize', resize);
  }
  function toggle(name) {
    if (name === 'follow') { if (A.follow) A.follow = false; else setCam('follow'); }
    else if (name === 'help') A.el.help.hidden = !A.el.help.hidden;
    else A[name] = !A[name];
    syncButtons();
  }
  function syncButtons() {
    if (!A.el.top) return;
    for (const b of A.el.top.querySelectorAll('button[data-tg]')) {
      const n = b.dataset.tg;
      b.classList.toggle('on', n === 'help' ? !A.el.help.hidden : !!A[n]);
    }
  }
  function setPlaying(p) {
    A.playing = p;
    if (p && !A.reverse && A.t >= A.sim.duration - 1e-6) A.t = 0;
    if (p && A.reverse && A.t <= 0) A.t = A.sim.duration;
    A.el.play.textContent = p ? 'Pause' : 'Play';
  }
  function seek(t) { A.t = clamp(t, 0, A.sim.duration); }
  function resize() {
    A.dpr = window.devicePixelRatio || 1;
    A.W = window.innerWidth; A.H = window.innerHeight;
    A.canvas.width = Math.round(A.W * A.dpr); A.canvas.height = Math.round(A.H * A.dpr);
    A.canvas.style.width = A.W + 'px'; A.canvas.style.height = A.H + 'px';
  }

  // ---------------- main loop ----------------
  function frame(now) {
    const dt = Math.min(0.1, (now - (A.last || now)) / 1000);
    A.last = now;
    if (A.playing) {
      A.t += dt * SPEEDS[A.speedIdx] * (A.reverse ? -1 : 1);
      if (A.t >= A.sim.duration) { A.t = A.sim.duration; setPlaying(false); }
      if (A.t <= 0) { A.t = 0; if (A.reverse) { setPlaying(false); } }
    }
    const st = stateAt(A.t);
    if (A.follow) A.cam.cx = st.x - 300;
    const ctx = A.ctx;
    ctx.setTransform(A.dpr, 0, 0, A.dpr, 0, 0);
    ctx.clearRect(0, 0, A.W, A.H);
    const v = mainView();
    drawScene(v, st);
    drawOverlays(v, st);
    A.el.slider.value = A.t;
    A.el.clock.textContent = fmtTime(A.t) + ' / ' + fmtTime(A.sim.duration) + '  ×' + SPEEDS[A.speedIdx] + (A.reverse ? ' ◀' : '');
    if (!A._pt || now - A._pt > 66) { updatePanel(st); A._pt = now; }
    requestAnimationFrame(frame);
  }

  function start(cfg) {
    cfg.sheaveName = cfg.sheaveName || 'pulley';
    cfg.footnote = cfg.footnote || '';
    A.cfg = cfg;
    A.sim = simulate(cfg);
    buildDom();
    resize();
    // optional URL params, e.g. ?t=120&cam=pool&paused=1&speed=1
    const q = new URLSearchParams(location.search);
    if (q.has('t')) A.t = clamp(+q.get('t') || 0, 0, A.sim.duration);
    setCam(q.get('cam') || 'winch');
    if (q.has('speed')) { const i = SPEEDS.indexOf(+q.get('speed')); if (i >= 0) { A.speedIdx = i; A.el.speed.value = i; } }
    setPlaying(!q.has('paused'));
    syncButtons();
    requestAnimationFrame(frame);
    window.__winchSim = A;   // handy for debugging from the console
  }

  window.WinchSim = { start, LBF, IN: 25.4, POOL_L, Z_WATER, Z_DECK, X_STOP, ropeZAt, unit, hyp, clamp, fmt };
})();
