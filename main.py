"""Phala Cloud Python starter — exhaustive dstack-sdk demo.

Every endpoint maps to one capability on the dstack guest-agent socket
(/var/run/dstack.sock). The server itself is plain FastAPI; the goal is to
show, in one file, the full surface of dstack-sdk 0.5.4b1 so you can
copy/paste pieces into your own app.
"""

from __future__ import annotations

import time
import warnings
from typing import Any
from typing import List
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from dstack_sdk import AsyncDstackClient  # noqa: E402
from dstack_sdk import EnvVar  # noqa: E402
from dstack_sdk import encrypt_env_vars  # noqa: E402
from dstack_sdk import get_compose_hash  # noqa: E402
from dstack_sdk import verify_env_encrypt_public_key  # noqa: E402
from dstack_sdk import verify_env_encrypt_public_key_legacy  # noqa: E402
from dstack_sdk.ethereum import to_account_secure  # noqa: E402
from dstack_sdk.solana import to_keypair_secure  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from pydantic import BaseModel  # noqa: E402
from pydantic import Field  # noqa: E402

SDK_VERSION = "0.5.4b1"
app = FastAPI(
    title="Phala Cloud Python starter",
    description=(
        "Reference app exercising every capability on dstack-sdk "
        f"{SDK_VERSION}. Each endpoint talks to /var/run/dstack.sock."
    ),
    version=SDK_VERSION,
)


def _client() -> AsyncDstackClient:
    """Build a fresh client per request — the SDK is cheap to instantiate."""
    return AsyncDstackClient()


@app.get("/", summary="Index", tags=["meta"])
async def index() -> dict[str, Any]:
    """Quick capability map so the demo is self-describing."""
    return {
        "sdk_version": SDK_VERSION,
        "endpoints": {
            "diagnostics": ["/health", "/version", "/info"],
            "keys": ["/keys/derive", "/keys/derive/ed25519"],
            "attestation": ["/attestation/quote", "/attestation/attest"],
            "tls_key": ["/tls-key", "/tls-key/with-app-info"],
            "sign_verify": ["/sign", "/verify"],
            "events": ["/emit-event"],
            "blockchain": ["/blockchain/ethereum", "/blockchain/solana"],
            "utilities": [
                "/utils/compose-hash",
                "/utils/encrypt-env-vars",
                "/utils/verify-env-encrypt-public-key",
                "/utils/verify-env-encrypt-public-key/legacy",
            ],
        },
    }


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


@app.get("/health", tags=["diagnostics"])
async def health() -> dict[str, Any]:
    """Reachability probe — does not raise; mirrors `is_reachable()`."""
    reachable = await _client().is_reachable()
    return {"reachable": reachable}


@app.get("/version", tags=["diagnostics"])
async def version() -> dict[str, Any]:
    """Guest-agent version (requires dstack OS >= 0.5.7)."""
    try:
        result = await _client().version()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Version RPC unavailable: {exc}",
        )
    return result.model_dump()


@app.get("/info", tags=["diagnostics"])
async def info() -> dict[str, Any]:
    """Full instance info, including the 0.5.7-only cloud_* fields."""
    result = await _client().info()
    return result.model_dump()


# ---------------------------------------------------------------------------
# Key derivation
# ---------------------------------------------------------------------------


class GetKeyParams(BaseModel):
    path: str = Field(default="", description="Derivation path")
    purpose: str = Field(default="", description="Signature chain context")


@app.post("/keys/derive", tags=["keys"])
async def derive_key(params: GetKeyParams) -> dict[str, Any]:
    """secp256k1 key (default algorithm)."""
    result = await _client().get_key(params.path, params.purpose)
    return result.model_dump()


@app.post("/keys/derive/ed25519", tags=["keys"])
async def derive_key_ed25519(params: GetKeyParams) -> dict[str, Any]:
    """ed25519 key — requires dstack OS >= 0.5.7."""
    try:
        result = await _client().get_key(
            params.path, params.purpose, algorithm="ed25519"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"ed25519 not supported by this OS: {exc}",
        )
    return result.model_dump()


# ---------------------------------------------------------------------------
# Attestation
# ---------------------------------------------------------------------------


class ReportDataParams(BaseModel):
    report_data: str = Field(
        ..., max_length=128, description="Up to 64 bytes (text or hex)"
    )


@app.post("/attestation/quote", tags=["attestation"])
async def attestation_quote(params: ReportDataParams) -> dict[str, Any]:
    quote = await _client().get_quote(params.report_data)
    return {
        **quote.model_dump(),
        "rtmrs_replayed": quote.replay_rtmrs(),
    }


@app.post("/attestation/attest", tags=["attestation"])
async def attestation_attest(params: ReportDataParams) -> dict[str, Any]:
    """Versioned attestation envelope (preferred for new verifiers)."""
    result = await _client().attest(params.report_data)
    return result.model_dump()


# ---------------------------------------------------------------------------
# TLS keys (random per call)
# ---------------------------------------------------------------------------


class TlsKeyParams(BaseModel):
    subject: Optional[str] = None
    alt_names: Optional[List[str]] = None
    usage_ra_tls: bool = False
    usage_server_auth: bool = True
    usage_client_auth: bool = False


class TlsKeyWithAppInfoParams(TlsKeyParams):
    """0.5.7+ variant exercising not_before / not_after / with_app_info."""

    not_before: Optional[int] = Field(
        default=None, description="Unix seconds; defaults to now"
    )
    not_after: Optional[int] = Field(
        default=None,
        description="Unix seconds; defaults to now + 30 days",
    )
    with_app_info: bool = True


@app.post("/tls-key", tags=["tls"])
async def tls_key(params: TlsKeyParams) -> dict[str, Any]:
    result = await _client().get_tls_key(
        subject=params.subject,
        alt_names=params.alt_names,
        usage_ra_tls=params.usage_ra_tls,
        usage_server_auth=params.usage_server_auth,
        usage_client_auth=params.usage_client_auth,
    )
    return result.model_dump()


@app.post("/tls-key/with-app-info", tags=["tls"])
async def tls_key_with_app_info(
    params: TlsKeyWithAppInfoParams,
) -> dict[str, Any]:
    """Uses the 0.5.7-only options. Raises if OS does not support them."""
    not_before = params.not_before or int(time.time())
    not_after = params.not_after or not_before + 30 * 86400
    try:
        result = await _client().get_tls_key(
            subject=params.subject,
            alt_names=params.alt_names,
            usage_ra_tls=params.usage_ra_tls,
            usage_server_auth=params.usage_server_auth,
            usage_client_auth=params.usage_client_auth,
            not_before=not_before,
            not_after=not_after,
            with_app_info=params.with_app_info,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"0.5.7-only TLS options unsupported: {exc}",
        )
    return result.model_dump()


# ---------------------------------------------------------------------------
# Sign / verify
# ---------------------------------------------------------------------------


class SignParams(BaseModel):
    algorithm: str = Field(default="ed25519")
    data: str = Field(..., description="Text (utf-8 encoded before signing)")


@app.post("/sign", tags=["sign"])
async def sign(params: SignParams) -> dict[str, Any]:
    result = await _client().sign(params.algorithm, params.data)
    return result.model_dump()


class VerifyParams(BaseModel):
    algorithm: str
    data: str
    signature: str = Field(..., description="Hex-encoded signature")
    public_key: str = Field(..., description="Hex-encoded public key")


@app.post("/verify", tags=["sign"])
async def verify(params: VerifyParams) -> dict[str, Any]:
    result = await _client().verify(
        params.algorithm,
        params.data,
        bytes.fromhex(params.signature),
        bytes.fromhex(params.public_key),
    )
    return result.model_dump()


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class EmitEventParams(BaseModel):
    event: str = Field(..., min_length=1)
    payload: str = ""


@app.post("/emit-event", tags=["events"])
async def emit_event(params: EmitEventParams) -> dict[str, str]:
    """Extends RTMR3. Side-effecting — every call mutates attestation."""
    await _client().emit_event(params.event, params.payload)
    return {"status": "emitted", "event": params.event}


# ---------------------------------------------------------------------------
# Blockchain helpers
# ---------------------------------------------------------------------------


class WalletPath(BaseModel):
    path: str = "wallet/default"


@app.post("/blockchain/ethereum", tags=["blockchain"])
async def ethereum_account(params: WalletPath) -> dict[str, str]:
    key = await _client().get_key(params.path)
    account = to_account_secure(key)
    return {"address": account.address}


@app.post("/blockchain/solana", tags=["blockchain"])
async def solana_keypair(params: WalletPath) -> dict[str, str]:
    key = await _client().get_key(params.path)
    keypair = to_keypair_secure(key)
    return {"address": str(keypair.pubkey())}


# ---------------------------------------------------------------------------
# Deployment utilities (no socket required)
# ---------------------------------------------------------------------------


class ComposeHashParams(BaseModel):
    app_compose: dict[str, Any]


@app.post("/utils/compose-hash", tags=["utils"])
async def compose_hash(params: ComposeHashParams) -> dict[str, str]:
    return {"compose_hash": get_compose_hash(params.app_compose)}


class EncryptEnvParams(BaseModel):
    env: List[EnvVar]
    public_key_hex: str


@app.post("/utils/encrypt-env-vars", tags=["utils"])
async def encrypt_env(params: EncryptEnvParams) -> dict[str, str]:
    encrypted = await encrypt_env_vars(params.env, params.public_key_hex)
    return {"encrypted": encrypted}


class VerifyKmsParams(BaseModel):
    public_key_hex: str
    signature_hex: str
    app_id: str
    timestamp: int
    max_age_seconds: int = 300


@app.post("/utils/verify-env-encrypt-public-key", tags=["utils"])
async def verify_kms_key(params: VerifyKmsParams) -> dict[str, Optional[str]]:
    signer = verify_env_encrypt_public_key(
        bytes.fromhex(params.public_key_hex),
        bytes.fromhex(params.signature_hex),
        params.app_id,
        params.timestamp,
        max_age_seconds=params.max_age_seconds,
    )
    return {"signer": signer}


class VerifyKmsLegacyParams(BaseModel):
    public_key_hex: str
    signature_hex: str
    app_id: str


@app.post("/utils/verify-env-encrypt-public-key/legacy", tags=["utils"])
async def verify_kms_key_legacy(
    params: VerifyKmsLegacyParams,
) -> dict[str, Optional[str]]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        signer = verify_env_encrypt_public_key_legacy(
            bytes.fromhex(params.public_key_hex),
            bytes.fromhex(params.signature_hex),
            params.app_id,
        )
    return {"signer": signer}
