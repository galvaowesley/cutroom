/* cutroom_motionkit: the dynamic, never-still style for HyperFrames compositions (GSAP).

   Copy into the project and load it after GSAP:
     cp ~/.local/share/cutroom/harness/cutroom_motionkit.js "$J/src/<slug>/assets/"
     <script src="assets/cutroom_motionkit.js"></script>      then   const K = CutroomMotion;

   Two kinds of piece, both seek-safe (a render may jump to any time):
     tween helpers   take the paused timeline `tl` and a start time:     K.words(tl, ...), K.circleIn(tl, ...)
     time functions  return at(t) and set the state for time t; register them once with K.clock(tl, DUR, [at, ...])

   Every time comes from the narration (harness/cutroom_timing.py), never typed by hand.
   Patterns are catalogued in skills/cutroom-motion/references/dynamic-style.md: add new ones here and there.

   Transitions     K.circleIn   K.whipIn / K.whipOut   K.pushIn / K.pushOut   K.zoomThrough (with K.ring)
   Text            K.words      K.typed      K.counter
   Space           K.ring       K.feed       K.camera      K.pathTable / K.pointAt
   Plumbing        K.clock      K.clamp  K.ss  K.lerp
*/
(function (root) {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const ss = (x) => { x = clamp(x); return x * x * (3 - 2 * x); };       // smoothstep
  const lerp = (a, b, k) => a + (b - a) * k;
  const all = (s) => (typeof s === "string" ? [...document.querySelectorAll(s)] : s);

  // ------------------------------------------------------------------ text
  /** Words rise out of a mask. Markup: <span class="ln"><span class="w"><i>word</i></span> ...</span>;
   *  `.w` is inline-block with overflow hidden. times[i] is when word i is spoken. */
  function words(tl, sel, times, dur = 0.55, ease = "expo.out") {
    all(sel + " .w i").forEach((el, i) => tl.fromTo(el, { yPercent: 118 }, { yPercent: 0, duration: dur, ease }, times[i]));
  }

  /** Typing driven by time: text shown from t0 to t1, with a blinking cursor until `cursorUntil` (default t1). */
  function typed(el, cursor, text, t0, t1, cursorUntil = t1) {
    el = all(el)[0]; cursor = all(cursor)[0];
    return (t) => {
      el.textContent = text.slice(0, Math.round(text.length * ss((t - t0) / (t1 - t0))));
      if (cursor) cursor.style.opacity = t < cursorUntil ? (Math.floor(t * 3) % 2 ? 0.2 : 1) : 0;
    };
  }

  /** A number that counts up with an ease between t0 and t0 + dur. */
  function counter(el, to, t0, dur, fmt = (n) => String(n)) {
    el = all(el)[0];
    return (t) => { el.textContent = fmt(Math.round(to * ss((t - t0) / dur))); };
  }

  // ------------------------------------------------------------------ transitions (the incoming scene covers the outgoing one)
  /** Circular mask opening from a point: the new scene is revealed through a growing circle. */
  function circleIn(tl, sel, at, o = {}) {
    const { x = "50%", y = "50%", r = 80, dur = 0.75, ease = "power3.inOut" } = o;
    tl.fromTo(sel, { clipPath: `circle(0% at ${x} ${y})` }, { clipPath: `circle(${r}% at ${x} ${y})`, duration: dur, ease }, at);
  }
  /** Whip pan: the new scene slides in from the right, blurred, and snaps sharp. */
  function whipIn(tl, sel, at, o = {}) {
    const { dur = 0.8, blur = 30, ease = "power4.out" } = o;
    tl.fromTo(sel, { xPercent: 100, filter: `blur(${blur}px)` }, { xPercent: 0, filter: "blur(0px)", duration: dur, ease }, at);
  }
  /** The outgoing content of a whip pan: pulled left, smaller, blurred. */
  function whipOut(tl, sel, at, o = {}) {
    const { x = -300, scale = 0.92, blur = 10, dur = 0.75, ease = "power2.in" } = o;
    tl.to(sel, { x, scale, filter: `blur(${blur}px)`, duration: dur, ease }, at);
  }
  /** Vertical push: the new scene comes up from below. */
  function pushIn(tl, sel, at, o = {}) {
    const { dur = 0.95, blur = 24, ease = "power2.inOut" } = o;
    tl.fromTo(sel, { yPercent: 100, filter: `blur(${blur}px)` }, { yPercent: 0, filter: "blur(0px)", duration: dur, ease }, at);
  }
  /** The outgoing content of a push: carried up and away. */
  function pushOut(tl, sel, at, o = {}) {
    const { y = -520, scale = 0.92, blur = 8, dur = 0.95, ease = "power2.inOut" } = o;
    tl.to(sel, { y, scale, filter: `blur(${blur}px)`, duration: dur, ease }, at);
  }

  // ------------------------------------------------------------------ space
  /** A ring of items that bursts out from the centre, turns slowly, and at `zoomStart` rushes past the camera
   *  (zoom-through): the exit of a scene. The ring's origin is the item container's position. */
  function ring(items, o = {}) {
    items = all(items);
    const { start, zoomStart, radius = 372, squash = 0.92, spin = 0.2, burst = 1.5, stagger = 0.04, zoomDur = 0.9 } = o;
    return (t) => {
      const b = clamp((t - start) / burst), rot = Math.max(0, t - start) * spin, z = ss((t - zoomStart) / zoomDur);
      items.forEach((c, i) => {
        const own = clamp((b - i * stagger) / 0.55), e = 1 - Math.pow(1 - own, 3);
        const ang = (i / items.length) * Math.PI * 2 - Math.PI / 2 + rot, rad = radius * e * (1 + z * 3.4);
        gsap.set(c, { x: Math.cos(ang) * rad, y: Math.sin(ang) * rad * squash, scale: e * (1 + z * 3.2), opacity: e * (1 - clamp((z - 0.35) / 0.65)) });
      });
    };
  }

  /** A vertical feed of cards that never stops: it scrolls to bring card i into focus at A[i] and drifts in between.
   *  The focused card is full size; the others are smaller and dimmer. Cards sit at top = i * pitch in the feed.
   *  Cards closer than 0.6 s: space them in A first (a card needs about that long to take focus).
   *  o: { top (focus position), pitch, enterFrom, enterAt, enterDur, lead, dur, drift, extra: [{at, shift, dur}],
   *       hl (selector of a highlight child, opacity = focus weight) }
   *  Returns at(t), with at.weight(i, t). */
  function feed(feedEl, cards, A, o = {}) {
    feedEl = all(feedEl)[0]; cards = all(cards);
    const { top = 800, pitch = 440, enterFrom = 340, enterAt = A[0] - 0.6, enterDur = 0.85, lead = 0.8, dur = 0.95, drift = 18,
            extra = [], hl = ".hl2" } = o;
    const weight = (i, t) => {
      const nx = i < A.length - 1 ? A[i + 1] : 1e9;
      return ss((t - (A[i] - 0.35)) / 0.4) * (1 - ss((t - (nx - 0.35)) / 0.4));
    };
    const at = (t) => {
      let y = top + enterFrom * (1 - ss((t - enterAt) / enterDur));
      for (let i = 1; i < A.length; i++) y -= pitch * ss((t - (A[i] - lead)) / dur);
      y -= drift * Math.max(0, t - A[0]);
      extra.forEach((e) => { y -= e.shift * ss((t - e.at) / e.dur); });
      gsap.set(feedEl, { y });
      A.forEach((a, i) => {
        const w = weight(i, t);
        gsap.set(cards[i], { scale: 0.9 + 0.1 * w, opacity: 0.5 + 0.5 * w });
        const h = hl && cards[i].querySelector(hl);
        if (h) gsap.set(h, { opacity: w });
      });
    };
    at.weight = weight;
    return at;
  }

  /** A camera over a stage (a wrapper `el` with transform-origin 0 0, inside a clipped viewport w x h).
   *  keys: [{t, cx, cy, s}]: at time t the camera is centred on (cx, cy) at zoom s. Moves chain (each one blends
   *  from where the previous left the camera) and clamp to the stage, so the frame never shows outside it.
   *  o: { w, h, base: t => {cx, cy, s} (what the camera does between keys, e.g. a slow push-in), lead, dur } */
  function camera(el, keys, o = {}) {
    el = all(el)[0];
    const { w, h, lead = 0.45, dur = 0.65 } = o;
    const base = o.base || (() => ({ cx: w / 2, cy: h / 2, s: 1 }));
    return (t) => {
      let st = base(t);
      keys.forEach((f) => { const k = ss((t - (f.t - lead)) / dur); st = { cx: lerp(st.cx, f.cx, k), cy: lerp(st.cy, f.cy, k), s: lerp(st.s, f.s, k) }; });
      const s = st.s;
      let x = w / 2 - s * st.cx, y = h / 2 - s * st.cy;
      x = Math.min(0, Math.max(w - w * s, x)); y = Math.min(0, Math.max(h - h * s, y));
      gsap.set(el, { x, y, scale: s });
    };
  }

  /** Path geometry sampled ONCE at build time (reading it inside a timeline callback is order-dependent in a render).
   *  pathTable(sel, n) -> table; pointAt(table, u in 0..1) -> {x, y}. */
  function pathTable(sel, n = 300) {
    const el = all(sel)[0], L = el.getTotalLength();
    return Array.from({ length: n + 1 }, (_, i) => { const q = el.getPointAtLength(L * i / n); return [q.x, q.y]; });
  }
  function pointAt(T, u) {
    const f = clamp(u) * (T.length - 1), i = Math.min(T.length - 2, Math.floor(f)), k = f - i;
    return { x: lerp(T[i][0], T[i + 1][0], k), y: lerp(T[i][1], T[i + 1][1], k) };
  }

  // ------------------------------------------------------------------ plumbing
  /** One clock drives every time function: a single tween whose onUpdate calls them all with the scene time. */
  function clock(tl, duration, fns) {
    const c = { t: 0 };
    const update = () => fns.forEach((f) => f(c.t));
    update();
    tl.to(c, { t: duration, duration, ease: "none", onUpdate: update }, 0);
  }

  root.CutroomMotion = { clamp, ss, lerp, words, typed, counter, circleIn, whipIn, whipOut, pushIn, pushOut, ring, feed, camera,
                         pathTable, pointAt, clock };
})(typeof window !== "undefined" ? window : globalThis);
