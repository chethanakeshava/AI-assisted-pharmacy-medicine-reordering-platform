import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import { Empty, ErrorBox, ScheduleBadge, Spinner } from "../components/ui";
import { formatINR, INVOICE_RE, waitingLabel } from "../lib/format";

const TABS = [["APPROVED", "To pack"], ["PACKED", "Ready for handover"], ["DISPATCHED", "Handed over"]];

export default function StoreHome() {
  const { user } = useAuth();
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("APPROVED");
  const load = useCallback(() => api.get("/store/orders").then((r) => { setOrders(r); setError(null); }).catch(setError), []);
  useEffect(() => { load(); const t = setInterval(load, 20000); return () => clearInterval(t); }, [load]);

  const shown = orders?.filter((o) => o.status === tab) ?? [];
  const count = (s) => orders?.filter((o) => o.status === s).length ?? 0;

  return (
    <>
      <h1>{user.store_name} store</h1>
      <p className="sub">Pick, pack and hand over approved orders. Only pharmacist-approved items appear here.</p>
      <div className="row" role="tablist" style={{ marginBottom: "1rem" }}>
        {TABS.map(([s, label]) => (
          <button key={s} role="tab" aria-selected={tab === s} className={`btn small ${tab === s ? "" : "secondary"}`} onClick={() => setTab(s)}>{label} ({count(s)})</button>
        ))}
      </div>
      <ErrorBox error={error} onRetry={load} />
      {!orders && !error && <Spinner />}
      {orders && shown.length === 0 && <Empty title="Nothing here">{tab === "APPROVED" ? "New approved orders will show up here." : "No orders in this step."}</Empty>}
      {shown.map((o) => <StoreOrder key={o.id} o={o} onChange={load} />)}
    </>
  );
}

function StoreOrder({ o, onChange }) {
  const [picked, setPicked] = useState({});
  const [invoice, setInvoice] = useState("");
  const [handed, setHanded] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const run = async (fn) => { setBusy(true); setError(null); try { await fn(); await onChange(); } catch (e) { setError(e); } finally { setBusy(false); } };
  const allPicked = o.items.every((i) => picked[i.id]);

  return (
    <div className="card">
      <div className="row between">
        <div><strong>{o.code}</strong> <span className="muted small">· {o.customer}</span>
          <div className="muted small">Placed {waitingLabel(o.created_at)} ago{o.distance_km != null && ` · ${o.distance_km} km from customer`}</div></div>
        {o.invoice_no && <span className="badge">Invoice {o.invoice_no}</span>}
        <span className={`badge ${o.payment_method === "COD" ? "warn" : "ok"}`}>{o.payment_method === "COD" ? `Collect ${formatINR(o.total)} on delivery` : o.payment_status === "PAID_TEST" ? "Paid online (test)" : "UPI payment pending"}</span>
      </div>
      <div style={{ margin: ".6rem 0" }}>
        {o.items.map((i) => (
          <label key={i.id} className="list-item" style={{ margin: 0, fontWeight: 400, cursor: o.status === "APPROVED" ? "pointer" : "default" }}>
            <span>
              {o.status === "APPROVED" && <input type="checkbox" checked={!!picked[i.id]} onChange={(e) => setPicked({ ...picked, [i.id]: e.target.checked })} style={{ marginRight: ".6rem", width: 20, height: 20 }} />}
              <strong>{i.product_name}</strong> <ScheduleBadge schedule={i.schedule} />
              <span className="muted small"> · {i.pack} × {i.qty}</span>
            </span>
          </label>
        ))}
      </div>
      <ErrorBox error={error} />
      {o.status === "APPROVED" && (
        <div className="field">
          <label htmlFor={`inv${o.id}`}>Store invoice number</label>
          <div className="row">
            <input id={`inv${o.id}`} type="text" style={{ maxWidth: 240 }} value={invoice} onChange={(e) => setInvoice(e.target.value.trim())} placeholder="e.g. SL/2026/0412" />
            <button className="btn" disabled={!allPicked || !INVOICE_RE.test(invoice) || busy}
              onClick={() => run(() => api.post(`/store/orders/${o.id}/pack`, { invoice_no: invoice }))}>{busy ? "Saving…" : "Mark packed"}</button>
          </div>
          <p className="small muted" style={{ margin: ".4rem 0 0" }}>{!allPicked ? "Tick every item once it is picked." : !INVOICE_RE.test(invoice) ? "Use 3–30 letters, numbers, / or -." : ""}</p>
        </div>
      )}
      {o.status === "PACKED" && (
        <div className="field">
          <label htmlFor={`h${o.id}`}>Handed to (delivery person)</label>
          <div className="row">
            <input id={`h${o.id}`} type="text" style={{ maxWidth: 240 }} value={handed} onChange={(e) => setHanded(e.target.value)} />
            <button className="btn" disabled={handed.trim().length < 2 || busy}
              onClick={() => run(() => api.post(`/store/orders/${o.id}/handover`, { handed_to: handed.trim() }))}>{busy ? "Saving…" : "Hand over"}</button>
          </div>
        </div>
      )}
      {o.status === "DISPATCHED" && <p className="small muted" style={{ margin: 0 }}>Handed to {o.handover_to}.</p>}
    </div>
  );
}
