export const formatINR = (n) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n ?? 0);

export const STATUS = {
  AWAITING_PHARMACIST: { label: "Pharmacist is checking", tone: "warn" },
  ON_HOLD: { label: "Needs a new photo", tone: "danger" },
  APPROVED: { label: "Approved", tone: "ok" },
  PACKED: { label: "Packed", tone: "ok" },
  DISPATCHED: { label: "On the way", tone: "ok" },
  REJECTED: { label: "Not approved", tone: "danger" },
};

export const REORDERABLE = ["APPROVED", "PACKED", "DISPATCHED"];

const STEPS = ["Order placed", "Pharmacist check", "Approved", "Packed", "On the way"];
// index of the step that is happening now (steps before it are done)
const CURRENT = { AWAITING_PHARMACIST: 1, ON_HOLD: 1, APPROVED: 3, PACKED: 4, DISPATCHED: 5 };

export function timeline(status) {
  const cur = CURRENT[status] ?? 1;
  return STEPS.map((label, i) => ({
    label,
    state: i < cur ? "done" : i === cur ? (status === "ON_HOLD" ? "blocked" : "current") : "todo",
  }));
}

export const isQtyValid = (q) => Number.isInteger(q) && q >= 1 && q <= 20;

export function waitingLabel(iso, now = Date.now()) {
  const mins = Math.max(0, Math.round((now - new Date(iso).getTime()) / 60000));
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min`;
  const h = Math.floor(mins / 60);
  return h < 24 ? `${h} h` : `${Math.floor(h / 24)} d`;
}
