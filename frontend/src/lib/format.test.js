import { describe, expect, it } from "vitest";
import { formatINR, isQtyValid, timeline, waitingLabel } from "./format";

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
