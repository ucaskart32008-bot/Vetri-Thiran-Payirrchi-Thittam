# PocketSmart AI
FastAPI + Gemini budget recommendation app for Home, Party, and Jewelry planning.

## VS Code setup
1. Install Python 3.10+ and open this folder in VS Code.
2. Terminal: `py -m venv .venv` (Windows) or `python3 -m venv .venv` (macOS/Linux).
3. Activate: `.venv\\Scripts\\activate` (Windows) or `source .venv/bin/activate` (macOS/Linux).
4. Install: `python -m pip install -r requirements.txt`.
5. Copy `.env.example` to `.env`, change `SECRET_KEY`, optionally set `GEMINI_API_KEY`.
6. Run: `uvicorn app.main:app --reload`; open http://127.0.0.1:8000. API docs: /docs.
7. Test: `pytest -q`.

Without a Gemini key the app uses clearly identified demo recommendations. Marketplace links are search links, not verified live inventory or prices. Production deployment should use HTTPS, rate limiting, a managed database, secure cookie settings and secret rotation.

API: POST /api/auth/register (JSON); POST /api/auth/login (form username/password); GET /api/auth/me; POST /api/generate-home and /api/generate-party (JSON); POST /api/generate-jewelry (multipart); GET /api/history; GET/DELETE /api/history/{id}.
