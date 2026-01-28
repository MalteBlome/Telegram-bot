import os
import json
import hmac
import hashlib
import secrets
import string
from typing import Optional

import asyncpg
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse

DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL fehlt")
if not ADMIN_API_KEY:
    raise RuntimeError("ADMIN_API_KEY fehlt")

app = FastAPI()
pool: Optional[asyncpg.Pool] = None


# ---------- Helpers ----------
def gen_code(length: int = 20) -> str:
    """
    Erzeugt Code wie: ABCD-EFGH-IJKL-MNOP-QRST
    """
    alphabet = string.ascii_uppercase + string.digits
    raw = "".join(secrets.choice(alphabet) for _ in range(length))
    return "-".join(raw[i:i+4] for i in range(0, len(raw), 4))


def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def require_admin(request: Request):
    key = request.headers.get("x-api-key", "")
    if not hmac.compare_digest(key, ADMIN_API_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized")


# ---------- Lifecycle ----------
@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)


@app.get("/health", response_class=PlainTextResponse)
async def health():
    return "ok"


# ---------- Admin Routes ----------
@app.post("/admin/create-license")
async def create_license(request: Request):
    """
    Header: x-api-key: <ADMIN_API_KEY>
    Body JSON: { "email": "kunde@example.com", "meta": {...optional...} }
    """
    require_admin(request)

    data = await request.json()
    email = (data.get("email") or "").strip().lower()
    meta = data.get("meta") or {}

    if not email:
        raise HTTPException(status_code=400, detail="email required")

    code = gen_code()
    code_hash = hash_code(code)

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO licenses (code_hash, status, email, meta)
            VALUES ($1, 'unused', $2, $3)
            """,
            code_hash,
            email,
            json.dumps(meta),
        )

    # Wichtig: Code wird hier zurückgegeben (weil ohne Mail)
    return {
        "status": "ok",
        "email": email,
        "code": code
    }


@app.get("/admin/list-licenses")
async def list_licenses(request: Request, limit: int = 50):
    """
    Header: x-api-key: <ADMIN_API_KEY>
    """
    require_admin(request)

    limit = max(1, min(limit, 200))
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, status, email, created_at, redeemed_at, redeemed_telegram_id
            FROM licenses
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )

    return {"items": [dict(r) for r in rows]}
