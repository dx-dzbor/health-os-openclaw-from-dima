#!/usr/bin/env python3
"""
WHOOP OAuth Authentication Helper

Runs OAuth flow to get access and refresh tokens.
Use this for first-time setup or when tokens expire.

Usage:
    python auth.py
"""

import os
import json
import secrets
import webbrowser
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from flask import Flask, request
import requests
from dotenv import load_dotenv


# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
CONFIG_FILE = BASE_DIR / "data" / "integrations" / "whoop" / "config.json"


def run_oauth_flow():
    """Run full OAuth flow with local callback server."""
    load_dotenv()

    client_id = os.getenv("WHOOP_CLIENT_ID")
    client_secret = os.getenv("WHOOP_CLIENT_SECRET")
    redirect_uri = os.getenv("WHOOP_REDIRECT_URI", "https://localhost:8000/callback")

    if not client_id or not client_secret:
        print("Error: Missing WHOOP_CLIENT_ID or WHOOP_CLIENT_SECRET in .env")
        print("Create .env file with your WHOOP API credentials.")
        return False

    # OAuth endpoints
    auth_url = "https://api.prod.whoop.com/oauth/oauth2/auth"
    token_url = "https://api.prod.whoop.com/oauth/oauth2/token"

    # Generate state for CSRF protection
    oauth_state = secrets.token_urlsafe(32)

    # Storage for authorization code
    auth_data = {"code": None, "error": None, "state": None}

    # Create Flask app for callback
    app = Flask(__name__)
    app.logger.disabled = True

    @app.route('/callback')
    def callback():
        auth_data["code"] = request.args.get('code')
        auth_data["error"] = request.args.get('error')
        auth_data["state"] = request.args.get('state')

        if auth_data["error"]:
            return f"""
            <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: #d32f2f;">Authentication Failed</h1>
                <p>Error: {auth_data["error"]}</p>
            </body></html>
            """, 400

        return """
        <html><body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: #4caf50;">Authentication Successful!</h1>
            <p>You can close this window.</p>
            <script>setTimeout(() => window.close(), 2000);</script>
        </body></html>
        """

    # Build authorization URL
    scopes = "offline read:recovery read:cycles read:sleep read:workout read:profile read:body_measurement"
    auth_params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scopes,
        "state": oauth_state
    }
    authorization_url = f"{auth_url}?{urlencode(auth_params)}"

    # Start server
    port = int(redirect_uri.split(":")[-1].split("/")[0])

    print("\n" + "="*60)
    print("WHOOP OAuth Authentication")
    print("="*60 + "\n")

    server_thread = threading.Thread(
        target=lambda: app.run(port=port, ssl_context='adhoc', debug=False, use_reloader=False),
        daemon=True
    )
    server_thread.start()
    time.sleep(1)

    print(f"Opening browser for authentication...")
    print(f"If browser doesn't open, visit:\n{authorization_url}\n")
    webbrowser.open(authorization_url)

    print("Waiting for authentication callback...")
    while auth_data["code"] is None and auth_data["error"] is None:
        time.sleep(0.5)

    if auth_data["error"]:
        print(f"Error: {auth_data['error']}")
        return False

    if auth_data["state"] != oauth_state:
        print("Error: OAuth state mismatch")
        return False

    print("Authorization code received! Exchanging for tokens...\n")

    # Exchange code for tokens
    token_response = requests.post(
        token_url,
        data={
            "grant_type": "authorization_code",
            "code": auth_data["code"],
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri
        }
    )

    if token_response.status_code != 200:
        print(f"Error getting tokens: {token_response.text}")
        return False

    tokens = token_response.json()

    # Save tokens
    config = {
        'access_token': tokens['access_token'],
        'expires_at': tokens.get('expires_in', 3600) + int(time.time()),
        'saved_at': datetime.now().isoformat()
    }

    if 'refresh_token' in tokens:
        config['refresh_token'] = tokens['refresh_token']

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

    print("="*60)
    print(f"Tokens saved to: {CONFIG_FILE}")
    print("="*60 + "\n")

    # Quick test
    try:
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        profile = requests.get(
            "https://api.prod.whoop.com/developer/v1/user/profile/basic",
            headers=headers
        ).json()
        print(f"Connected as: {profile.get('first_name')} {profile.get('last_name')}")
    except Exception as e:
        print(f"Profile check failed: {e}")

    return True


if __name__ == "__main__":
    success = run_oauth_flow()
    exit(0 if success else 1)
