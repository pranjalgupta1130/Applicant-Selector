const API_BASE = (import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:5000/api').replace(/\/$/, '');

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'content-type': 'application/json', ...init?.headers },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.message || body.error || body.detail || `Backend request failed (${response.status})`);
  return body.data as T;
}

export type BackendRole = { _id: string; title: string; description: string; competencies: Array<{ name: string } | string> };
export type BackendQuestion = { id: string; _id?: string; text: string; stage: string; competency: string; difficulty: number; expectedConcepts: string[]; sources?: string[]; isFallback?: boolean; relevanceScore?: number };
export type BackendInterview = { _id: string; status: string; question?: BackendQuestion; scorecard?: Record<string, unknown> };
export type BackendTurn = { answer: unknown; evaluation: Record<string, unknown>; nextQuestion: BackendQuestion | null; termination: { shouldTerminate: boolean; reason: string }; decision: Record<string, unknown>; trace: Record<string, unknown>; report: Record<string, unknown> | null; diagnostics?: Record<string, unknown> | null };

export const listRoles = () => request<BackendRole[]>('/roles');
export const createCandidate = (input: { name: string; email: string; experience: string; education: string; extractedSkills: string[]; resumeUrl?: string }) => request<{ _id: string }>('/candidates', { method: 'POST', body: JSON.stringify(input) });
export const createInterview = (candidateId: string, roleId: string) => request<BackendInterview>('/interviews', { method: 'POST', body: JSON.stringify({ candidateId, roleId }) });
export const startInterview = (id: string) => request<BackendInterview>(`/interviews/${id}/start`, { method: 'POST', body: '{}' });
export const submitInterviewAnswer = (id: string, questionId: string, answerText: string) => request<BackendTurn>(`/interviews/${id}/answers`, { method: 'POST', body: JSON.stringify({ interviewQuestionId: questionId, answerText }) });
export const getInterviewReport = (id: string) => request<Record<string, unknown>>(`/interviews/${id}/report`);
export const recordInterviewIntegrity = (id: string, events: unknown[], status?: string) => request<{ status: string; warnings: number }>(`/interviews/${id}/integrity`, { method: 'POST', body: JSON.stringify({ events, status }) });
