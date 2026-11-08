import { describe, expect, it } from "vitest";
import { LANGS, translate } from "./i18n.jsx";

describe("translate", () => {
  it("fills variables", () => expect(translate("en", "home.hello", { name: "Rina" })).toBe("Hello, Rina"));
  it("returns Hindi and Bengali text", () => {
    expect(translate("hi", "home.reorder")).toBe("दोबारा ऑर्डर करें");
    expect(translate("bn", "home.reorder")).toBe("আবার অর্ডার করুন");
  });
  it("falls back to the key for plain staff labels", () => expect(translate("hi", "Verification queue")).toBe("Verification queue"));
  it("has every English key in every language", async () => {
    const mod = await import("./i18n.jsx");
    for (const [code] of LANGS) {
      for (const key of ["nav.home", "login.send", "home.reorder", "upload.title", "cart.place", "cart.upi"]) {
        expect(mod.translate(code, key)).not.toBe(key);
      }
    }
  });
});
