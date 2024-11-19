import json
import pickle
import requests
from pathlib import Path


class SessionLoader:
    def __init__(self, sessions_dir="captured_sessions"):
        self.sessions_dir = Path(sessions_dir)

    def load_session(self, host):
        """Load a captured session for a specific host"""
        filename = host.replace('.', '_').replace(':', '_')
        pkl_path = self.sessions_dir / f"{filename}.pkl"

        if not pkl_path.exists():
            raise FileNotFoundError(f"No session found for {host}")

        with open(pkl_path, 'rb') as f:
            return pickle.load(f)

    def create_requests_session(self, host):
        """Create a requests session with the captured authentication data"""
        session_data = self.load_session(host)
        session = requests.Session()

        # Add cookies from list
        for cookie_name in session_data['cookies']:
            session.cookies.set(
                cookie_name, session_data['cookies'][cookie_name], domain=session_data['host'])

        for header in session_data['headers']:
            session.headers[header] = session_data['headers'][header]

        return session
