const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

async function main() {
  const outputDir = path.resolve("output/video/raw");
  fs.mkdirSync(outputDir, { recursive: true });

  const browser = await chromium.launch({ channel: "chrome", headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: {
      dir: outputDir,
      size: { width: 1280, height: 720 },
    },
  });
  const page = await context.newPage();

  await page.goto("https://whatsapp-school-assistant-demo.vercel.app", {
    waitUntil: "networkidle",
  });
  await page.waitForTimeout(2500);
  await page.getByRole("button", { name: "Krankmeldung" }).click();
  await page.waitForTimeout(4500);

  await page.goto("https://operations-kpi-automation-demo.vercel.app", {
    waitUntil: "networkidle",
  });
  await page.waitForTimeout(3000);
  await page.getByRole("button", { name: "Pipeline neu ausführen" }).click();
  await page.waitForTimeout(4500);
  await page.mouse.wheel(0, 520);
  await page.waitForTimeout(3500);

  const video = page.video();
  await context.close();
  const recordedPath = await video.path();
  await browser.close();

  process.stdout.write(recordedPath);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
