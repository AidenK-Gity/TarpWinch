/*
  v4.2 mechanism: the v4 mechanism (../../sim/v4_mechanism.js) with the changes picked from
  the v4 sim analysis (../docs/v4_sim_analysis.md). Must be loaded after v4_mechanism.js.
*/
window.WinchV4_2 = (function () {
  'use strict';
  const IN = WinchSim.IN;
  const V42 = {
    version: 'v4.2',
    title: 'Tarp Winch v4.2 — Stronger Motor, 3:1 Gears, Wider Spool',
    spool: { between: 8 * IN },                       // 3 rope layers instead of 4
    gear: { teeth: 36 },                              // 3:1 instead of 4:1
    motor: { name: '12 V worm motor (55 N·m)', stallNm: 55, stallA: 45, tripA: 30 },
    guard: true,
    subtitleExtra: ' · v4.2: 55 N·m motor, 8 in spool, mesh guard',
    footExtra: 'v4.2 changes come from the v4 sim analysis.',
  };
  function config(style) { return WinchV4.config(style, V42); }
  return { config, V42 };
})();
