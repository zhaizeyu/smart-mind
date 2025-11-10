import axios from 'axios';

interface AskPayload {
  question: string;
}

interface AskResponse {
  answer: string;
}

export interface SummaryEntry {
  question: string;
  answer?: string;
  depth: number;
}

export interface SummaryPayload {
  topic: string;
  entries: SummaryEntry[];
}

interface SummaryResponse {
  summary: string;
}

const client = axios.create({
  baseURL: '/api'
});

export async function askQuestion(payload: AskPayload): Promise<AskResponse> {
  const { data } = await client.post<AskResponse>('/ask', payload);
  return data;
}

export async function summarizeNode(payload: SummaryPayload): Promise<SummaryResponse> {
  const { data } = await client.post<SummaryResponse>('/summary', payload);
  return data;
}
