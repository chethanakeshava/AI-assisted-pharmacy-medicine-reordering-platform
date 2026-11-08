import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { Empty, ErrorBox, ProductPicker, ScheduleBadge, Spinner, StatusBadge, useBlobUrl } from "../components/ui";
import { formatINR, waitingLabel } from "../lib/format";

export default function Queue() {
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState(null);
  const [sel, setSel] = useState(null);

  const load = useCallback(() => {
    return api.get("/pharmacist/queue").then((r) => { setOrders(r); setError(null); setSel((s) => s ?? r[0]?.id ?? null); }).catch(setError);
  }, []);
  useEffect(() => { load(); const t = setInterval(load, 20000); return () => clearInterval(t); }, [load]);

  const current = orders?.find((o) => o.id === sel);
  const needsAttention = (o) => o.ai_draft && (o.ai_draft.readable === false || o.ai_draft.source === "failed" || o.ai_draft.items.some((i) => i.low_confidence));

  return (
    <>
      <h1>Verification queue</h1>
      <p className="sub">Compare the prescription with the items. Nothing is sent until you approve it. Every view of a prescription is logged.</p>
      <ErrorBox error={error} onRetry={load} />
      {!orders && !error && <Spinner />}
      {orders && orders.length === 0 && <Empty title="Queue is clear">New orders will appear here.</Empty>}
      {orders && orders.length > 0 && (
        <div className="queue">
          <div>
            {orders.map((o) => (
              <button key={o.id} className={`q-item ${o.id === sel ? "sel" : ""}`} onClick={() => setSel(o.id)}>
                <div className="row between"><strong>{o.code}</strong><span className="muted small">{waitingLabel(o.created_at)}</span></div>
                <div className="small muted">{o.customer} · {o.items.length} item{o.items.length > 1 ? "s" : ""}</div>
                <div style={{ marginTop: ".3rem" }}>
                  <StatusBadge status={o.status} />{" "}
                  {needsAttention(o) && o.status === "AWAITING_PHARMACIST" && <span className="badge warn">AI unsure</span>}
                </div>
              </button>
            ))}
          </div>
          {current && <OrderReview key={current.id} order={current} onChange={load} />}
        </div>
      )}
    </>
  );
}

function OrderReview({ order, onChange }) {
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [reuploadReason, setReuploadReason] = useState(null);
  const [adding, setAdding] = useState(false);
  const rx = useBlobUrl(order.prescription_id ? `/prescriptions/${order.prescription_id}/image` : null);
  const open = order.status === "AWAITING_PHARMACIST";
  const undecided = order.items.some((i) => i.status === "PENDING");

  const act = async (fn) => {
    setBusy(true); setError(null);
    try { await fn(); await onChange(); } catch (e) { setError(e); } finally { setBusy(false); }
  };
  const base = `/pharmacist/orders/${order.id}`;

  return (
    <div>
      <div className="row between"><h2>{order.code} <span className="muted small">· {order.customer}</span></h2><StatusBadge status={order.status} /></div>
      {order.status === "ON_HOLD" && <div className="banner warn">Waiting for the customer to upload a new photo.</div>}
      <ErrorBox error={error} />
      <div className="compare">
        <div className="card">
          <h2>Prescription</h2>
          {rx.loading && <Spinner label="Opening image…" />}
          {rx.error && <ErrorBox error={rx.error} />}
          {!order.prescription_id && <p className="muted">No prescription attached.</p>}
          {rx.url && <img className="rx-img" src={rx.url} alt={`Prescription for order ${order.code}`} />}
          <AiDraft draft={order.ai_draft} />
        </div>
        <div className="card">
          <h2>Items to verify</h2>
          {order.items.map((i) => (
            <ItemRow key={i.id} item={i} open={open && !busy} base={base} act={act} setError={setError} />
          ))}
          <div className="row between small muted"><span>Total (not rejected)</span><strong style={{ color: "var(--ink)" }}>{formatINR(order.total)}</strong></div>
          {open && (
            <div className="stack" style={{ marginTop: "1rem" }}>
              {adding ? (
                <div>
                  <ProductPicker label="Add a medicine from the catalogue" onPick={(p) => act(async () => { await api.post(`${base}/items`, { product_id: p.product_id, qty: 1 }); setAdding(false); })} />
                  <button className="btn secondary small" onClick={() => setAdding(false)}>Cancel</button>
                </div>
              ) : <button className="btn secondary small" onClick={() => setAdding(true)}>Add a medicine</button>}
              {reuploadReason === null ? (
                <button className="btn danger small" onClick={() => setReuploadReason("")}>Ask for a new photo</button>
              ) : (
                <div className="field">
                  <label htmlFor="rr">Why is a new photo needed?</label>
                  <input id="rr" type="text" value={reuploadReason} onChange={(e) => setReuploadReason(e.target.value)} placeholder="e.g. Dose is not readable" />
                  <div className="row" style={{ marginTop: ".5rem" }}>
                    <button className="btn danger small" disabled={reuploadReason.trim().length < 3 || busy} onClick={() => act(() => api.post(`${base}/reupload`, { reason: reuploadReason.trim() }))}>Send request</button>
                    <button className="btn secondary small" onClick={() => setReuploadReason(null)}>Cancel</button>
                  </div>
                </div>
              )}
              <button className="btn" disabled={undecided || busy} onClick={() => act(() => api.post(`${base}/finalize`))}>Finish review</button>
              {undecided && <p className="small muted" style={{ margin: 0 }}>Approve or reject every item to finish.</p>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AiDraft({ draft }) {
  if (!draft) return null;
  return (
    <div style={{ marginTop: "1rem" }}>
      <h2>What the AI read <span className="badge">draft only</span></h2>
      {draft.source === "failed" && <div className="banner warn small">The AI could not read this image. Please enter items manually.</div>}
      {draft.readable === false && <div className="banner warn small">The AI could not read this prescription.{draft.notes && ` ${draft.notes}`}</div>}
      {draft.items.length === 0 && draft.source !== "failed" && draft.readable !== false && <p className="muted small">No items detected.</p>}
      {draft.items.map((i, idx) => (
        <div key={idx} className={`list-item ${i.low_confidence ? "ai-low" : ""}`} style={{ padding: ".5rem .4rem" }}>
          <span className="small">
            <strong>{i.raw_name}</strong> {i.strength} {i.qty ? `× ${i.qty}` : "· quantity not read"}
            <br /><span className="muted">{i.product_name ? `Matched: ${i.product_name}` : "No catalogue match"}</span>
            {i.blocked && <><br /><span className="badge danger">Cannot be sold online</span></>}
            {i.generic_options.map((g) => (
              <span key={g.product_id} className="muted" style={{ display: "block" }}>Generic: {g.name}, saves ₹{g.saving}. Needs your approval and the customer's consent; not applied.</span>
            ))}
          </span>
          <span className={`badge ${i.low_confidence ? "warn" : "ok"}`}>{Math.round(i.confidence * 100)}%{i.low_confidence ? " · check" : ""}</span>
        </div>
      ))}
    </div>
  );
}

function ItemRow({ item, open, base, act, setError }) {
  const [mode, setMode] = useState(null); // null | edit | reject | h1
  const [qty, setQty] = useState(item.qty);
  const [reason, setReason] = useState("");
  const [h1, setH1] = useState({ patient_name: "", prescriber_name: "", prescriber_reg_no: "" });
  const pending = item.status === "PENDING";
  const done = () => setMode(null);
  const valid = (v) => v.trim().length >= 2;

  return (
    <div className="list-item" style={{ display: "block" }}>
      <div className="row between">
        <span><strong>{item.product_name}</strong> <ScheduleBadge schedule={item.schedule} /><br /><span className="muted small">{item.pack} × {item.qty}</span></span>
        {item.status === "APPROVED" && <span className="badge ok">Approved</span>}
        {item.status === "REJECTED" && <span className="badge danger">Rejected</span>}
      </div>
      {item.status === "REJECTED" && <p className="small muted" style={{ margin: ".3rem 0 0" }}>Reason: {item.reject_reason}</p>}
      {pending && open && mode === null && (
        <div className="row" style={{ marginTop: ".5rem" }}>
          <button className="btn small" onClick={() => (item.schedule === "H1" ? setMode("h1") : act(() => api.post(`${base}/items/${item.id}/approve`)))}>Approve</button>
          <button className="btn secondary small" onClick={() => setMode("edit")}>Edit</button>
          <button className="btn danger small" onClick={() => setMode("reject")}>Reject</button>
        </div>
      )}
      {mode === "edit" && (
        <div className="stack" style={{ marginTop: ".6rem" }}>
          <div className="field"><label htmlFor={`q${item.id}`}>Packs</label>
            <input id={`q${item.id}`} className="qty" type="number" min="1" max="20" value={qty} onChange={(e) => setQty(Number(e.target.value))} /></div>
          <ProductPicker label="Change medicine (optional)" onPick={(p) => act(async () => { await api.patch(`${base}/items/${item.id}`, { product_id: p.product_id, qty }); done(); })} />
          <div className="row">
            <button className="btn small" onClick={() => act(async () => { await api.patch(`${base}/items/${item.id}`, { qty }); done(); })}>Save quantity</button>
            <button className="btn secondary small" onClick={done}>Cancel</button>
          </div>
        </div>
      )}
      {mode === "reject" && (
        <div className="field" style={{ marginTop: ".6rem" }}>
          <label htmlFor={`r${item.id}`}>Reason (required)</label>
          <input id={`r${item.id}`} type="text" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. Not on the prescription" />
          <div className="row" style={{ marginTop: ".5rem" }}>
            <button className="btn danger small" disabled={reason.trim().length < 3} onClick={() => act(async () => { await api.post(`${base}/items/${item.id}/reject`, { reason: reason.trim() }); done(); })}>Reject item</button>
            <button className="btn secondary small" onClick={done}>Cancel</button>
          </div>
        </div>
      )}
      {mode === "h1" && (
        <div className="stack" style={{ marginTop: ".6rem" }}>
          <div className="banner info small">Schedule H1: record these details in the H1 register.</div>
          {[["patient_name", "Patient name"], ["prescriber_name", "Prescriber name"], ["prescriber_reg_no", "Prescriber registration no."]].map(([k, label]) => (
            <div className="field" key={k}><label htmlFor={`${k}${item.id}`}>{label}</label>
              <input id={`${k}${item.id}`} type="text" value={h1[k]} onChange={(e) => setH1({ ...h1, [k]: e.target.value })} /></div>
          ))}
          <div className="row">
            <button className="btn small" disabled={!Object.values(h1).every(valid)} onClick={() => act(async () => { await api.post(`${base}/items/${item.id}/approve`, { h1 }); done(); })}>Approve and log</button>
            <button className="btn secondary small" onClick={done}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}
