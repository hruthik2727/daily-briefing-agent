import secrets
from urllib.parse import urlencode
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from google_auth_oauthlib.flow import Flow
from .models import GmailConnection
from .services import GMAIL_SCOPES, fetch_gmail_highlights, summarize_with_ai

DEMO_MESSAGES = [
    {"id":"demo-1","source":"Email","sender":"Priya","title":"Q4 budget","desc":"She proposed an 8% cut to the events line and needs your sign-off by Monday.","priority":"action","icon":"✉","unread":True,"time":"Today","url":"#"},
    {"id":"demo-2","source":"WhatsApp","sender":"Team group","title":"Offsite venue","desc":"Two venues left; voting closes tomorrow at noon. Most people lean toward the lakeside option.","priority":"urgent","icon":"◉","unread":True,"time":"Today","url":"#"},
    {"id":"demo-3","source":"Telegram","sender":"DevOps channel","title":"Server alert","desc":"A brief outage this afternoon was resolved. No action needed; post-mortem planned for Friday.","priority":"info","icon":"➤","unread":False,"time":"Today","url":"#"},
    {"id":"demo-4","source":"WhatsApp","sender":"Mom","title":"Dinner plans","desc":"She's asking if you're free Sunday and is waiting on your reply.","priority":"action","icon":"◉","unread":True,"time":"Today","url":"#"},
    {"id":"demo-5","source":"Email","sender":"Alex","title":"Vendor contract","desc":"Revised terms extend the notice period. Legal wants feedback before Friday's call.","priority":"urgent","icon":"✉","unread":True,"time":"Today","url":"#"},
]

@ensure_csrf_cookie
def dashboard(request):
    return render(request, "dashboard.html")

@require_GET
def health(request):
    return JsonResponse({"status":"ok","service":"daily-briefing-agent"})

def _get_messages():
    try:
        live = fetch_gmail_highlights()
        if live is not None:
            return summarize_with_ai(live), "gmail"
    except Exception as exc:
        return DEMO_MESSAGES, "demo"
    return DEMO_MESSAGES, "demo"

@require_GET
def highlights(request):
    messages, mode = _get_messages()
    source = request.GET.get("source", "all")
    priority = request.GET.get("priority", "all")
    query = request.GET.get("q", "").strip().lower()
    if source != "all":
        messages = [m for m in messages if m["source"].lower() == source.lower()]
    if priority != "all":
        messages = [m for m in messages if m["priority"] == priority]
    if query:
        messages = [m for m in messages if query in " ".join([m["title"],m["sender"],m["source"],m["desc"]]).lower()]
    return JsonResponse({"mode":mode,"count":len(messages),"items":messages,
        "notice":"Live Gmail metadata/snippets" if mode == "gmail" else "Sample data only; connect Gmail to use live email."})

@require_GET
def overview(request):
    messages, mode = _get_messages()
    unread = sum(1 for m in messages if m["unread"])
    actions = sum(1 for m in messages if m["priority"] == "action")
    urgent = sum(1 for m in messages if m["priority"] == "urgent")
    return JsonResponse({"mode":mode,"messages_scanned":len(messages),"unread":unread,
                         "action_items":actions,"needs_attention":urgent})

@require_GET
def status(request):
    connected = GmailConnection.objects.filter(provider="gmail").exists()
    connection = GmailConnection.objects.filter(provider="gmail").first()
    return JsonResponse({
        "gmail_connected": connected,
        "connected_email": connection.connected_email if connection else "",
        "ai_enabled": bool(settings.OPENAI_API_KEY),
        "mode": "gmail" if connected else "demo",
        "whatsapp": "not connected",
        "telegram": "not connected",
    })

def _flow(state=None):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise RuntimeError("Google OAuth is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env.")
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    flow = Flow.from_client_config(client_config, scopes=GMAIL_SCOPES, state=state)
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    return flow

@require_GET
def gmail_start(request):
    try:
        flow = _flow()
        state = secrets.token_urlsafe(32)
        request.session["gmail_oauth_state"] = state
        authorization_url, _ = flow.authorization_url(
            access_type="offline", include_granted_scopes="true", prompt="consent", state=state
        )
        return HttpResponseRedirect(authorization_url)
    except Exception as exc:
        return HttpResponse("Gmail setup error: " + str(exc) + ". See README.md for setup steps.", status=400)

@require_GET
def gmail_callback(request):
    state = request.session.get("gmail_oauth_state")
    if not state or request.GET.get("state") != state:
        return HttpResponse("OAuth state validation failed. Please restart Gmail connection.", status=400)
    if request.GET.get("error"):
        return HttpResponse("Google authorization was not completed. You can return to the dashboard.", status=400)
    try:
        flow = _flow(state=state)
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials
        # Save encrypted credentials; profile lookup confirms the authorized account.
        from .services import save_credentials
        save_credentials(credentials)
        request.session.pop("gmail_oauth_state", None)
        return HttpResponseRedirect("/")
    except Exception as exc:
        return HttpResponse("Could not complete Gmail connection: " + str(exc) + ". Check server logs and OAuth configuration.", status=400)

@require_POST
def gmail_disconnect(request):
    GmailConnection.objects.filter(provider="gmail").delete()
    return JsonResponse({"ok": True, "message": "Local encrypted Gmail token removed. You can also revoke access from your Google Account security settings."})

@require_POST
def refresh_briefing(request):
    messages, mode = _get_messages()
    return JsonResponse({"ok": True, "mode": mode, "count": len(messages), "message": "Briefing refreshed."})
