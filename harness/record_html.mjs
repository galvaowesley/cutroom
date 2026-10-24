#!/usr/bin/env node
// Record an HTML page (local file or URL) to video or GIF, in the system Chrome.
// For interactive pieces that cannot export video by themselves (Archify, Anatomy, Hairline, cutroom graphics).
//
//   record-html <page> <out.mp4|webm|gif> [--seconds 6] [--size 1280x800] [--wait 1]
//               [--hover "x,y;x,y;..."] [--hover-sel "css;css;..."] [--click "x,y"] [--click-sel "css;css"]
//               [--fps 12] [--width 720]
//
// The page may carry a query string (e.g. "page.html?play=1&theme=light").
// --hover walks the pointer through the points (window px); --hover-sel through the centers of elements (also
// inside iframes). The total time is --seconds, split evenly between the points.
// --click-sel clicks the elements before starting (e.g. to open drawers).
// --fps and --width apply to GIF (default 12 fps, 720 px); mp4 and webm come out at 30 fps at the window size.
// Sharp 2x PNG: `cutroom render page.html -o x.png --size WxH --scale 2`.
// Captures through Chrome's screencast (CDP) and encodes with the system ffmpeg.
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve, extname } from "node:path";
import { tmpdir } from "node:os";
import { pathToFileURL } from "node:url";

const args = process.argv.slice(2);
const opt = (name, def) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args.splice(i, 2)[1] : def;
};
const seconds = Number(opt("seconds", 6));
const [w, h] = opt("size", "1280x800").split("x").map(Number);
const wait = Number(opt("wait", 1));
const hover = opt("hover", "");
const hoverSel = opt("hover-sel", "");
const click = opt("click", "");
const clickSel = opt("click-sel", "");
const fps = Number(opt("fps", 12));
const gifWidth = Number(opt("width", 720));
const [page, output] = args;
if (!page || !output) {
  console.error('usage: record-html <page> <out.mp4|webm|gif> [--seconds 6] [--size 1280x800] [--hover "x,y;..."] [--hover-sel "css;..."]');
  process.exit(2);
}

const home = process.env.CUTROOM_HOME || (process.platform === "win32"
  ? join(process.env.LOCALAPPDATA || join(process.env.USERPROFILE, "AppData", "Local"), "cutroom")
  : join(process.env.HOME, ".local/share/cutroom"));
const req = createRequire(join(home, "cache", "playwright", "x.cjs"));
let chromium;
try {
  ({ chromium } = req("playwright-core"));
} catch {
  console.error(`playwright-core is not in ${home}/cache/playwright. Run: cutroom setup diagram (or iso3d)`);
  process.exit(127);
}

function toUrl(p) {
  if (/^(https?|file|data):/.test(p)) return p;
  const q = p.search(/[?#]/);
  const file = q < 0 ? p : p.slice(0, q);
  return pathToFileURL(resolve(file)).href + (q < 0 ? "" : p.slice(q));
}

const dir = mkdtempSync(join(tmpdir(), "record-html-"));
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined });
const context = await browser.newContext({ viewport: { width: w, height: h } });
const tab = await context.newPage();
await tab.goto(toUrl(page), { waitUntil: "load" });
await tab.waitForTimeout(wait * 1000);

async function centers(selectors, flag = "--hover-sel") {
  const pts = [];
  for (const sel of selectors) {
    let box = null;
    for (const frame of tab.frames()) {
      const el = await frame.$(sel).catch(() => null);
      box = el && (await el.boundingBox());
      if (box) break;
    }
    if (!box) {
      console.error(`${flag}: nothing found for "${sel}"`);
      process.exit(2);
    }
    pts.push([box.x + box.width / 2, box.y + box.height / 2]);
  }
  return pts;
}
const points = hoverSel
  ? await centers(hoverSel.split(";").map((s) => s.trim()).filter(Boolean))
  : hover ? hover.split(";").map((p) => p.split(",").map(Number)) : [];

// Screencast: Chrome sends a frame on every screen change, with its time. Each frame lasts until the next one.
const cdp = await context.newCDPSession(tab);
const frames = [];
cdp.on("Page.screencastFrame", (f) => {
  frames.push({ data: f.data, t: f.metadata.timestamp });
  cdp.send("Page.screencastFrameAck", { sessionId: f.sessionId }).catch(() => {});
});
const clicks = clickSel ? await centers(clickSel.split(";").map((s) => s.trim()).filter(Boolean), "--click-sel") : [];
for (const [x, y] of clicks) {
  await tab.mouse.click(x, y);
  await tab.waitForTimeout(250);
}
await cdp.send("Page.startScreencast", { format: "png", maxWidth: w, maxHeight: h });
const t0 = Date.now() / 1000;
if (click) {
  const [x, y] = click.split(",").map(Number);
  await tab.mouse.click(x, y);
}
if (points.length) {
  const slot = (seconds * 1000) / points.length;
  for (const [x, y] of points) {
    const start = Date.now();
    await tab.mouse.move(x, y, { steps: 20 });
    await tab.waitForTimeout(Math.max(0, slot - (Date.now() - start)));
  }
}
await tab.waitForTimeout(Math.max(0, (t0 + seconds) * 1000 - Date.now()));
const t1 = Date.now() / 1000;
await cdp.send("Page.stopScreencast");
await browser.close();

if (!frames.length) {
  console.error("no frame captured");
  process.exit(1);
}
const lines = ["ffconcat version 1.0"];
frames.forEach((f, i) => {
  const name = `f${String(i).padStart(5, "0")}.png`;
  writeFileSync(join(dir, name), Buffer.from(f.data, "base64"));
  const start = Math.max(f.t, t0);
  const end = i + 1 < frames.length ? frames[i + 1].t : t1;
  lines.push(`file '${name}'`, `duration ${Math.max(0.001, end - start).toFixed(4)}`);
});
lines.push(`file 'f${String(frames.length - 1).padStart(5, "0")}.png'`);  // concat ignores the last duration
writeFileSync(join(dir, "list.txt"), lines.join("\n") + "\n");

const ext = extname(output).toLowerCase();
const input = ["-f", "concat", "-safe", "0", "-i", join(dir, "list.txt")];
const even = "scale=trunc(iw/2)*2:trunc(ih/2)*2";
const vf = {
  ".gif": ["-vf", `fps=${fps},scale=${gifWidth}:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4`],
  ".mp4": ["-vf", `fps=30,${even}`, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-movflags", "+faststart"],
  ".webm": ["-vf", `fps=30,${even}`, "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "34"],
}[ext];
if (!vf) {
  console.error("output format: .mp4, .webm or .gif");
  process.exit(2);
}
const r = spawnSync("ffmpeg", ["-y", "-loglevel", "error", ...input, ...vf, "-t", String(seconds), output], { stdio: "inherit" });
rmSync(dir, { recursive: true, force: true });
if (r.status !== 0 || !existsSync(output)) process.exit(1);
console.log(`${output} (${frames.length} frames captured in ${(t1 - t0).toFixed(1)} s)`);
