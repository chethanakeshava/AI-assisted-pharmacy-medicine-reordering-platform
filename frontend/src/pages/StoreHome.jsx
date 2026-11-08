import { Empty } from "../components/ui";

// Built next (Day 5): orders routed to this store, with pick, pack, invoice and handover.
export default function StoreHome() {
  return (
    <>
      <h1>Store orders</h1>
      <Empty title="The store screen is being built">Approved orders routed to your store will appear here.</Empty>
    </>
  );
}
