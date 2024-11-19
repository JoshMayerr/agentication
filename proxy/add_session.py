import pickle
from pathlib import Path

# Create test session
session_data = {
    "cookies": {"test_cookie": "value"},
    "headers": {"User-Agent": "test"},
    "scopes": ["read", "write"]
}

# Save it
sessions_dir = Path("captured_sessions")
sessions_dir.mkdir(exist_ok=True)

# The host will be converted from e.g. 'api.example.com' to 'api_example_com.pkl'
host = "localhost8001"
with open(sessions_dir / f"{host}.pkl", "wb") as f:
    pickle.dump(session_data, f)
