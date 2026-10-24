// 2x preview PNG in the frame: opens it, clicks four drawers open (bottom to top) and hovers voice-clone.
const { createRequire } = require("node:module");
const path = require("node:path");
const req = createRequire(path.join(process.env.CUTROOM_HOME, "cache", "playwright", "x.cjs"));
const { chromium } = req("playwright-core");
(async () => {
  const [page, out] = process.argv.slice(2);
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH });
  const tab = await (await browser.newContext({ viewport: { width: 800, height: 1000 }, deviceScaleFactor: 2 })).newPage();
  await tab.goto("file://" + path.resolve(page), { waitUntil: "load" });
  await tab.waitForTimeout(1200);
  const frame = tab.frames().find((f) => f.url().endsWith("drawers.html"));
  for (const i of [2, 3, 4, 5]) {  // voice, math, motion, diagram
    const box = await (await frame.$(`[data-drawer="${i}"] [data-led]`)).boundingBox();
    await tab.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
    await tab.waitForTimeout(200);
  }
  const lamp = await (await frame.$('[data-drawer="0"] [data-led]')).boundingBox();
  await tab.mouse.move(lamp.x + lamp.width / 2, lamp.y + lamp.height / 2, { steps: 10 });
  await tab.waitForTimeout(2200);
  await (await tab.$(".frame")).screenshot({ path: out });
  await browser.close();
})();
