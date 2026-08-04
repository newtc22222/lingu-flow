# 🚀 LinguFlow Release v0.1.0

**Release Tag**: `v0.1.0`  
**Release Date**: August 5, 2026  
**Target Environment**: Production (Vercel Frontend + Railway FastAPI/PostgreSQL Backend)

---

## 🌟 Overview

LinguFlow v0.1.0 represents the complete architectural migration from Node.js/MongoDB to a high-performance **Python FastAPI** backend powered by **PostgreSQL 16**, **SQLAlchemy 2.0 (Async)**, **Alembic**, and **SuperMemo-2 (SM-2)** spaced repetition engine.

---

## 📋 Changelog & Key Features

### 🔐 1. Authentication & Security (`/api/auth`)
- Direct password hashing using `bcrypt` and JWT token handling.
- Social login via Google OAuth2.
- In-place guest account data migration preserving 100% of guest cards and decks.
- Added `POST /api/auth/forgot-password` endpoint.

### 🃏 2. Flashcards & SM-2 Engine (`/api/cards`)
- Pure Python SM-2 algorithm mapping review ratings (1-4 -> 0-5), dynamic interval calculation, and ease factor floor (1.3).
- Study queue filtering (`GET /api/cards/study`).
- CamelCase `srsData` formatting for seamless Vue 3 frontend integration.

### 📚 3. Deck Management (`/api/decks`)
- Deck CRUD operations.
- Dynamic `cardCount` aggregation via Outer Join queries.

### 📝 4. Exam Simulator Engine (`/api/exams`)
- Pre-seeded with **33 built-in practice questions** across TOEIC Part 5, IELTS Academic Reading, HSK Level 2, and JLPT N5.
- Timed practice sessions, passage rendering, multiple-choice options, instant scoring, and detailed review maps.

### ⚡ 5. Real-Time Events & Storage
- Server-Sent Events (`GET /api/events`) for progress stream with 15s keepalive heartbeats.
- S3 presigned PUT/GET URLs for Cloudflare R2 media storage (`/api/media`).

---

## 🧪 Automated Test Verification
- **Backend Unit & Integration Tests**: 31 test cases passing (`pytest` completed in 5.46s).
- **Frontend Production Build**: Vue 3 / Vite production bundle compiled in 738ms without errors.
