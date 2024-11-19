import http.server
import requests
import sys
import time
from urllib.parse import urlencode, parse_qs, urlparse

# generic client for interacting with the API using the OAuth flow


class GenericClient:
    def __init__(self, client_id: str, client_secret: str):
        self.tokens = {}
        self.client_id = client_id
        self.client_secret = client_secret

    def _print_info(self, message):
        """Print formatted info message"""
        print(f"\n[INFO] {message}")

    def _print_error(self, message):
        """Print formatted error message"""
        print(f"\n[ERROR] {message}", file=sys.stderr)

    def _confirm_scopes(self, scopes):
        """Ask user to confirm the requested scopes"""
        if not scopes:
            return True

        self._print_info("The application is requesting the following scopes:")
        for scope in scopes:
            self._print_info(f" - [ ] {scope}")

        while True:
            response = input(
                "\nDo you want to authorize these permissions? (y/n): ").lower()
            if response in ['yes', 'y']:
                return True
            elif response in ['no', 'n']:
                return False
            self._print_error("Please answer 'yes' or 'no'")

    def get_token(self, host, scopes=None):
        """Get OAuth token for a specific host with optional scopes"""
        code = None

        def handler(req):
            nonlocal code
            query = parse_qs(urlparse(req.path).query)
            code = query.get('code', [None])[0]
            req.send_response(200)
            req.send_header('Content-Type', 'text/html')
            req.end_headers()
            req.wfile.write(b"Got code, you can close this window")

        # First confirm scopes with user
        if not self._confirm_scopes(scopes):
            self._print_info("Authorization cancelled by user")
            return None

        # Start local server to receive the OAuth callback
        server = http.server.HTTPServer(('', 8080), lambda *args:
                                        type('Handler', (http.server.BaseHTTPRequestHandler,), {'do_GET': lambda self: handler(self)})(*args))

        formatted_host = host.replace('.', '_').replace(':', '_')

        # Include scopes in authorization request
        auth_params = {
            'client_id': self.client_id,
            'redirect_uri': 'http://localhost:8080',
            'host': formatted_host
        }
        if scopes:
            auth_params['scope'] = ' '.join(scopes)

        auth_url = 'http://localhost:8000/oauth/authorize?' + \
            urlencode(auth_params)

        # Instead of opening browser, show URL and instructions
        self._print_info(
            f"To authorize access to {host}, please open this URL in your browser:")
        self._print_info(f"\n{auth_url}\n")
        self._print_info(
            "Waiting for authorization... (Press Ctrl+C to cancel)")

        try:
            server.handle_request()
        except KeyboardInterrupt:
            self._print_info("\nAuthorization cancelled by user")
            return None

        if not code:
            self._print_error("Failed to get authorization code")
            return None

        self._print_info(
            "Authorization code received, requesting access token...")

        # Exchange code for token
        token_url = 'http://localhost:8000/oauth/token?' + urlencode({
            'code': code,
            'client_id': self.client_id,
            'redirect_uri': 'http://localhost:8080'
        })

        r = requests.post(token_url)
        if r.status_code != 200:
            self._print_error(f"Failed to get token: {r.text}")
            return None

        self._print_info("Access token received successfully")
        return r.json()['access_token']

    def make_request(self, url, method="GET", token=None, body=None):
        """Make a proxied request using the token"""
        response = requests.post(
            'http://localhost:8000/api/proxy',
            params={
                'url': url,
                'method': method
            },
            headers={'Authorization': f'Bearer {token}'},
            json=body
        )

        if response.status_code != 200:
            self._print_error(
                f"Request failed with status {response.status_code}: {response.text}")
            return response.text

        return response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
