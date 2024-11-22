import json
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Dict, Optional, List
import jwt
from datetime import datetime, timedelta
import pickle
from pathlib import Path
import httpx
import secrets
from urllib.parse import urljoin


class SessionCapture(BaseModel):
    host: str
    cookies: Dict[str, str]
    headers: Dict[str, str]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    scope: str


# --- Session Storage ---


class SessionStore:
    def __init__(self, sessions_dir: Path = Path("captured_sessions")):
        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(exist_ok=True)

    def get_session(self, host: str) -> Optional[Dict]:
        normalized_host = host.lstrip('www.')
        filename = normalized_host.replace('.', '_').replace(':', '_') + '.pkl'
        try:
            with open(self.sessions_dir / filename, 'rb') as f:
                return pickle.load(f)
        except (FileNotFoundError, EOFError) as e:
            print(f"Error loading session for {host}: {e}")
            return None

# --- OAuth Implementation ---


class AuthCodeStore:
    def __init__(self):
        self.codes: Dict[str, Dict] = {}

    def create_code(self, client_id: str, host: str, scopes: List[str]) -> str:
        code = secrets.token_urlsafe(32)
        self.codes[code] = {
            "client_id": client_id,
            "host": host,
            "scopes": scopes,
            "created_at": datetime.now()
        }
        return code

    def validate_code(self, code: str, client_id: str) -> Optional[Dict]:
        code_data = self.codes.get(code)
        if not code_data or code_data["client_id"] != client_id:
            return None
        if datetime.now() - code_data["created_at"] > timedelta(minutes=10):
            return None
        del self.codes[code]
        return code_data


app = FastAPI()
session_store = SessionStore()
auth_codes = AuthCodeStore()
JWT_SECRET = "your-secret-key"  # Change in production


@app.get("/oauth/authorize")
async def authorize(
    client_id: str,
    redirect_uri: str,
    host: str,
    scope: str = "",
    state: Optional[str] = None
):
    """Authorize endpoint that accepts space-separated scopes"""
    scopes = scope.split() if scope else ["default"]

    session = session_store.get_session(host)
    if not session:
        raise HTTPException(
            status_code=400,
            detail=f"No valid session for {host}"
        )

    code = auth_codes.create_code(client_id, host, scopes)

    params = {"code": code}
    if state:
        params["state"] = state

    redirect_url = f"{redirect_uri}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    return RedirectResponse(url=redirect_url)


@app.post("/oauth/token")
async def token(
    code: str,
    client_id: str,
    redirect_uri: str
):
    """Token endpoint that includes scopes in the JWT"""
    code_data = auth_codes.validate_code(code, client_id)
    if not code_data:
        raise HTTPException(
            status_code=401, detail="Invalid authorization code")

    session = session_store.get_session(code_data["host"])
    if not session:
        raise HTTPException(status_code=401, detail="Session not found")

    token_data = {
        "sub": client_id,
        "host": code_data["host"],
        "scope": " ".join(code_data["scopes"]),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "session": {
            "cookies": session["cookies"],
            "headers": session["headers"]
        }
    }

    access_token = jwt.encode(token_data, JWT_SECRET, algorithm="HS256")
    return TokenResponse(
        access_token=access_token,
        scope=" ".join(code_data["scopes"])
    )


async def get_token_data(authorization: str = Header(...)) -> Dict:
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(401, "Invalid auth scheme")
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except:
        raise HTTPException(401, "Invalid authorization header")


@app.post("/api/proxy")
async def proxy_request(
    url: str,
    method: str = "GET",
    token_data: Dict = Depends(get_token_data),
    body: Optional[Dict] = None
):
    """Proxy that supports all HTTP methods and passes through stored session data"""
    session = token_data["session"]

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=method,
            url=url,
            cookies=session["cookies"],
            headers=session["headers"],
            json=body if body else None,
            follow_redirects=True
        )

        print(response, "from proxy")

        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return response.text


if __name__ == "__main__":
    input_file = Path("output.json")
    output_dir = Path("captured_sessions")
    output_dir.mkdir(exist_ok=True)

    with open(input_file, "r") as f:
        data = json.load(f)

    for host, session in data.items():
        output_file = output_dir / \
            Path(f"{host.replace('.', '_')}.pkl")
        with open(output_file, "wb") as f:
            pickle.dump(session, f)

    print(f"Saved {len(data)} sessions to {output_dir}")

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
