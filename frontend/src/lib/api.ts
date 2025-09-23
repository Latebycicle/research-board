export async function postChatMessage(query: string): Promise<{ response: string; sources?: string[] }> {
  const response = await fetch("http://127.0.0.1:8000/api/v1/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!response.ok) {
    throw new Error(`Failed to send chat message: ${response.statusText}`);
  }
  return response.json();
}
export async function getPageById(id: number): Promise<Page> {
  const response = await fetch(`http://127.0.0.1:8000/api/v1/pages/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch page: ${response.statusText}`);
  }
  return response.json();
}
import { Page } from "../types";

export async function getPages(): Promise<Page[]> {
  const response = await fetch("http://127.0.0.1:8000/api/v1/pages");
  if (!response.ok) {
    throw new Error(`Failed to fetch pages: ${response.statusText}`);
  }
  return response.json();
}
