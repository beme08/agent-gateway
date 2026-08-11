import { NextRequest, NextResponse } from "next/server";

const BLOCKED_BOT_PATTERNS = [
  /facebookexternalhit/i,
  /facebot/i,
  /meta-externalagent/i,
  /gptbot/i,
  /chatgpt-user/i,
  /claudebot/i,
  /anthropic-ai/i,
  /perplexitybot/i,
  /bytespider/i,
  /ccbot/i,
  /amazonbot/i,
  /applebot/i,
  /google-extended/i,
  /semrushbot/i,
  /ahrefsbot/i,
  /mj12bot/i,
  /dotbot/i,
  /petalbot/i,
  /dataforseobot/i,
  /aspiegelbot/i,
  /seekportbot/i,
];

const ALLOWED_SEO_PATTERNS = [
  /^googlebot/i,
  /^bingbot/i,
  /^duckduckbot/i,
  /^yandex/i,
  /^baiduspider/i,
  /^linkedinbot/i,
  /^twitterbot/i,
  /^slackbot/i,
  /^slack-imgproxy/i,
];

const BLOCKED_RESPONSE = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Access Denied</title></head><body style="font-family:system-ui;background:#0b0b0f;color:#e8e8ea;display:grid;place-items:center;min-height:100vh;margin:0"><div style="text-align:center"><h1 style="font-size:2rem;margin:0 0 .5rem">403 Forbidden</h1><p>This service does not respond to automated crawling.</p></div></body></html>`;

export function middleware(req: NextRequest) {
  const ua = req.headers.get("user-agent") || "";
  if (!ua) return NextResponse.next();

  const isBlockedBot = BLOCKED_BOT_PATTERNS.some((re) => re.test(ua));
  if (!isBlockedBot) return NextResponse.next();

  const isAllowedSeo = ALLOWED_SEO_PATTERNS.some((re) => re.test(ua));
  if (isAllowedSeo) return NextResponse.next();

  const res = new NextResponse(BLOCKED_RESPONSE, {
    status: 403,
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
  res.headers.set("X-Robots-Tag", "noindex, nofollow");
  return res;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:png|jpg|jpeg|gif|svg|webp|ico)$).*)"],
};
