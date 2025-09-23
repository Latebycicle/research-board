import React, { useEffect, useState } from "react";
import { getPages } from "../lib/api";
import { Page } from "../types";

interface HistoryListProps {
  setSelectedPageId: (id: number) => void;
}

const HistoryList: React.FC<HistoryListProps> = ({ setSelectedPageId }) => {
  const [pages, setPages] = useState<Page[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPages()
      .then((data) => setPages(data))
      .catch(() => setPages([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-gray-500">Loading...</div>;

  return (
    <ul className="space-y-1 mb-6">
      {pages.map((page) => (
        <li
          key={page.id}
          className="hover:bg-gray-200 rounded px-2 py-1 cursor-pointer"
          onClick={() => setSelectedPageId(page.id)}
        >
          {page.title}
        </li>
      ))}
    </ul>
  );
};

export default HistoryList;
