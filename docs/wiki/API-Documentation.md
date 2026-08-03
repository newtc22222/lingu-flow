# 📡 API Documentation

LinguFlow exposes a RESTful JSON API implemented using **FastAPI**. All endpoints are prefixed with `/api`.

Interactive API documentation is automatically available at runtime:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🔒 Authentication Headers

Protected endpoints require a valid JWT bearer token in the HTTP request header:
```http
Authorization: Bearer <your_jwt_access_token>
```

---

## 1. Authentication Endpoints (`/api/auth`)

| Method | Endpoint | Description | Protected |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register new account with email & password | No |
| `POST` | `/api/auth/login` | Authenticate user with credentials | No |
| `POST` | `/api/auth/guest` | Instant guest login (returns temporary guest token) | No |
| `POST` | `/api/auth/google` | Authenticate via Google OAuth2 ID token | No |
| `POST` | `/api/auth/forgot-password` | Request password reset verification link | No |
| `GET` | `/api/auth/me` | Fetch authenticated user profile | **Yes** |

### Request & Response Schemas:

#### `POST /api/auth/register`
**Request Body**:
```json
{
  "username": "candidate1",
  "email": "candidate1@example.com",
  "password": "Password123!"
}
```
**Response (201 Created)**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "c1f7b8e2-9d3a-4e2b-8a1f-0b2c3d4e5f6a",
    "username": "candidate1",
    "email": "candidate1@example.com",
    "isGuest": false
  }
}
```

---

## 2. Flashcard & SM-2 Endpoints (`/api/cards`)

| Method | Endpoint | Description | Protected |
|---|---|---|---|
| `GET` | `/api/cards/study` | Fetch cards due for review (`srs_next_review <= now()`) | **Yes** |
| `POST` | `/api/cards/review/{id}` | Process review score (1-4) via SM-2 algorithm | **Yes** |
| `GET` | `/api/cards` | List all flashcards owned by user | **Yes** |
| `POST` | `/api/cards` | Create a new flashcard | **Yes** |
| `PUT` | `/api/cards/{id}` | Update flashcard prompt or definition | **Yes** |
| `DELETE` | `/api/cards/{id}` | Delete flashcard | **Yes** |

#### Card Response Format (CamelCase `srsData` Contract):
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d4e5",
  "userId": "c1f7b8e2-9d3a-4e2b-8a1f-0b2c3d4e5f6a",
  "deckId": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "front": "Ephemeral",
  "back": "Lasting for a very short time",
  "srsData": {
    "interval": 1,
    "easeFactor": 2.5,
    "repetitions": 1,
    "nextReviewDate": "2026-08-05T00:00:00Z"
  },
  "createdAt": "2026-08-04T00:00:00Z",
  "updatedAt": "2026-08-04T00:00:00Z"
}
```

---

## 3. Deck Management Endpoints (`/api/decks`)

| Method | Endpoint | Description | Protected |
|---|---|---|---|
| `GET` | `/api/decks` | List all decks owned by user with aggregated `cardCount` | **Yes** |
| `POST` | `/api/decks` | Create a new study deck | **Yes** |
| `PUT` | `/api/decks/{id}` | Update deck name and description | **Yes** |
| `DELETE` | `/api/decks/{id}` | Delete deck (unlinks attached cards) | **Yes** |

#### Deck Response Format:
```json
{
  "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "userId": "c1f7b8e2-9d3a-4e2b-8a1f-0b2c3d4e5f6a",
  "name": "TOEIC Essential Vocabulary",
  "description": "High-frequency Part 5 & 6 words",
  "cardCount": 42,
  "createdAt": "2026-08-04T00:00:00Z",
  "updatedAt": "2026-08-04T00:00:00Z"
}
```

---

## 4. Exam Simulator Endpoints (`/api/exams`)

| Method | Endpoint | Description | Protected |
|---|---|---|---|
| `GET` | `/api/exams/templates` | List public & user custom templates | Optional |
| `POST` | `/api/exams/templates` | Create custom exam template | **Yes** |
| `GET` | `/api/exams/templates/{id}` | Get template metadata | Optional |
| `DELETE` | `/api/exams/templates/{id}` | Delete custom template | **Yes** |
| `GET` | `/api/exams/templates/{id}/questions` | List template questions | Optional |
| `POST` | `/api/exams/templates/{id}/questions` | Add question to template | **Yes** |
| `GET` | `/api/exams/sessions` | List user exam history (last 50) | **Yes** |
| `POST` | `/api/exams/sessions` | Start new exam session | **Yes** |
| `GET` | `/api/exams/sessions/{id}` | Fetch session status | **Yes** |
| `GET` | `/api/exams/sessions/{id}/details` | Fetch session, template, questions, & user answers map | **Yes** |
| `PUT` | `/api/exams/sessions/{id}/answer` | Record answer for a question | **Yes** |
| `PUT` | `/api/exams/sessions/{id}/finish` | Finalize session & calculate percentage score | **Yes** |

---

## 5. Real-Time & Media Endpoints

| Method | Endpoint | Description | Protected |
|---|---|---|---|
| `GET` | `/api/events` | Server-Sent Events (SSE) progress stream (`text/event-stream`) | Optional |
| `POST` | `/api/media/presign-upload` | Generate presigned PUT URL for Cloudflare R2 upload | **Yes** |
| `GET` | `/api/media/presign-download/{file_key}` | Generate presigned GET URL for private R2 media | **Yes** |
| `GET` | `/api/health` | Health check endpoint (`{"status": "ok"}`) | No |
