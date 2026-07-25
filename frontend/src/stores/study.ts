import { reactive } from 'vue'
import type { AIAnalysisResponse, AnswerResult, DailyTask } from '../types'

interface StudyState { task: DailyTask | null; answers: Record<number, AnswerResult>; analyses: Record<number, AIAnalysisResponse> }
const state = reactive<StudyState>({ task: null, answers: {}, analyses: {} })

export function resetStudy() {
  state.task = null
  state.answers = {}
  state.analyses = {}
}

export function restoreAnswers(answers: AnswerResult[]) {
  state.answers = {}
  state.analyses = {}
  for (const answer of answers) {
    if (answer.daily_task_item_id === null) continue
    state.answers[answer.daily_task_item_id] = answer
    state.analyses[answer.daily_task_item_id] = {
      answer_id: answer.id,
      status: answer.analysis_status === 'not_requested' ? 'not_required' : answer.analysis_status,
      analysis: answer.ai_analysis,
    }
  }
}

export function useStudy() { return { state, resetStudy, restoreAnswers } }
