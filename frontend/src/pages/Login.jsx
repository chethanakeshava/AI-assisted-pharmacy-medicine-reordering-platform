import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { ErrorBox } from "../components/ui";
import { LangSwitch, useT } from "../i18n";

const DEMOS = [["Customer · Debasish", "9000000001"], ["Customer · Rina", "9000000002"],
  ["Customer · Arif", "9000000003"], ["Pharmacist", "9000000010"], ["Store staff", "9000000020"], ["Operations", "9000000030"]];
const HOME = { customer: "/", pharmacist: "/pharmacist", store_staff: "/store", ops: "/ops" };

export default function Login() {
  const { user, login } = useAuth();
  const { t } = useT();
  const nav = useNavigate();
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [devOtp, setDevOtp] = useState(null);
  const [step, setStep] = useState("phone");
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  if (user) return <Navigate to={HOME[user.role]} replace />;

  const send = async (e) => {
    e?.preventDefault();
    setBusy(true); setError(null);
    try {
      const registering = mode === "register";
      const r = registering
        ? await api.post("/auth/register/request-otp", { name: name.trim(), phone })
        : await api.post("/auth/request-otp", { phone });
      setDevOtp(r.dev_otp); setStep("code");
      setCode("");
    } catch (err) {
      setError(err.status === 404
        ? new Error("We couldn't find an account for this number.")
        : err);
    } finally { setBusy(false); }
  };

  const verify = async (e) => {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      const r = mode === "register"
        ? await api.post("/auth/register/verify-otp", { name: name.trim(), phone, code })
        : await api.post("/auth/verify-otp", { phone, code });
      await login(r.token);
      nav(HOME[r.role], { replace: true });
    } catch (err) { setError(err); } finally { setBusy(false); }
  };

  const startLogin = () => {
    setMode("login"); setStep("phone"); setCode(""); setDevOtp(null); setError(null);
  };
  const startRegistration = () => {
    setMode("register"); setStep("phone"); setPhone(""); setName("");
    setCode(""); setDevOtp(null); setError(null);
  };
  const nameValid = name.trim().length >= 2 && name.trim().length <= 80;

  return (
    <main className={`auth-page ${step === "code" ? "auth-page--code" : "auth-page--phone"}`}>
      <section className="auth-hero" aria-label="MediBridge">
        <strong className="auth-hero-brand">MediBridge</strong>
        <div className="auth-hero-main">
          <p className="auth-eyebrow">{t("login.heroEyebrow")}</p>
          <h2>{t("login.heroTitle")}</h2>
          <p className="auth-hero-copy">{t("login.heroCopy")}</p>
          <ol className="auth-benefits">
            <li><strong>01&nbsp; {t("login.heroStep1")}</strong><span>{t("login.heroStep1Copy")}</span></li>
            <li><strong>02&nbsp; {t("login.heroStep2")}</strong><span>{t("login.heroStep2Copy")}</span></li>
            <li><strong>03&nbsp; {t("login.heroStep3")}</strong><span>{t("login.heroStep3Copy")}</span></li>
          </ol>
        </div>
        <p className="auth-hero-footer">{t("login.heroFooter")}</p>
      </section>
      <section className="auth-panel">
        <div className="auth-panel-content">
          <div className="auth-heading">
            <h1>{step === "code" ? "Verify your phone" : "MediBridge"}</h1>
            <LangSwitch />
          </div>
          {step === "phone" ? (
            <>
              <p className="auth-tagline">{t("login.tagline")}</p>
              <div className="auth-card">
                <form onSubmit={send}>
                  {mode === "register" && (
                    <div className="field">
                      <label htmlFor="name">{t("login.name")}</label>
                      <input id="name" type="text" maxLength={80} value={name} autoFocus
                        onChange={(e) => setName(e.target.value)} autoComplete="name" required />
                    </div>
                  )}
                  <div className="field">
                    <label htmlFor="phone">{t("login.mobile")}</label>
                    <input id="phone" type="tel" inputMode="numeric" maxLength={10} value={phone}
                      autoFocus={mode === "login"}
                      onChange={(e) => setPhone(e.target.value.replace(/\D/g, ""))} placeholder="10-digit number" />
                    {mode === "login" && <span className="auth-helper">{t("login.phoneHelper")}</span>}
                  </div>
                  <ErrorBox error={error} />
                  <button className="btn hero auth-submit" disabled={phone.length !== 10 || busy || (mode === "register" && !nameValid)}>
                    {busy ? "Sending…" : mode === "register" ? t("login.register") : t("login.send")}
                  </button>
                  {mode === "login" ? (
                    <p className="auth-switch">
                      <button type="button" className="chip" disabled={busy} onClick={startRegistration}>{t("login.createAccount")}</button>
                    </p>
                  ) : (
                    <p className="auth-switch">
                      {t("login.haveAccount")}{" "}
                      <a href="#" onClick={(e) => { e.preventDefault(); startLogin(); }}>{t("login.returnLogin")}</a>
                    </p>
                  )}
                </form>
              </div>
              <p className="auth-terms">{t("login.termsNote")}</p>
              <details className="auth-demos small muted">
                <summary>Demo accounts for reviewers</summary>
                <div className="chips auth-demo-grid">
                  {DEMOS.map(([label, p]) => (
                    <button key={p} className="chip" disabled={busy} onClick={() => {
                      setMode("login"); setPhone(p); setStep("phone"); setCode(""); setDevOtp(null); setError(null);
                    }}>{label}</button>
                  ))}
                </div>
              </details>
            </>
          ) : (
            <>
              <p className="sub">{t("login.sentTo")} <strong>{phone}</strong></p>
              <div className="auth-card">
                <form onSubmit={verify}>
                  {devOtp && (
                    <div className="dev-box">Test mode: no SMS is sent. Your code is <strong>{devOtp}</strong>{" "}
                      <button type="button" className="chip" onClick={() => setCode(devOtp)}>Fill it in</button></div>
                  )}
                  <div className="field">
                    <label htmlFor="code">{t("login.code")}</label>
                    <input id="code" className="auth-code-input" type="text" inputMode="numeric" maxLength={6} value={code} autoFocus
                      onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} autoComplete="one-time-code" />
                  </div>
                  <ErrorBox error={error} />
                  <button className="btn hero auth-submit" disabled={code.length !== 6 || busy}>
                    {busy ? "Verifying…" : mode === "register" ? t("login.register") : t("login.signIn")}
                  </button>
                  <p className="auth-switch auth-switch--left">
                    <a href="#" onClick={(e) => { e.preventDefault(); setStep("phone"); setCode(""); setError(null); }}>{t("login.other")}</a>
                    {mode === "register" && <> · <a href="#" onClick={(e) => { e.preventDefault(); startLogin(); }}>{t("login.returnLogin")}</a></>}
                  </p>
                </form>
              </div>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
