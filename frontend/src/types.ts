export type AnswerValue = string | string[] | boolean
export type QuestionType = 'single_choice' | 'multiple_choice' | 'true_false' | 'short_answer'
export type DifficultyFeedback = 'easy' | 'difficult' | 'dont_know'
export type AnalysisStatus = 'not_required' | 'pending' | 'completed' | 'failed'

export interface User { id: number; email: string; username: string; is_active: boolean }
export interface Question { id: number; title: string; content: string; subject: string; question_type: QuestionType; options: string[] | null; explanation: string | null; difficulty: number; knowledge_points: string[]; tags: string[] }
export interface TaskItem { id: number; position: number; recommendation_reason: string | null; question: Question }
export interface DailyTask { id: number; task_date: string; day_number: number; status: 'pending' | 'in_progress' | 'completed'; completed_at: string | null; version: number; refresh_count: number; refreshed_at: string | null; items: TaskItem[] }
export interface AnswerResult { id: number; question_id: number; daily_task_item_id: number | null; training_session_item_id?: number | null; submitted_answer: AnswerValue; is_correct: boolean; correct_answer: AnswerValue; explanation: string | null; analysis_status: 'not_requested' | 'pending' | 'completed' | 'failed'; ai_analysis: AIAnalysis | null; difficulty_feedback: DifficultyFeedback | null; created_at: string }
export interface AIAnalysis { mistake_type: '概念理解错误' | '计算错误' | '审题错误' | '方法选择错误' | '知识记忆错误' | '其他'; reason: string; knowledge_gap: string; suggestion: string; next_training: string }
export interface AIAnalysisResponse { answer_id: number; status: AnalysisStatus; analysis: AIAnalysis | null }
export interface AnswerStats { total: number; correct: number; accuracy: number }
export interface LearningReportSummary { completed: number; correct: number; accuracy: number }
export interface LearningReportTrendDay extends LearningReportSummary { date: string }
export interface LearningReportWeakPoint { subject: string; knowledge_point_code: string | null; knowledge_point_name: string; mastery_score: number; attempt_count: number; error_count: number }
export interface LearningReportRecommendation { subject: string | null; knowledge_point_code: string | null; knowledge_point_name: string | null; message: string }
export interface LearningReport { generated_at: string; timezone: string; today: LearningReportSummary; week: LearningReportSummary; recent_trend: LearningReportTrendDay[]; weak_points: LearningReportWeakPoint[]; recommendation: LearningReportRecommendation }
export interface AnswerRecord { id: number; question_id: number; daily_task_item_id: number | null; submitted_answer: AnswerValue; is_correct: boolean; difficulty_feedback?: DifficultyFeedback | null; created_at: string }
export interface Page<T> { items: T[]; total: number; page: number; page_size: number }
export type WrongQuestionSort = 'error_count_desc' | 'recent_desc'
export interface WrongQuestion {
  answer_id: number
  question_id: number
  title: string
  content: string
  question_type: QuestionType
  options: string[] | null
  subject: string
  chapter: string | null
  knowledge_point_code: string
  knowledge_point_name: string
  difficulty: number
  submitted_answer: AnswerValue
  correct_answer: AnswerValue
  explanation: string | null
  analysis_status: 'not_requested' | 'pending' | 'completed' | 'failed'
  ai_analysis: AIAnalysis | null
  last_wrong_at: string
  error_count: number
}
export interface SubjectTrainingKnowledgePoint { code: string; name: string; question_count: number; difficulty_counts: Record<number, number> }
export interface SubjectTrainingChapter { name: string; question_count: number; difficulty_counts: Record<number, number>; knowledge_points: SubjectTrainingKnowledgePoint[] }
export interface SubjectTrainingSubject { name: string; question_count: number; difficulty_counts: Record<number, number>; chapters: SubjectTrainingChapter[] }
export interface SubjectTrainingCatalog { subjects: SubjectTrainingSubject[] }
export interface TrainingSessionItem { id: number; position: number; recommendation_reason: string | null; source_answer_id: number | null; question: Question }
export interface TrainingSession {
  id: number
  training_type: 'daily' | 'subject' | 'wrong_review' | 'mixed'
  title: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  total_questions: number
  completed_questions: number
  subject: string | null
  chapter: string | null
  knowledge_point: string | null
  items: TrainingSessionItem[]
}
