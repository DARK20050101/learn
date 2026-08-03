import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import LoginView from './views/LoginView.vue'
import QuestionView from './views/QuestionView.vue'
import StatsView from './views/StatsView.vue'
import SubjectTrainingView from './views/SubjectTrainingView.vue'
import FillTrainingView from './views/FillTrainingView.vue'
import TrainingSessionView from './views/TrainingSessionView.vue'
import WrongQuestionsView from './views/WrongQuestionsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView, meta: { public: true } },
    { path: '/', component: HomeView },
    { path: '/question/:position', component: QuestionView },
    { path: '/stats', component: StatsView },
    { path: '/wrong-questions', component: WrongQuestionsView },
    { path: '/training/subject', component: SubjectTrainingView },
    { path: '/training/fill', component: FillTrainingView },
    { path: '/training/:sessionId/:position?', component: TrainingSessionView },
  ],
  scrollBehavior: () => ({ top: 0 }),
})
router.beforeEach((to) => {
  if (!to.meta.public && !localStorage.getItem('access_token')) return '/login'
  if (to.path === '/login' && localStorage.getItem('access_token')) return '/'
})
export default router
