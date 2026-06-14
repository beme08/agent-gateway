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

try {
  log("=== Sign in as Manager, approve the pending sick leave ===");
  await page.goto(`${URL}/`);
  await page.waitForLoadState("networkidle");
  await page.locator(`button[type=submit]:has-text("Try as Manager")`).first().click();
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(2000);
  log("  url:", page.url());
  await shot("approve-01-arrived");

  // Click the Approve button on the first row
  const approveBtn = page.locator("button:has-text(\"Approve\")").first();
  if (await approveBtn.count() > 0) {
    log("  Found Approve button — clicking");
    await approveBtn.click();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);
    await shot("approve-02-after");
    const body = await page.locator("body").innerText();
    log("  body after approve:", body.slice(0, 600).replace(/\n+/g, " | "));
  } else {
    log("  No Approve button visible");
    const body = await page.locator("body").innerText();
    log("  body:", body.slice(0, 500).replace(/\n+/g, " | "));
  }

  log("\n=== Check admin audit log shows the new event ===");
  await page.goto(`${URL}/`);
  await page.waitForLoadState("networkidle");
  await page.locator(`button[type=submit]:has-text("Try as Admin")`).first().click();
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(2000);
  await page.goto(`${URL}/audit`);
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(2000);
  await shot("approve-03-admin-audit");
  const auditBody = await page.locator("body").innerText();
  log("  audit body:", auditBody.slice(0, 800).replace(/\n+/g, " | "));

  log("\n=== Try the chat UI as Employee (will show the demo questions) ===");
  await page.goto(`${URL}/`);
  await page.waitForLoadState("networkidle");
  await page.locator(`button[type=submit]:has-text("Try as Employee")`).first().click();
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(2000);
  await page.goto(`${URL}/agents/hr-policy-agent`);
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(2000);
  await shot("chat-01-employee-agent");
  const chatBody = await page.locator("body").innerText();
  log("  chat body:", chatBody.slice(0, 700).replace(/\n+/g, " | "));
} catch (e) {
  log("ERROR:", e.message);
  log(e.stack);
  await shot("error");
} finally {
  await browser.close();
}
