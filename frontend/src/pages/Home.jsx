import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { useCart } from "../cart";
import { Empty, ErrorBox, Spinner, StatusBadge } from "../components/ui";
import { useT } from "../i18n";
import { REORDERABLE, refillText } from "../lib/format";

export default function Home() {
  const { user } = useAuth();
  const { t } = useT();
  const cart = useCart();
  const nav = useNavigate();
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [refills, setRefills] = useState([]);

  const load = useCallback(() => {
    setError(null);
    api.get("/orders").then(setOrders).catch(setError);
  }, []);
  useEffect(load, [load]);
  useEffect(() => { api.get("/refills").then(setRefills).catch(() => {}); }, []);
  const due = refills.filter((r) => r.state === "due");
  useEffect(() => { if (!cart.profileId && user?.profiles?.length) cart.setProfileId(user.profiles[0].id); }, [user]); // eslint-disable-line

  const last = orders?.find((o) => REORDERABLE.includes(o.status));

  const reorder = async () => {
    setBusy(true); setError(null);
    try { nav(`/orders/${(await api.post(`/orders/${last.id}/reorder`)).id}`); }
    catch (e) { setError(e); setBusy(false); }
  };

  return (
    <>
      <h1>{t("home.hello", { name: user.name.split(" ")[0] })}</h1>
      {user.profiles.length > 1 && (
        <div className="field" style={{ maxWidth: 360 }}>
          <label htmlFor="who">{t("home.orderingFor")}</label>
          <select id="who" value={cart.profileId ?? ""} onChange={(e) => cart.setProfileId(Number(e.target.value))}>
            {user.profiles.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>
      )}
      <ErrorBox error={error} onRetry={load} />
      {!orders && !error && <Spinner />}
      {orders && (
        <>
          <div className="card">
            {last ? (
              <>
                <h2>{t("home.lastOrder")}</h2>
                <p className="muted">{last.items.map((i) => `${i.product_name} × ${i.qty}`).join(", ")}</p>
                <button className="btn hero" onClick={reorder} disabled={busy}>{busy ? "…" : t("home.reorder")}</button>
                <p className="small muted" style={{ margin: ".6rem 0 0" }}>{t("home.checkNote")}</p>
              </>
            ) : (
              <>
                <h2>{t("home.startFirst")}</h2>
                <p className="muted">{t("home.startFirstSub")}</p>
                <Link to="/upload" className="btn hero" style={{ display: "block", textAlign: "center", textDecoration: "none" }}>{t("home.uploadRx")}</Link>
              </>
            )}
          </div>
          {due.length > 0 && (
            <Link to="/refills" className="banner warn" style={{ display: "block", textDecoration: "none", color: "inherit" }}>
              <strong>{due.length === 1 ? "A refill is due" : `${due.length} refills are due`}</strong>
              <div className="small">{due.map((r) => `${r.product_name}: ${refillText(r).toLowerCase()}`).join(" · ")}</div>
            </Link>
          )}
          <div className="row" style={{ marginBottom: "1.5rem" }}>
            {last && <Link to="/upload" className="btn secondary">{t("home.uploadNew")}</Link>}
            <Link to="/cart" className="btn secondary">{t("home.search")}</Link>
          </div>
          <h2>{t("home.recent")}</h2>
          {orders.length === 0 ? <Empty title="No orders yet">Your orders will appear here.</Empty> : (
            <div className="card">
              {orders.slice(0, 3).map((o) => (
                <Link key={o.id} to={`/orders/${o.id}`} className="list-item">
                  <span><strong>{o.code}</strong><br /><span className="muted small">{o.items.map((i) => i.product_name).join(", ")}</span></span>
                  <StatusBadge status={o.status} />
                </Link>
              ))}
              {orders.length > 3 && <p style={{ margin: ".6rem 0 0" }}><Link to="/orders">See all orders</Link></p>}
            </div>
          )}
        </>
      )}
    </>
  );
}
