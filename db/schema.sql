CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    parent_kp_id INTEGER REFERENCES knowledge_points(id),
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    difficulty TEXT CHECK(difficulty IN ('easy', 'medium', 'hard')) DEFAULT 'medium',
    level INTEGER DEFAULT 0,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kp_subject ON knowledge_points(subject_id);
CREATE INDEX IF NOT EXISTS idx_kp_parent ON knowledge_points(parent_kp_id);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kp_id INTEGER NOT NULL REFERENCES knowledge_points(id),
    question_type TEXT CHECK(question_type IN ('choice', 'fill', 'true_false', 'short_answer', 'essay')) DEFAULT 'choice',
    content TEXT NOT NULL,
    options TEXT DEFAULT NULL,
    answer TEXT NOT NULL,
    explanation TEXT DEFAULT '',
    difficulty TEXT CHECK(difficulty IN ('easy', 'medium', 'hard')) DEFAULT 'medium',
    source TEXT DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_questions_kp ON questions(kp_id);
CREATE INDEX IF NOT EXISTS idx_questions_diff ON questions(difficulty);

CREATE TABLE IF NOT EXISTS question_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL REFERENCES questions(id),
    tag_name TEXT NOT NULL,
    UNIQUE(question_id, tag_name)
);

CREATE INDEX IF NOT EXISTS idx_tags_name ON question_tags(tag_name);

CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    total_questions INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    mode TEXT CHECK(mode IN ('practice', 'review', 'exam', 'free')) DEFAULT 'practice',
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS practice_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES study_sessions(id),
    question_id INTEGER NOT NULL REFERENCES questions(id),
    student_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    time_spent_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_practice_session ON practice_records(session_id);
CREATE INDEX IF NOT EXISTS idx_practice_question ON practice_records(question_id);

CREATE TABLE IF NOT EXISTS mistake_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL REFERENCES questions(id),
    student_answer TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    error_type TEXT DEFAULT 'unknown',
    resolved BOOLEAN DEFAULT FALSE,
    session_id INTEGER REFERENCES study_sessions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mistake_question ON mistake_log(question_id);
CREATE INDEX IF NOT EXISTS idx_mistake_resolved ON mistake_log(resolved);

CREATE TABLE IF NOT EXISTS mastery_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kp_id INTEGER NOT NULL REFERENCES knowledge_points(id),
    score REAL CHECK(score >= 0.0 AND score <= 1.0) DEFAULT 0.0,
    confidence REAL CHECK(confidence >= 0.0 AND confidence <= 1.0) DEFAULT 0.0,
    last_practiced TIMESTAMP,
    review_count INTEGER DEFAULT 0,
    next_review_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(kp_id)
);

CREATE TABLE IF NOT EXISTS study_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_type TEXT CHECK(report_type IN ('daily', 'weekly', 'session', 'analysis', 'plan')) NOT NULL,
    content_path TEXT NOT NULL,
    session_id INTEGER REFERENCES study_sessions(id),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL DEFAULT 'default',
    seq INTEGER NOT NULL DEFAULT 0,
    role TEXT CHECK(role IN ('user', 'assistant')) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conv_session ON conversation_messages(session_id, seq);

CREATE TABLE IF NOT EXISTS general_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    category TEXT DEFAULT '通用',
    tags TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gk_category ON general_knowledge(category);
