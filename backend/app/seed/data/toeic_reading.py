"""
TOEIC Reading test content — Parts 5, 6 and 7.

Structure mirrors the real exam:
  * Part 5 — Incomplete Sentences: one standalone sentence with a blank.
  * Part 6 — Text Completion: one passage with several blanks; every question
    in a set repeats the passage and shares a `passageGroup`.
  * Part 7 — Reading Comprehension: single passages and one double-passage set,
    again grouped by `passageGroup`.

`passageGroup` is what lets the UI render a set together and lets the composer
warn before attaching half of one. Questions in a set intentionally repeat the
passage text: there is no passages table yet (tracked as a follow-up), so the
passage lives on each question.

Listening (Parts 1-4) is deliberately out of scope — it needs audio, tracked
separately in issue #19.
"""

# ─── Part 6 passages ──────────────────────────────────────────────────────────
P6_MEMO = (
    "MEMORANDUM\n\n"
    "To: All Regional Sales Staff\n"
    "From: Daniela Okonkwo, Director of Operations\n"
    "Subject: Updated Expense Reporting Procedure\n\n"
    "Beginning on 1 March, all travel expenses must be submitted through the "
    "new Ardent portal rather than by email. Receipts should be uploaded "
    "within five business days of your return. Claims filed after that window "
    "____(1)____ by the finance team, and reimbursement may be delayed until "
    "the following payment cycle.\n\n"
    "The portal also allows you to save a trip in progress, so you no longer "
    "need to wait until a journey is complete before entering costs. "
    "____(2)____ We expect this will considerably reduce the end-of-quarter "
    "backlog.\n\n"
    "Training sessions will be held twice weekly throughout February. "
    "Attendance is ____(3)____ for anyone who travels more than four times a "
    "year. If you are unable to attend a session, a recording will be made "
    "____(4)____ on the internal knowledge base."
)

P6_NOTICE = (
    "NOTICE TO BUILDING TENANTS\n\n"
    "The lobby renovation at Harbourpoint Tower is scheduled to begin on "
    "12 September and is expected to last approximately six weeks. During "
    "this period the main entrance on Waterfront Road will be closed, and all "
    "visitors ____(1)____ to use the side entrance on Miller Lane.\n\n"
    "____(2)____ Deliveries should continue to be directed to the loading bay, "
    "which remains fully operational.\n\n"
    "We appreciate your patience while this work is carried out. The "
    "improvements will ____(3)____ a redesigned reception desk, additional "
    "seating, and upgraded lighting throughout the ground floor. Tenants with "
    "questions about access arrangements should contact the building "
    "management office ____(4)____ than emailing individual contractors."
)

# ─── Part 7 passages ──────────────────────────────────────────────────────────
P7_EMAIL = (
    "From: r.castellanos@meridianlogistics.com\n"
    "To: pt.nguyen@brightfieldfoods.com\n"
    "Date: 14 April\n"
    "Subject: Revised delivery schedule for Q3\n\n"
    "Dear Ms. Nguyen,\n\n"
    "Thank you for your patience while we reviewed the routing changes you "
    "requested last month. I am writing to confirm that from 1 July, "
    "Brightfield Foods' weekly shipments to the northern distribution centre "
    "will move from Tuesday to Thursday.\n\n"
    "This change allows us to consolidate your consignment with two other "
    "clients on the same corridor, which reduces your per-pallet cost by "
    "roughly eleven percent. The saving is reflected in the revised rate card "
    "attached to this message.\n\n"
    "One consequence worth flagging: because Thursday collections leave our "
    "depot later in the day, arrival at your Aberdeen site will shift from "
    "early morning to mid-afternoon. If your receiving team cannot "
    "accommodate that, we can hold the Tuesday slot at the existing rate.\n\n"
    "Please let me know your preference by 1 May so we can finalise the "
    "schedule.\n\n"
    "Best regards,\n"
    "Rafael Castellanos\n"
    "Account Manager, Meridian Logistics"
)

P7_ADVERT = (
    "THE GRANARY WORKSPACE — Now Leasing\n\n"
    "Purpose-built studio and office space in the restored Granary Building, "
    "two minutes from Eastgate Station.\n\n"
    "* Flexible terms from three months, with no penalty for early exit after "
    "the first ninety days\n"
    "* Fibre connectivity included in all tariffs\n"
    "* Shared workshop and photography studio, bookable by the hour\n"
    "* 24-hour access with a staffed reception between 07:00 and 19:00\n\n"
    "Units range from 18 to 240 square metres. Rates begin at 310 per month "
    "for a single studio and are quoted inclusive of utilities and business "
    "rates; parking is charged separately at 45 per space per month.\n\n"
    "Viewings take place every Wednesday and Saturday. To arrange one outside "
    "these times, contact the leasing office at least 48 hours in advance. "
    "Note that the workshop facility will not be available until the second "
    "phase of works concludes in November."
)

P7_ARTICLE = (
    "Regional Rail Reports Second Consecutive Year of Growth\n\n"
    "Passenger numbers on the Kestrel Valley line rose 7.4 percent last year, "
    "the second annual increase since services were restored in 2021. "
    "Operator Northline attributes the rise chiefly to the introduction of "
    "off-peak flat fares, which replaced a distance-based structure widely "
    "criticised as difficult to understand.\n\n"
    "Independent transport analyst Marguerite Adeyemi cautions against "
    "reading too much into a single measure. \"Flat fares clearly helped, but "
    "the line also benefited from a road closure that diverted commuters onto "
    "rail for eight months,\" she noted. \"The real test comes next year, once "
    "that road reopens.\"\n\n"
    "Northline has announced plans to add two evening services on weekdays "
    "and to extend the flat-fare structure to weekend travel from April. The "
    "company has not committed to restoring the Sunday morning services "
    "withdrawn in 2019, despite repeated requests from local councils."
)

P7_DOUBLE_A = (
    "From: s.varga@aldercroftinstitute.org\n"
    "To: conference-committee@aldercroftinstitute.org\n"
    "Date: 3 February\n"
    "Subject: Venue shortlist for the autumn symposium\n\n"
    "Colleagues,\n\n"
    "I have now visited all three shortlisted venues for the November "
    "symposium. My notes are below.\n\n"
    "The Waterline Centre is the largest and the only one able to seat all "
    "400 delegates in a single room, but it has no breakout spaces and the "
    "nearest hotels are a twenty-minute drive away.\n\n"
    "Hollis Hall seats 320 in the main auditorium with four adjoining "
    "breakout rooms, and there are three hotels within walking distance. It "
    "is, however, the most expensive of the three by a considerable margin.\n\n"
    "The Fenwick Rooms would cost least, but the main hall seats only 260 and "
    "the building has no step-free access to the upper floor, where the "
    "catering is located.\n\n"
    "Given that last year's attendance was 340 and registrations are already "
    "ahead of this point last year, I recommend we proceed with Hollis Hall "
    "and seek sponsorship to offset the cost.\n\n"
    "Sofia Varga"
)

P7_DOUBLE_B = (
    "From: conference-committee@aldercroftinstitute.org\n"
    "To: s.varga@aldercroftinstitute.org\n"
    "Date: 6 February\n"
    "Subject: RE: Venue shortlist for the autumn symposium\n\n"
    "Sofia,\n\n"
    "Thank you for the thorough write-up. The committee met yesterday and "
    "agreed with your assessment on accessibility — we cannot in good "
    "conscience book a venue where some delegates would be unable to reach "
    "the catering independently, whatever the saving.\n\n"
    "We have approved your recommendation, subject to one condition: the "
    "finance office will only release the additional funds if we secure at "
    "least two sponsors before the end of March. Priya has agreed to lead on "
    "that.\n\n"
    "If sponsorship falls short, our fallback is the larger venue you listed "
    "first, and we would arrange a shuttle service to the hotels rather than "
    "ask delegates to drive.\n\n"
    "Regards,\n"
    "Conference Committee"
)


TOEIC_READING_QUESTIONS = [
    # ─── PART 5 — Incomplete Sentences (15) ──────────────────────────────────
    {
        "part": "part5",
        "questionText": "The project manager asked that all quarterly reports _____ submitted to the steering committee by Friday afternoon.",
        "options": ["A. are", "B. be", "C. were", "D. being"],
        "correctAnswer": "B",
        "explanation": "'Asked that' introduces a subjunctive clause of request, which takes the base form: 'be submitted'.",
        "difficulty": "medium",
        "tags": ["grammar", "subjunctive"],
    },
    {
        "part": "part5",
        "questionText": "Despite several technical delays during testing, the software update was launched _____ schedule.",
        "options": ["A. on", "B. at", "C. in", "D. to"],
        "correctAnswer": "A",
        "explanation": "'On schedule' is a fixed prepositional phrase meaning at the expected time.",
        "difficulty": "easy",
        "tags": ["prepositions", "collocation"],
    },
    {
        "part": "part5",
        "questionText": "Ms. Lawson has proved to be _____ of the two candidates interviewed for the senior marketing role.",
        "options": [
            "A. the most qualified",
            "B. more qualified",
            "C. the more qualified",
            "D. qualified",
        ],
        "correctAnswer": "C",
        "explanation": "Comparing exactly two people requires the comparative with 'the': 'the more qualified'.",
        "difficulty": "hard",
        "tags": ["grammar", "comparatives"],
    },
    {
        "part": "part5",
        "questionText": "_____ you intend to take extended leave during the third quarter, please inform the Human Resources manager.",
        "options": ["A. Should", "B. Whether", "C. Unless", "D. Provided"],
        "correctAnswer": "A",
        "explanation": "Inverted conditional: 'Should you intend' is a formal equivalent of 'If you intend'.",
        "difficulty": "hard",
        "tags": ["conditionals", "inversion"],
    },
    {
        "part": "part5",
        "questionText": "All attendees at the annual shareholder summit are required to display their badges _____ at all times.",
        "options": ["A. prominent", "B. prominence", "C. prominently", "D. most prominent"],
        "correctAnswer": "C",
        "explanation": "An adverb is needed to modify the verb 'display'.",
        "difficulty": "easy",
        "tags": ["parts-of-speech", "adverbs"],
    },
    {
        "part": "part5",
        "questionText": "Neither the chief executive officer nor the company directors _____ available to comment on the merger.",
        "options": ["A. was", "B. were", "C. is", "D. has been"],
        "correctAnswer": "B",
        "explanation": "With 'neither... nor', the verb agrees with the nearer subject; 'directors' is plural.",
        "difficulty": "medium",
        "tags": ["grammar", "subject-verb-agreement"],
    },
    {
        "part": "part5",
        "questionText": "The newly installed solar grid is expected to reduce factory energy costs _____ nearly 30 percent.",
        "options": ["A. by", "B. with", "C. for", "D. from"],
        "correctAnswer": "A",
        "explanation": "'By' expresses the margin of an increase or decrease.",
        "difficulty": "easy",
        "tags": ["prepositions", "business-vocabulary"],
    },
    {
        "part": "part5",
        "questionText": "Had the client submitted the requested documentation sooner, the loan application _____ processed earlier.",
        "options": ["A. will be", "B. would have been", "C. had been", "D. is being"],
        "correctAnswer": "B",
        "explanation": "Inverted third conditional: 'Had + past participle ... would have + past participle'.",
        "difficulty": "hard",
        "tags": ["conditionals", "third-conditional"],
    },
    {
        "part": "part5",
        "questionText": "The board of directors reached a _____ decision regarding the acquisition of the logistics firm.",
        "options": ["A. unanimous", "B. unanimousness", "C. unanimously", "D. unanimity"],
        "correctAnswer": "A",
        "explanation": "An adjective is required to modify the noun 'decision'.",
        "difficulty": "medium",
        "tags": ["vocabulary", "word-family"],
    },
    {
        "part": "part5",
        "questionText": "The factory manager insisted that all safety procedures be strictly _____ to at every stage of production.",
        "options": ["A. adhered", "B. followed", "C. observed", "D. compiled"],
        "correctAnswer": "A",
        "explanation": "'Adhere to' is the correct prepositional verb; 'followed' and 'observed' are close in meaning but do not take 'to'.",
        "difficulty": "medium",
        "tags": ["collocation", "phrasal-verbs"],
    },
    {
        "part": "part5",
        "questionText": "The consultants _____ the feasibility study for six weeks when the client abruptly changed the brief.",
        "options": ["A. conduct", "B. have conducted", "C. had been conducting", "D. will conduct"],
        "correctAnswer": "C",
        "explanation": "Past perfect continuous marks an action already in progress when a later past event interrupted it.",
        "difficulty": "hard",
        "tags": ["grammar", "verb-tense"],
    },
    {
        "part": "part5",
        "questionText": "Employees who wish to transfer to the Singapore office must submit their applications _____ themselves.",
        "options": ["A. they", "B. them", "C. their", "D. themselves"],
        "correctAnswer": "D",
        "explanation": "The reflexive pronoun is required because the subject and object refer to the same people.",
        "difficulty": "medium",
        "tags": ["grammar", "pronouns"],
    },
    {
        "part": "part5",
        "questionText": "_____ the supplier reduces its lead times, we will need to hold a larger buffer stock.",
        "options": ["A. Unless", "B. Despite", "C. Otherwise", "D. However"],
        "correctAnswer": "A",
        "explanation": "'Unless' introduces the negative condition under which the main clause holds.",
        "difficulty": "medium",
        "tags": ["conjunctions", "conditionals"],
    },
    {
        "part": "part5",
        "questionText": "The auditors found the accounts to be in _____ compliance with the revised reporting standards.",
        "options": ["A. full", "B. fully", "C. fullness", "D. filled"],
        "correctAnswer": "A",
        "explanation": "An adjective modifies the noun 'compliance'; 'in full compliance' is the standard collocation.",
        "difficulty": "easy",
        "tags": ["parts-of-speech", "collocation"],
    },
    {
        "part": "part5",
        "questionText": "Revenue growth in the third quarter was modest, _____ the substantial investment in advertising.",
        "options": ["A. although", "B. because of", "C. given", "D. despite"],
        "correctAnswer": "D",
        "explanation": "'Despite' takes a noun phrase and signals contrast; 'although' would require a full clause.",
        "difficulty": "medium",
        "tags": ["prepositions", "conjunctions"],
    },
    # ─── PART 6 — Text Completion (8: two sets of four) ───────────────────────
    {
        "part": "part6",
        "passageGroup": "toeic-p6-expense-memo",
        "passage": P6_MEMO,
        "questionText": "(1) Claims filed after that window _____ by the finance team, and reimbursement may be delayed.",
        "options": ["A. reviews", "B. will be reviewed", "C. have reviewed", "D. reviewing"],
        "correctAnswer": "B",
        "explanation": "The claim is acted upon, so a future passive is required.",
        "difficulty": "medium",
        "tags": ["grammar", "verb-tense", "text-cohesion"],
    },
    {
        "part": "part6",
        "passageGroup": "toeic-p6-expense-memo",
        "passage": P6_MEMO,
        "questionText": "(2) Which sentence best fits the blank?",
        "options": [
            "A. Costs may therefore be logged as they are incurred.",
            "B. The previous email address will remain active indefinitely.",
            "C. Receipts are no longer required for any claim.",
            "D. Training sessions have been cancelled this year.",
        ],
        "correctAnswer": "A",
        "explanation": "It follows directly from saving a trip in progress and leads into the reduced backlog.",
        "difficulty": "hard",
        "tags": ["sentence-insertion", "text-cohesion"],
    },
    {
        "part": "part6",
        "passageGroup": "toeic-p6-expense-memo",
        "passage": P6_MEMO,
        "questionText": "(3) Attendance is _____ for anyone who travels more than four times a year.",
        "options": ["A. mandatory", "B. mandate", "C. mandatorily", "D. mandating"],
        "correctAnswer": "A",
        "explanation": "An adjective is needed after the linking verb 'is'.",
        "difficulty": "easy",
        "tags": ["parts-of-speech", "word-family"],
    },
    {
        "part": "part6",
        "passageGroup": "toeic-p6-expense-memo",
        "passage": P6_MEMO,
        "questionText": "(4) A recording will be made _____ on the internal knowledge base.",
        "options": ["A. available", "B. availability", "C. avail", "D. availably"],
        "correctAnswer": "A",
        "explanation": "'Make something available' is the fixed pattern; the adjective completes it.",
        "difficulty": "medium",
        "tags": ["collocation", "word-family"],
    },
    {
        "part": "part6",
        "passageGroup": "toeic-p6-renovation-notice",
        "passage": P6_NOTICE,
        "questionText": "(1) All visitors _____ to use the side entrance on Miller Lane.",
        "options": ["A. asking", "B. are asked", "C. ask", "D. have asked"],
        "correctAnswer": "B",
        "explanation": "Visitors receive the instruction, so the passive is required.",
        "difficulty": "easy",
        "tags": ["grammar", "passive-voice"],
    },
    {
        "part": "part6",
        "passageGroup": "toeic-p6-renovation-notice",
        "passage": P6_NOTICE,
        "questionText": "(2) Which sentence best fits the blank?",
        "options": [
            "A. The loading bay will be closed for the duration of the works.",
            "B. Signage will be posted at both entrances throughout the works.",
            "C. All tenants must vacate the building by 12 September.",
            "D. The renovation has been postponed until next year.",
        ],
        "correctAnswer": "B",
        "explanation": "Only B is consistent with the surrounding text; A and D contradict it, and C is unsupported.",
        "difficulty": "hard",
        "tags": ["sentence-insertion", "text-cohesion"],
    },
    {
        "part": "part6",
        "passageGroup": "toeic-p6-renovation-notice",
        "passage": P6_NOTICE,
        "questionText": "(3) The improvements will _____ a redesigned reception desk, additional seating, and upgraded lighting.",
        "options": ["A. consist", "B. include", "C. compose", "D. contain"],
        "correctAnswer": "B",
        "explanation": "'Include' takes a direct object; 'consist' would need 'of', and the list is partial rather than exhaustive.",
        "difficulty": "medium",
        "tags": ["vocabulary", "collocation"],
    },
    {
        "part": "part6",
        "passageGroup": "toeic-p6-renovation-notice",
        "passage": P6_NOTICE,
        "questionText": "(4) Tenants should contact the management office _____ than emailing individual contractors.",
        "options": ["A. rather", "B. other", "C. sooner", "D. instead"],
        "correctAnswer": "A",
        "explanation": "'Rather than' is the correct comparative structure here; 'instead' would need 'of'.",
        "difficulty": "medium",
        "tags": ["conjunctions", "collocation"],
    },
    # ─── PART 7 — Reading Comprehension (15) ─────────────────────────────────
    {
        "part": "part7",
        "passageGroup": "toeic-p7-delivery-email",
        "passage": P7_EMAIL,
        "questionText": "What is the main purpose of the email?",
        "options": [
            "A. To confirm a change to a delivery schedule",
            "B. To apologise for a series of late shipments",
            "C. To request payment of an outstanding invoice",
            "D. To announce the closure of a distribution centre",
        ],
        "correctAnswer": "A",
        "explanation": "The opening paragraph states the writer is confirming the move from Tuesday to Thursday.",
        "difficulty": "easy",
        "tags": ["main-idea"],
    },
    {
        "part": "part7",
        "passageGroup": "toeic-p7-delivery-email",
        "passage": P7_EMAIL,
        "questionText": "Why is the cost per pallet decreasing?",
        "options": [
            "A. A fuel surcharge has been withdrawn",
            "B. Brightfield Foods has increased its order volume",
            "C. The shipment will be combined with other clients' consignments",
            "D. A long-term contract has been renewed",
        ],
        "correctAnswer": "C",
        "explanation": "The saving is attributed to consolidating the consignment with two other clients.",
        "difficulty": "medium",
        "tags": ["detail"],
    },
    {
        "part": "part7",
        "passageGroup": "toeic-p7-delivery-email",
        "passage": P7_EMAIL,
        "questionText": "What drawback does Mr. Castellanos identify?",
        "options": [
            "A. Deliveries will arrive later in the day",
            "B. The rate card will no longer be itemised",
            "C. Shipments will be limited to a single pallet",
            "D. The Aberdeen site will close on Thursdays",
        ],
        "correctAnswer": "A",
        "explanation": "He flags that arrival shifts from early morning to mid-afternoon.",
        "difficulty": "medium",
        "tags": ["detail", "inference"],
    },
    {
        "part": "part7",
        "passageGroup": "toeic-p7-workspace-advert",
        "passage": P7_ADVERT,
        "questionText": "What is indicated about the workshop facility?",
        "options": [
            "A. It is reserved for tenants of the largest units",
            "B. It will not be usable until November",
            "C. It is available only during staffed hours",
            "D. It is charged at an additional monthly rate",
        ],
        "correctAnswer": "B",
        "explanation": "The final line states it is unavailable until the second phase concludes in November.",
        "difficulty": "medium",
        "tags": ["detail"],
    },
    {
        "part": "part7",
        "passageGroup": "toeic-p7-workspace-advert",
        "passage": P7_ADVERT,
        "questionText": "What is NOT included in the quoted monthly rate?",
        "options": ["A. Utilities", "B. Business rates", "C. Parking", "D. Fibre connectivity"],
        "correctAnswer": "C",
        "explanation": "Parking is explicitly charged separately; the other three are stated as included.",
        "difficulty": "medium",
        "tags": ["detail", "negative-fact"],
    },
    {
        "part": "part7",
        "passageGroup": "toeic-p7-workspace-advert",
        "passage": P7_ADVERT,
        "questionText": "What must someone do to view a unit on a Monday?",
        "options": [
            "A. Pay a refundable deposit",
            "B. Contact the leasing office at least two days ahead",
            "C. Attend a scheduled open day",
            "D. Sign a minimum three-month agreement",
        ],
        "correctAnswer": "B",
        "explanation": "Viewings outside Wednesday and Saturday require 48 hours' notice.",
        "difficulty": "medium",
        "tags": ["inference", "detail"],
    },
    {
        "part": "part7",
        "passageGroup": "toeic-p7-workspace-advert",
        "passage": P7_ADVERT,
        "questionText": "The word \"terms\" in the first bullet point is closest in meaning to",
        "options": ["A. conditions of rental", "B. specialist vocabulary", "C. periods of study", "D. friendly relations"],
        "correctAnswer": "A",
        "explanation": "In a leasing context 'flexible terms' refers to the conditions of the rental agreement.",
        "difficulty": "easy",
        "tags": ["vocabulary-in-context"],
    },
    {
        "part": "part7",
        "passageGroup": "toeic-p7-rail-article",
        "passage": P7_ARTICLE,
        "questionText": "What does Northline credit for the rise in passenger numbers?",
        "options": [
            "A. The reopening of a major road",
            "B. The introduction of off-peak flat fares",
            "C. The restoration of Sunday services",
            "D. A reduction in journey times",
        ],
        "correctAnswer": "B",
        "explanation": "The operator attributes the rise chiefly to flat off-peak fares.",
        "difficulty": "easy",
        "tags": ["detail", "main-idea"],
    },
    {
        "part": "part7",
        "passageGroup": "toeic-p7-rail-article",
        "passage": P7_ARTICLE,
        "questionText": "What does Ms. Adeyemi suggest about the growth figure?",
        "options": [
            "A. It has been calculated incorrectly",
            "B. It understates the line's true performance",
            "C. It may partly reflect a temporary road closure",
            "D. It is typical of rail operators nationally",
        ],
        "correctAnswer": "C",
        "explanation": "She notes the line benefited from a road closure and that the real test comes when it reopens.",
        "difficulty": "hard",
        "tags": ["inference"],
    },
    {
        "part": "part7",
        "passageGroup": "toeic-p7-rail-article",
        "passage": P7_ARTICLE,
        "questionText": "What has Northline declined to commit to?",
        "options": [
            "A. Adding weekday evening services",
            "B. Extending flat fares to weekends",
            "C. Restoring the withdrawn Sunday morning services",
            "D. Publishing its passenger figures",
        ],
        "correctAnswer": "C",
        "explanation": "The final sentence says it has not committed to restoring those services.",
        "difficulty": "medium",
        "tags": ["detail", "negative-fact"],
    },
    {
        "part": "part7",
        "passageGroup": "toeic-p7-symposium-double",
        "passage": P7_DOUBLE_A + "\n\n---\n\n" + P7_DOUBLE_B,
        "questionText": "Why did Ms. Varga write the first email?",
        "options": [
            "A. To report on venue visits and recommend one",
            "B. To confirm a booking already made",
            "C. To request additional funding for catering",
            "D. To propose postponing the symposium",
        ],
        "correctAnswer": "A",
        "explanation": "She summarises visits to all three venues and recommends Hollis Hall.",
        "difficulty": "easy",
        "tags": ["main-idea"],
    },
    {
        "part": "part7",
        "passageGroup": "toeic-p7-symposium-double",
        "passage": P7_DOUBLE_A + "\n\n---\n\n" + P7_DOUBLE_B,
        "questionText": "Which venue did the committee agree to book?",
        "options": ["A. The Waterline Centre", "B. Hollis Hall", "C. The Fenwick Rooms", "D. No decision was reached"],
        "correctAnswer": "B",
        "explanation": "The reply approves her recommendation, which was Hollis Hall.",
        "difficulty": "medium",
        "tags": ["cross-reference", "detail"],
    },
    {
        "part": "part7",
        "passageGroup": "toeic-p7-symposium-double",
        "passage": P7_DOUBLE_A + "\n\n---\n\n" + P7_DOUBLE_B,
        "questionText": "Why was the least expensive venue rejected?",
        "options": [
            "A. It was already booked in November",
            "B. It lacked step-free access to the catering",
            "C. It had no breakout rooms",
            "D. It was too far from the hotels",
        ],
        "correctAnswer": "B",
        "explanation": "The Fenwick Rooms was cheapest; the committee cited accessibility to the catering as decisive.",
        "difficulty": "hard",
        "tags": ["cross-reference", "inference"],
    },
    {
        "part": "part7",
        "passageGroup": "toeic-p7-symposium-double",
        "passage": P7_DOUBLE_A + "\n\n---\n\n" + P7_DOUBLE_B,
        "questionText": "What condition did the finance office impose?",
        "options": [
            "A. That attendance exceed 340 delegates",
            "B. That at least two sponsors be secured by the end of March",
            "C. That the venue be booked before February ends",
            "D. That a shuttle service be arranged",
        ],
        "correctAnswer": "B",
        "explanation": "Funds are released only if at least two sponsors are secured before the end of March.",
        "difficulty": "medium",
        "tags": ["detail"],
    },
    {
        "part": "part7",
        "passageGroup": "toeic-p7-symposium-double",
        "passage": P7_DOUBLE_A + "\n\n---\n\n" + P7_DOUBLE_B,
        "questionText": "What is the fallback plan, and what problem would it create?",
        "options": [
            "A. The Waterline Centre, which lacks breakout spaces",
            "B. The Fenwick Rooms, which is too small",
            "C. Postponing the symposium until spring",
            "D. Reducing the number of delegates invited",
        ],
        "correctAnswer": "A",
        "explanation": "The fallback is 'the larger venue you listed first' — the Waterline Centre, which Varga noted has no breakout spaces.",
        "difficulty": "hard",
        "tags": ["cross-reference", "inference"],
    },
]

TOEIC_READING_TEMPLATE = {
    "seedKey": "toeic-reading-full",
    "seedVersion": "2",
    "name": "TOEIC Reading — Full Practice Test (Parts 5-7)",
    "examType": "toeic",
    "description": (
        "A complete TOEIC Reading practice test covering Part 5 (Incomplete "
        "Sentences), Part 6 (Text Completion) and Part 7 (Reading "
        "Comprehension, including a double-passage set)."
    ),
    "durationMinutes": 50,
    "passingScore": 60,
    "level": "Intermediate",
    "questions": TOEIC_READING_QUESTIONS,
}
