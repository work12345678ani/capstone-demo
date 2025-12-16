import { useState } from "react";
import { useNavigate } from "react-router";
import type { Route } from "./+types/_auth.login";

const API_BASE = "http://localhost:5173";

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async () => {
    setError("");
    const endpoint = isLogin ? "/api/login" : "/api/register";
    const body = isLogin ? { email, password } : { username, email, password };

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.message || "Authentication failed");
      }

      navigate("/");
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        <h2 className="text-center text-3xl font-bold text-gray-900 dark:text-white">
          {isLogin ? "Sign in" : "Create account"}
        </h2>

        <div className="space-y-4">
          {!isLogin && (
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              placeholder="Username"
              name="username"
            />
          )}
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="Email"
            name="email"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="Password"
            name="password"
          />
        </div>

        {error && <div className="text-red-600 text-sm text-center">{error}</div>}

        <button
          onClick={handleSubmit}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-md"
        >
          {isLogin ? "Sign in" : "Register"}
        </button>

        <button
          onClick={() => setIsLogin(!isLogin)}
          className="w-full text-blue-600 dark:text-blue-400 text-sm hover:underline"
        >
          {isLogin ? "Need an account? Register" : "Already have an account? Sign in"}
        </button>
      </div>
    </div>
  );
}
