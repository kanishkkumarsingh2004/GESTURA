# Gesture Recognition Frontend (Next.js)

Next.js frontend for the Gesture Recognition FastAPI backend.

## Environment Variables

The backend API URL is configured strictly via environment variables in `.env`:

```env
# Backend API URL (FastAPI instance)
BACK_END_url="http://localhost:8000"
NEXT_PUBLIC_BACKEND_URL="http://localhost:8000"
NEXT_PUBLIC_API_URL="http://localhost:8000"
```

Next.js will proxy `/api/*` requests to this backend URL using Next.js rewrites, avoiding browser cross-origin (CORS) restrictions.

## Getting Started

First, run the development server:

```bash
npm run dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.
