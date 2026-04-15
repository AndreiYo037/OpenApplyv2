# Run OpenApplyv2 with Docker

## 1) Prerequisites

- Install Docker Desktop
- Ensure `docker` and `docker compose` commands are available

## 2) Configure environment

From project root, create `.env` from template:

```bash
cp .env.example .env
```

Set your API key in `.env`:

```env
OPENAI_API_KEY=your_real_openai_api_key
```

## 3) Build and run

From project root:

```bash
docker compose up --build
```

## 4) Access services

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Health check: `http://localhost:8000/health`

## 5) Stop services

In the same terminal:

```bash
Ctrl + C
```

Or in a new terminal:

```bash
docker compose down
```
