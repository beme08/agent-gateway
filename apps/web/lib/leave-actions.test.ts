import { describe, expect, it } from "vitest";

describe("smoke", () => {
  it("imports", async () => {
    const mod = await import("./leave-actions");
    expect(typeof mod.createLeaveRequest).toBe("function");
    expect(typeof mod.approveLeaveRequest).toBe("function");
    expect(typeof mod.rejectLeaveRequest).toBe("function");
    expect(typeof mod.cancelLeaveRequest).toBe("function");
  });
});
