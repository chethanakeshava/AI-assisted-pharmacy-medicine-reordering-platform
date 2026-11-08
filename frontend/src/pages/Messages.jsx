import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { Empty, ErrorBox, Spinner } from "../components/ui";

export default function Messages() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);
  const load = useCallback(() => { setError(null); api.get("/notifications").then(setRows).catch(setError); }, []);
  useEffect(load, [load]);
  return (
    <>
      <h1>Messages</h1>
      <p className="sub">Test mode: these are the text messages we would send to your phone.</p>
      <ErrorBox error={error} onRetry={load} />
      {!rows && !error && <Spinner />}
      {rows && rows.length === 0 && <Empty title="No messages yet">Order updates and refill reminders will appear here.</Empty>}
      {rows && rows.length > 0 && (
        <div className="card">
          {rows.map((n) => (
            <div key={n.id} className="list-item" style={{ display: "block" }}>
              <div className="small muted">{new Date(n.created_at).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })} · SMS</div>
              <div>{n.body}</div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
