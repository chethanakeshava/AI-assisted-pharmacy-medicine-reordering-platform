import { useState } from "react";
import { api } from "../api";
import { ErrorBox } from "../components/ui";

export default function Stock() {
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [rem, setRem] = useState(null);
  const [remErr, setRemErr] = useState(null);

  const upload = async () => {
    setBusy(true); setError(null); setResult(null);
    try { const f = new FormData(); f.append("file", file); setResult(await api.upload("/stock/upload", f)); setFile(null); }
    catch (e) { setError(e); } finally { setBusy(false); }
  };
  const runReminders = async () => {
    setRemErr(null); setRem(null);
    try { setRem(await api.post("/admin/run-reminders")); } catch (e) { setRemErr(e); }
  };
  const lines = error?.detail?.errors;

  return (
    <>
      <h1>Stock and reminders</h1>
      <div className="card">
        <h2>Daily stock file</h2>
        <p className="muted small">CSV with the columns <code>store, product, qty</code>. If any line is wrong, nothing is applied. Orders waiting for stock are routed again after a good upload.</p>
        <div className="field"><label htmlFor="csv">CSV file</label>
          <input id="csv" type="file" accept=".csv,text/csv" onChange={(e) => { setFile(e.target.files?.[0] ?? null); setError(null); setResult(null); }} /></div>
        {lines ? (
          <div className="banner danger" role="alert"><strong>Nothing was applied. Please fix these lines:</strong>
            <ul>{lines.map((l) => <li key={l}>{l}</li>)}</ul></div>
        ) : <ErrorBox error={error} />}
        {result && <div className="banner info">Updated {result.applied} stock lines. {result.rerouted} waiting order{result.rerouted === 1 ? "" : "s"} sent to a store.</div>}
        <button className="btn" disabled={!file || busy} onClick={upload}>{busy ? "Uploading…" : "Upload stock file"}</button>
      </div>
      <div className="card">
        <h2>Refill reminders</h2>
        <p className="muted small">In production this runs once a day on its own. Run it now to see the messages customers would get. Each refill is reminded once, and not while an order for it is already open.</p>
        <ErrorBox error={remErr} />
        {rem && <div className="banner info">{rem.sent} reminder{rem.sent === 1 ? "" : "s"} sent.</div>}
        <button className="btn secondary" onClick={runReminders}>Run reminders now</button>
      </div>
    </>
  );
}
