from mitmproxy import ctx, http
import json
import pickle
from datetime import datetime
import os
from pathlib import Path

# add global list of hosts to capture
hosts_to_capture = ["www.linkedin.com", "x.com"]

# global dict of cookies and headers to capture per host
cookies_to_capture = {
    'www.linkedin.com': ['li_at', 'JSESSIONID', 'bcookie'],
    'x.com': ['auth_token', 'ct0', 'twid', 'guest_id']
}

headers_to_capture = {
    'www.linkedin.com': ['csrf-token', 'user-agent'],
    'x.com': ['x-csrf-token', 'x-twitter-client-language', 'authorization', 'user-agent']
}


class SessionCapturer:
    def __init__(self):
        self.sessions = {}
        self.save_dir = Path("captured_sessions")
        self.save_dir.mkdir(exist_ok=True)

    def request(self, flow: http.HTTPFlow) -> None:
        """Process each request to capture session data"""
        host = flow.request.pretty_host
        if host not in hosts_to_capture:
            return

        if host not in self.sessions:
            self.sessions[host] = {
                'cookies': {},
                'headers': {},
                'timestamp': datetime.now().isoformat(),
                'host': host
            }

        # Capture cookies from requests
        for cookie in flow.request.cookies.fields:
            name, value = cookie
            # Decode bytes to strings and store as simple key-value pairs
            cookie_name = name.decode(
                'utf-8', 'ignore') if isinstance(name, bytes) else str(name)
            cookie_value = value.decode(
                'utf-8', 'ignore') if isinstance(value, bytes) else str(value)
            if cookie_name in cookies_to_capture[host]:
                self.sessions[host]['cookies'][cookie_name] = cookie_value

        # Capture important headers
        for header, value in flow.request.headers.items():
            if header in headers_to_capture[host]:
                self.sessions[host]['headers'][header] = value

        self.save_session(host)

    def save_session(self, host: str) -> None:
        """Save the captured session data"""
        if host not in self.sessions:
            return

        # Create a clean filename from the host
        filename = host.replace('.', '_').replace(':', '_')

        # Save as JSON for human readability
        json_path = self.save_dir / f"{filename}.json"
        with open(json_path, 'w') as f:
            json.dump(self.sessions[host], f, indent=2)

        # Save as pickle for complete object serialization
        pkl_path = self.save_dir / f"{filename}.pkl"
        with open(pkl_path, 'wb') as f:
            pickle.dump(self.sessions[host], f)


addons = [SessionCapturer()]
