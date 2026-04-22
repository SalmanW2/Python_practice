import logging
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from config import RENDER_URL, SCOPES
from database import create_auth_session, verify_auth_session, save_login_data, is_blocked

def get_login_url(tg_id: int):
    state_uuid = create_auth_session(tg_id)
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri=f"{RENDER_URL}/callback"
    )
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', state=state_uuid)
    return auth_url

def process_callback(code: str, state_uuid: str):
    tg_id = verify_auth_session(state_uuid)
    
    if not tg_id:
        return False, "Security Error: Session expired or invalid CSRF token."
    
    try:
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES,
            redirect_uri=f"{RENDER_URL}/callback"
        )
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        user_info_service = build('oauth2', 'v2', credentials=creds)
        user_info = user_info_service.userinfo().get().execute()
        email = user_info.get("email")

        if is_blocked("email", email):
            return False, "Access Denied: This email address is blacklisted."

        token_json = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes
        }

        save_login_data(tg_id, email, token_json)
        return True, "Success! Your account is linked."
    except Exception as e:
        logging.error(f"Auth Error: {e}")
        return False, f"Authentication failed: {e}"
