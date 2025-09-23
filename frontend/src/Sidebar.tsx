import React from "react";
import HistoryList from "./components/HistoryList";

interface SidebarProps {
  setSelectedPageId: (id: number) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ setSelectedPageId }) => (
  <aside className="flex flex-col h-full w-[300px] bg-gray-100 border-r border-gray-200 p-4 justify-between">
    <div>
      <h2 className="text-lg font-semibold mb-2">History</h2>
      <HistoryList setSelectedPageId={setSelectedPageId} />
    </div>
    <div>
      <h2 className="text-lg font-semibold mb-2">Recent Chats</h2>
      <ul className="space-y-1">
        <li className="hover:bg-gray-200 rounded px-2 py-1 cursor-pointer">Chat with Copilot</li>
        <li className="hover:bg-gray-200 rounded px-2 py-1 cursor-pointer">AI Research Notes</li>
        <li className="hover:bg-gray-200 rounded px-2 py-1 cursor-pointer">Frontend Q&A</li>
      </ul>
    </div>
  </aside>
);

export default Sidebar;
