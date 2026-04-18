"""
WHOOP API Client for Health OS (Headless)

Adapted from whoop-api project. Removes browser OAuth flow,
keeps only token-based operations with auto-refresh.

Rate limits:
- 100 requests/minute
- 10,000 requests/day
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

import requests
from dotenv import load_dotenv

# Try to use whoopy if available, otherwise use raw requests
try:
    from whoopy import WhoopClient as WhoopyClient
    HAS_WHOOPY = True
except ImportError:
    HAS_WHOOPY = False


class WhoopClient:
    """
    Headless WHOOP API Client.

    Uses existing tokens from config.json, refreshes automatically.
    Does NOT support initial OAuth flow - use whoop-api for that.

    Example:
        client = WhoopClient(config_file="data/integrations/whoop/config.json")
        sleep_data = client.get_sleep(start_date="2026-01-01")
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        config_file: str = "data/integrations/whoop/config.json"
    ):
        """
        Initialize WHOOP client.

        Args:
            client_id: OAuth client ID (defaults to WHOOP_CLIENT_ID env var)
            client_secret: OAuth client secret (defaults to WHOOP_CLIENT_SECRET env var)
            config_file: Path to config file with tokens
        """
        load_dotenv()

        self.client_id = client_id or os.getenv("WHOOP_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("WHOOP_CLIENT_SECRET")
        self.config_file = Path(config_file)

        # OAuth endpoints
        self.token_url = "https://api.prod.whoop.com/oauth/oauth2/token"
        self.api_base = "https://api.prod.whoop.com/developer/v1"

        # Rate limiting
        self._request_times: List[float] = []
        self._max_requests_per_minute = 100

        # Initialize
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._whoopy_client = None

        self._load_tokens()

    def _load_tokens(self):
        """Load tokens from config file."""
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_file}\n"
                "Run initial OAuth flow using whoop-api project first, then copy config.json"
            )

        with open(self.config_file, 'r') as f:
            config = json.load(f)

        self._access_token = config.get('access_token')
        self._refresh_token = config.get('refresh_token')
        expires_at = config.get('expires_at', 0)

        if not self._access_token:
            raise ValueError("No access_token in config file")

        # Check if token is expired or about to expire (5 min buffer)
        if expires_at < time.time() + 300:
            if self._refresh_token and self.client_id and self.client_secret:
                print("Token expired or expiring soon, refreshing...")
                self._refresh_access_token()
            else:
                print("Warning: Token may be expired, no refresh token available")

        # Initialize whoopy client if available
        if HAS_WHOOPY and self._refresh_token:
            try:
                self._whoopy_client = WhoopyClient.from_token(
                    access_token=self._access_token,
                    refresh_token=self._refresh_token,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
            except Exception as e:
                print(f"Could not initialize whoopy client: {e}")
                self._whoopy_client = None

    def _refresh_access_token(self):
        """Refresh the access token using refresh token."""
        if not self._refresh_token:
            raise ValueError("No refresh token available")

        response = requests.post(
            self.token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
        )

        if response.status_code != 200:
            raise Exception(f"Failed to refresh token: {response.text}")

        tokens = response.json()
        self._access_token = tokens['access_token']
        if 'refresh_token' in tokens:
            self._refresh_token = tokens['refresh_token']

        # Save updated tokens
        self._save_tokens(tokens)
        print("Token refreshed successfully")

    def _save_tokens(self, tokens: Dict[str, Any]):
        """Save tokens to config file."""
        config = {
            'access_token': tokens['access_token'],
            'expires_at': tokens.get('expires_in', 3600) + int(time.time()),
            'saved_at': datetime.now().isoformat()
        }

        if 'refresh_token' in tokens:
            config['refresh_token'] = tokens['refresh_token']
        elif self._refresh_token:
            config['refresh_token'] = self._refresh_token

        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def _rate_limit(self):
        """Enforce rate limiting."""
        now = time.time()
        # Remove requests older than 1 minute
        self._request_times = [t for t in self._request_times if now - t < 60]

        if len(self._request_times) >= self._max_requests_per_minute:
            sleep_time = 60 - (now - self._request_times[0])
            if sleep_time > 0:
                print(f"Rate limit reached, sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)

        self._request_times.append(time.time())

    def _request(self, endpoint: str, params: Optional[Dict] = None, api_version: Optional[str] = None) -> Dict[str, Any]:
        """Make authenticated API request."""
        self._rate_limit()

        if api_version:
            url = f"https://api.prod.whoop.com/developer/{api_version}/{endpoint}"
        else:
            url = f"{self.api_base}/{endpoint}"
        headers = {"Authorization": f"Bearer {self._access_token}"}

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 401:
            # Token expired, try refresh
            self._refresh_access_token()
            headers["Authorization"] = f"Bearer {self._access_token}"
            response = requests.get(url, headers=headers, params=params)

        response.raise_for_status()
        return response.json()

    def _parse_date(self, date: Union[str, datetime, None]) -> Optional[str]:
        """Convert date to ISO format string."""
        if date is None:
            return None
        if isinstance(date, datetime):
            return date.isoformat()
        return date

    def _get_collection(
        self,
        endpoint: str,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        limit: Optional[int] = None,
        api_version: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get paginated collection from API."""
        params = {}
        if start_date:
            params['start'] = self._parse_date(start_date)
        if end_date:
            params['end'] = self._parse_date(end_date)
        if limit:
            params['limit'] = min(limit, 25)  # API max is 25 per page
        else:
            params['limit'] = 25

        results = []
        next_token = None

        while True:
            if next_token:
                params['nextToken'] = next_token

            data = self._request(endpoint, params, api_version=api_version)
            records = data.get('records', [])
            results.extend(records)

            if limit and len(results) >= limit:
                return results[:limit]

            next_token = data.get('next_token')
            if not next_token or not records:
                break

        return results

    # Data access methods

    def get_profile(self) -> Dict[str, Any]:
        """Get user profile information."""
        if self._whoopy_client:
            profile = self._whoopy_client.user.get_profile()
            return profile.model_dump() if hasattr(profile, 'model_dump') else profile.dict()
        return self._request("user/profile/basic")

    def get_body_measurements(self) -> Dict[str, Any]:
        """Get body measurements (height, weight, max HR)."""
        if self._whoopy_client:
            measurements = self._whoopy_client.user.get_body_measurements()
            return measurements.model_dump() if hasattr(measurements, 'model_dump') else measurements.dict()
        return self._request("user/measurement/body")

    def get_sleep(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get sleep data.

        Args:
            start_date: Start date (YYYY-MM-DD or datetime)
            end_date: End date (YYYY-MM-DD or datetime)
            limit: Maximum records to return

        Returns:
            List of sleep records
        """
        if self._whoopy_client:
            start = datetime.fromisoformat(start_date) if isinstance(start_date, str) else start_date
            end = datetime.fromisoformat(end_date) if isinstance(end_date, str) else end_date
            if start and start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end and end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            results = self._whoopy_client.sleep.get_all(start=start, end=end, max_records=limit)
            return [r.model_dump(mode='json') if hasattr(r, 'model_dump') else r.dict() for r in results]

        return self._get_collection("activity/sleep", start_date, end_date, limit)

    def get_recovery(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recovery data.

        Args:
            start_date: Start date (YYYY-MM-DD or datetime)
            end_date: End date (YYYY-MM-DD or datetime)
            limit: Maximum records to return

        Returns:
            List of recovery records with scores
        """
        # Skip whoopy for recovery — its v1 endpoint returns 404
        # Always use v2 API directly
        return self._get_collection("recovery", start_date, end_date, limit, api_version="v2")

    def get_workouts(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get workout data.

        Args:
            start_date: Start date (YYYY-MM-DD or datetime)
            end_date: End date (YYYY-MM-DD or datetime)
            limit: Maximum records to return

        Returns:
            List of workout records
        """
        if self._whoopy_client:
            start = datetime.fromisoformat(start_date) if isinstance(start_date, str) else start_date
            end = datetime.fromisoformat(end_date) if isinstance(end_date, str) else end_date
            if start and start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end and end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            results = self._whoopy_client.workouts.get_all(start=start, end=end, max_records=limit)
            return [r.model_dump(mode='json') if hasattr(r, 'model_dump') else r.dict() for r in results]

        return self._get_collection("activity/workout", start_date, end_date, limit)

    def get_cycles(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get physiological cycle data.

        Args:
            start_date: Start date (YYYY-MM-DD or datetime)
            end_date: End date (YYYY-MM-DD or datetime)
            limit: Maximum records to return

        Returns:
            List of cycle records
        """
        if self._whoopy_client:
            start = datetime.fromisoformat(start_date) if isinstance(start_date, str) else start_date
            end = datetime.fromisoformat(end_date) if isinstance(end_date, str) else end_date
            if start and start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end and end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            results = self._whoopy_client.cycles.get_all(start=start, end=end, max_records=limit)
            return [r.model_dump(mode='json') if hasattr(r, 'model_dump') else r.dict() for r in results]

        return self._get_collection("cycle", start_date, end_date, limit)

    def close(self):
        """Close the underlying HTTP client session."""
        if self._whoopy_client and hasattr(self._whoopy_client, 'close'):
            self._whoopy_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Quick test
    import sys

    config_path = sys.argv[1] if len(sys.argv) > 1 else "data/integrations/whoop/config.json"

    client = WhoopClient(config_file=config_path)
    profile = client.get_profile()
    print(f"\nConnected as: {profile.get('first_name')} {profile.get('last_name')}")
    print(f"User ID: {profile.get('user_id')}")

    # Test sleep data
    sleep = client.get_sleep(limit=1)
    if sleep:
        print(f"\nLatest sleep: {sleep[0].get('start')} - {sleep[0].get('end')}")
