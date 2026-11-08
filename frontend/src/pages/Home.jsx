import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { useCart } from "../cart";
import { Empty, ErrorBox, Spinner, StatusBadge } from "../components/ui";
import { REORDERABLE } from "../lib/format";

export default function Home() {
  const { user } = useAuth();
  const cart = useCart();
  const nav = useNavigate();
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    setError(null);
    api.get("/orders").then(setOrders).catch(setError);
  }, []);
  useEffect(load, [load]);
  useEffect(() => { if (!cart.profileId && user?.profiles?.length) cart.setProfileId(user.profiles[0].id); }, [user]); // eslint-disable-line

  const last = orders?.find((o) => REORDERABLE.includes(o.status));

  const reorder = async () => {
    setBusy(true); setError(null);
    try { nav(`/orders/${(await api.post(`/orders/${last.id}/reorder`)).id}`); }
    catch (e) { setError(e); setBusy(false); }
  };

  return (
    <>
      <h1>Hello, {user.name.split(" ")[0]}</h1>
      {user.profiles.length > 1 && (
        <div className="field" style={{ maxWidth: 360 }}>
          <label htmlFor="who">Ordering for</label>
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
                <h2>Your last order</h2>
                <p className="muted">{last.items.map((i) => `${i.product_name} × ${i.qty}`).join(", ")}</p>
                <button className="btn hero" onClick={reorder} disabled={busy}>{busy ? "Placing…" : "Reorder"}</button>
                <p className="small muted" style={{ margin: ".6rem 0 0" }}>A pharmacist checks every order before it is sent.</p>
              </>
            ) : (
              <>
                <h2>Start your first refill</h2>
                <p className="muted">Upload a photo of your prescription. We will read it and a pharmacist will check it.</p>
                <Link to="/upload" className="btn hero" style={{ display: "block", textAlign: "center", textDecoration: "none" }}>Upload prescription</Link>
              </>
            )}
          </div>
          <div className="row" style={{ marginBottom: "1.5rem" }}>
            {last && <Link to="/upload" className="btn secondary">Upload a new prescription</Link>}
            <Link to="/cart" className="btn secondary">Search medicines</Link>
          </div>
          <h2>Recent orders</h2>
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
