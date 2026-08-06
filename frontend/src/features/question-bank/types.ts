/** Mirrors `QuestionResponse` in `backend/app/schemas/exam.py`. */
export interface BankQuestion {
  id: string
  userId?: string | null
  examType: string
  part?: string | null
  passageGroup?: string | null
  questionText: string
  passage?: string | null
  type: string
  options: string[]
  correctAnswer: string
  explanation?: string | null
  tags?: string[] | null
  difficulty: string
  /** Server-computed: the viewer may edit/delete this question. Seeded
   *  questions have no owner, so this is false for everyone. */
  isOwned: boolean
  createdAt: string
  updatedAt: string
}

/** `TemplateQuestionResponse` — a bank question plus its slot in one exam. */
export interface TemplateQuestion extends BankQuestion {
  orderIndex: number
}

export interface QuestionFilterState {
  examType: string
  part: string
  difficulty: string
  tags: string[]
  search: string
}

export const EXAM_TYPES = ['toeic', 'ielts', 'hsk', 'jlpt', 'custom'] as const
export const DIFFICULTIES = ['easy', 'medium', 'hard'] as const

export function emptyFilters(): QuestionFilterState {
  return { examType: '', part: '', difficulty: '', tags: [], search: '' }
}
