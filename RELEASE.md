# Release Notes - v1.0.0 (MVP)

**Date**: 2026-07-12

## 🎉 Initial Release

We are excited to announce the initial release of LinguFlow MVP!

### Features
- **Spaced Repetition Algorithm**: Implementation of SuperMemo-2 (SM-2) for optimal flashcard scheduling.
- **Minimalist Dashboard**: Distraction-free interface built with Vue 3 and Tailwind CSS v4.
- **Keyboard Shortcuts**: Spacebar to flip, keys `1` to `4` for instant review scoring.
- **Markdown Ready**: Create rich flashcards with full Markdown support, sanitized securely via DOMPurify.
- **Real-Time Notifications**: Integrated Server-Sent Events (SSE) that trigger instant visual feedback upon card completion.

### DevOps
- **Dockerized Architecture**: Simplified orchestration with `docker-compose.yml`, spinning up MongoDB, the Node/Express Backend, and an Nginx-served Vue Frontend instantly.

## Known Limitations (MVP)
- Single mock user system. Authentication (JWT/OAuth) will be introduced in the next iterations.
- Flashcard management interface (Add/Edit/Delete) is not yet built in the UI, but API endpoints are available.
