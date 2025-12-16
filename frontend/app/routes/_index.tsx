import { useState, useEffect } from "react";
import { useNavigate, redirect } from "react-router";
import type { Route } from "./+types/_index";
import { isAuthenticated } from "~/lib/auth";
import { useTheme } from "~/lib/theme";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkParse from 'remark-parse';
import remarkRehype from 'remark-rehype';
import rehypeStringify from 'rehype-stringify';



const API_BASE = "http://localhost:5173";

export async function clientLoader() {
  const auth = await isAuthenticated();
  if (!auth) {
    throw redirect("/login");
  }
  return null;
}

export default function ChatPage() {
  const [step, setStep] = useState<"init" | "confirm" | "chat">("init");
  const [interruptData, setInterruptData] = useState<any>(null);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [initialChatData, setInitialChatData] = useState<string | null>(null);
  const [userInput, setUserInput] = useState<any>(null);
  const [showProfile, setShowProfile] = useState(false);
  const [profile, setProfile] = useState<any>(null);

  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const [isFirstMessage, setIsFirstMessage] = useState(true);
  const [initialMessage, setInitialMessage] = useState<string | null>(null);

  const navigate = useNavigate();
  const { isDark, setIsDark } = useTheme();

  const handleInitSubmit = async (name: string, desc: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/get-questions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ name, desc }),
      });

      if (!res.ok) throw new Error("Failed to get questions");

      const data = await res.json();
      setInterruptData(data.interrupt);
      setThreadId(data.thread_id);
      setUserInput({ name, desc });
      setStep("confirm");
    } catch (err) {
      console.error(err);
      alert("Failed to submit. Please try again.");
    }
  };

  const handleConfirm = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ thread_id: threadId, is_valid: true, additional_info: ""}),
      });

      if (!res.ok) throw new Error("Failed to validate");

      const data = await res.json();
      setInitialChatData(data.response);
      console.log(data.response)
      setStep("chat");
    } catch (err) {
      console.error(err);
      alert("Failed to validate. Please try again.");
    }
  };

  const handleCancel = () => {
    setStep("init");
    setInterruptData(null);
    setThreadId(null);
    setUserInput(null);
  };

  const handleClearChat = () => {
    setStep("init");
    setInterruptData(null);
    setThreadId(null);
    setInitialChatData(null);
    setUserInput(null);
    setMessages([]);
    setInitialized(false);
  };

  const fetchProfile = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/me`, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch profile");
      const data = await res.json();
      setProfile(data);
      setShowProfile(true);
    } catch (err) {
      console.error(err);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE}/api/logout`, { method: "POST", credentials: "include" });
      document.cookie = "session_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
      navigate("/login");
    } catch (err) {
      console.error(err);
    }
  };

  const sendMessage = async (userMessage: string, initialResponse: string | null = null) => {
    const newMessages = [...messages, { role: "user", content: userMessage }];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    if (initialResponse) {
      setMessages([...newMessages, { role: "assistant", content: initialResponse }]);
      setInitialMessage(initialResponse);
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/conversation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ 
          message: isFirstMessage? `${initialChatData}\n\n${userMessage}` : userMessage, 
          thread_id: threadId 
        }),
      });
      setIsFirstMessage(false);
      if (!res.ok) throw new Error("Failed to get response");

      const data = await res.json();
      setMessages([...newMessages, { role: "assistant", content: data.response || data.message || data }]);
    } catch (err) {
      console.error(err);
      setMessages([...newMessages, { role: "assistant", content: "Error: Failed to get response" }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = () => {
    if (input.trim() && !loading) {
      sendMessage(input.trim());
    }
  };

  const downloadMarkdown = (content: string) => {
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `message-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
  if (!initialized && initialChatData && step === "chat") {
    // Add both the initial prompt and response to messages immediately
    setMessages([
      { role: "user", content: `Name: ${userInput.name}, Topic: ${userInput.topic}` },
      { role: "assistant", content: initialChatData }
    ]);
    setInitialized(true);
  }
}, [initialized, initialChatData, step, userInput]);


  return (
    <div className="h-screen flex flex-col bg-white dark:bg-gray-900">
      <header className="border-b dark:border-gray-700 p-4">
        <div className="flex justify-between items-center">
          <div>
            {step !== "init" && (
              <button
                onClick={handleClearChat}
                className="px-4 py-2 text-sm bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-md"
              >
                Clear Chat
              </button>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setIsDark(!isDark)}
              className="p-2 rounded-md bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-300 dark:hover:bg-gray-600"
              title="Toggle theme"
            >
              {isDark ? "☀️" : "🌙"}
            </button>
            <button
              onClick={fetchProfile}
              className="p-2 rounded-md bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-300 dark:hover:bg-gray-600"
              title="Profile"
            >
              👤
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-6">
        {step === "init" && <InitForm onSubmit={handleInitSubmit} />}
        {step === "confirm" && (
          <ConfirmPage interrupt={interruptData} onConfirm={handleConfirm} onCancel={handleCancel} />
        )}
        {step === "chat" && (
          <ChatInterface
            messages={messages}
            input={input}
            setInput={setInput}
            loading={loading}
            handleSubmit={handleSubmit}
            downloadMarkdown={downloadMarkdown}
          />
        )}
      </main>

      {showProfile && profile && (
        <ProfileModal
          profile={profile}
          onClose={() => setShowProfile(false)}
          onLogout={handleLogout}
        />
      )}
    </div>
  );
}

// Components

function InitForm({ onSubmit }: { onSubmit: (name: string, topic: string) => void }) {
  const [name, setName] = useState("");
  const [topic, setTopic] = useState("");

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">Start a Conversation</h2>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="Enter name"
            name="name"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Topic</label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="Enter topic"
            name="desc"
          />
        </div>
        <button
          onClick={() => name.trim() && topic.trim() && onSubmit(name, topic)}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-md"
        >
          Continue
        </button>
      </div>
    </div>
  );
}

function ConfirmPage({ interrupt, onConfirm, onCancel }: any) {
  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">{interrupt.name}</h2>
      <p className="mb-6 text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{interrupt.desc}</p>
      <p className="mb-6 text-gray-600 dark:text-gray-400">Is this what you wanted?</p>
      <div className="flex gap-4">
        <button
          onClick={onConfirm}
          className="flex-1 py-2 px-4 bg-green-600 hover:bg-green-700 text-white rounded-md"
        >
          Yes, continue
        </button>
        <button
          onClick={onCancel}
          className="flex-1 py-2 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded-md"
        >
          No, go back
        </button>
      </div>
    </div>
  );
}

function ChatInterface({ messages, input, setInput, loading, handleSubmit, downloadMarkdown }: any) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg: any, idx: number) => (
          <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-3xl rounded-lg p-4 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white"
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="whitespace-pre-wrap flex-1"><Markdown remarkPlugins={[remarkGfm, remarkParse, remarkRehype]} rehypePlugins={[rehypeStringify]}>{msg.content}</Markdown></div>
                {msg.role === "assistant" && (
                  <button
                    onClick={() => downloadMarkdown(msg.content)}
                    className="flex-shrink-0 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-xl"
                    title="Export as Markdown"
                  >
                    ⬇
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 dark:bg-gray-700 rounded-lg p-4">
              <span className="text-gray-600 dark:text-gray-300">Thinking...</span>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t dark:border-gray-700">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            disabled={loading}
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            placeholder="Type your message..."
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !input.trim()}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

function ProfileModal({ profile, onClose, onLogout }: any) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-sm w-full"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Profile</h3>
        <div className="space-y-2 mb-4">
          <p className="text-gray-700 dark:text-gray-300">
            <strong>Username:</strong> {profile.username}
          </p>
          <p className="text-gray-700 dark:text-gray-300">
            <strong>Email:</strong> {profile.email}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onLogout}
            className="flex-1 py-2 px-4 bg-red-600 hover:bg-red-700 text-white rounded-md"
          >
            Logout
          </button>
          <button onClick={onClose} className="flex-1 py-2 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded-md">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
