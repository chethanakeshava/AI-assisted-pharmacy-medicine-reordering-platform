import { createContext, useContext, useState } from "react";

const Ctx = createContext(null);
export const useCart = () => useContext(Ctx);

// Cart lives in memory only: it is a draft until the order is placed.
export function CartProvider({ children }) {
  const [items, setItems] = useState([]);        // {product_id, name, pack, price, schedule, qty, needs_check}
  const [prescriptionId, setPrescriptionId] = useState(null);
  const [profileId, setProfileId] = useState(null);
  const [notice, setNotice] = useState("");

  const add = (p) => setItems((cur) => (cur.some((i) => i.product_id === p.product_id) ? cur : [...cur, { qty: "", ...p }]));
  const setQty = (id, qty) => setItems((cur) => cur.map((i) => (i.product_id === id ? { ...i, qty } : i)));
  const remove = (id) => setItems((cur) => cur.filter((i) => i.product_id !== id));
  const clear = () => { setItems([]); setPrescriptionId(null); setNotice(""); };

  return (
    <Ctx.Provider value={{ items, setItems, add, setQty, remove, clear, prescriptionId, setPrescriptionId,
                           profileId, setProfileId, notice, setNotice }}>
      {children}
    </Ctx.Provider>
  );
}
