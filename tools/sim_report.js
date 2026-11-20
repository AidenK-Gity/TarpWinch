/*
  Headless run of the browser winch sim (sim_common/winch_sim_engine.js) under Node.
  Usage: node tools/sim_report.js <mechanism.js> <GlobalName> <style> [overridesJSON] [mechanism2.js ...]
  Prints a JSON summary: pull time, peak tension, peak current/torque, speeds, slot loads, etc.
*/
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const root = path.join(__dirname, '..');
const [mechFile, globalName, style, ovJson, ...extra] = process.argv.slice(2);
const ctx = { window: {}, console, Math, JSON, URLSearchParams };
ctx.window = ctx; vm.createContext(ctx);
let eng = fs.readFileSync(path.join(root, 'sim_common/winch_sim_engine.js'), 'utf8');
// expose internals for reporting (no change to the file on disk)
eng = eng.replace('window.WinchSim = { start,', 'window.__int = { simulate, stateAt, drumState, loadAt, baseGeo, ropeGeom, A }; window.WinchSim = { start,');
vm.runInContext(eng, ctx);
for (const f of [mechFile, ...extra]) vm.runInContext(fs.readFileSync(path.resolve(f), 'utf8'), ctx);
const ov = ovJson ? JSON.parse(ovJson) : undefined;
const cfg = ctx[globalName].config(style, ov);
cfg.sheaveName = cfg.sheaveName || 'pulley'; cfg.footnote = cfg.footnote || '';
const I = ctx.__int; I.A.cfg = cfg;
const sim = I.simulate(cfg); I.A.sim = sim;
const LBF = 4.448222;
let pk = { T: 0, I: 0, tau: 0, Fz: -1e9 }, vmin = 1e9, vmax = 0, contacts = {}, tPk = 0, minLatch = 1e9;
const series = [];
for (let t = 0; t <= sim.duration; t += 1) {
  const st = I.stateAt(t);
  if (st.T > pk.T) { pk.T = st.T; tPk = t; }
  if (st.running) { pk.I = Math.max(pk.I, st.I); pk.tau = Math.max(pk.tau, st.tauIn); vmin = Math.min(vmin, st.v); vmax = Math.max(vmax, st.v); }
  contacts[st.geom.contact] = (contacts[st.geom.contact] || 0) + 1;
  const ro = cfg.readouts(st);
  if (t % 30 === 0 || Math.abs(t - sim.tDone) < 0.6) series.push({ t, pulled_m: +(st.s / 1000).toFixed(2), T: +st.T.toFixed(0), ang: +st.ropeAngDeg.toFixed(1), v_ftmin: +(st.v / 1000 * 60 * 3.28084).toFixed(1), I: +st.I.toFixed(1), tau: +st.tauIn.toFixed(1), layer: st.drum.layer, r: +st.drum.r.toFixed(1), phase: st.phase, readouts: ro.map(r => r[0] + ': ' + r[1]).join(' | ') });
}
const last = sim.out[sim.out.length - 1];
let elec = 0; if (cfg.drive.volts) for (const o of sim.out) elec += o.I * cfg.drive.volts * 0.05 / 3600;   // 50 ms records
console.log(JSON.stringify({
  title: cfg.title, ratio: cfg.ratio, pullTime_s: +(sim.tDone - 1).toFixed(1), endPhase: last.phase, pulled_m: +(sim.geo.sEnd / 1000).toFixed(2),
  peakT_lbf: +pk.T.toFixed(0), peakAt_s: tPk, rating: cfg.ratingLbf, peakI_A: +pk.I.toFixed(1), tripA: cfg.drive.tripA, peakTauIn_Nm: +pk.tau.toFixed(1),
  speed_ftmin: [+(vmin / 1000 * 60 * 3.28084).toFixed(1), +(vmax / 1000 * 60 * 3.28084).toFixed(1)], energy_Wh: +(last.energy / 3600).toFixed(1), batteryEnergy_Wh: +elec.toFixed(1),
  ropeContactSamples: contacts, series,
}, null, 1));
