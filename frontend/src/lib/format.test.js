import { describe, expect, it } from "vitest";
import { formatINR, INVOICE_RE, isQtyValid, refillText, timeline, waitingLabel } from "./format";

describe("timeline", () => {
  it("marks pharmacist check as current while awaiting", () => {
    expect(timeline("AWAITING_PHARMACIST").map((s) => s.state)).toEqual(["done", "current", "todo", "todo", "todo"]);
  });
  it("blocks the check step when on hold", () => {
    expect(timeline("ON_HOLD")[1].state).toBe("blocked");
  });
  it("is fully done once dispatched", () => {
    expect(timeline("DISPATCHED").every((s) => s.state === "done")).toBe(true);
  });
});

describe("helpers", () => {
  it("validates quantity 1-20 integers only", () => {
    expect([0, 1, 20, 21, 2.5, "", null].map(isQtyValid)).toEqual([false, true, true, false, false, false, false]);
  });
  it("formats rupees", () => expect(formatINR(1200)).toContain("1,200"));
  it("labels waiting time", () => {
    const now = Date.parse("2026-11-07T10:00:00Z");
    expect(waitingLabel("2026-11-07T09:30:00Z", now)).toBe("30 min");
    expect(waitingLabel("2026-11-07T07:00:00Z", now)).toBe("3 h");
  });
});

describe("store and refill helpers", () => {
  it("accepts sensible invoice numbers only", () => {
    expect(["INV-001", "SL/2026/001", "AB1"].every((v) => INVOICE_RE.test(v))).toBe(true);
    expect(["!!", "ab", "has space", ""].some((v) => INVOICE_RE.test(v))).toBe(false);
  });
  it("describes refill timing in plain words", () => {
    expect(refillText({ days_left: 2 })).toBe("About 2 days left");
    expect(refillText({ days_left: 1 })).toBe("About 1 day left");
    expect(refillText({ days_left: 0 })).toBe("Runs out today");
    expect(refillText({ days_left: -3 })).toBe("Ran out 3 days ago");
    expect(refillText({ days_left: null })).toContain("how many");
  });
  it("shows the waiting-for-stock state as an approved order being prepared", () => {
    expect(timeline("NO_STOCK").map((s) => s.state)).toEqual(["done", "done", "done", "current", "todo"]);
  });
});
