import { useEffect, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { LangSwitch, useT } from "../i18n";
import { STATUS } from "../lib/format";

export const Spinner = ({ label = "Loading…" }) => (
  <div className="center" role="status"><div><div className="spinner" />{label}</div></div>
);

export const Empty = ({ title, children }) => (
  <div className="center"><div><p><strong>{title}</strong></p>{children}</div></div>
);

export const ErrorBox = ({ error, onRetry }) =>
  error ? (
    <div className="banner danger" role="alert">
      {error.message || String(error)}
      {onRetry && <> <button className="btn secondary small" onClick={onRetry}>Try again</button></>}
    </div>
  ) : null;

export const StatusBadge = ({ status }) => {
  const s = STATUS[status] || { label: status, tone: "" };
  return <span className={`badge ${s.tone}`}>{s.label}</span>;
};

export const ScheduleBadge = ({ schedule }) =>
  schedule && schedule !== "OTC" ? <span className="badge sched">Schedule {schedule}</span> : null;

const NAV = {
  customer: [["/", "nav.home"], ["/refills", "nav.refills"], ["/orders", "nav.orders"], ["/messages", "nav.messages"]],
  pharmacist: [["/pharmacist", "Verification queue"], ["/pharmacist/stock", "Stock & reminders"]],
  store_staff: [["/store", "Store orders"]],
  ops: [["/ops", "Dashboard"]],
};

export function Layout({ children, wide }) {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const { t } = useT();
  return (
    <>
      <header className="topbar">
        <div className="topbar-in">
          <Link to="/" className="brand">MediBridge</Link>
          <nav className="nav" aria-label="Main">
            {(NAV[user?.role] || []).map(([to, label]) => (
              <NavLink key={to} to={to} end className={({ isActive }) => (isActive ? "active" : "")}>{t(label)}</NavLink>
            ))}
          </nav>
          <div className="who">
            {user?.role === "customer" && <LangSwitch />}
            {user?.name}
            <button className="btn secondary small" onClick={() => { logout(); nav("/login"); }}>{t("nav.signOut")}</button>
          </div>
        </div>
      </header>
      <main className={`page ${wide ? "wide" : ""}`}>{children}</main>
    </>
  );
}

// Search the catalogue; blocked medicines are shown but cannot be picked.
export function ProductPicker({ onPick, label = "Search medicines" }) {
  const [q, setQ] = useState("");
  const [res, setRes] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (q.trim().length < 2) { setRes(null); return; }
    const t = setTimeout(() => {
      api.get(`/catalog/search?q=${encodeURIComponent(q.trim())}`).then((r) => { setRes(r); setErr(null); }).catch(setErr);
    }, 250);
    return () => clearTimeout(t);
  }, [q]);

  return (
    <div className="field">
      <label htmlFor="psearch">{label}</label>
      <input id="psearch" type="text" value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. Metformin" autoComplete="off" />
      <ErrorBox error={err} />
      {res && (
        <div className="results">
          {res.length === 0 && <div className="center small">No medicine found for “{q}”.</div>}
          {res.map((p) => (
            <button key={p.id} disabled={!p.sellable} onClick={() => { onPick({ product_id: p.id, name: p.name, pack: p.pack, price: p.price, schedule: p.schedule }); setQ(""); setRes(null); }}>
              <span>{p.name} <span className="muted small">· {p.pack}</span> <ScheduleBadge schedule={p.schedule} /></span>
              <span>{p.sellable ? `₹${p.price}` : "Not sold online"}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function useBlobUrl(path) {
  const [state, setState] = useState({ url: null, error: null, loading: !!path });
  useEffect(() => {
    if (!path) { setState({ url: null, error: null, loading: false }); return; }
    let url;
    setState({ url: null, error: null, loading: true });
    api.blob(path).then((b) => {
      url = URL.createObjectURL(b);
      setState({ url, error: null, loading: false });
    }).catch((error) => setState({ url: null, error, loading: false }));
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [path]);
  return state;
}
