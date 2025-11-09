import axios from 'axios';

interface AskPayload {
  question: string;
}

interface AskResponse {
  answer: string;
}

const client = axios.create({
  baseURL: '/api'
});

export async function askQuestion(payload: AskPayload): Promise<AskResponse> {
  const { data } = await client.post<AskResponse>('/ask', payload);
  return data;
}
