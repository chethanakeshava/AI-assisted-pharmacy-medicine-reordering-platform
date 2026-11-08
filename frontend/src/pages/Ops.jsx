import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { ErrorBox, Spinner } from "../components/ui";

const Kpi = ({ label, value, note, tone }) => (
  <div className="card" style={{ marginBottom: 0 }}>
    <div className="muted small">{label}</div>
    <div style={{ fontSize: "1.8rem", fontWeight: 700, color: tone === "bad" ? "var(--danger)" : tone === "good" ? "var(--ok)" : "var(--ink)" }}>{value}</div>
    <div className="small muted">{note}</div>
  </div>
);

export default function Ops() {
  const [days, setDays] = useState(30);
  const [d, setD] = useState(null);
  const [error, setError] = useState(null);
  const load = useCallback(() => { setError(null); api.get(`/dashboard?days=${days}`).then(setD).catch(setError); }, [days]);
  useEffect(() => { setD(null); load(); }, [load]);

  const v = d?.verification;
  const max = Math.max(1, ...(d?.by_store.map((s) => s.orders) ?? [1]));
  const openTotal = d ? Object.values(d.open).reduce((a, b) => a + b, 0) : 0;

  return (
    <>
      <div className="row between">
        <div><h1>All stores</h1><p className="sub">Orders, verification time and rejections across the chain.</p></div>
        <div className="field" style={{ minWidth: 150 }}>
          <label htmlFor="days">Period</label>
          <select id="days" value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value={7}>Last 7 days</option><option value={30}>Last 30 days</option><option value={90}>Last 90 days</option>
          </select>
        </div>
      </div>
      <ErrorBox error={error} onRetry={load} />
      {!d && !error && <Spinner />}
      {d && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", marginBottom: "1rem" }}>
            <Kpi label="Orders" value={d.orders} note={`${openTotal} still open`} />
            <Kpi label="Median verification" value={v.median_minutes == null ? "–" : `${v.median_minutes} min`}
              note={v.within_target_pct == null ? "No data yet" : `${v.within_target_pct}% within ${v.target_minutes} min target`}
              tone={v.median_minutes != null && v.median_minutes <= v.target_minutes ? "good" : "bad"} />
            <Kpi label="Orders rejected" value={d.rejections.rate_pct == null ? "–" : `${d.rejections.rate_pct}%`} note={`${d.rejections.orders} orders`} />
            <Kpi label="Schedule H/H1 sent without approval" value={d.gate_violations} note="Must always be 0" tone={d.gate_violations === 0 ? "good" : "bad"} />
          </div>
          <div className="compare">
            <div className="card">
              <h2>Orders by store</h2>
              {d.by_store.map((s) => (
                <div key={s.store} style={{ margin: ".6rem 0" }}>
                  <div className="row between small"><span>{s.store}</span><span className="muted">{s.orders} orders · {s.median_hours_to_dispatch == null ? "no deliveries" : `${s.median_hours_to_dispatch} h median to dispatch`}</span></div>
                  <div style={{ background: "var(--primary-soft)", borderRadius: 99, height: 10 }} role="img" aria-label={`${s.store}: ${s.orders} orders`}>
                    <div style={{ width: `${(s.orders / max) * 100}%`, background: "var(--primary)", height: 10, borderRadius: 99 }} />
                  </div>
                </div>
              ))}
            </div>
            <div className="card">
              <h2>Why items were rejected</h2>
              {d.rejections.reasons.length === 0 ? <p className="muted">No rejections in this period.</p> : d.rejections.reasons.map((r) => (
                <div key={r.reason} className="list-item"><span>{r.reason}</span><strong>{r.count}</strong></div>
              ))}
              <p className="small muted" style={{ margin: ".8rem 0 0" }}>Prescription images viewed (logged): {d.prescription_views}</p>
            </div>
          </div>
        </>
      )}
    </>
  );
}
