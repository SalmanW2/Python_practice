import logging
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from config import RENDER_URL, SCOPES
from database import save_login_data

# Temporary memory to store Flow
oauth_sessions = {}

def get_login_url(tg_id: int):
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri=f"{RENDER_URL}/callback"
    )
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', state=str(tg_id))
    oauth_sessions[str(tg_id)] = flow
    return auth_url

def process_callback(code: str, tg_id: str):
    flow = oauth_sessions.get(tg_id)
    if not flow:
        return False, "Session expired. Please type /start in bot again."
    
    try:
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        user_info_service = build('oauth2', 'v2', credentials=creds)
        user_info = user_info_service.userinfo().get().execute()
        email = user_info.get("email")

        token_json = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes
        }

        # Save to Database
        save_login_data(tg_id, email, token_json)
        del oauth_sessions[tg_id]
        
        return True, "Success! Your account is linked. You can close this tab."
    except Exception as e:
        logging.error(f"Auth Error: {e}")
        return False, f"Authentication failed: {e}"
