# backend/authenticate_google_browser.py

from google_auth_oauthlib.flow import InstalledAppFlow
import json
import os
import webbrowser

SCOPES = ['https://www.googleapis.com/auth/assistant-sdk-prototype']

def authenticate():
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        return
    
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES
    )
    
    # Try different port
    try:
        print("🌐 Opening browser for authentication...")
        print("If browser doesn't open, go to: http://localhost:8090")
        
        credentials = flow.run_local_server(
            port=8090,  # Different port
            open_browser=True,
            authorization_prompt_message='Please visit this URL: {url}',
            success_message='Authentication successful! You can close this window.',
        )
        
        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        with open('google_assistant_credentials.json', 'w') as f:
            json.dump(creds_data, f, indent=2)
        
        print("✅ Authentication successful!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Try the manual method: python authenticate_google.py")

if __name__ == '__main__':
    authenticate()