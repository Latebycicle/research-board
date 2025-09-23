
import Sidebar from "./Sidebar";
import React, { useState } from "react";

import PageViewer from "./components/PageViewer";
import ChatView from "./components/ChatView";


function App() {
  const [selectedPageId, setSelectedPageId] = useState<number | null>(null);
  const [view, setView] = useState<"page" | "chat">("page");

  return (
    <div className="flex h-screen w-screen">
      <Sidebar setSelectedPageId={(id) => { setSelectedPageId(id); setView("page"); }} />
      <main className="flex-1 flex flex-col items-center justify-center bg-white">
        <div className="w-full flex justify-end p-2">
          <button
            className={`mr-2 px-4 py-2 rounded ${view === "page" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700"}`}
            onClick={() => setView("page")}
          >
            Page View
          </button>
          <button
            className={`px-4 py-2 rounded ${view === "chat" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700"}`}
            onClick={() => setView("chat")}
          >
            Chat
          </button>
        </div>
        <div className="flex-1 w-full flex items-center justify-center">
          {view === "chat" ? (
            <ChatView />
          ) : selectedPageId ? (
            <PageViewer pageId={selectedPageId} />
          ) : (
            <span className="text-gray-500 text-xl">Select an item from the sidebar</span>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
