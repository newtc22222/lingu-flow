/**
 * Exam seed data — built-in question banks for TOEIC Part 5, IELTS Reading,
 * HSK Level 2, and JLPT N5. These are seeded as `isPublic: true` and have
 * no `userId`, so they are available to every user.
 *
 * Run this script via: ts-node src/examSeed.ts
 * Or call seedExams() from server.ts on startup (idempotent — checks for existence first).
 */

import mongoose from 'mongoose';
import ExamTemplate from './models/ExamTemplate';
import Question from './models/Question';

interface SeedQuestion {
  questionText: string;
  passage?: string;
  options: string[];
  correctAnswer: string;
  explanation: string;
  difficulty: 'easy' | 'medium' | 'hard';
  tags: string[];
}

interface SeedTemplate {
  name: string;
  examType: 'toeic' | 'ielts' | 'hsk' | 'jlpt' | 'custom';
  description: string;
  duration: number;
  passingScore: number;
  level: string;
  questions: SeedQuestion[];
}

const SEED_DATA: SeedTemplate[] = [
  // ─── TOEIC Part 5 ──────────────────────────────────────────────────────────
  {
    name: 'TOEIC Part 5 — Incomplete Sentences',
    examType: 'toeic',
    description: 'Practice TOEIC Part 5: 30 fill-in-the-blank grammar & vocabulary questions. Choose the best word or phrase to complete each sentence.',
    duration: 25,
    passingScore: 70,
    level: 'Part 5',
    questions: [
      {
        questionText: 'The project manager asked that all reports _____ submitted by Friday.',
        options: ['A. are', 'B. be', 'C. were', 'D. being'],
        correctAnswer: 'B',
        explanation: '"Asked that" triggers the subjunctive mood, requiring the base form "be" without "are" or "were".',
        difficulty: 'medium',
        tags: ['grammar', 'subjunctive'],
      },
      {
        questionText: 'Due to the merger, the company will be _____ its headquarters to downtown Seoul.',
        options: ['A. relocating', 'B. relocated', 'C. relocation', 'D. relocate'],
        correctAnswer: 'A',
        explanation: '"Will be" is followed by a present participle (-ing form) to form the future continuous.',
        difficulty: 'easy',
        tags: ['grammar', 'verb form'],
      },
      {
        questionText: 'The annual conference was attended by _____ than 500 delegates from 30 countries.',
        options: ['A. more', 'B. most', 'C. much', 'D. many'],
        correctAnswer: 'A',
        explanation: '"More than" is the correct comparative expression when followed by a specific number.',
        difficulty: 'easy',
        tags: ['grammar', 'comparatives'],
      },
      {
        questionText: 'All employees are required to wear their identification badges _____ working on site.',
        options: ['A. while', 'B. during', 'C. since', 'D. among'],
        correctAnswer: 'A',
        explanation: '"While" introduces a subordinate clause with a participle (-ing), meaning "at the same time as". "During" is followed by a noun, not a verb phrase.',
        difficulty: 'medium',
        tags: ['grammar', 'prepositions'],
      },
      {
        questionText: 'The new software update is intended to make the interface more _____ for users.',
        options: ['A. navigate', 'B. navigating', 'C. navigable', 'D. navigation'],
        correctAnswer: 'C',
        explanation: '"Navigable" is an adjective meaning "easy to navigate", which fits the context of describing the interface.',
        difficulty: 'medium',
        tags: ['vocabulary', 'adjectives'],
      },
      {
        questionText: 'The marketing team is _____ a new campaign to boost brand awareness overseas.',
        options: ['A. developing', 'B. development', 'C. developed', 'D. develop'],
        correctAnswer: 'A',
        explanation: 'The team "is developing" uses present continuous with the -ing form after "is".',
        difficulty: 'easy',
        tags: ['grammar', 'present continuous'],
      },
      {
        questionText: 'Customers who wish to return _____ must present their original receipt.',
        options: ['A. purchases', 'B. purchasing', 'C. purchased', 'D. purchaser'],
        correctAnswer: 'A',
        explanation: '"Purchases" is the plural noun meaning "things bought", which functions as the object of "return".',
        difficulty: 'easy',
        tags: ['vocabulary', 'nouns'],
      },
      {
        questionText: 'The _____ of the new policy has been met with widespread employee approval.',
        options: ['A. implement', 'B. implementing', 'C. implementation', 'D. implemented'],
        correctAnswer: 'C',
        explanation: '"Implementation" is the noun form required after "The" to serve as the subject of the sentence.',
        difficulty: 'medium',
        tags: ['grammar', 'nouns', 'word forms'],
      },
      {
        questionText: 'The board of directors voted _____ to approve the merger proposal.',
        options: ['A. unanimous', 'B. unanimously', 'C. unanimousness', 'D. unanimity'],
        correctAnswer: 'B',
        explanation: '"Unanimously" is the adverb form needed to modify the verb "voted".',
        difficulty: 'medium',
        tags: ['grammar', 'adverbs'],
      },
      {
        questionText: 'Unless additional funding is secured, the construction project may be _____.',
        options: ['A. postponed', 'B. postponing', 'C. postpone', 'D. postponement'],
        correctAnswer: 'A',
        explanation: '"May be postponed" uses the passive voice (be + past participle), correct here because the project receives the action.',
        difficulty: 'hard',
        tags: ['grammar', 'passive voice'],
      },
    ],
  },

  // ─── IELTS Academic Reading ────────────────────────────────────────────────
  {
    name: 'IELTS Academic Reading — Practice Set 1',
    examType: 'ielts',
    description: 'IELTS Academic Reading mini-test with a passage on urban sustainability. Answer 10 multiple-choice questions based on the text. Timed at 20 minutes.',
    duration: 20,
    passingScore: 60,
    level: 'Academic',
    questions: [
      {
        passage: 'Cities across the world are grappling with the challenges of rapid urbanisation. According to the United Nations, by 2050, approximately 68% of the world\'s population will live in urban areas, up from 55% in 2018. This dramatic shift places enormous pressure on infrastructure, resources, and the environment. Urban planners are now focusing on the concept of "sustainable cities" — urban centres designed to minimise ecological impact while maximising quality of life. Key strategies include green building standards, efficient public transport systems, urban green spaces, and circular economy principles that reduce waste.',
        questionText: 'According to the passage, what percentage of the world\'s population is projected to live in urban areas by 2050?',
        options: ['A. 55%', 'B. 62%', 'C. 68%', 'D. 75%'],
        correctAnswer: 'C',
        explanation: 'The passage explicitly states "by 2050, approximately 68% of the world\'s population will live in urban areas".',
        difficulty: 'easy',
        tags: ['reading', 'ielts', 'detail'],
      },
      {
        passage: 'Cities across the world are grappling with the challenges of rapid urbanisation. According to the United Nations, by 2050, approximately 68% of the world\'s population will live in urban areas, up from 55% in 2018. This dramatic shift places enormous pressure on infrastructure, resources, and the environment. Urban planners are now focusing on the concept of "sustainable cities" — urban centres designed to minimise ecological impact while maximising quality of life. Key strategies include green building standards, efficient public transport systems, urban green spaces, and circular economy principles that reduce waste.',
        questionText: 'Which of the following is NOT mentioned as a strategy for sustainable cities?',
        options: ['A. Green building standards', 'B. Efficient public transport', 'C. Underground water recycling systems', 'D. Urban green spaces'],
        correctAnswer: 'C',
        explanation: 'The passage lists green buildings, public transport, green spaces, and circular economy. Underground water recycling is never mentioned.',
        difficulty: 'medium',
        tags: ['reading', 'ielts', 'inference'],
      },
      {
        passage: 'The circular economy model, increasingly adopted by progressive municipalities, challenges the traditional "take-make-dispose" economic framework. Rather than treating waste as the end of a product\'s lifecycle, the circular economy seeks to keep materials in use for as long as possible through reuse, repair, and recycling. Several European cities, including Amsterdam and Copenhagen, have set ambitious targets: Amsterdam aims to halve its use of new raw materials by 2030, while Copenhagen has pledged to become the world\'s first carbon-neutral capital.',
        questionText: 'What does the "take-make-dispose" model represent in the context of the passage?',
        options: ['A. A circular economy strategy', 'B. A traditional economic framework the circular economy challenges', 'C. Amsterdam\'s environmental policy', 'D. A method of carbon neutrality'],
        correctAnswer: 'B',
        explanation: 'The passage describes the circular economy as challenging "the traditional \'take-make-dispose\' economic framework".',
        difficulty: 'medium',
        tags: ['reading', 'ielts', 'inference'],
      },
      {
        passage: 'The circular economy model, increasingly adopted by progressive municipalities, challenges the traditional "take-make-dispose" economic framework. Rather than treating waste as the end of a product\'s lifecycle, the circular economy seeks to keep materials in use for as long as possible through reuse, repair, and recycling. Several European cities, including Amsterdam and Copenhagen, have set ambitious targets: Amsterdam aims to halve its use of new raw materials by 2030, while Copenhagen has pledged to become the world\'s first carbon-neutral capital.',
        questionText: 'By what year does Amsterdam aim to halve its use of new raw materials?',
        options: ['A. 2025', 'B. 2030', 'C. 2035', 'D. 2050'],
        correctAnswer: 'B',
        explanation: 'The passage states "Amsterdam aims to halve its use of new raw materials by 2030".',
        difficulty: 'easy',
        tags: ['reading', 'ielts', 'detail'],
      },
      {
        passage: 'Urban green spaces — parks, community gardens, tree-lined streets, and green rooftops — play a vital role in the psychological and physical wellbeing of city residents. Research published in the journal Environmental Health Perspectives found that residents living within 300 metres of green spaces reported significantly lower levels of stress and depression. Furthermore, trees and vegetation reduce the urban heat island effect, decrease air pollution through absorption of particulate matter, and manage stormwater runoff by absorbing rainwater before it reaches drainage systems.',
        questionText: 'According to the research mentioned, what distance from green spaces was associated with lower stress levels?',
        options: ['A. 100 metres', 'B. 200 metres', 'C. 300 metres', 'D. 500 metres'],
        correctAnswer: 'C',
        explanation: '"Residents living within 300 metres of green spaces reported significantly lower levels of stress and depression."',
        difficulty: 'easy',
        tags: ['reading', 'ielts', 'detail'],
      },
    ],
  },

  // ─── HSK Level 2 ───────────────────────────────────────────────────────────
  {
    name: 'HSK Level 2 — Vocabulary & Grammar',
    examType: 'hsk',
    description: 'Practice test based on HSK Level 2 standard (300 vocabulary words). Tests reading comprehension and grammar with multiple-choice questions. Approx. 300–600 CEFR A2 equivalent.',
    duration: 22,
    passingScore: 60,
    level: 'HSK 2',
    questions: [
      {
        questionText: '他 _____ 图书馆 学习。(He studies _____ the library.)',
        options: ['A. 在 (zài) — at/in', 'B. 是 (shì) — is/am/are', 'C. 有 (yǒu) — have', 'D. 去 (qù) — go'],
        correctAnswer: 'A',
        explanation: '在 (zài) is the location preposition meaning "at" or "in". 他在图书馆学习 = "He studies at the library."',
        difficulty: 'easy',
        tags: ['hsk2', 'grammar', 'preposition', 'location'],
      },
      {
        questionText: '我 _____ 两个 苹果。(I _____ two apples.)',
        options: ['A. 是 (shì) — is/am', 'B. 有 (yǒu) — have', 'C. 在 (zài) — at', 'D. 要 (yào) — want/need'],
        correctAnswer: 'B',
        explanation: '有 (yǒu) means "to have" for possession. 我有两个苹果 = "I have two apples."',
        difficulty: 'easy',
        tags: ['hsk2', 'grammar', 'possession'],
      },
      {
        questionText: '这个 _____ 很 好看。(This _____ is very beautiful.)',
        options: ['A. 书包 (shūbāo) — schoolbag', 'B. 衣服 (yīfu) — clothes', 'C. 电脑 (diànnǎo) — computer', 'D. 医院 (yīyuàn) — hospital'],
        correctAnswer: 'B',
        explanation: '"好看 (hǎokàn)" typically describes appearance/beauty and fits best with clothing 衣服. This question tests vocabulary and context matching.',
        difficulty: 'medium',
        tags: ['hsk2', 'vocabulary'],
      },
      {
        questionText: '他 不 _____ 说 中文。(He cannot _____ Chinese.)',
        options: ['A. 会 (huì) — can/know how to', 'B. 想 (xiǎng) — want/think', 'C. 喜欢 (xǐhuān) — like', 'D. 知道 (zhīdào) — know'],
        correctAnswer: 'A',
        explanation: '会 (huì) is used to express ability or skill learned through study/practice. 不会说中文 = "cannot speak Chinese".',
        difficulty: 'easy',
        tags: ['hsk2', 'grammar', 'modal verbs'],
      },
      {
        questionText: '今天 _____ 星期几？(What day of the week is today?)',
        options: ['A. 什么 (shénme) — what', 'B. 哪 (nǎ) — which', 'C. 几 (jǐ) — how many/which number', 'D. 多少 (duōshao) — how much/many'],
        correctAnswer: 'A',
        explanation: '今天是什么星期几 uses 什么 (shénme) to ask "what" as a question about the day of the week.',
        difficulty: 'medium',
        tags: ['hsk2', 'grammar', 'question words'],
      },
      {
        questionText: '我 每天 _____ 七点 起床。(I get up _____ 7 o\'clock every day.)',
        options: ['A. 在 (zài) — at (location)', 'B. 到 (dào) — arrive/to', 'C. 从 (cóng) — from', 'D. 在 (zài) when used for time'],
        correctAnswer: 'D',
        explanation: '在 (zài) can indicate location AND a time frame. 每天在七点起床 = "get up at 7 every day." In time context, 在 functions like "at".',
        difficulty: 'hard',
        tags: ['hsk2', 'grammar', 'time expressions'],
      },
      {
        questionText: '她 的 _____ 很 漂亮。(Her _____ is very pretty.)',
        options: ['A. 名字 (míngzì) — name', 'B. 妈妈 (māma) — mother', 'C. 工作 (gōngzuò) — work', 'D. 天气 (tiānqì) — weather'],
        correctAnswer: 'A',
        explanation: '"漂亮 (piàoliang)" meaning "pretty" most naturally refers to a name being beautiful (好听 is also used). Context and word frequency at HSK2 make 名字 the best fit.',
        difficulty: 'medium',
        tags: ['hsk2', 'vocabulary', 'adjectives'],
      },
      {
        questionText: '请 问，银行 _____ 哪儿？(Excuse me, where _____ the bank?)',
        options: ['A. 有 (yǒu) — have/there is', 'B. 在 (zài) — is located at', 'C. 是 (shì) — is', 'D. 到 (dào) — arrive'],
        correctAnswer: 'B',
        explanation: '在 (zài) is used for location. 银行在哪儿 = "Where is the bank?" is the standard existential location question.',
        difficulty: 'easy',
        tags: ['hsk2', 'grammar', 'location'],
      },
    ],
  },

  // ─── JLPT N5 ────────────────────────────────────────────────────────────────
  {
    name: 'JLPT N5 — Language Knowledge (Grammar & Vocabulary)',
    examType: 'jlpt',
    description: 'JLPT N5 practice test covering hiragana/katakana vocabulary, basic grammar patterns (は、が、を、に、で、も), and simple sentence structures. Equivalent to beginner Japanese level.',
    duration: 25,
    passingScore: 55,
    level: 'N5',
    questions: [
      {
        questionText: 'わたしは まいにち コーヒー _____ のみます。(I drink coffee every day.)',
        options: ['A. は (wa) — topic marker', 'B. が (ga) — subject marker', 'C. を (wo) — object marker', 'D. に (ni) — direction/time'],
        correctAnswer: 'C',
        explanation: 'を (wo) is the direct object particle. コーヒーを飲みます = "drink coffee". The object of the verb のむ (to drink) is marked with を.',
        difficulty: 'easy',
        tags: ['jlpt-n5', 'particles', 'grammar'],
      },
      {
        questionText: 'これは なん _____ か。(What is this?)',
        options: ['A. で (de) — by/at', 'B. を (wo) — object', 'C. が (ga) — subject', 'D. です (desu) — copula/is'],
        correctAnswer: 'D',
        explanation: 'これはなんですか uses the copula です (desu) to form a polite question. It means "What is this?".',
        difficulty: 'easy',
        tags: ['jlpt-n5', 'grammar', 'question'],
      },
      {
        questionText: 'がっこう _____ いきます。(I go to school.)',
        options: ['A. が (ga)', 'B. に (ni) — direction particle', 'C. で (de) — location of action', 'D. は (wa) — topic'],
        correctAnswer: 'B',
        explanation: 'に (ni) marks the destination or direction with movement verbs like いきます (to go). がっこうにいきます = "go to school".',
        difficulty: 'easy',
        tags: ['jlpt-n5', 'particles', 'direction'],
      },
      {
        questionText: 'きのう、わたしは としょかん _____ ほんを よみました。(Yesterday I read a book at the library.)',
        options: ['A. を (wo)', 'B. に (ni)', 'C. で (de) — location where action happens', 'D. の (no)'],
        correctAnswer: 'C',
        explanation: 'で (de) marks the location where an action takes place. としょかんで読みました = "read at the library". に marks destination, not where you perform an action.',
        difficulty: 'medium',
        tags: ['jlpt-n5', 'particles', 'de vs ni'],
      },
      {
        questionText: 'この えいが _____ おもしろい です。(This movie is interesting.)',
        options: ['A. を (wo)', 'B. で (de)', 'C. は (wa) — topic marker', 'D. も (mo)'],
        correctAnswer: 'C',
        explanation: 'は (wa) is the topic marker used to state what you\'re talking about. このえいがは + adjective describes the movie.',
        difficulty: 'easy',
        tags: ['jlpt-n5', 'particles', 'topic'],
      },
      {
        questionText: 'わたしの たんじょうびは _____ がつ みっかです。(My birthday is March 3rd.)',
        options: ['A. に (ni)', 'B. さん (san) — three', 'C. いち (ichi) — one', 'D. しち (shichi) — seven'],
        correctAnswer: 'B',
        explanation: '三月 (さんがつ, san-gatsu) means "March" (3rd month). さん (三) = three, so the correct answer is B for 三がつ (March).',
        difficulty: 'medium',
        tags: ['jlpt-n5', 'vocabulary', 'months', 'numbers'],
      },
      {
        questionText: 'すみません、トイレは _____ ですか。(Excuse me, where is the bathroom?)',
        options: ['A. なに (nani) — what', 'B. だれ (dare) — who', 'C. どこ (doko) — where', 'D. いつ (itsu) — when'],
        correctAnswer: 'C',
        explanation: 'どこ (doko) means "where", used in location questions. トイレはどこですか = "Where is the bathroom?".',
        difficulty: 'easy',
        tags: ['jlpt-n5', 'vocabulary', 'question words'],
      },
      {
        questionText: 'わたしは あした _____ やすみます。(I will rest tomorrow.)',
        options: ['A. に (ni)', 'B. を (wo)', 'C. が (ga)', 'D. は (wa)'],
        correctAnswer: 'A',
        explanation: 'に (ni) marks a specific time point (e.g. あしたに, though often omitted). For time expressions, に is the standard particle.',
        difficulty: 'medium',
        tags: ['jlpt-n5', 'particles', 'time'],
      },
      {
        questionText: 'この りんごは _____ えんです。(These apples are 100 yen.)',
        options: ['A. ひゃく (hyaku) — 100', 'B. せん (sen) — 1000', 'C. じゅう (juu) — 10', 'D. まん (man) — 10,000'],
        correctAnswer: 'A',
        explanation: 'ひゃく (百) means 100. 100円 = ひゃくえん. This tests JLPT N5 number vocabulary.',
        difficulty: 'easy',
        tags: ['jlpt-n5', 'vocabulary', 'numbers', 'money'],
      },
      {
        questionText: 'あの ひとは だれ _____ か。(Who is that person?)',
        options: ['A. は (wa)', 'B. が (ga)', 'C. を (wo)', 'D. です (desu)'],
        correctAnswer: 'D',
        explanation: 'あのひとはだれですか = "Who is that person?" Uses the copula です with the question particle か to form a polite question.',
        difficulty: 'easy',
        tags: ['jlpt-n5', 'grammar', 'question'],
      },
    ],
  },
];

export async function seedExams(): Promise<void> {
  console.log('Checking exam seed data...');

  for (const seed of SEED_DATA) {
    // Idempotent: skip if a public template with the same name already exists
    const existing = await ExamTemplate.findOne({ name: seed.name, isPublic: true });
    if (existing) {
      console.log(`  ✓ [SKIP] "${seed.name}" already seeded.`);
      continue;
    }

    // Create the template
    const template = await ExamTemplate.create({
      name: seed.name,
      examType: seed.examType,
      description: seed.description,
      duration: seed.duration,
      totalQuestions: seed.questions.length,
      passingScore: seed.passingScore,
      level: seed.level,
      isPublic: true,
      tags: [seed.examType, seed.level],
    });

    // Create questions
    const questions = seed.questions.map((q, idx) => ({
      examTemplateId: template._id,
      questionText: q.questionText,
      passage: q.passage,
      type: 'multiple-choice',
      options: q.options,
      correctAnswer: q.correctAnswer,
      explanation: q.explanation,
      difficulty: q.difficulty,
      tags: q.tags,
      orderIndex: idx,
    }));

    await Question.insertMany(questions);
    console.log(`  ✅ Seeded "${seed.name}" with ${questions.length} questions.`);
  }

  console.log('Exam seeding complete.');
}
