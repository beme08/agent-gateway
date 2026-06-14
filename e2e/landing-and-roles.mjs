import { chromium } from "playwright";
import fs from "fs";

const URL = "https://agent-gateway-qdauk3e09-beme08s-projects.vercel.app";
const SHOTS = "/tmp/e2e/shots";
fs.mkdirSync(SHOTS, { recursive: true });

const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await context.newPage();
const log = (...a) => console.log(...a);
const shot = async (name) => {
  const p = `${SHOTS}/${name}.png`;
  await page.screenshot({ path: p, fullPage: true });
  log(`  📸 ${p}`);
};

const tryAsRole = async (label) => {
  log(`\n=== Try as ${label} ===`);
  // Start from a clean landing
  await page.goto(`${URL}/`);
  await page.waitForLoadState("networkidle");
  const btn = page.locator(`button[type=submit]:has-text("Try as ${label}")`).first();
  await btn.scrollIntoViewIfNeeded();
  await btn.click();
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(2500);
  log(`  url: ${page.url()}`);
  await shot(`try-${label.toLowerCase()}`);
  const body = await page.locator("body").innerText();
  log(`  body (first 400):`, body.slice(0, 400).replace(/\n+/g, " | "));
  return body;
};

try {
  log("=== STEP 1: Landing ===");
  await page.goto(`${URL}/`);
  await page.waitForLoadState("networkidle");
  await shot("01-landing");

  log("\n=== STEP 2: Try as Employee ===");
  const empBody = await tryAsRole("Employee");

  log("\n=== STEP 3: Visit /leave as Employee ===");
  await page.goto(`${URL}/leave`);
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(1500);
  await shot("03-leave");
  const leaveBody = await page.locator("body").innerText();
  log("  leave body (first 500):", leaveBody.slice(0, 500).replace(/\n+/g, " | "));

  log("\n=== STEP 4: Try as Manager ===");
  const mgrBody = await tryAsRole("Manager");

  log("\n=== STEP 5: Visit /leave/approvals as Manager ===");
  await page.goto(`${URL}/leave/approvals`);
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(2000);
  await shot("05-approvals");
  const apprBody = await page.locator("body").innerText();
  log("  approvals body (first 500):", apprBody.slice(0, 500).replace(/\n+/g, " | "));

  log("\n=== STEP 6: Try as Admin ===");
  const admBody = await tryAsRole("Admin");

  log("\n=== STEP 7: Visit /audit as Admin ===");
  await page.goto(`${URL}/audit`);
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(2000);
  await shot("07-audit");
  const auditBody = await page.locator("body").innerText();
  log("  audit body (first 500):", auditBody.slice(0, 500).replace(/\n+/g, " | "));

  log("\n=== STEP 8: Try as Viewer ===");
  const viewBody = await tryAsRole("Viewer");

  log("\n=== DONE ===");
  log(`screenshots: ${SHOTS}/`);
} catch (e) {
  log("ERROR:", e.message);
  log(e.stack);
  await shot("error");
} finally {
  await browser.close();
}
