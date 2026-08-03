import type { AIAnalysisResponse, AnswerResult, AnswerStats, AnswerValue, DailyTask, DifficultyFeedback, LearningReport, Page, AnswerRecord, SubjectTrainingCatalog, TrainingSession, User, WrongQuestion, WrongQuestionSort } from '../types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message) }
}

export class NetworkError extends Error {}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('access_token')
  const headers = new Headers(init.headers)
  if (!(init.body instanceof URLSearchParams)) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers,
      signal: init.signal ?? AbortSignal.timeout(15_000),
    })
  } catch (error) {
    throw new NetworkError(
      error instanceof DOMException && error.name === 'TimeoutError'
        ? '请求超时，请检查网络后重试'
        : '网络连接失败，请检查网络后重试',
    )
  }
  if (response.status === 401) {
    localStorage.removeItem('access_token')
    if (!location.pathname.includes('/login')) location.assign('/login')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(response.status, typeof body.detail === 'string' ? body.detail : '请求失败，请稍后重试')
  }
  return response.json() as Promise<T>
}

export const api = {
  async login(username: string, password: string) {
    const body = new URLSearchParams({ username, password })
    return request<{ access_token: string; token_type: string }>('/users/login', { method: 'POST', body })
  },
  me: () => request<User>('/users/me'),
  today: () => request<DailyTask>('/daily-tasks/today'),
  refreshToday: () => request<DailyTask>('/daily-tasks/today/refresh', { method: 'POST' }),
  taskAnswers: (id: number) => request<AnswerResult[]>(`/daily-tasks/${id}/answers`),
  completeTask: (id: number) => request<DailyTask>(`/daily-tasks/${id}/complete`, { method: 'POST' }),
  submitAnswer: (payload: { question_id: number; daily_task_item_id: number; answer: AnswerValue; duration_seconds: number; idempotency_key: string }) => request<AnswerResult>('/student-answers', { method: 'POST', body: JSON.stringify(payload) }),
  answerAnalysis: (answerId: number) => request<AIAnalysisResponse>(`/student-answers/${answerId}/analysis`),
  retryAnswerAnalysis: (answerId: number) => request<AIAnalysisResponse>(`/student-answers/${answerId}/analysis/retry`, { method: 'POST' }),
  updateAnswerFeedback: (answerId: number, difficulty_feedback: DifficultyFeedback) => request<{ answer_id: number; difficulty_feedback: DifficultyFeedback }>(`/student-answers/${answerId}/feedback`, { method: 'PATCH', body: JSON.stringify({ difficulty_feedback }) }),
  stats: () => request<AnswerStats>('/student-answers/stats'),
  learningReport: () => request<LearningReport>('/learning-report'),
  answers: () => request<Page<AnswerRecord>>('/student-answers?page=1&page_size=20'),
  wrongQuestions: (filters: { subject?: string; knowledge_point_code?: string; sort?: WrongQuestionSort } = {}) => {
    const params = new URLSearchParams({ page: '1', page_size: '100' })
    if (filters.subject) params.set('subject', filters.subject)
    if (filters.knowledge_point_code) params.set('knowledge_point_code', filters.knowledge_point_code)
    if (filters.sort) params.set('sort', filters.sort)
    return request<Page<WrongQuestion>>(`/wrong-questions?${params}`)
  },
  practiceWrongQuestion: (questionId: number) =>
    request<TrainingSession>(`/wrong-questions/${questionId}/practice`, { method: 'POST' }),
  subjectTrainingCatalog: () => request<SubjectTrainingCatalog>('/training-sessions/subject/catalog'),
  createSubjectTraining: (payload: { subject: string; chapter?: string; knowledge_point_code?: string; difficulty?: number; question_count: number }) =>
    request<TrainingSession>('/training-sessions/subject', { method: 'POST', body: JSON.stringify(payload) }),
  fillTrainingCatalog: () => request<SubjectTrainingCatalog>('/training-sessions/fill/catalog'),
  createFillTraining: (payload: { subject: string; chapter?: string; knowledge_point_code?: string; difficulty?: number; question_count: number }) =>
    request<TrainingSession>('/training-sessions/fill', { method: 'POST', body: JSON.stringify(payload) }),
  trainingSession: (id: number) => request<TrainingSession>(`/training-sessions/${id}`),
  trainingAnswers: (id: number) => request<AnswerResult[]>(`/training-sessions/${id}/answers`),
  submitTrainingAnswer: (itemId: number, payload: { answer: AnswerValue; duration_seconds: number; idempotency_key: string }) =>
    request<AnswerResult>(`/training-session-items/${itemId}/answer`, { method: 'POST', body: JSON.stringify(payload) }),
  completeTraining: (id: number) => request<TrainingSession>(`/training-sessions/${id}/complete`, { method: 'POST' }),
}
