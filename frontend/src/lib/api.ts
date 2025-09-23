import { Page } from '../types';

export async function getPages(): Promise<Page[]> {
  const response = await fetch('http://127.0.0.1:8000/api/v1/pages');
  if (!response.ok) {
    throw new Error(`Failed to fetch pages: ${response.status} ${response.statusText}`);
  }
  return response.json();
}
