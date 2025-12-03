"""
Authentication using AWS Cognito User Pools.

This module replaces the previous SQL-backed password/login flow and instead
verifies incoming Bearer tokens (ID or access tokens) issued by Cognito.

Environment variables used:
  - COGNITO_USER_POOL_ID
  - COGNITO_APP_CLIENT_ID
  - AWS_REGION

The JWKS keys are fetched from Cognito's well-known JWKS endpoint and cached
in-memory for the lifetime of the process.
"""
import os
import time
import requests
from jose import jwk, jwt
from jose.utils import base64url_decode
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Cognito configuration read from environment
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
AWS_REGION = os.getenv("AWS_REGION")

if not (COGNITO_USER_POOL_ID and COGNITO_APP_CLIENT_ID and AWS_REGION):
    # Fail early if these are not configured — keep behavior predictable.
    raise RuntimeError("COGNITO_USER_POOL_ID, COGNITO_APP_CLIENT_ID and AWS_REGION must be set")

JWKS_URL = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
ISSUER = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Simple in-memory cache for JWKS
_JWKS_CACHE: dict | None = None
_JWKS_LAST_FETCH = 0
_JWKS_TTL = 60 * 60  # 1 hour


def _fetch_jwks():
    global _JWKS_CACHE, _JWKS_LAST_FETCH
    now = time.time()
    if _JWKS_CACHE and (now - _JWKS_LAST_FETCH) < _JWKS_TTL:
        return _JWKS_CACHE
    resp = requests.get(JWKS_URL, timeout=5)
    resp.raise_for_status()
    jwks = resp.json()
    _JWKS_CACHE = jwks
    _JWKS_LAST_FETCH = now
    return jwks


class CognitoUser:
    def __init__(self, claims: dict):
        self.claims = claims
        # `sub` is the Cognito user id (UUID-like string)
        self.id = claims.get("sub")
        self.email = claims.get("email")

    def __repr__(self):
        return f"CognitoUser(id={self.id}, email={self.email})"


def get_current_user(token: str = Depends(oauth2_scheme)) -> CognitoUser:
    """Validate a Cognito JWT (ID token or access token) and return claims.

    Validation performed:
      - Signature validation using Cognito JWKS (RS256)
      - Expiration (`exp`) claim
      - Issuer matches the configured user pool
      - Audience (`aud`) contains the configured App Client ID
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        jwks = _fetch_jwks()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch JWKS for token verification")

    try:
        headers = jwt.get_unverified_headers(token)
    except Exception:
        raise credentials_exception

    kid = headers.get("kid")
    if not kid:
        raise credentials_exception

    key = None
    for k in jwks.get("keys", []):
        if k.get("kid") == kid:
            key = k
            break
    if key is None:
        raise credentials_exception

    # Verify signature
    public_key = jwk.construct(key)
    message, encoded_sig = token.rsplit('.', 1)
    decoded_sig = base64url_decode(encoded_sig.encode('utf-8'))
    if not public_key.verify(message.encode("utf-8"), decoded_sig):
        raise credentials_exception

    # Extract and validate claims
    try:
        claims = jwt.get_unverified_claims(token)
    except Exception:
        raise credentials_exception

    # exp
    if "exp" in claims and time.time() > claims["exp"]:
        raise HTTPException(status_code=401, detail="Token is expired")

    # iss
    if claims.get("iss") != ISSUER:
        raise credentials_exception

    # aud — may be a single string or a list
    aud = claims.get("aud")
    if isinstance(aud, list):
        aud_ok = COGNITO_APP_CLIENT_ID in aud
    else:
        aud_ok = aud == COGNITO_APP_CLIENT_ID
    if not aud_ok:
        # Some Cognito access tokens use `client_id` instead — accept either
        if claims.get("client_id") != COGNITO_APP_CLIENT_ID:
            raise credentials_exception

    return CognitoUser(claims)
