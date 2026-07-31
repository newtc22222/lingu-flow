# Deploying LinguFlow to Vercel

This guide outlines the steps to successfully deploy LinguFlow—a monorepo containing a Vue/Vite frontend and a Node.js/Express backend—to Vercel.

Because the project has been restructured with a root `package.json` and a Serverless Function entry point (`api/index.ts`), Vercel can automatically build and deploy both the frontend and backend simultaneously in a single project.

## Prerequisites

1. **GitHub Account**: Your codebase must be pushed to a repository on GitHub (or GitLab/Bitbucket).
2. **Vercel Account**: Sign up or log in to [Vercel](https://vercel.com/).
3. **MongoDB Atlas Database**: Vercel is a serverless platform, which means you cannot run a local MongoDB instance. You will need a cloud-hosted MongoDB cluster (e.g., MongoDB Atlas).

## Step-by-Step Deployment Guide

### 1. Push Code to GitHub
Ensure all your recent changes (specifically the Vercel restructuring) are committed and pushed to your remote repository.

### 2. Import the Project into Vercel
1. Go to your Vercel Dashboard and click **Add New... > Project**.
2. Connect your GitHub account (if you haven't already) and select the LinguFlow repository.
3. Click **Import**.

### 3. Configure Project Settings
In the configuration screen, Vercel will attempt to auto-detect your project settings. Ensure the following configurations are set:

- **Framework Preset**: Leave it as `Vite`. Vercel will automatically detect the Vue frontend.
- **Root Directory**: Leave it as the root directory (`./`). Do **not** set it to `frontend` or `backend`, otherwise the serverless functions will not be detected.
- **Build Command**: Leave as default or explicitly set to `npm run build`. Since we set up NPM Workspaces in the root `package.json`, this will build both the frontend and backend.
- **Output Directory**: `frontend/dist` (This is where the compiled Vue SPA lives).
- **Install Command**: `npm install` (This will install both frontend and backend dependencies via workspaces).

### 4. Setup Environment Variables
Before clicking Deploy, expand the **Environment Variables** section and add the following required variables:

| Name | Value | Description |
|---|---|---|
| `MONGO_URI` | `mongodb+srv://<username>:<password>@cluster0.mongodb.net/linguflow?retryWrites=true&w=majority` | Your cloud MongoDB connection string. |
| `JWT_SECRET` | `your_secure_random_string` | A strong, random string used to sign JWT authentication tokens. |
| `PORT` | `3000` | Optional for serverless, but good practice. |

*(Note: If you have real Google OAuth credentials, replace `DUMMY_CLIENT_ID` in the frontend code with your real Client ID and configure any backend OAuth secrets if necessary).*

### 5. Deploy
Click the **Deploy** button. Vercel will:
1. Run `npm install` at the root, linking workspaces.
2. Build the Vite frontend into `frontend/dist`.
3. Detect the `api/index.ts` file and deploy the Express app as a Serverless Function.
4. Apply the routing rules from `vercel.json` (routing `/api/*` to the backend).

Once the deployment finishes, you will be given a live URL (e.g., `https://linguflow.vercel.app`). 

## Troubleshooting

- **500 Internal Server Error on API calls**: Check the "Logs" tab in your Vercel dashboard. This usually means your serverless function failed to connect to MongoDB. Ensure your `MONGO_URI` is correct and that your MongoDB Atlas network settings allow connections from anywhere (`0.0.0.0/0`).
- **404 on Page Refreshes**: The `vercel.json` file handles SPA rewrites (sending all non-API traffic to `/index.html`). Ensure this file exists at the root of your repository.
- **Missing Dependencies**: Ensure you committed the root `package.json` and `package-lock.json`. Vercel needs these to understand the workspace structure.
