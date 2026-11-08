import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { Empty, ErrorBox, Spinner } from "../components/ui";
import { refillText } from "../lib/format";

export default function Refills() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);
  const load = useCallback(() => { setError(null); api.get("/refills").then(setRows).catch(setError); }, []);
  useEffect(load, [load]);

  return (
    <>
      <h1>Your refills</h1>
      <p className="sub">We remind you 3 days before a medicine runs out. A pharmacist checks every refill order.</p>
      <ErrorBox error={error} onRetry={load} />
      {!rows && !error && <Spinner />}
      {rows && rows.length === 0 && <Empty title="No refills yet">After your first delivery, your regular medicines will appear here.</Empty>}
      {rows?.map((r) => <RefillCard key={r.id} r={r} onChange={load} />)}
    </>
  );
}

function RefillCard({ r, onChange }) {
  const nav = useNavigate();
  const [doses, setDoses] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const run = async (fn) => { setBusy(true); setError(null); try { await fn(); } catch (e) { setError(e); } finally { setBusy(false); } };
  const needsRx = error?.status === 409 && /prescription/i.test(error.message);

  return (
    <div className="card">
      <div className="row between">
        <div><strong>{r.product_name}</strong><div className="muted small">{r.pack} × {r.qty}</div></div>
        {r.state === "due" && <span className="badge warn">Running low</span>}
      </div>
      <p style={{ margin: ".6rem 0" }} className={r.state === "needs_dose" ? "muted" : ""}>
        {refillText(r)}{r.runout_date && r.days_left >= 0 && <span className="muted small"> · until {new Date(r.runout_date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</span>}
      </p>
      {r.state === "needs_dose" && (
        <div className="row" style={{ marginBottom: ".6rem" }}>
          <label htmlFor={`d${r.id}`} className="small" style={{ margin: 0 }}>Taken per day</label>
          <input id={`d${r.id}`} className="qty" type="number" min="0.25" max="8" step="0.25" value={doses} onChange={(e) => setDoses(e.target.value)} />
          <button className="btn secondary small" disabled={!(Number(doses) >= 0.25 && Number(doses) <= 8) || busy}
            onClick={() => run(async () => { await api.patch(`/refills/${r.id}`, { doses_per_day: Number(doses) }); await onChange(); })}>Save</button>
        </div>
      )}
      <ErrorBox error={error} />
      {needsRx && <p className="small"><Link to="/upload">Upload a new prescription</Link></p>}
      <div className="row">
        <button className="btn" disabled={busy} onClick={() => run(async () => nav(`/orders/${(await api.post(`/refills/${r.id}/reorder`)).id}`))}>
          {busy ? "Please wait…" : "Reorder"}
        </button>
        <button className="btn secondary small" disabled={busy}
          onClick={() => window.confirm(`Stop reminders for ${r.product_name}?`) && run(async () => { await api.del(`/refills/${r.id}`); await onChange(); })}>
          Stop reminders
        </button>
      </div>
    </div>
  );
}
