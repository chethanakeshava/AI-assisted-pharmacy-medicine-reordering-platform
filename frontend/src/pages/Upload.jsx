import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useCart } from "../cart";
import { ErrorBox } from "../components/ui";

export default function Upload() {
  const nav = useNavigate();
  const cart = useCart();
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!file) { setPreview(null); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const submit = async () => {
    setBusy(true); setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      if (cart.profileId) form.append("profile_id", cart.profileId);
      const rx = await api.upload("/prescriptions", form);
      const sug = await api.get(`/prescriptions/${rx.id}/suggestions`);
      cart.clear();
      cart.setPrescriptionId(rx.id);
      cart.setItems(sug.items.map((i) => ({ ...i, qty: i.qty ?? "" })));
      cart.setNotice(sug.items.length
        ? "We read your prescription. Please check each medicine and quantity."
        : "We couldn't read the medicines automatically. Add them below; the pharmacist will check against your photo.");
      nav("/cart");
    } catch (e) { setError(e); setBusy(false); }
  };

  const unreadable = error?.detail?.code === "unreadable_image";

  return (
    <>
      <h1>Upload your prescription</h1>
      <p className="sub">Take a clear photo of the whole page. Only our pharmacists can see it.</p>
      <div className="card">
        <div className="field">
          <label htmlFor="rx">Photo of prescription</label>
          <input id="rx" type="file" accept="image/jpeg,image/png,image/webp" capture="environment"
            onChange={(e) => { setFile(e.target.files?.[0] ?? null); setError(null); }} disabled={busy} />
        </div>
        {preview && <img src={preview} alt="Your prescription preview" className="rx-img" style={{ marginBottom: "1rem" }} />}
        {unreadable ? (
          <div className="banner warn" role="alert">
            <strong>This photo is hard to read.</strong>
            <ul>{error.detail.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
            <p style={{ margin: ".5rem 0 0" }}>To get a better photo:</p>
            <ul>{error.detail.tips.map((t) => <li key={t}>{t}</li>)}</ul>
          </div>
        ) : <ErrorBox error={error} />}
        <button className="btn hero" disabled={!file || busy || unreadable} onClick={submit}>
          {busy ? "Reading your prescription…" : unreadable ? "Choose a clearer photo above" : "Continue"}
        </button>
      </div>
    </>
  );
}
