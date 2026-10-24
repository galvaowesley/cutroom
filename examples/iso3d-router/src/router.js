/**
 * Router: routing cutroom requests as a railway turntable. A
 * request is a wagon that arrived on the entry track and waits on the
 * turntable bridge. Six exit tracks, one per tool, each with its
 * gate and buffer stop. The pointer chooses a track and the read-out
 * names where the request goes. With the wagon back on the bridge, the chosen
 * track's gate lowers while the others shut in a wave from it; the bridge
 * turns to it and the wagon rolls to the buffer stop. The slider sets the wave
 * interval, in ms.
 *
 * Pattern: one of many (Riffle). Tweens for choice, distance-based delay,
 * and a pointer test on the tracks' top plane, which never moves.
 */
const {
  Cam, circ, facing, fillet, fit, hull, poly, prism, proj, rad, rings, seg, unproj,
  tdone, tset, tval, tween, disposer, mk, pointer, put, register, solid,
} = HL;

const RD = 34, M = RD + 1.5, TOP = 4.5, TW = 6.5, GH = M + 2.5, GT = 1.3, WL = 11.5, EL = 54, ONB = RD - 4 - WL;
const ENTRY = 135, OPEN = 90, SHUT = 0, IDLE = 38;
const EXITS = [
  { a: 205, L: 68, say: "diagram → Archify" },
  { a: 240, L: 84, say: "math → ManimGX" },
  { a: 275, L: 62, say: "video → HyperFrames" },
  { a: 310, L: 78, say: "iso → Anatomy/Hairline" },
  { a: 345, L: 60, say: "document → Docling" },
  { a: 20,  L: 74, say: "voice → Kokoro" },
];
const PLATE = fillet([[-7, 0], [7, 0], [7, 10], [-7, 10]], [0.8, 0.8, 2.4, 2.4]);

/** The world point at u along a track at angle a, and v across. */
const at = (a, u, v) => { const c = Math.cos(rad(a)), s = Math.sin(rad(a)); return [u * c - v * s, u * s + v * c]; };
/** A ring rotated to angle a and offset d along it, with normals rotated. */
const turn = (ring, a, d = 0) => {
  const c = Math.cos(rad(a)), s = Math.sin(rad(a));
  return ring.map((q) => ({ u: (q.u + d) * c - q.v * s, v: (q.u + d) * s + q.v * c, nu: q.nu * c - q.nv * s, nv: q.nu * s + q.nv * c }));
};
/** Whether the line at angle a points toward the viewer (tip nearer than mouth). */
const near = (a) => Math.cos(rad(a)) + Math.sin(rad(a)) > 0;

function mount({ stage, svg, read }, value) {
  const bag = disposer();
  let stag = value;

  // Framed with the wagon at the end of each track, so no pose leaves the frame.
  const C = Cam(45, 0.5, 1.52), pts = [];
  EXITS.forEach((e) => [-TW, TW].forEach((v) => { const q = at(e.a, M + e.L, v); pts.push([...q, 0], [...q, TOP + 10.8]); }));
  [-TW, TW].forEach((v) => pts.push([...at(ENTRY, M + EL, v), TOP]));
  for (let k = 0; k < 8; k++) pts.push([...at(k * 45, RD, 0), 0]);
  fit(C, pts, 200, 166);
  const P = proj(C), front = facing(C), W = (a, u, v, z) => P(...at(a, u, v), z);
  const rails = (a, u0, u1, z) => [-3.2, 3.2].map((v) => seg(W(a, u0, v, z), W(a, u1, v, z))).join("");

  /** A track: bed, rails, and (for exits) the mouth gate and end buffer stop, painted back to front. */
  function line(g, a, L, exit) {
    const grp = mk("g", {}, g), [r0, i0] = rings(M, -TW, M + L, TW, 3, 1.2), bed = solid(grp);
    put(bed, prism(P, front, turn(r0, a), turn(i0, a), 0, TOP));
    mk("path", { d: rails(a, M + 1.5, M + L - (exit ? 7 : 2), TOP), class: "nf lo" }, grp);
    if (!exit) return { g: grp };
    const [b0, bi] = rings(M + L - 6.5, -5.5, M + L - 1.5, 5.5, 1.6, 0.8), buf = solid(grp), gate = solid(grp);
    put(buf, prism(P, front, turn(b0, a), turn(bi, a), TOP, TOP + 6.5));
    if (near(a)) gate.g.before(buf.g); // coming toward viewer, buffer stop is nearer than gate
    return { g: grp, bed, buf, gate, a: tween(IDLE), drawn: NaN };
  }

  /** An exit gate, tilted al degrees from vertical: silhouette for both faces, nearer face as crease. */
  function drawGate(ln, a, al) {
    const s = Math.sin(rad(al)), c = Math.cos(rad(al)), d = Math.cos(rad(a)) + Math.sin(rad(a));
    const pt = (v, t, k) => W(a, GH + t * s - k * c, v, TOP + t * c + k * s);
    const face = PLATE.map(([v, t]) => pt(v, t, 0)), back = PLATE.map(([v, t]) => pt(v, t, GT));
    const backNear = -c * d * 0.612 + s * 0.5 > 0;
    put(ln.gate, { sil: poly(hull(face.concat(back))), crease: poly(backNear ? back : face) });
  }

  const g = mk("g", {}, svg);
  const order = [{ a: ENTRY, L: EL, exit: false }, ...EXITS.map((e, i) => ({ ...e, i, exit: true }))];
  const key = (o) => Math.cos(rad(o.a)) + Math.sin(rad(o.a)) - (o.exit ? 0 : 0.01);
  const lines = [];
  let deckDone = false, bridgeG = null;
  /** The turntable: circular pit with ring rail, and the rotating bridge group. */
  function deck() {
    const [dr, di] = [circ(RD, 48), circ(RD - 2, 48)];
    put(solid(g), prism(P, front, dr, di, 0, 2.5));
    mk("path", { d: poly(circ(RD - 7, 48).map((q) => P(q.u, q.v, 2.5))), class: "nf lo" }, g);
    bridgeG = mk("g", {}, g);
    deckDone = true;
  }
  for (const o of order.slice().sort((p, q) => key(p) - key(q))) {
    if (!deckDone && key(o) > 0) deck();
    const ln = line(g, o.a, o.L, o.exit);
    if (o.exit) lines[o.i] = ln;
  }
  if (!deckDone) deck();

  const bridge = solid(bridgeG), brails = mk("path", { class: "nf lo" }, bridgeG);
  const [br0, bri] = rings(-(RD - 2.5), -TW, RD - 2.5, TW, 2.5, 1);
  const wagon = mk("g", {}, g);
  const under = solid(wagon), body = solid(wagon), roof = solid(wagon);
  const parts = [
    [under, rings(-8, -3.5, 8, 3.5, 1.5, 0.7), TOP, TOP + 2],
    [body, rings(-WL, -5.5, WL, 5.5, 2.5, 1.2), TOP + 1.6, TOP + 9.5],
    [roof, rings(-WL - 1, -6.4, WL + 1, 6.4, 3, 1), TOP + 9.5, TOP + 10.8],
  ];
  bridgeG.after(wagon);
  let placed = bridgeG;

  function drawTurn(th, r) {
    put(bridge, prism(P, front, turn(br0, th), turn(bri, th), 2.5, TOP));
    brails.setAttribute("d", rails(th, -(RD - 4), RD - 4, TOP));
    for (const [el, [ring, inner], z0, z1] of parts) put(el, prism(P, front, turn(ring, th, r), turn(inner, th, r), z0, z1));
    const ln = lines[cur], out = cur >= 0 && (near(EXITS[cur].a) ? Math.abs(r) > 0.5 : Math.abs(r) - WL > RD - 2);
    const anchor = out ? ln.gate.g : bridgeG;
    if (anchor !== placed) { anchor.after(wagon); placed = anchor; }
  }

  const TH = tween(ENTRY), R = tween(0);
  let want = -1, cur = -1, sign = 1, drawn = [NaN, NaN];
  /** Interlocking: gates move in a wave from the chosen exit, or the released one. */
  const gates = (from, now) => lines.forEach((ln, i) => tset(ln.a, cur < 0 ? IDLE : i === cur ? OPEN : SHUT, now, Math.abs(i - from) * stag));
  const reach = (i) => sign * (M + EXITS[i].L - 10.5 - WL);
  /** Turns the bridge to track cur via the nearest end; sign tells which end the wagon exits from. */
  function aim(now) {
    const goal = cur < 0 ? ENTRY : EXITS[cur].a, k = Math.round((tval(TH, now) - goal) / 180);
    sign = k % 2 === 0 ? 1 : -1;
    tset(TH, goal + 180 * k, now, 0);
  }

  const B = register(stage, (_dt, now) => {
    let r = tval(R, now);
    if (want !== cur) {
      if (Math.abs(r) > ONB) tset(R, 0, now, 0);
      else { const from = want >= 0 ? want : cur; cur = want; aim(now); tset(R, 0, now, 0); gates(from, now); }
    } else if (cur >= 0 && tdone(TH, now)) tset(R, reach(cur), now, 0);
    const th = tval(TH, now);
    r = tval(R, now);
    if (th !== drawn[0] || r !== drawn[1]) { drawn = [th, r]; drawTurn(th, r); }
    let moving = want !== cur || !tdone(TH, now) || !tdone(R, now) || (cur >= 0 && Math.abs(r - reach(cur)) > 0.01);
    lines.forEach((ln, i) => {
      const al = tval(ln.a, now);
      if (al !== ln.drawn) { ln.drawn = al; drawGate(ln, EXITS[i].a, al); }
      if (!tdone(ln.a, now)) moving = true;
    });
    return moving;
  });
  bag.add(B.unregister);

  /** Exit track under pointer on top track plane, which never moves; -1 on turntable, entry, or outside. */
  function hit([sx, sy]) {
    const [x, y] = unproj(C, sx, sy, TOP), d = Math.hypot(x, y), deg = (Math.atan2(y, x) * 180) / Math.PI;
    if (d < RD - 2) return -1;
    let best = -1, gap = 20;
    EXITS.forEach((e, i) => {
      const da = Math.abs(((deg - e.a) % 360 + 540) % 360 - 180);
      if (da < gap && d < M + e.L + 14) { gap = da; best = i; }
    });
    return best;
  }

  const lit = (a) => {
    lines.forEach((ln, i) => { ln.bed.sil.classList.toggle("hi", i === a); ln.buf.sil.classList.toggle("hi", i === a); });
    body.sil.classList.toggle("hi", a < 0); roof.sil.classList.toggle("hi", a < 0);
  };
  /** Selects exit track a (-1 is rest); the route switches once wagon is back on bridge. */
  function setActive(a) {
    if (a === want) return;
    want = a;
    lit(a);
    read.textContent = a < 0 ? "rest" : EXITS[a].say;
    B.wake();
  }
  lit(-1);

  bag.add(pointer(stage, { move: (p) => setActive(hit(p)), leave: () => setActive(-1) }));
  bag.add(() => svg.replaceChildren());

  return {
    set: (v) => { stag = v; },
    destroy: bag.dispose,
  };
}

hairline({
  name: "router",
  means: "You make a request: the bridge turns to the chosen tool track, the other gates shut, and the wagon rolls to it.",
  rules: [1, 2, 5, 8],
  range: [0, 50, 120],
  tour: [[146, 126], [212, 119], [259, 143], null],
  mount,
});
