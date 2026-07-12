# LinguFlow Project Memory & Guidelines

This document serves as the project-scoped memory and guidelines for agents working on LinguFlow, a minimalist, keyboard-driven flashcard web app utilizing a Spaced Repetition System (SRS) based on the SuperMemo-2 (SM-2) algorithm.

## Technology Stack
- **Backend**: Node.js, Express, TypeScript, MongoDB (Mongoose).
- **Frontend**: Vue 3 (Composition API), Vite, Tailwind CSS.
- **Real-time**: Server-Sent Events (SSE) implemented via `EventEmitter` in `app.ts` for real-time review updates.

## Architecture & Design Decisions
1. **Flashcard Organization**: Cards are organized into `Deck`s. The data model involves a `Deck` schema (name, description) and a `Card` schema containing a `deckId` reference.
2. **Authentication Flow**:
   - We support three types of authentication: Standard (JWT via Email/Password), Google OAuth2, and Anonymous Guest Auth.
   - **Guest Migration**: Guests use the app anonymously but receive a valid JWT token. When a guest registers or logs in with Google, the frontend passes their `guest_token`. The backend merges their existing progress (Cards/Decks) into their newly provisioned or logged-in account, and toggles `isGuest: false`.
   - **Frontend API**: A custom fetch wrapper (`api.ts`) automatically attaches the JWT token to all API requests.
3. **UI Layout Strategy**:
   - The app prioritizes a distraction-free `StudyDashboard.vue` for learning.
   - Administrative tasks (managing cards and decks) are handled in dedicated views (`CardManagement.vue`, `DeckManagement.vue`) rather than modals, accessible via a global navigation bar.
4. **Dependency Injection**: The backend uses basic DI (e.g., `CardController` receives `CardService`) for testability and modularity.

## Agent Instructions
- **Modifying Auth**: When altering authentication, always preserve the Guest data migration logic. Ensure `guest_token` fallback logic remains intact in the frontend.
- **Styling**: Maintain the sleek, dark-themed (slate/emerald) Tailwind CSS design language. Avoid cluttered UI elements.
- **Component State**: Use Vue 3 Composition API (`<script setup>`) exclusively.
