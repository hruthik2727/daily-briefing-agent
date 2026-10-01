# Daily Briefing Agent — Local Full-Stack MVP

This version includes a Django backend, connected dashboard/API, Gmail OAuth flow, encrypted local token storage, Gmail read-only metadata/snippet retrieval, rule-based priority classification, and optional AI summaries.

## 1. Install (Windows PowerShell)
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```
Generate a Fernet key and put the result in `TOKEN_ENCRYPTION_KEY` in `.env`:
```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Generate a Django secret too, and replace `DJANGO_SECRET_KEY`:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
Then:
```powershell
python manage.py makemigrations briefing
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```
Open http://127.0.0.1:8000/

## 2. Configure Gmail OAuth
1. Open Google Cloud Console and create/select a project.
2. Enable the Gmail API.
3. Configure the OAuth consent screen and add your Google account as a test user if the app is in testing.
4. Create an OAuth Client ID of type **Web application**.
5. Add this exact authorized redirect URI: `http://127.0.0.1:8000/auth/gmail/callback/`
6. Copy the Client ID and Client Secret into `.env` as `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
7. Restart Django and click **Connect Gmail**.
8. Approve the requested Gmail read-only scope. The app requests `gmail.readonly`; it does not send, delete, or modify emails.

For local development only, OAuth may require adding the local redirect URI to the client. Never expose this development server to the public internet.

## 3. Optional AI summaries
Set `OPENAI_API_KEY` in `.env` to enable the optional OpenAI summary step. Without it, the dashboard uses Gmail snippets and local rule-based prioritization. Review the AI provider's data-handling terms before sending any private email content to an external API. Email content is untrusted input; do not allow it to trigger tools or actions.

## 4. Endpoints
- `GET /api/health/`
- `GET /api/status/`
- `GET /api/overview/`
- `GET /api/highlights/`
- `POST /api/briefing/refresh/`
- `GET /auth/gmail/start/`
- `GET /auth/gmail/callback/`
- `POST /auth/gmail/disconnect/`

## 5. What is and isn't complete
Implemented: local Django app, connected dashboard, demo fallback, Gmail OAuth authorization-code flow with state checking, encrypted OAuth token storage, read-only Gmail metadata/snippet fetch, local urgency/action heuristics, optional AI summaries, disconnect endpoint.

Still needs before production: per-user authentication and authorization, stronger rate limiting, production HTTPS/security settings, tests and monitoring, proper OAuth verification/consent configuration, background scheduler, retention UI, and provider-specific integration work. WhatsApp personal chats are not available through a general public API; Telegram requires a bot and can only access conversations the bot is allowed to see. Do not promise access to arbitrary personal chats.

## Privacy and safety
- Run bound to localhost for personal development.
- Never commit `.env`, credentials, or tokens.
- Token JSON is encrypted using `TOKEN_ENCRYPTION_KEY` before being stored in SQLite.
- Disconnect deletes the local stored token; also revoke app access in Google Account security settings if you want to revoke the OAuth grant.
- The app reads Gmail metadata/snippets only, not full message bodies, in this MVP.
