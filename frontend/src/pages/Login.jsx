import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { ErrorBox } from "../components/ui";

const DEMOS = [["Customer · Debasish", "9000000001"], ["Customer · Rina", "9000000002"],
  ["Customer · Arif", "9000000003"], ["Pharmacist", "9000000010"], ["Store staff", "9000000020"]];
const HOME = { customer: "/", pharmacist: "/pharmacist", store_staff: "/store" };

export default function Login() {
  const { user, login } = useAuth();
  const nav = useNavigate();
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [devOtp, setDevOtp] = useState(null);
  const [step, setStep] = useState("phone");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  if (user) return <Navigate to={HOME[user.role]} replace />;

  const send = async (e) => {
    e?.preventDefault();
    setBusy(true); setError(null);
    try {
      const r = await api.post("/auth/request-otp", { phone });
      setDevOtp(r.dev_otp); setStep("code");
    } catch (err) {
      setError(err.status === 404 ? new Error("We couldn't find an account for this number.") : err);
    } finally { setBusy(false); }
  };

  const verify = async (e) => {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      const r = await api.post("/auth/verify-otp", { phone, code });
      await login(r.token);
      nav(HOME[r.role], { replace: true });
    } catch (err) { setError(err); } finally { setBusy(false); }
  };

  return (
    <main className="page" style={{ maxWidth: 440, paddingTop: "12vh" }}>
      <h1 style={{ color: "var(--primary)" }}>MediBridge</h1>
      <p className="sub">Refill your regular medicines in a minute.</p>
      <div className="card">
        {step === "phone" ? (
          <form onSubmit={send}>
            <div className="field">
              <label htmlFor="phone">Mobile number</label>
              <input id="phone" type="tel" inputMode="numeric" maxLength={10} value={phone} autoFocus
                onChange={(e) => setPhone(e.target.value.replace(/\D/g, ""))} placeholder="10-digit number" />
            </div>
            <ErrorBox error={error} />
            <button className="btn hero" disabled={phone.length !== 10 || busy}>{busy ? "Sending…" : "Send code"}</button>
          </form>
        ) : (
          <form onSubmit={verify}>
            <p>We sent a 6-digit code to <strong>{phone}</strong>.</p>
            {devOtp && (
              <div className="dev-box">Test mode: no SMS is sent. Your code is <strong>{devOtp}</strong>{" "}
                <button type="button" className="chip" onClick={() => setCode(devOtp)}>Fill it in</button></div>
            )}
            <div className="field">
              <label htmlFor="code">Code</label>
              <input id="code" type="text" inputMode="numeric" maxLength={6} value={code} autoFocus
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} autoComplete="one-time-code" />
            </div>
            <ErrorBox error={error} />
            <button className="btn hero" disabled={code.length !== 6 || busy}>{busy ? "Checking…" : "Sign in"}</button>
            <p className="small" style={{ marginTop: ".8rem" }}>
              <a href="#" onClick={(e) => { e.preventDefault(); setStep("phone"); setCode(""); setError(null); }}>Use a different number</a>
            </p>
          </form>
        )}
      </div>
      <details className="small muted">
        <summary>Demo accounts for reviewers</summary>
        <div className="chips" style={{ marginTop: ".5rem" }}>
          {DEMOS.map(([label, p]) => (
            <button key={p} className="chip" onClick={() => { setPhone(p); setStep("phone"); setError(null); }}>{label}</button>
          ))}
        </div>
      </details>
    </main>
  );
}
