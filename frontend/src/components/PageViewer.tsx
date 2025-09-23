import React, { useEffect, useState } from "react";
import { getPageById } from "../lib/api";
import { Page } from "../types";

interface PageViewerProps {
  pageId: number;
}

const PageViewer: React.FC<PageViewerProps> = ({ pageId }) => {
  const [page, setPage] = useState<Page | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getPageById(pageId)
      .then(setPage)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [pageId]);

  if (loading) return <div className="text-gray-500">Loading...</div>;
  if (error) return <div className="text-red-500">{error}</div>;
  if (!page) return null;

  return (
    <div className="max-w-2xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-2">{page.title}</h1>
      <a href={page.url} className="text-blue-600 underline mb-4 block" target="_blank" rel="noopener noreferrer">{page.url}</a>
      <div className="prose" dangerouslySetInnerHTML={{ __html: page.content_html }} />
    </div>
  );
};

export default PageViewer;
