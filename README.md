# LinguFlow

LinguFlow is a minimalist, keyboard-driven flashcard web app utilizing a Spaced Repetition System (SRS) based on the SuperMemo-2 (SM-2) algorithm. It is designed to be distraction-free and highly efficient.

## Features

- **Keyboard-Driven**: Press `Spacebar` to flip cards, and `1`, `2`, `3`, `4` to grade yourself.
- **Markdown Support**: Both front and back of the cards fully support Markdown.
- **Spaced Repetition System (SRS)**: Employs the robust SM-2 algorithm to schedule cards optimally.
- **Real-Time Updates**: Utilizes Server-Sent Events (SSE) to deliver instant progression notifications.
- **Docker-Ready**: Packaged for ease of deployment.

## Tech Stack

- **Backend**: Node.js, Express, TypeScript, Mongoose
- **Frontend**: Vue.js 3 (Composition API), Vite, TailwindCSS v4
- **Database**: MongoDB

## Quickstart (Docker)

The fastest way to test the MVP locally is using Docker.

1. Ensure [Docker](https://www.docker.com/) and Docker Compose are installed.
2. In the project root, run:
   ```bash
   docker-compose up --build
   ```
3. Open your browser to `http://localhost:8080`.
   - The backend API runs on port `3000`.
   - MongoDB runs on port `27017`.

### Local Development (Without Docker)

You can also run the components locally if you have MongoDB installed on your system.

**1. MongoDB:**
Ensure MongoDB is running locally on `127.0.0.1:27017`.

**2. Backend:**
```bash
cd backend
npm install
npm run dev
```

*(Optional: To seed the database with sample cards: `npx tsx src/seed.ts`)*

**3. Frontend:**
```bash
cd frontend
npm install
npm run dev
```
*(Vite proxies API requests to the backend automatically).*
