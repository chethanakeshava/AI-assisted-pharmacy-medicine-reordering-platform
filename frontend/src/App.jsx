import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import { Layout, Spinner } from "./components/ui";
import Cart from "./pages/Cart";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Orders, { OrderDetail } from "./pages/Orders";
import Queue from "./pages/Queue";
import StoreHome from "./pages/StoreHome";
import Upload from "./pages/Upload";

const HOME = { customer: "/", pharmacist: "/pharmacist", store_staff: "/store" };

function Guard({ role, wide, children }) {
  const { user, loading } = useAuth();
  if (loading) return <Spinner label="Signing you in…" />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={HOME[user.role]} replace />;
  return <Layout wide={wide}>{children}</Layout>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Guard role="customer"><Home /></Guard>} />
      <Route path="/upload" element={<Guard role="customer"><Upload /></Guard>} />
      <Route path="/cart" element={<Guard role="customer"><Cart /></Guard>} />
      <Route path="/orders" element={<Guard role="customer"><Orders /></Guard>} />
      <Route path="/orders/:id" element={<Guard role="customer"><OrderDetail /></Guard>} />
      <Route path="/pharmacist" element={<Guard role="pharmacist" wide><Queue /></Guard>} />
      <Route path="/store" element={<Guard role="store_staff"><StoreHome /></Guard>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
