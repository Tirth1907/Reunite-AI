import { createRoot } from "react-dom/client";
import App from "@/app/App";
import "./styles/index.css";
import { AuthProvider } from "./app/context/AuthContext";

createRoot(document.getElementById("root")!).render(
  <AuthProvider>
    <App />
  </AuthProvider>
);
