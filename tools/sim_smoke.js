/*
  Smoke test: draws every frame of a mechanism's sim against a stub canvas, so drawing bugs
  (typos, undefined values, NaN coordinates) show up without opening a browser.
  Usage: node tools/sim_smoke.js <mechanism.js> <GlobalName> <style> [overridesJSON] [extra.js ...]
*/
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const root = path.join(__dirname, '..');
const [mechFile, globalName, style, ovJson, ...extra] = process.argv.slice(2);
const ctx = { console, Math, JSON, URLSearchParams };
ctx.window = ctx; vm.createContext(ctx);
let eng = fs.readFileSync(path.join(root, 'sim_common/winch_sim_engine.js'), 'utf8');
eng = eng.replace('window.WinchSim = { start,', 'window.__int = { simulate, stateAt, makeG, drawCommonForces, drawRope, A }; window.WinchSim = { start,');
vm.runInContext(eng, ctx);
for (const f of [...extra, mechFile]) vm.runInContext(fs.readFileSync(path.resolve(f), 'utf8'), ctx);
const cfg = ctx[globalName].config(style, ovJson ? JSON.parse(ovJson) : undefined);
cfg.sheaveName = cfg.sheaveName || 'pulley'; cfg.footnote = cfg.footnote || '';
const I = ctx.__int; I.A.cfg = cfg; I.A.sim = I.simulate(cfg);
let calls = 0, nan = 0;
const check = (...a) => { calls++; for (const v of a) if (typeof v === 'number' && !isFinite(v)) nan++; };
const stub = new Proxy({}, { get: (t, k) => (k in t ? t[k] : (...a) => { check(...a); return { addColorStop() {}, width: 10 }; }), set: (t, k, v) => { t[k] = v; return true; } });
const view = { x: 0, y: 0, w: 1200, h: 800, ox: 600, oy: 400, cx: -300, cz: 60, scale: 1.2, main: true };
for (let t = 0; t <= I.A.sim.duration; t += 2) {
  const st = I.stateAt(t), g = I.makeG(stub, view);
  cfg.drawBack(g, st); I.drawRope(g, st); cfg.drawFront(g, st);
  const f = I.drawCommonForces(g, st); cfg.drawForces(g, st, f);
  for (const L of cfg.labels(st)) g.callout(L[0], L[1], L[2], L[3], L[4]);
  cfg.readouts(st);
}
console.log(nan ? 'FAIL' : 'OK', cfg.title, '| draw calls', calls, '| non-finite args', nan);
process.exit(nan ? 1 : 0);
