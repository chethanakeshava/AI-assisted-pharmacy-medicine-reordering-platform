import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { Empty, ErrorBox, Spinner, StatusBadge, ScheduleBadge } from "../components/ui";
import { formatINR, REORDERABLE, timeline } from "../lib/format";

export default function Orders() {
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState(null);
  const load = useCallback(() => { setError(null); api.get("/orders").then(setOrders).catch(setError); }, []);
  useEffect(load, [load]);
  return (
    <>
      <h1>My orders</h1>
      <ErrorBox error={error} onRetry={load} />
      {!orders && !error && <Spinner />}
      {orders && (orders.length === 0 ? <Empty title="No orders yet"><Link to="/upload">Upload a prescription</Link> to place your first one.</Empty> : (
        <div className="card">
          {orders.map((o) => (
            <Link key={o.id} to={`/orders/${o.id}`} className="list-item">
              <span><strong>{o.code}</strong> <span className="muted small">· {formatINR(o.total)}</span><br />
                <span className="muted small">{o.items.map((i) => `${i.product_name} × ${i.qty}`).join(", ")}</span></span>
              <StatusBadge status={o.status} />
            </Link>
          ))}
        </div>
      ))}
    </>
  );
}

export function OrderDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const [o, setO] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [file, setFile] = useState(null);
  const payNow = async () => {
    setBusy(true); setError(null);
    try { setO(await api.post(`/orders/${id}/pay`)); } catch (e) { setError(e); } finally { setBusy(false); }
  };

  const load = useCallback(() => api.get(`/orders/${id}`).then((r) => { setO(r); setError(null); }).catch(setError), [id]);
  useEffect(() => { load(); const t = setInterval(load, 15000); return () => clearInterval(t); }, [load]);

  const reupload = async () => {
    setBusy(true); setError(null);
    try {
      const form = new FormData(); form.append("file", file);
      setO(await api.upload(`/orders/${id}/reupload`, form)); setFile(null);
    } catch (e) { setError(e); } finally { setBusy(false); }
  };
  const reorder = async () => {
    setBusy(true); setError(null);
    try { nav(`/orders/${(await api.post(`/orders/${id}/reorder`)).id}`); } catch (e) { setError(e); setBusy(false); }
  };

  if (!o) return error ? <ErrorBox error={error} onRetry={load} /> : <Spinner />;
  const rejected = o.items.filter((i) => i.status === "REJECTED");

  return (
    <>
      <p className="small"><Link to="/orders">← All orders</Link></p>
      <div className="row between"><h1>{o.code}</h1><StatusBadge status={o.status} /></div>
      <ErrorBox error={error} />

      {o.status === "ON_HOLD" && (
        <div className="banner danger">
          <strong>We need a clearer photo of your prescription.</strong>
          {o.review_note && <p style={{ margin: ".3rem 0 0" }}>{o.review_note}</p>}
          <div className="field" style={{ marginTop: ".8rem" }}>
            <label htmlFor="again">New photo</label>
            <input id="again" type="file" accept="image/jpeg,image/png,image/webp" capture="environment" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </div>
          <button className="btn" disabled={!file || busy} onClick={reupload}>{busy ? "Uploading…" : "Send new photo"}</button>
        </div>
      )}
      {o.status === "NO_STOCK" && <div className="banner warn">Your order is approved. We are finding a store that has all your medicines and will message you.</div>}
      {o.store_name && o.status !== "NO_STOCK" && (
        <div className="banner info">
          {o.status === "DISPATCHED" ? `On its way from ${o.store_name}${o.handover_to ? `, with ${o.handover_to}` : ""}.`
            : `Being prepared at ${o.store_name}${o.distance_km != null ? `, ${o.distance_km} km from you` : ""}.`}
          {o.invoice_no && <> Invoice {o.invoice_no}.</>}
        </div>
      )}
      {o.payment_method === "UPI_TEST" && o.payment_status === "PENDING" && ["APPROVED", "NO_STOCK", "PACKED"].includes(o.status) && (
        <div className="banner info row between">
          <span>Approved. Pay {formatINR(o.total)} by UPI (test mode).</span>
          <button className="btn small" disabled={busy} onClick={payNow}>{busy ? "…" : "Pay now (test)"}</button>
        </div>
      )}
      {o.status === "REJECTED" && <div className="banner danger">This order could not be approved. Please contact your store if you have questions.</div>}

      {o.status !== "REJECTED" && (
        <div className="card">
          <h2>Progress</h2>
          <ol className="timeline">
            {timeline(o.status).map((s) => (
              <li key={s.label} className={s.state}><span className="dot" aria-hidden>{s.state === "done" ? "✓" : s.state === "blocked" ? "!" : ""}</span>{s.label}</li>
            ))}
          </ol>
        </div>
      )}

      <div className="card">
        <h2>Medicines</h2>
        {o.items.map((i) => (
          <div key={i.id} className="list-item">
            <span><strong>{i.product_name}</strong> <ScheduleBadge schedule={i.schedule} /><br />
              <span className="muted small">{i.pack} × {i.qty}</span>
              {i.status === "REJECTED" && <span className="small" style={{ color: "var(--danger)" }}><br />Not approved: {i.reject_reason}</span>}</span>
            <span>{formatINR(i.qty * i.unit_price)}</span>
          </div>
        ))}
        <div className="row between" style={{ marginTop: ".6rem" }}><span className="muted">Total{rejected.length ? " (approved items)" : ""}</span><strong>{formatINR(o.total)}</strong></div>
        <p className="small muted" style={{ margin: ".4rem 0 0" }}>{o.payment_method === "COD" ? "Pay on delivery" : o.payment_status === "PAID_TEST" ? "Paid by UPI (test)" : "UPI payment pending"}</p>
      </div>
      {REORDERABLE.includes(o.status) && <button className="btn secondary" onClick={reorder} disabled={busy}>Order the same again</button>}
    </>
  );
}
