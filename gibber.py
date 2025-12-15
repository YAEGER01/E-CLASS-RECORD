from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadData, SignatureExpired
from typing import Optional, Dict, Any

try:
    from cryptography.fernet import Fernet, InvalidToken as FernetInvalid

    _have_fernet = True
except Exception:
    _have_fernet = False


def _get_secret() -> str:
    try:
        return current_app.config.get("SECRET_KEY") or current_app.secret_key
    except RuntimeError:
        return "dev-secret-key-change-in-production"


def _get_serializer() -> URLSafeTimedSerializer:
    secret = _get_secret()
    return URLSafeTimedSerializer(secret, salt="eclass-gibber")


def _get_fernet() -> Optional[Any]:
    if not _have_fernet:
        return None
    try:
        key = current_app.config.get("GIBBER_FERNET_KEY")
        if not key:
            return None
        if isinstance(key, str):
            key = key.encode()
        return Fernet(key)
    except RuntimeError:
        return None


def _make_payload(path: str, qs: Optional[str]) -> Dict[str, Any]:
    return {"path": path, "qs": qs or ""}


def gibberize(
    path: str, qs: Optional[str] = None, expires: Optional[int] = None
) -> str:
    """Create a token that encodes `path` and optional query-string `qs`.

    - `expires` is not embedded in the token but is used when resolving (max_age).
    - If `GIBBER_FERNET_KEY` is configured, the signed token is additionally encrypted with Fernet.
    """
    s = _get_serializer()
    payload = _make_payload(path, qs)
    token = s.dumps(payload)
    f = _get_fernet()
    if f:
        token = f.encrypt(token.encode()).decode()
    return token


def resolve(token: str, max_age: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Resolve a token back into payload {path, qs}.

    Returns dict on success or None on failure/expiration.
    """
    f = _get_fernet()
    try:
        if f:
            # decrypt first
            token = f.decrypt(token.encode()).decode()
    except Exception:
        # Fernet decryption failed
        return None

    s = _get_serializer()
    try:
        data = s.loads(token, max_age=max_age) if max_age else s.loads(token)
        if isinstance(data, dict) and "path" in data:
            return data
        return None
    except SignatureExpired:
        return None
    except BadData:
        return None
    except Exception:
        return None


def gibber_form_token(
    path: str, qs: Optional[str] = None, expires: Optional[int] = None
) -> str:
    """Helper to create a token suitable for use as a form action: `/g/<token>`."""
    return gibberize(path, qs=qs, expires=expires)


def gibber_form_action(
    path: str, qs: Optional[str] = None, expires: Optional[int] = None
) -> str:
    """Return the full form action URL (`/g/<token>`) for use in templates."""
    return f"/g/{gibber_form_token(path, qs=qs, expires=expires)}"
