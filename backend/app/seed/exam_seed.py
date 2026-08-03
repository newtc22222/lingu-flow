import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.exam import ExamTemplate, Question

logger = logging.getLogger("linguflow")

BUILTIN_SEED_DATA = [
    # ─── TOEIC PART 5 ──────────────────────────────────────────────────────────
    {
        "name": "TOEIC Part 5 — Incomplete Sentences Practice",
        "examType": "toeic",
        "description": "Authentic TOEIC Part 5 multiple-choice questions testing grammar, vocabulary, collocations, and business English usage.",
        "duration": 25,
        "passingScore": 60,
        "level": "Intermediate",
        "questions": [
            {
                "questionText": "The project manager asked that all quarterly reports _____ submitted to the steering committee by Friday afternoon.",
                "options": ["A. are", "B. be", "C. were", "D. being"],
                "correctAnswer": "B",
                "explanation": "The verb 'asked' introduces a subjunctive clause (demand/request), requiring the base form of the verb: 'be submitted'.",
                "difficulty": "medium",
                "tags": ["grammar", "subjunctive"],
            },
            {
                "questionText": "Despite several technical delays during testing, the software update was launched _____ schedule.",
                "options": ["A. on", "B. at", "C. in", "D. to"],
                "correctAnswer": "A",
                "explanation": "'On schedule' is a fixed business prepositional phrase meaning happening at the expected time.",
                "difficulty": "easy",
                "tags": ["prepositions", "collocation"],
            },
            {
                "questionText": "Ms. Lawson has proved to be _____ of the two candidates interviewed for the senior marketing officer role.",
                "options": ["A. the most qualified", "B. more qualified", "C. the more qualified", "D. qualified"],
                "correctAnswer": "C",
                "explanation": "When comparing exactly two items or people, the comparative form with 'the' ('the more qualified') is grammatically required.",
                "difficulty": "hard",
                "tags": ["grammar", "comparatives"],
            },
            {
                "questionText": "Please inform the Human Resources manager _____ you intend to take extended leave during the third quarter.",
                "options": ["A. should", "B. whether", "C. unless", "D. provided"],
                "correctAnswer": "A",
                "explanation": "Inverted conditional: 'Should you intend' is formal for 'If you intend'.",
                "difficulty": "hard",
                "tags": ["conditionals", "inversion"],
            },
            {
                "questionText": "All attendees at the annual shareholder summit are required to display their badges _____ at all times.",
                "options": ["A. prominent", "B. prominence", "C. prominently", "D. most prominent"],
                "correctAnswer": "C",
                "explanation": "The adverb 'prominently' is needed to modify the verb 'display'.",
                "difficulty": "easy",
                "tags": ["parts-of-speech", "adverbs"],
            },
            {
                "questionText": "Neither the chief executive officer nor the company directors _____ available to comment on the merger rumor.",
                "options": ["A. was", "B. were", "C. is", "D. has been"],
                "correctAnswer": "B",
                "explanation": "With 'neither... nor...', the verb agrees with the closer subject. 'Directors' is plural, so 'were' is correct.",
                "difficulty": "medium",
                "tags": ["grammar", "subject-verb-agreement"],
            },
            {
                "questionText": "The newly installed solar panel grid is expected to reduce factory energy expenditures _____ nearly 30 percent.",
                "options": ["A. by", "B. with", "C. for", "D. from"],
                "correctAnswer": "A",
                "explanation": "The preposition 'by' indicates the margin or amount of increase/decrease.",
                "difficulty": "easy",
                "tags": ["prepositions", "business-vocabulary"],
            },
            {
                "questionText": "Had the client submitted the requested documentation sooner, the loan application _____ processed earlier.",
                "options": ["A. will be", "B. would have been", "C. had been", "D. is being"],
                "correctAnswer": "B",
                "explanation": "Inverted third conditional ('Had + past participle... would have + past participle') used for hypothetical past situations.",
                "difficulty": "hard",
                "tags": ["conditionals", "third-conditional"],
            },
            {
                "questionText": "The board of directors reached a _____ decision regarding the acquisition of the regional logistics firm.",
                "options": ["A. unanimous", "B. unanimousness", "C. unanimously", "D. unanimity"],
                "correctAnswer": "A",
                "explanation": "The adjective 'unanimous' is required to modify the noun 'decision'.",
                "difficulty": "medium",
                "tags": ["vocabulary", "word-family"],
            },
            {
                "questionText": "The factory manager insisted that all safety procedures be strictly _____ to avoid industrial accidents.",
                "options": ["A. adhered", "B. followed", "C. observed", "D. compiled"],
                "correctAnswer": "A",
                "explanation": "'Adhered to' is the correct prepositional verb idiom. Note that while 'followed' and 'observed' are synonyms, only 'adhered' pairs with 'to'.",
                "difficulty": "medium",
                "tags": ["collocation", "phrasal-verbs"],
            },
        ],
    },
    # ─── IELTS READING ────────────────────────────────────────────────────────
    {
        "name": "IELTS Academic Reading — Practice Set 1",
        "examType": "ielts",
        "description": "Short IELTS Academic reading comprehension set featuring an academic passage on urban rewilding.",
        "duration": 20,
        "passingScore": 60,
        "level": "Advanced",
        "questions": [
            {
                "passage": "Urban rewilding is an environmental management strategy that seeks to restore natural ecological processes within urban environments...",
                "questionText": "According to Paragraph 1, what is the primary objective of urban rewilding?",
                "options": [
                    "A. To replace all traditional city parks with agricultural land",
                    "B. To restore natural ecological processes and foster biodiversity within human-dominated urban landscapes",
                    "C. To relocate wild animal populations away from metropolitan areas",
                    "D. To eliminate municipal maintenance costs for public green spaces"
                ],
                "correctAnswer": "B",
                "explanation": "The passage explicitly defines urban rewilding as restoring ecological processes and enhancing biodiversity within urban environments.",
                "difficulty": "easy",
                "tags": ["ielts-reading", "factual-information"],
            },
            {
                "passage": "Urban rewilding is an environmental management strategy that seeks to restore natural ecological processes within urban environments...",
                "questionText": "What does the term 'microclimates' in Paragraph 2 refer to?",
                "options": [
                    "A. Large-scale weather patterns spanning entire continents",
                    "B. Localized atmospheric zones where environmental conditions differ from the surrounding area",
                    "C. Indoor air-conditioning systems used in commercial buildings",
                    "D. Historical climate data collected over previous centuries"
                ],
                "correctAnswer": "B",
                "explanation": "'Microclimates' refers to small, localized areas where temperature and climate conditions vary from the surrounding region.",
                "difficulty": "medium",
                "tags": ["ielts-reading", "vocabulary-in-context"],
            },
            {
                "passage": "Urban rewilding is an environmental management strategy that seeks to restore natural ecological processes within urban environments...",
                "questionText": "Which of the following is cited as a major obstacle to implementing urban rewilding projects?",
                "options": [
                    "A. The complete absence of native plant seeds in temperate climates",
                    "B. Public resistance caused by safety concerns and aesthetic preferences for manicured landscapes",
                    "C. Federal laws banning trees from being planted near roads",
                    "D. High costs of purchasing electronic sensors for monitoring"
                ],
                "correctAnswer": "B",
                "explanation": "The text notes that public aesthetics favoring traditional lawns and fears regarding pests or safety pose key challenges.",
                "difficulty": "medium",
                "tags": ["ielts-reading", "detail"],
            },
            {
                "passage": "Urban rewilding is an environmental management strategy that seeks to restore natural ecological processes within urban environments...",
                "questionText": "What can be inferred about the impact of urban green corridors from the text?",
                "options": [
                    "A. They isolate species populations from one another permanently",
                    "B. They allow wildlife to move safely between fragmented habitat patches, increasing genetic diversity",
                    "C. They increase traffic congestion in city centers",
                    "D. They are only effective in tropical climate zones"
                ],
                "correctAnswer": "B",
                "explanation": "Green corridors connect habitat fragments, facilitating movement and genetic flow among isolated species populations.",
                "difficulty": "hard",
                "tags": ["ielts-reading", "inference"],
            },
            {
                "passage": "Urban rewilding is an environmental management strategy that seeks to restore natural ecological processes within urban environments...",
                "questionText": "Which title best summarizes the main idea of the reading passage?",
                "options": [
                    "A. Why City Parks Are Obsolete",
                    "B. Urban Rewilding: Balancing Ecological Restoration and City Living",
                    "C. The Economic Cost of Planting Trees in Urban Centers",
                    "D. A History of Agricultural Development in Western Europe"
                ],
                "correctAnswer": "B",
                "explanation": "The passage discusses both the ecological benefits of rewilding cities and the practical challenges of integrating nature into urban design.",
                "difficulty": "medium",
                "tags": ["ielts-reading", "main-idea"],
            },
        ],
    },
    # ─── HSK LEVEL 2 ──────────────────────────────────────────────────────────
    {
        "name": "HSK Level 2 — Vocabulary & Grammar",
        "examType": "hsk",
        "description": "Standard HSK 2 practice test covering everyday Chinese vocabulary, basic sentence patterns, time words, and pinyin.",
        "duration": 22,
        "passingScore": 60,
        "level": "Elementary",
        "questions": [
            {
                "questionText": "昨天 的 考试，我 都 _____ 懂 了。(I understood everything in yesterday's exam.)",
                "options": ["A. 听 (tīng)", "B. 看 (kàn)", "C. 写 (xiě)", "D. 做 (zuò)"],
                "correctAnswer": "A",
                "explanation": "听懂 (tīng dǒng) is a resultative verb compound meaning 'listen and understand'. 听懂了 = understood upon hearing/reading test instructions.",
                "difficulty": "easy",
                "tags": ["hsk2", "resultative-verb"],
            },
            {
                "questionText": "下 雨 了，外面 太 冷，你 还是 _____ 出去 了吧。(It's raining and too cold outside, you'd better not go out.)",
                "options": ["A. 没 (méi)", "B. 别 (bié)", "C. 不 (bù)", "D. 没有 (méiyǒu)"],
                "correctAnswer": "B",
                "explanation": "别 (bié) is used for negative imperatives/suggestions meaning 'don't'. 别出去了吧 = 'better not go out'.",
                "difficulty": "medium",
                "tags": ["hsk2", "grammar", "imperative"],
            },
            {
                "questionText": "我 比 弟弟 _____ 两 岁。(I am two years older than my younger brother.)",
                "options": ["A. 大 (dà)", "B. 高 (gāo)", "C. 多 (duō)", "D. 长 (zhǎng)"],
                "correctAnswer": "A",
                "explanation": "In Chinese age comparisons, 比...大几岁 (bǐ... dà jǐ suì) is used to express being older by a number of years.",
                "difficulty": "medium",
                "tags": ["hsk2", "grammar", "comparison"],
            },
            {
                "questionText": "医生 说，他 需要 在 医院 _____ 几天。(The doctor said he needs to stay in the hospital for a few days.)",
                "options": ["A. 住 (zhù)", "B. 去 (qù)", "C. 来 (lái)", "D. 坐 (zuò)"],
                "correctAnswer": "A",
                "explanation": "住院 (zhù yuàn) / 住几天 means to stay/be hospitalized.",
                "difficulty": "easy",
                "tags": ["hsk2", "vocabulary"],
            },
            {
                "questionText": "公共汽车 已经 _____ 了，我们 跑步 去 吧。(The bus has already left, let's run.)",
                "options": ["A. 走 (zǒu)", "B. 飞 (fēi)", "C. 跑 (pǎo)", "D. 进 (jìn)"],
                "correctAnswer": "A",
                "explanation": "公共汽车走了 = 'The bus has left/departed'. 走 is used for vehicle departures in everyday spoken Chinese.",
                "difficulty": "easy",
                "tags": ["hsk2", "vocabulary"],
            },
            {
                "questionText": "他 正在 _____ 呢，请 你 等 一下。(He is taking a phone call right now, please wait a moment.)",
                "options": ["A. 打电话 (dǎ diànhuà)", "B. 唱歌 (chànggē)", "C. 跑步 (pǎobù)", "D. 看电视 (kàn diànshì)"],
                "correctAnswer": "A",
                "explanation": "正在...呢 indicates progressive aspect (doing something right now). 打电话 = making a phone call.",
                "difficulty": "easy",
                "tags": ["hsk2", "aspect", "progressive"],
            },
            {
                "questionText": "她 的 _____ 很 漂亮。(Her _____ is very pretty.)",
                "options": ["A. 名字 (míngzì)", "B. 妈妈 (māma)", "C. 工作 (gōngzuò)", "D. 天气 (tiānqì)"],
                "correctAnswer": "A",
                "explanation": "名字 (míngzì) meaning 'name' fits naturally with 漂亮 (pretty/nice-sounding name).",
                "difficulty": "medium",
                "tags": ["hsk2", "vocabulary"],
            },
            {
                "questionText": "请 问，银行 _____ 哪儿？(Excuse me, where is the bank?)",
                "options": ["A. 有 (yǒu)", "B. 在 (zài)", "C. 是 (shì)", "D. 到 (dào)"],
                "correctAnswer": "B",
                "explanation": "在 (zài) is used for location. 银行在哪儿 = 'Where is the bank?'.",
                "difficulty": "easy",
                "tags": ["hsk2", "grammar", "location"],
            },
        ],
    },
    # ─── JLPT N5 ──────────────────────────────────────────────────────────────
    {
        "name": "JLPT N5 — Language Knowledge",
        "examType": "jlpt",
        "description": "JLPT N5 practice test covering hiragana/katakana vocabulary, basic particles (は, が, を, に, で), and polite sentence forms.",
        "duration": 25,
        "passingScore": 60,
        "level": "N5",
        "questions": [
            {
                "questionText": "わたしは まいにち コーヒー _____ のみます。(I drink coffee every day.)",
                "options": ["A. は (wa)", "B. が (ga)", "C. を (wo)", "D. に (ni)"],
                "correctAnswer": "C",
                "explanation": "を (wo) is the direct object particle. コーヒーを飲みます = 'drink coffee'.",
                "difficulty": "easy",
                "tags": ["jlpt-n5", "particles"],
            },
            {
                "questionText": "这是 なん _____ か。(What is this?)",
                "options": ["A. で (de)", "B. を (wo)", "C. が (ga)", "D. です (desu)"],
                "correctAnswer": "D",
                "explanation": "なんですか uses copula です (desu) to form a polite question ('What is it?').",
                "difficulty": "easy",
                "tags": ["jlpt-n5", "grammar"],
            },
            {
                "questionText": "がっこう _____ いきます。(I go to school.)",
                "options": ["A. が (ga)", "B. に (ni)", "C. で (de)", "D. は (wa)"],
                "correctAnswer": "B",
                "explanation": "に (ni) marks destination or direction with movement verbs like いきます (to go).",
                "difficulty": "easy",
                "tags": ["jlpt-n5", "particles"],
            },
            {
                "questionText": "きのう、わたしは としょかん _____ ほんを よみました。(Yesterday I read a book at the library.)",
                "options": ["A. を (wo)", "B. に (ni)", "C. で (de)", "D. の (no)"],
                "correctAnswer": "C",
                "explanation": "で (de) marks the location where an action takes place.",
                "difficulty": "medium",
                "tags": ["jlpt-n5", "particles"],
            },
            {
                "questionText": "この えいが _____ おもしろい です。(This movie is interesting.)",
                "options": ["A. を (wo)", "B. で (de)", "C. は (wa)", "D. も (mo)"],
                "correctAnswer": "C",
                "explanation": "は (wa) is the topic marker.",
                "difficulty": "easy",
                "tags": ["jlpt-n5", "particles"],
            },
            {
                "questionText": "わたしの たんじょうびは _____ がつ みっかです。(My birthday is March 3rd.)",
                "options": ["A. に (ni)", "B. さん (san)", "C. いち (ichi)", "D. しち (shichi)"],
                "correctAnswer": "B",
                "explanation": "三月 (さんがつ, san-gatsu) means March (3rd month). さん = 3.",
                "difficulty": "medium",
                "tags": ["jlpt-n5", "vocabulary"],
            },
            {
                "questionText": "すみません、トイレは _____ ですか。(Excuse me, where is the bathroom?)",
                "options": ["A. なに (nani)", "B. だれ (dare)", "C. どこ (doko)", "D. いつ (itsu)"],
                "correctAnswer": "C",
                "explanation": "どこ (doko) means 'where'.",
                "difficulty": "easy",
                "tags": ["jlpt-n5", "vocabulary"],
            },
            {
                "questionText": "わたしは あした _____ やすみます。(I will rest tomorrow.)",
                "options": ["A. に (ni)", "B. を (wo)", "C. が (ga)", "D. は (wa)"],
                "correctAnswer": "A",
                "explanation": "に (ni) marks a specific time point.",
                "difficulty": "medium",
                "tags": ["jlpt-n5", "particles"],
            },
            {
                "questionText": "この りんごは _____ えんです。(These apples are 100 yen.)",
                "options": ["A. ひゃく (hyaku)", "B. せん (sen)", "C. じゅう (juu)", "D. まん (man)"],
                "correctAnswer": "A",
                "explanation": "ひゃく (百) = 100.",
                "difficulty": "easy",
                "tags": ["jlpt-n5", "numbers"],
            },
            {
                "questionText": "あの ひとは だれ _____ か。(Who is that person?)",
                "options": ["A. は (wa)", "B. が (ga)", "C. を (wo)", "D. です (desu)"],
                "correctAnswer": "D",
                "explanation": "だれですか forms the question 'Who is that person?'.",
                "difficulty": "easy",
                "tags": ["jlpt-n5", "grammar"],
            },
        ],
    },
]


async def seed_builtin_exams(db: AsyncSession) -> None:
    """Idempotently seed the 33 built-in exam questions across TOEIC, IELTS, HSK, and JLPT."""
    logger.info("Checking built-in exam seed data...")

    for seed in BUILTIN_SEED_DATA:
        # Idempotent check: skip if public template with exact name exists
        result = await db.execute(
            select(ExamTemplate).where(
                ExamTemplate.name == seed["name"],
                ExamTemplate.is_public == True,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            logger.info(f"  ✓ [SKIP] '{seed['name']}' already seeded.")
            continue

        template = ExamTemplate(
            user_id=None,
            name=seed["name"],
            exam_type=seed["examType"],
            description=seed["description"],
            duration_minutes=seed["duration"],
            total_questions=len(seed["questions"]),
            passing_score=seed["passingScore"],
            level=seed["level"],
            is_public=True,
            tags=[seed["examType"], seed["level"]],
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)

        questions = [
            Question(
                exam_template_id=template.id,
                user_id=None,
                question_text=q["questionText"],
                passage=q.get("passage"),
                type="multiple-choice",
                options=q["options"],
                correct_answer=q["correctAnswer"],
                explanation=q.get("explanation"),
                difficulty=q.get("difficulty", "medium"),
                tags=q.get("tags", []),
                order_index=idx,
            )
            for idx, q in enumerate(seed["questions"])
        ]
        db.add_all(questions)
        await db.commit()
        logger.info(f"  ✅ Seeded '{seed['name']}' with {len(questions)} questions.")

    logger.info("Exam seeding complete.")
