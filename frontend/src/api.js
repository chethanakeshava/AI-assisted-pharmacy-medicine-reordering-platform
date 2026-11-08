const BASE = import.meta.env.VITE_API_URL || "/api";
const KEY = "medibridge.token";

export const getToken = () => localStorage.getItem(KEY);
export const setToken = (t) => (t ? localStorage.setItem(KEY, t) : localStorage.removeItem(KEY));

export class ApiError extends Error {
  constructor(status, detail) {
    super(messageOf(detail));
    this.status = status;
    this.detail = detail;
  }
}

function messageOf(detail) {
  if (!detail) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join(", ");
  if (detail.reasons) return detail.reasons.join(". ");
  return "Something went wrong. Please try again.";
}

async function request(path, { method = "GET", json, form, blob } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (json) headers["Content-Type"] = "application/json";
  let res;
  try {
    res = await fetch(BASE + path, { method, headers, body: form ?? (json ? JSON.stringify(json) : undefined) });
  } catch {
    throw new ApiError(0, "Can't reach the server. Check your connection and try again.");
  }
  if (res.status === 401 && token) window.dispatchEvent(new Event("auth:expired"));
  if (!res.ok) {
    let detail;
    try { detail = (await res.json()).detail; } catch { /* non-JSON error */ }
    throw new ApiError(res.status, detail);
  }
  return blob ? res.blob() : res.json();
}

export const api = {
  get: (p) => request(p),
  post: (p, json) => request(p, { method: "POST", json }),
  patch: (p, json) => request(p, { method: "PATCH", json }),
  upload: (p, form) => request(p, { method: "POST", form }),
  blob: (p) => request(p, { blob: true }),
};
