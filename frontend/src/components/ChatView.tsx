import React, { useState } from "react";
import { postChatMessage } from "../lib/api";

interface Message {
  sender: "user" | "ai";
  text: string;
  sources?: string[];
}

const ChatView: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setMessages((msgs) => [...msgs, { sender: "user", text: input }]);
    setLoading(true);
    setError(null);
    try {
      const res = await postChatMessage(input);
      setMessages((msgs) => [
        ...msgs,
        { sender: "ai", text: res.response, sources: res.sources },
      ]);
    } catch (err: any) {
      setError(err.message || "Failed to get response");
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  return (
    <div className="flex flex-col h-full w-full max-w-2xl mx-auto">
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 rounded-t">
        {messages.map((msg, i) => (
          <div key={i} className={msg.sender === "user" ? "text-right" : "text-left"}>
            <div className={msg.sender === "user" ? "inline-block bg-blue-100 text-blue-900 px-3 py-2 rounded-lg" : "inline-block bg-gray-200 text-gray-900 px-3 py-2 rounded-lg"}>
              {msg.text}
            </div>
            {msg.sender === "ai" && msg.sources && msg.sources.length > 0 && (
              <div className="text-xs text-gray-500 mt-1">Sources: {msg.sources.join(", ")}</div>
            )}
          </div>
        ))}
        {error && <div className="text-red-500">{error}</div>}
        {loading && <div className="text-gray-400">AI is typing...</div>}
      </div>
      <form onSubmit={handleSubmit} className="flex p-2 border-t bg-white">
        <input
          className="flex-1 border rounded px-3 py-2 mr-2 focus:outline-none"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={loading}
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatView;
