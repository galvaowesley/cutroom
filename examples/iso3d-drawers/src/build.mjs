// Component drawers: cutroom's opt-in installation as a steel drawer cabinet on a workbench.
// Each drawer is a component and its depth is the download size, on a logarithmic scale.
//
//   node build.mjs            writes ../out/drawers.html (the kit's light theme, in the cutroom brand)
//   node build.mjs --dark     writes ../out/drawers-dark.html (the kit's dark theme, for checking)
//   node build.mjs --audit    writes and runs the kit's audit (must end in "audit passed")
//   node build.mjs --quick    only to iterate: settles the order in 3 states instead of 1,129 (same page)
//
// The Anatomy kit is read-only and imported from where cutroom-init installed it:
//   ~/.local/share/cutroom/upstream/anatomy   (or $ANATOMY_HOME)
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { DECADE, DRAWERS, ORIGIN_MB, depthOf, sizeText } from "./model.mjs";

const AN = process.env.ANATOMY_HOME ?? join(homedir(), ".local/share/cutroom/upstream/anatomy");
const load = (rel) => import(pathToFileURL(join(AN, rel)).href);
const k = await load("kit/iso-kit.mjs");
const A = await load("kit/audit.mjs");
const { kitScript } = await load("scripts/inline-kit.mjs");

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = join(HERE, "..", "out");
const theme = process.argv.includes("--dark") ? "dark" : "light";

// ---------------------------------------------------------------- world (1 unit ~ 1 px)
const W = 600;
const H = 430;

const PLATE = { x: -10, y: -10, w: 110, d: 198, r: 6 }; // workbench (perforated plate) under the cabinet
const PLATE_T = 7;
const FOOT_Z = -PLATE_T - 5;

const SIDE = 3; // thickness of the sides and back
const FRONT_Y = 92; // the cabinet's front plane
const LIP = 3; // depth of the front frame (shelf edge)
const Z0 = 6; // top of the plinth
const SHELF_T = 2.4;
const OPEN_H = 12;
const PITCH = OPEN_H + SHELF_T;
const COUNT = DRAWERS.length;
const shelfZ = (j) => Z0 + PITCH * j; // bottom of shelf j (0 = floor, COUNT = top rail)
const openZ = (i) => shelfZ(i) + SHELF_T; // bottom of drawer i's opening
const TOP_Z = shelfZ(COUNT) + SHELF_T;
const TOP_T = 3;
const CAB_TOP = TOP_Z + TOP_T;
const HANDLE_TOP = CAB_TOP + 7;

const FRONT_T = 2.4; // thickness of the drawer front
const BOX_Y1 = FRONT_Y - FRONT_T; // where the box meets the front
const BOX_X0 = 5;
const BOX_X1 = 66;
const WALL = 1.2;
const WALL_H = 8.4;
const PULL_Y = FRONT_Y + 2.6; // the handle bar sits 2.6 in front of the drawer
const PULL_D = 1.8;

const DEPTHS = DRAWERS.map((d) => depthOf(d.mb));
const MAX_OUT = Math.max(...DEPTHS);

// Logarithmic ruler on the bench, from the front plane (10 MB) to 10 GB, and the rider that reads the pulled drawer.
const RULER = { x: 77, y: 86, w: 9, d: 96, r: 1 };
const RULER_T = 0.6;
const SPAN = 3 * DECADE; // 10 MB → 10 GB
const tickY = (mb) => FRONT_Y + depthOf(mb);
const RIDER_X = RULER.x + RULER.w + 0.4;

const P = k.fitProjection(
  [
    ...k.boxCorners(PLATE, FOOT_Z, 0),
    ...k.boxCorners({ x: -1, y: -1, w: 74, d: 94, r: 0 }, 0, HANDLE_TOP),
    [BOX_X0, FRONT_Y + MAX_OUT + 6, openZ(0)],
  ],
  W,
  H,
  { pad: 22, azimuth: 46 },
);
const V = A.cameraBasis(P).V;
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const Dots = (points, style) => k.dotsSvg(points, style);
const slab = (plan, z, h, steps = 3, bevel = 0) => k.slabOf(plan, z, h, P, steps, bevel);
const byDepth = (points) => [...points].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));
const path = (points, closed = false) => k.pathOf(points.map(at), closed);

// Rounded outline on a vertical plane: y = constant (front) or x = constant (side).
function faceRect(axis, fixed, u0, u1, z0, z1, r = 0.6, steps = 4) {
  const ring = k.roundedPlan({ x: u0, y: z0, w: u1 - u0, d: z1 - z0, r }, steps);
  return path(
    ring.map(([u, z]) => (axis === "y" ? [u, fixed, z] : [fixed, u, z])),
    true,
  );
}

// ---------------------------------------------------------------- recorder and items
const ORDER = [...DRAWERS.map((_, i) => `d${i}`).reverse(), "rider"];
const SPRING = { stagger: 0.035, stiffness: 1 / 0.22 ** 2, damping: 2 / 0.22, substeps: 4 }; // critical damping, tau 0.22 s
const R = A.recorder(P, { order: ORDER, spring: SPRING });
const items = [];
const STEP = 1000; // fixed order: keys apart by more than any lift (see the check at the end)
function put(name, piece, svg, shapes, { move = [0, 0, 0], attrs = "" } = {}) {
  const item = R.put({ name, piece, ride: piece, key: items.length * STEP, move, svg, attrs, shapes: shapes.map((shape) => R.solid(shape)) });
  items.push(item);
  return item;
}
const shape = (plan, z, h, name, steps = 3) => A.slab(plan, z, h, { name }, steps);

// ---------------------------------------------------------------- workbench
const halo = `<path class="iso-halo" d="${k.haloOf(PLATE, FOOT_Z, PLATE_T + 5, P)}"/>`;

for (const [x, y] of byDepth(k.corners(PLATE, 20))) {
  put(
    `stand.foot@${x},${y}`,
    "stand",
    S(k.cylinder(x, y, 7, FOOT_Z, 1.6, P, 28), { tone: "lo" }) + S(k.cylinder(x, y, 5.4, FOOT_Z + 1.6, 3.4, P, 28), { tone: "mid" }),
    [A.cylinder(x, y, 7, FOOT_Z, 1.6, { name: `stand.foot-pad@${x},${y}` }), A.cylinder(x, y, 5.4, FOOT_Z + 1.6, 3.4, { name: `stand.foot@${x},${y}` })],
  );
}

{
  const out = [S(slab(PLATE, -PLATE_T, PLATE_T, 8, 1.6), { tone: "mid" })];
  out.push(L(k.planOutline(k.insetPlan(PLATE, 5), 0, P), { tone: "lo" }));
  const screws = k.corners(PLATE, 10);
  out.push(L(screws.map(([x, y]) => k.ring(x, y, 2.2, 0, P, 16)).join(""), { tone: "lo" }));
  out.push(Dots(screws.map(([x, y]) => at([x, y, 0])), { size: 0.5 }));
  // threaded holes of the tooling plate, every 8, where the drawers slide out
  out.push(Dots(k.dotGrid(-2, 100, 9, 11, 8, 0, P), { size: 0.45, tone: "lo" }));
  // recessed track for the ruler's rider
  out.push(L(k.planOutline({ x: RIDER_X + 1.4, y: RULER.y + 1, w: 3.6, d: RULER.d - 2, r: 1.8 }, 0, P), { tone: "faint" }));
  put("stand.plate", "stand", out.join(""), [shape(PLATE, -PLATE_T, PLATE_T, "stand.plate", 8)]);
}

{
  const out = [S(slab(RULER, 0, RULER_T, 3), { tone: "lo", crease: "none" })];
  const edge = RULER.x + RULER.w - 0.8;
  const minor = [];
  const major = [];
  for (let decade = 0; decade < 3; decade++)
    for (let m = 2; m <= 9; m++) minor.push(k.lineOnTop([edge, tickY(ORIGIN_MB * 10 ** decade * m)], [edge - 2, tickY(ORIGIN_MB * 10 ** decade * m)], RULER_T, P));
  for (let decade = 1; decade <= 3; decade++) major.push(k.lineOnTop([edge, tickY(ORIGIN_MB * 10 ** decade)], [edge - 3.8, tickY(ORIGIN_MB * 10 ** decade)], RULER_T, P));
  out.push(L(minor.join(""), { tone: "lo" }), L(major.join(""), { tone: "mid" }));
  out.push(L(k.lineOnTop([edge, FRONT_Y], [edge - 4.4, FRONT_Y], RULER_T, P), { tone: "hi" })); // zero: 10 MB, on the front plane
  out.push(Dots([at([RULER.x + 4.5, RULER.y + 2, RULER_T]), at([RULER.x + 4.5, RULER.y + RULER.d - 2, RULER_T])], { size: 0.45 }));
  put("stand.ruler", "stand", out.join(""), [shape(RULER, 0, RULER_T, "stand.ruler")]);
}

{
  // rider mounted at zero; the page moves it along +y to the reading of the drawer in focus
  const body = { x: RIDER_X, y: FRONT_Y - 2.6, w: 6.6, d: 5.2, r: 1 };
  const knob = [RIDER_X + 4.6, FRONT_Y];
  const out = [`<path class="iso-halo" d="${k.haloOf(k.insetPlan(body, 1), 0, 0.1, P)}" style="filter:blur(2px)"/>`];
  out.push(S(slab(body, 0, 2.2, 3, 0.4), { tone: "mid" }));
  out.push(L(k.lineOnTop([RIDER_X, FRONT_Y], [RIDER_X + 2.6, FRONT_Y], 2.2, P), { tone: "lit", free: "end" }));
  out.push(S(k.cylinder(knob[0], knob[1], 1.3, 2.2, 1.8, P, 20), { tone: "mid" }));
  out.push(L(k.knurl(knob[0], knob[1], 1.3, 2.2, 4, 14, P, 0.3), { tone: "lo" }));
  put("rider", "rider", out.join(""), [shape(body, 0, 2.2, "rider.body"), A.cylinder(knob[0], knob[1], 1.3, 2.2, 1.8, { name: "rider.knob" })], { move: [0, SPAN, 0], attrs: ' data-rider=""' });
}

// ---------------------------------------------------------------- cabinet
put("stand.plinth", "stand", S(slab({ x: 4, y: 4, w: 64, d: 84, r: 1 }, 0, Z0, 3, 0.5), { tone: "lo" }), [shape({ x: 4, y: 4, w: 64, d: 84, r: 1 }, 0, Z0, "stand.plinth")]);

const cavity = (svg) => `<g class="gv-cavity">${svg}</g>`;
{
  const inner = { x: 0, y: 0, w: SIDE, d: FRONT_Y - LIP, r: 0 };
  const stile = { x: 0, y: FRONT_Y - LIP, w: SIDE, d: LIP, r: 0.4 };
  put("stand.left", "stand", cavity(S(slab(inner, Z0, TOP_Z - Z0, 2), { tone: "lo", crease: "none" })) + S(slab(stile, Z0, TOP_Z - Z0, 3, 0.4), { tone: "mid" }), [
    shape(inner, Z0, TOP_Z - Z0, "stand.left", 2),
    shape(stile, Z0, TOP_Z - Z0, "stand.left-stile"),
  ]);
}
{
  const plan = { x: SIDE, y: 0, w: 72 - 2 * SIDE, d: SIDE, r: 0 };
  put("stand.back", "stand", cavity(S(slab(plan, Z0, TOP_Z - Z0, 2), { tone: "lo", crease: "none" })), [shape(plan, Z0, TOP_Z - Z0, "stand.back", 2)]);
}

function shelf(j) {
  const z = shelfZ(j);
  const inner = { x: SIDE, y: SIDE, w: 72 - 2 * SIDE, d: FRONT_Y - LIP - SIDE, r: 0 };
  const lip = { x: SIDE, y: FRONT_Y - LIP, w: 72 - 2 * SIDE, d: LIP, r: 0.3 };
  const svg = cavity(S(slab(inner, z, SHELF_T, 2), { tone: "lo", crease: "none" })) + S(slab(lip, z, SHELF_T, 3, 0.4), { tone: "mid" });
  put(`stand.shelf${j}`, "stand", svg, [shape(inner, z, SHELF_T, `stand.shelf${j}`, 2), shape(lip, z, SHELF_T, `stand.shelf${j}-lip`)]);
}

function drawer(i) {
  const d = DRAWERS[i];
  const depth = DEPTHS[i];
  const oz = openZ(i);
  const zc = oz + OPEN_H / 2;
  const y0 = BOX_Y1 - depth;
  const floor = { x: BOX_X0, y: y0, w: BOX_X1 - BOX_X0, d: depth, r: 0.4 };
  const left = { x: BOX_X0, y: y0, w: WALL, d: depth, r: 0 };
  const back = { x: BOX_X0 + WALL, y: y0, w: BOX_X1 - BOX_X0 - 2 * WALL, d: WALL, r: 0 };
  const right = { x: BOX_X1 - WALL, y: y0, w: WALL, d: depth, r: 0 };
  const runner = { x: BOX_X1, y: y0 + 1.5, w: 1, d: depth - 3, r: 0.3 };
  const front = { x: SIDE + 0.5, y: BOX_Y1, w: 72 - 2 * SIDE - 1, d: FRONT_T, r: 0.6 };
  const holder = { x: 8, y: FRONT_Y, w: 15, d: 0.4, r: 0.3 };
  const card = { x: 8.8, y: FRONT_Y + 0.4, w: 13.4, d: 0.3, r: 0.2 };
  const posts = [{ x: 27, y: FRONT_Y, w: 1.8, d: 2.6, r: 0.4 }, { x: 43.2, y: FRONT_Y, w: 1.8, d: 2.6, r: 0.4 }];
  const bar = { x: 25.6, y: PULL_Y, w: 21, d: PULL_D, r: 0.9 };
  const lamp = { x: 57.6, y: FRONT_Y, w: 3.6, d: 0.6, r: 0.4 };
  const lampAt = [lamp.x + lamp.w / 2, FRONT_Y + lamp.d, zc];
  const fz = oz + 0.5;
  const fh = OPEN_H - 1;
  const out = [];
  out.push(S(slab(floor, oz, 1, 2), { tone: "lo", crease: "none" }));
  out.push(L(k.planOutline(k.insetPlan({ x: BOX_X0 + WALL, y: y0 + WALL, w: BOX_X1 - BOX_X0 - 2 * WALL, d: depth - WALL, r: 0 }, 2.4), oz + 1, P, 2), { tone: "faint" }));
  out.push(S(slab(left, oz + 1, WALL_H, 2), { tone: "mid", crease: "none" }));
  out.push(S(slab(back, oz + 1, WALL_H, 2), { tone: "mid", crease: "none" }));
  // one divider per decade from the front: a drawer has one compartment per 10x above 10 MB
  const dividers = [];
  for (let n = Math.ceil(depth / DECADE) - 1; n >= 1; n--) dividers.push({ x: BOX_X0 + WALL, y: BOX_Y1 - n * DECADE - 0.5, w: BOX_X1 - BOX_X0 - 2 * WALL, d: 1, r: 0 });
  for (const plan of dividers) out.push(S(slab(plan, oz + 1, WALL_H - 2.4, 2), { tone: "mid", crease: "none" }));
  out.push(S(slab(right, oz + 1, WALL_H, 2), { tone: "mid", crease: "none" }));
  out.push(S(slab(runner, oz + 3.6, 2.6, 2), { tone: "lo", crease: "none" }));
  const balls = [];
  for (let y = y0 + 4; y < BOX_Y1 - 2; y += 5) balls.push(at([BOX_X1 + 1, y, oz + 4.9]));
  out.push(Dots(balls, { size: 0.4, tone: "lo" }));
  out.push(`<g data-front="">${S(slab(front, fz, fh, 3, 0.4), { tone: "hi", crease: "lo" })}</g>`);
  out.push(S(slab(holder, zc - 3, 6, 2), { tone: "mid", crease: "none" }));
  out.push(S(slab(card, zc - 2.3, 4.6, 2), { tone: "lo", crease: "none" }));
  const cy = card.y + card.d;
  out.push(L([[9.8, 19.6, zc + 1.1], [9.8, 17.4, zc], [9.8, 18.4, zc - 1.1]].map(([x0, x1, z]) => k.segment([x0, cy, z], [x1, cy, z], P)).join(""), { tone: "mid", free: true }));
  out.push(Dots([at([holder.x + 0.6, FRONT_Y + 0.4, zc + 2.4]), at([holder.x + holder.w - 0.6, FRONT_Y + 0.4, zc - 2.4])], { size: 0.4 }));
  for (const post of posts) out.push(S(slab(post, zc - 0.9, 1.8, 2), { tone: "mid", crease: "none" }));
  out.push(`<g data-pull="">${S(slab(bar, zc - 1, 2, 3, 0.3), { tone: "hi", crease: "lo" })}</g>`);
  out.push(S(slab(lamp, zc - 1.8, 3.6, 2), { tone: "mid", crease: "none" }));
  out.push(`<path class="gv-glow" d="${k.sideRing(lampAt, 1.5, "y", P, 24)}"/><path class="gv-led" data-led="" d="${k.sideRing(lampAt, 0.95, "y", P, 24)}"/>`);
  out.push(L(k.sideRing(lampAt, 1.25, "y", P, 24), { tone: "lo" }));
  const shapes = [
    shape(floor, oz, 1, `d${i}.floor`, 2),
    shape(left, oz + 1, WALL_H, `d${i}.left`, 2),
    shape(back, oz + 1, WALL_H, `d${i}.back`, 2),
    shape(right, oz + 1, WALL_H, `d${i}.right`, 2),
    ...dividers.map((plan, n) => shape(plan, oz + 1, WALL_H - 2.4, `d${i}.divider${n}`, 2)),
    shape(runner, oz + 3.6, 2.6, `d${i}.runner`, 2),
    shape(front, fz, fh, `d${i}.front`),
    shape(holder, zc - 3, 6, `d${i}.holder`, 2),
    shape(card, zc - 2.3, 4.6, `d${i}.card`, 2),
    ...posts.map((post, n) => shape(post, zc - 0.9, 1.8, `d${i}.post${n}`, 2)),
    shape(bar, zc - 1, 2, `d${i}.pull`),
    shape(lamp, zc - 1.8, 3.6, `d${i}.lamp`, 2),
  ];
  put(`d${i}.drawer`, `d${i}`, out.join(""), shapes, { move: [0, depth, 0], attrs: ` data-drawer="${i}" data-id="${d.id}"` });
}

for (let i = 0; i < COUNT; i++) {
  shelf(i);
  drawer(i);
}
shelf(COUNT);

{
  const plan = { x: 72 - SIDE, y: 0, w: SIDE, d: FRONT_Y, r: 0.4 };
  const out = [S(slab(plan, Z0, TOP_Z - Z0, 3, 0.4), { tone: "mid" })];
  // louvers: six closed slots high on the side
  const slots = [];
  for (let n = 0; n < 6; n++) slots.push(faceRect("x", 72, 12, 40, 80 + n * 3.4, 81.6 + n * 3.4, 0.8));
  out.push(`<path class="gv-slot" d="${slots.join("")}"/>`);
  out.push(L(slots.join(""), { tone: "lo" }));
  // riveted name plate on the side, with three lines of printed text
  const tag = { x: 72, y: 50, w: 0.5, d: 28, r: 0.3 };
  out.push(S(slab(tag, 58, 14, 2), { tone: "lo", crease: "none" }));
  out.push(L(faceRect("x", 72.5, 51.6, 76.4, 59.6, 70.4, 0.6), { tone: "faint" }));
  out.push(L([[54, 72, 67.6], [54, 67, 65], [54, 70, 62.4]].map(([y0, y1, z]) => k.segment([72.5, y0, z], [72.5, y1, z], P)).join(""), { tone: "mid", free: true }));
  out.push(Dots([[50.9, 71], [77.1, 71], [50.9, 59], [77.1, 59]].map(([y, z]) => at([72.5, y, z])), { size: 0.45 }));
  put("stand.right", "stand", out.join(""), [shape(plan, Z0, TOP_Z - Z0, "stand.right"), shape(tag, 58, 14, "stand.right-tag", 2)]);
}

{
  const top = { x: -1, y: -1, w: 74, d: FRONT_Y + 2, r: 1.6 };
  const brand = { x: 20, y: 72, w: 32, d: 10, r: 1 };
  const out = [S(slab(top, TOP_Z, TOP_T, 6, 0.8), { tone: "mid" })];
  out.push(L(k.planOutline(k.insetPlan(top, 3.5), CAB_TOP, P, 6), { tone: "faint" }));
  const screws = k.corners(top, 6);
  out.push(L(screws.map(([x, y]) => k.ring(x, y, 1.4, CAB_TOP, P, 14)).join(""), { tone: "lo" }));
  out.push(Dots(screws.map(([x, y]) => at([x, y, CAB_TOP])), { size: 0.45 }));
  out.push(S(slab(brand, CAB_TOP, 0.6, 3), { tone: "lo", crease: "none" }));
  out.push(L(k.planOutline(k.insetPlan(brand, 1.2), CAB_TOP + 0.6, P, 3), { tone: "faint" }));
  out.push(k.faceTextSvg(k.topMatrix([36, 77.6], CAB_TOP + 0.6, P, "x"), "cutroom", { size: 3.4, tone: "mid", anchor: "middle" }));
  out.push(Dots([at([brand.x + 2.4, brand.y + 5, CAB_TOP + 0.6]), at([brand.x + brand.w - 2.4, brand.y + 5, CAB_TOP + 0.6])], { size: 0.4 }));
  put("stand.top", "stand", out.join(""), [shape(top, TOP_Z, TOP_T, "stand.top", 6), shape(brand, CAB_TOP, 0.6, "stand.brand")]);
}

{
  const posts = byDepth([[13.5, 46.3], [58.5, 46.3]]).map(([x, y]) => ({ x: x - 1.5, y: y - 1.5, w: 3, d: 3, r: 0.6 }));
  const bar = { x: 11, y: 45.1, w: 50, d: 2.4, r: 1.2 };
  const out = posts.map((post) => S(slab(post, CAB_TOP, 5, 3), { tone: "mid", crease: "none" }));
  out.push(S(slab(bar, CAB_TOP + 5, 2, 4, 0.4), { tone: "mid" }));
  put("stand.handle", "stand", out.join(""), [...posts.map((post, n) => shape(post, CAB_TOP, 5, `stand.handle-post${n}`)), shape(bar, CAB_TOP + 5, 2, "stand.handle-bar", 4)]);
}

// ---------------------------------------------------------------- audit and order
// --quick is only for iterating on the drawing: it settles keys in three states. --audit uses all of them.
const quick = process.argv.includes("--quick") && !process.argv.includes("--audit");
A.settle(R, P, quick ? { states: [0, 0.5, 1] } : {});
const settled = [...R.items].sort((a, b) => a.key - b.key);
const moved = settled.filter((item, index) => item !== items[index]).map((item) => item.name);
if (moved.length) console.warn("ordem mudou no settle:", moved.join(", "));
// The page does not reorder per frame: the DOM order is fixed. Check that it holds in every state the audit measures.
const orderIn = (state) => [...settled].sort((a, b) => A.keyAt(a, state, V) - A.keyAt(b, state, V));
const flips = R.settled.states.filter((state) => orderIn(state).some((item, index) => item !== settled[index]));
if (flips.length) console.warn(`the fixed order flips in ${flips.length} states, for example ${A.labelOf(flips[0])}`);

// ---------------------------------------------------------------- page
const unit = (vector) => {
  const o = at([0, 0, 0]);
  const p = at(vector);
  return [p[0] - o[0], p[1] - o[1]];
};
const groups = settled.map((item) => `<g class="it" data-name="${item.name}"${item.attrs}>${item.svg}</g>`);

const LABEL =
  "A steel cabinet with seven drawers on a perforated workbench. Each drawer is a cutroom component and its depth is the download size on a logarithmic scale: from bottom to top, voice-clone ~4.5 GB, extract ~2.3 GB, voice ~740 MB, math ~400 MB, motion ~150 MB, diagram ~40 MB and iso3d ~30 MB. Beside it, a logarithmic ruler from 10 MB to 10 GB with a rider that reads the pulled drawer.";
const svg = k.figureSvg({ width: W, height: H, label: LABEL, body: [halo, ...groups] });

const DATA = {
  P,
  V,
  EY: unit([0, 1, 0]),
  frontY: FRONT_Y,
  span: SPAN,
  x: [SIDE, 72 - SIDE],
  box: [SIDE + 0.5, 72 - SIDE - 0.5],
  pull: PULL_Y + PULL_D,
  openZ: DRAWERS.map((_, i) => openZ(i)),
  openH: OPEN_H,
  shelfT: SHELF_T,
  tau: 0.22,
  drawers: DRAWERS.map((d, i) => ({ id: d.id, tool: d.tool, size: d.size, mb: d.mb, depth: DEPTHS[i] })),
};

const LIVE = `
const D = ${JSON.stringify(DATA)};
const sizeText = ${sizeText.toString()};
const root = document.querySelector(".gv");
const stage = root.querySelector(".gv-stage");
const svg = stage.querySelector("svg");
const readout = root.querySelector("[data-readout]");
const live = root.querySelector("[data-live]");
const groups = [...svg.querySelectorAll("[data-drawer]")].sort((a, b) => a.dataset.drawer - b.dataset.drawer);
const rider = svg.querySelector("[data-rider]");
const buttons = [...root.querySelectorAll(".gv-part")];
const still = matchMedia("(prefers-reduced-motion: reduce)");
const N = D.drawers.length;
const drawers = D.drawers.map((d, i) => ({ ...d, x: 0, v: 0, installed: false, el: groups[i], solids: [...groups[i].querySelectorAll("[data-front] .iso-solid, [data-pull] .iso-solid")], led: groups[i].querySelector("[data-led]") }));
const reading = { x: 0, v: 0 };
let focus = -1, touring = !still.matches, clock = 0, frame = 0, last = 0, visible = false, idle = 0;

// critically damped spring, four sub-steps
function follow(s, target, dt, tau, calm) {
  if (calm) { s.x = target; s.v = 0; return false; }
  const w = 1 / tau;
  for (let n = 0; n < 4; n++) { const h = dt / 4; s.v += (w * w * (target - s.x) - 2 * w * s.v) * h; s.x += s.v * h; }
  if (Math.abs(target - s.x) < 0.01 && Math.abs(s.v) < 0.01) { s.x = target; s.v = 0; return false; }
  return true;
}
const targetOf = (i) => (drawers[i].installed || focus === i ? drawers[i].depth : 0);
const total = () => drawers.reduce((sum, d) => sum + (d.installed ? d.mb : 0), 0);
const count = () => drawers.filter((d) => d.installed).length;
const totalText = () => (count() ? "~" + sizeText(total()) : "0 MB");
function say() {
  const d = drawers[focus];
  const text = d ? d.id + " · " + d.tool + " · " + d.size + " · open " + totalText() : (count() ? count() + " of " + N + " open · " + totalText() : "no drawer open · 0 MB");
  if (readout.textContent !== text) readout.textContent = text;
}
function draw() {
  drawers.forEach((d) => {
    const t = d.x === 0 ? "" : "translate(" + (D.EY[0] * d.x).toFixed(2) + " " + (D.EY[1] * d.x).toFixed(2) + ")";
    if (t !== (d.shown ?? "")) { d.shown = t; t ? d.el.setAttribute("transform", t) : d.el.removeAttribute("transform"); }
  });
  const r = reading.x === 0 ? "" : "translate(" + (D.EY[0] * reading.x).toFixed(2) + " " + (D.EY[1] * reading.x).toFixed(2) + ")";
  r ? rider.setAttribute("transform", r) : rider.removeAttribute("transform");
  say();
}
function mark() {
  drawers.forEach((d, i) => {
    for (const el of d.solids) el.toggleAttribute("data-lit", i === focus);
    d.led.toggleAttribute("data-on", d.installed);
    buttons[i].setAttribute("aria-pressed", String(d.installed));
    buttons[i].toggleAttribute("data-focus", i === focus);
  });
}
const tourAt = (t) => N - 1 - (Math.floor(t / 1.9) % N); // from the top (iso3d) down (voice-clone)
function tick(now) {
  const dt = last ? Math.min((now - last) / 1000, 1 / 30) : 1 / 60;
  last = now;
  const calm = still.matches;
  if (touring) { clock += dt; const next = tourAt(clock); if (next !== focus) { focus = next; mark(); } }
  let moving = false;
  drawers.forEach((d, i) => { moving = follow(d, targetOf(i), dt, D.tau, calm) || moving; });
  moving = follow(reading, focus >= 0 ? drawers[focus].x : 0, dt, 0.12, calm) || moving;
  draw();
  frame = visible && (moving || touring) ? requestAnimationFrame(tick) : 0;
}
const run = () => { if (!frame && visible) { last = 0; frame = requestAnimationFrame(tick); } };
function hold() { touring = false; clearTimeout(idle); }
function rest() { clearTimeout(idle); if (!still.matches) idle = setTimeout(() => { touring = true; clock = 0; run(); }, 3600); }
function setFocus(i) { if (i !== focus) { focus = i; mark(); } run(); }
function toggle(i) {
  if (i < 0) return;
  const d = drawers[i];
  d.installed = !d.installed;
  live.textContent = d.id + (d.installed ? " open, " : " closed, ") + d.size + ". Open: " + totalText() + ".";
  mark();
  run();
}

// Pointer to drawer: the pixel's ray against the boxes of open (clicked) drawers and the bands of the front frame,
// in the order the figure paints them (top to bottom). A drawer pulled only by hover does not hold the pointer:
// open, it covers the front of the drawer below, and the pointer would get stuck on it.
const cam = cameraOf(D.P);
function rayAt(event) {
  const m = svg.getScreenCTM();
  if (!m) return null;
  const p = new DOMPoint(event.clientX, event.clientY).matrixTransform(m.inverse());
  const sx = (p.x - D.P.origin[0]) / cam.k, sy = (p.y - D.P.origin[1]) / cam.k;
  const q = sy / cam.sinE; // the ray's point on the floor (z = 0)
  return [cam.sinA * sx + cam.cosA * q, -cam.cosA * sx + cam.sinA * q, 0];
}
function hits(o, lo, hi) {
  let t0 = -1e9, t1 = 1e9;
  for (let a = 0; a < 3; a++) {
    if (Math.abs(D.V[a]) < 1e-9) { if (o[a] < lo[a] || o[a] > hi[a]) return false; continue; }
    let ta = (lo[a] - o[a]) / D.V[a], tb = (hi[a] - o[a]) / D.V[a];
    if (ta > tb) [ta, tb] = [tb, ta];
    t0 = Math.max(t0, ta); t1 = Math.min(t1, tb);
  }
  return t0 <= t1;
}
function pick(event) {
  const o = rayAt(event);
  if (!o) return -1;
  for (let i = N - 1; i >= 0; i--) {
    const z = D.openZ[i];
    if (drawers[i].installed && drawers[i].x > 0.5 && hits(o, [D.box[0], D.frontY, z], [D.box[1], D.pull + drawers[i].x, z + D.openH])) return i;
    if (hits(o, [D.x[0], D.frontY - 0.5, z - D.shelfT / 2], [D.x[1], D.pull, z + D.openH + D.shelfT / 2])) return i;
  }
  return -1;
}
stage.addEventListener("pointermove", (event) => { hold(); setFocus(pick(event)); });
stage.addEventListener("pointerleave", () => { setFocus(-1); rest(); });
stage.addEventListener("click", (event) => { hold(); const i = pick(event); setFocus(i); toggle(i); rest(); });
stage.addEventListener("focus", hold);
stage.addEventListener("blur", rest);
stage.addEventListener("keydown", (event) => {
  let to = null;
  if (event.key === "ArrowUp" || event.key === "ArrowRight") to = Math.min(N - 1, focus < 0 ? N - 1 : focus + 1);
  if (event.key === "ArrowDown" || event.key === "ArrowLeft") to = Math.max(0, focus < 0 ? N - 1 : focus - 1);
  if (event.key === "Home") to = N - 1;
  if (event.key === "End") to = 0;
  if (event.key === "Escape") to = -1;
  if (event.key === "Enter" || event.key === " ") { event.preventDefault(); hold(); toggle(focus); return; }
  if (to === null) return;
  event.preventDefault();
  hold();
  setFocus(to);
});
buttons.forEach((button, i) => {
  button.addEventListener("pointerenter", () => { hold(); setFocus(i); });
  button.addEventListener("pointerleave", () => { setFocus(-1); rest(); });
  button.addEventListener("focus", () => { hold(); setFocus(i); });
  button.addEventListener("blur", rest);
  button.addEventListener("click", () => { hold(); setFocus(i); toggle(i); });
});
new IntersectionObserver((entries) => { visible = entries[entries.length - 1].isIntersecting; if (visible) run(); }, { rootMargin: "120px 0px" }).observe(stage);
if (touring) { touring = false; idle = setTimeout(() => { touring = true; clock = 0; run(); }, 1400); }
// inside an iframe (the brand frame): no page margins, and the height goes to the frame
if (window.self !== window.top) {
  document.body.classList.add("gv-embed");
  const tell = () => parent.postMessage({ drawers: document.documentElement.scrollHeight }, "*");
  new ResizeObserver(tell).observe(document.body);
  tell();
}
mark();
draw();
`;

// cutroom brand (Hot Signal): Bricolage Grotesque in the title and readout, Inter in the legend, hot pink for active
// states and the drawer in focus, sunflower for the lamp of an open drawer. The kit's shading tokens (paper, top,
// shade-0..3, hi/mid/lo/faint) do not change: the four faces stay the kit's. Fonts are embedded (Latin subset in
// woff2, OFL), so the page stays self-contained.
const font = (file, family, weight) =>
  `@font-face{font-family:"${family}";font-weight:${weight};font-style:normal;font-display:block;src:url(data:font/woff2;base64,${readFileSync(join(HERE, "fonts", file)).toString("base64")}) format("woff2")}`;
const FONTS = [font("BricolageGrotesque-600.subset.woff2", "Bricolage Grotesque", 600), font("BricolageGrotesque-500.subset.woff2", "Bricolage Grotesque", 400), font("Inter-400.subset.woff2", "Inter", 400)].join("");
const CSS = `${FONTS}
.gv{--gv-primary:#FF2D6F;--gv-led:#FFC43D;--gv-glow:#FF2D6F;--gv-ink:#16072B;--gv-display:"Bricolage Grotesque",ui-sans-serif,system-ui,sans-serif;--gv-text:Inter,ui-sans-serif,system-ui,sans-serif}
body.iso[data-theme]{--anatomy-page:#ffffff}
.iso[data-theme="dark"]{--anatomy-page:#0b0b0b}
.iso[data-theme="dark"] .gv{--gv-ink:#FF9BC0}
.gv [data-drawer]{--anatomy-lit:#FF2D6F}
.gv [data-rider]{--anatomy-lit:#FF2D6F}
.gv .iso-plate{overflow:hidden;border-radius:16px}
.gv-stage{outline:none;touch-action:pan-y;cursor:pointer}
.gv-stage:focus-visible{outline:2px solid var(--gv-primary);outline-offset:6px;border-radius:12px}
.gv .iso-plate-corner[data-corner="title"]{font-family:var(--gv-display);font-weight:600;font-size:13.5px;letter-spacing:0;text-transform:none;color:var(--gv-ink);top:-2px}
.gv .iso-plate-corner[data-corner="readout"]{font-family:var(--gv-display);font-weight:400;font-size:12px;letter-spacing:0;color:var(--gv-ink);bottom:-2px}
.gv .iso-plate-corner[data-corner="hint"]{text-transform:none;letter-spacing:.04em}
.gv .iso-legend,.gv .iso-caption{font-family:var(--gv-text);font-size:13.5px}
body.gv-embed .iso-page{width:100%;margin:0}
body.gv-embed .iso-figure{margin:0}
body.gv-embed .iso-plate{box-shadow:none;border-radius:0}
body.gv-embed .iso-legend{padding:0 20px 20px}
body.gv-embed .iso-caption{display:none}
.gv-cavity{--anatomy-paper:#0c0c0c;--anatomy-top:#111;--anatomy-shade-0:#090909;--anatomy-shade-1:#0a0a0a;--anatomy-shade-2:#0b0b0b;--anatomy-shade-3:#0d0d0d;--anatomy-lo:#2c2c2c}
.iso[data-theme="light"] .gv-cavity{--anatomy-paper:#c9c9c5;--anatomy-top:#d2d2ce;--anatomy-shade-0:#b9b9b5;--anatomy-shade-1:#bfbfbb;--anatomy-shade-2:#c4c4c0;--anatomy-shade-3:#cacac6;--anatomy-lo:#a2a2a6}
.gv-slot{fill:var(--anatomy-shade-0);stroke:none}
.gv-led{fill:var(--anatomy-shade-0);stroke:none;transition:fill .24s cubic-bezier(.2,.8,.2,1)}
.gv-led[data-on]{fill:var(--gv-led)}
.gv-glow{fill:var(--gv-glow);opacity:0;stroke:none;filter:blur(1.2px);transition:opacity .24s cubic-bezier(.2,.8,.2,1)}
[data-drawer]:has(.gv-led[data-on]) .gv-glow{opacity:.75}
.gv{--gv-led:#FFC43D;--gv-glow:#FF2D6F;--gv-primary:#FF2D6F}
.gv-parts{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:6px}
.gv-part{display:flex;align-items:baseline;gap:8px;padding:7px 10px;border:1px solid var(--anatomy-faint);border-radius:10px;background:transparent;color:var(--anatomy-text);font:500 12.5px/1.35 var(--gv-text);text-align:left;cursor:pointer;transition:border-color .15s,background-color .15s}
.gv-part .gv-num{font-family:var(--anatomy-mono);color:var(--anatomy-muted);font-size:11px}
.gv-part .gv-size{margin-left:auto;white-space:nowrap;font-family:var(--anatomy-mono);font-variant-numeric:tabular-nums;color:var(--anatomy-muted)}
.gv-part[data-focus]{border-color:var(--anatomy-mid)}
.gv-part[aria-pressed="true"]{background:var(--gv-primary);border-color:var(--gv-primary);color:#16072B}
.gv-part[aria-pressed="true"] .gv-num,.gv-part[aria-pressed="true"] .gv-size{color:#3a1530}
.gv-part:focus-visible{outline:1px solid var(--anatomy-muted);outline-offset:2px}
.gv-live{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
@media (max-width:560px){.gv-stage svg{width:118%;margin:-6% -9% -4%}}
@media (prefers-reduced-motion:reduce){.gv-led,.gv-glow,.gv-part{transition:none}}
`;

const BUTTONS = DRAWERS.map((d, i) => ({ d, i }))
  .reverse()
  .map(({ d, i }, n) => `<button type="button" class="gv-part" data-drawer-button="${i}" aria-pressed="false"><span class="gv-num">${String(n + 1).padStart(2, "0")}</span><span>${d.id} · ${d.tool}${d.note ? ` (${d.note})` : ""}</span><span class="gv-size">${d.size}</span></button>`);
// the buttons must be in drawer order (0 = bottom) for the script; the visual order comes from CSS
const PARTS = `<span class="gv-parts">${BUTTONS.map((html, n) => html.replace('class="gv-part"', `class="gv-part" style="order:${n}"`)).reverse().join("")}</span>`;

const CAPTION =
  "Each drawer is a cutroom component, and its depth is the download size. The scale is logarithmic: every 10x in size adds the same amount of drawer, which is why the ruler on the bench has its major ticks at 100 MB, 1 GB and 10 GB, with zero (10 MB) on the front plane. The dividers inside each drawer fall on the same decades. On a linear scale, the 30 MB drawer would be 1/150 of the voice-clone drawer and vanish. Nothing comes open: you open only the drawers you choose, and the open total is what you download.";

const READOUT0 = "no drawer open · 0 MB";
const body = `<figure class="iso-figure gv"><div class="iso-plate"><div class="iso-plate-corners" aria-hidden="true"><span class="iso-plate-corner" data-corner="fig">Fig. 1</span><span class="iso-plate-corner" data-corner="title">Only the drawers you choose open</span><span class="iso-plate-corner" data-corner="hint">Hover to pull · click to open</span><span class="iso-plate-corner" data-corner="readout" data-readout>${READOUT0}</span></div><div class="iso-stage gv-stage" tabindex="0" role="group" aria-label="cutroom component drawers. Arrow keys move between drawers, Enter or Space opens or closes the drawer in focus, Escape lets go.">${svg}</div><span class="gv-live" aria-live="polite" data-live></span></div><figcaption class="iso-legend">${PARTS}<span class="iso-caption">${CAPTION}</span></figcaption></figure>`;

let page = k.pageHtml({ title: "Component drawers", theme, body: `<style>${CSS}</style>${body}`, script: kitScript() + LIVE, width: 680 });
mkdirSync(OUT, { recursive: true });
const name = theme === "dark" ? "drawers-dark.html" : "drawers.html";
writeFileSync(join(OUT, name), page);
console.log("wrote", join("out", name), `${(page.length / 1024).toFixed(0)} KB`, `${items.length} items`, `${R.solids.length} solids`, `depths ${DEPTHS.map((d) => d.toFixed(1)).join(" ")}`);

A.auditOrExit(R, P);
