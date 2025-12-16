import { Outlet, Navigate } from "react-router";
import { isAuthenticated } from "~/lib/auth";

export async function clientLoader() {
  const auth = await isAuthenticated();
  if (auth) {
    throw new Response(null, {
      status: 302,
      headers: { Location: "/" },
    });
  }
  return null;
}

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Outlet />
    </div>
  );
}
