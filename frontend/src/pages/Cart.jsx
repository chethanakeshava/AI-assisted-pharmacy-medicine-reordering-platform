import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useCart } from "../cart";
import { ErrorBox, ProductPicker, ScheduleBadge } from "../components/ui";
import { useT } from "../i18n";
import { formatINR, isQtyValid } from "../lib/format";

const GATED = ["H", "H1"];

export default function Cart() {
  const cart = useCart();
  const nav = useNavigate();
  const { t } = useT();
  const [method, setMethod] = useState("COD");
  const [earlier, setEarlier] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => { api.get("/prescriptions").then((r) => setEarlier(r.filter((x) => x.status !== "REUPLOAD" && x.status !== "REJECTED"))).catch(() => {}); }, []);

  const needsRx = cart.items.some((i) => GATED.includes(i.schedule));
  const missingRx = needsRx && !cart.prescriptionId;
  const allQty = cart.items.length > 0 && cart.items.every((i) => isQtyValid(i.qty));
  const total = cart.items.reduce((s, i) => s + (isQtyValid(i.qty) ? i.qty * i.price : 0), 0);

  const place = async () => {
    setBusy(true); setError(null);
    try {
      const o = await api.post("/orders", {
        profile_id: cart.profileId, prescription_id: cart.prescriptionId, payment_method: method,
        items: cart.items.map((i) => ({ product_id: i.product_id, qty: i.qty })),
      });
      cart.clear();
      nav(`/orders/${o.id}`);
    } catch (e) { setError(e); setBusy(false); }
  };

  return (
    <>
      <h1>{t("cart.title")}</h1>
      <p className="sub">{t("cart.sub")}</p>
      {cart.notice && <div className="banner info">{cart.notice}</div>}

      <div className="card">
        {cart.items.length === 0 ? (
          <p className="muted" style={{ margin: 0 }}>Nothing added yet. Search for a medicine below, or <Link to="/upload">upload a prescription</Link>.</p>
        ) : (
          <table className="items-table">
            <thead><tr><th>Medicine</th><th>{t("cart.packs")}</th><th></th></tr></thead>
            <tbody>
              {cart.items.map((i) => (
                <tr key={i.product_id}>
                  <td>
                    <strong>{i.name}</strong> <ScheduleBadge schedule={i.schedule} />
                    <div className="muted small">{i.pack} · {formatINR(i.price)} each</div>
                    {i.needs_check && <div className="small" style={{ color: "var(--warn)" }}>We weren't sure about this one. Please check.</div>}
                  </td>
                  <td>
                    <input className="qty" type="number" min="1" max="20" inputMode="numeric" aria-label={`Packs of ${i.name}`}
                      value={i.qty} onChange={(e) => cart.setQty(i.product_id, e.target.value === "" ? "" : Number(e.target.value))} />
                    {!isQtyValid(i.qty) && <div className="small" style={{ color: "var(--danger)" }}>1–20</div>}
                  </td>
                  <td><button className="btn secondary small" onClick={() => cart.remove(i.product_id)} aria-label={`Remove ${i.name}`}>Remove</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card"><ProductPicker onPick={(p) => cart.add(p)} label="Add a medicine" /></div>

      {needsRx && (
        <div className="card">
          <h2>Prescription</h2>
          {cart.prescriptionId ? <p className="muted" style={{ margin: 0 }}>Prescription attached. <Link to="/upload">Use a different photo</Link></p> : (
            <>
              <div className="banner warn">These medicines need a prescription.</div>
              {earlier.length > 0 && (
                <div className="field">
                  <label htmlFor="earlier">Use a prescription you uploaded before</label>
                  <select id="earlier" value="" onChange={(e) => cart.setPrescriptionId(Number(e.target.value))}>
                    <option value="">Choose…</option>
                    {earlier.map((r) => <option key={r.id} value={r.id}>Uploaded {new Date(r.created_at).toLocaleDateString("en-IN")}</option>)}
                  </select>
                </div>
              )}
              <Link to="/upload" className="btn secondary">Upload a new prescription</Link>
            </>
          )}
        </div>
      )}

      <div className="card">
        <h2>{t("cart.payment")}</h2>
        {[["COD", t("cart.cod")], ["UPI_TEST", t("cart.upi")]].map(([v, label]) => (
          <label key={v} className="row" style={{ fontWeight: 400, padding: ".3rem 0", cursor: "pointer" }}>
            <input type="radio" name="pay" value={v} checked={method === v} onChange={() => setMethod(v)} style={{ width: 20, height: 20 }} /> {label}
          </label>
        ))}
        {method === "UPI_TEST" && <p className="small muted" style={{ margin: ".3rem 0 0" }}>You pay after the pharmacist approves, when the final amount is known.</p>}
      </div>
      <ErrorBox error={error} />
      <div className="row between" style={{ marginBottom: ".6rem" }}>
        <span className="muted">{t("cart.total")}</span><strong>{formatINR(total)}</strong>
      </div>
      <button className="btn hero" disabled={!allQty || missingRx || busy} onClick={place}>
        {busy ? "…" : t("cart.place")}
      </button>
      <p className="small muted" style={{ marginTop: ".6rem" }}>
        {missingRx ? "Add a prescription to continue." : !allQty && cart.items.length > 0 ? "Enter a quantity for every medicine." : "Test mode: no real money moves."}
      </p>
    </>
  );
}
