import { Navigate } from "react-router";

export default function RegisterPage() {
  // Redirect to login - we handle both in login.tsx
  return <Navigate to="/api/login" replace />;
}