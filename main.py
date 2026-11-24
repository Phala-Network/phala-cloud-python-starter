"""Phala Cloud Python starter — exhaustive dstack-sdk demo.

Every endpoint maps to one capability on the dstack guest-agent socket
(/var/run/dstack.sock). The server itself is plain FastAPI; the goal is to
show, in one file, the full surface of dstack-sdk 0.6.0 so you can
copy/paste pieces into your own app.

The /v1/ routes use the current guest API (`AsyncDstackClient`, dstack OS
>= 0.6.0) and are the ones to copy. The remaining guest routes use the
frozen v0 API (`AsyncDstackClientV0`) and are kept for apps already
running on it.
"""

from __future__ import annotations

import hashlib
import time
import warnings
from typing import Any
from typing import List
from typing import Literal
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from dstack_sdk import AsyncDstackClient  # noqa: E402
from dstack_sdk import AsyncDstackClientV0  # noqa: E402
from dstack_sdk import EnvVar  # noqa: E402
from dstack_sdk import encrypt_env_vars  # noqa: E402
from dstack_sdk import get_compose_hash  # noqa: E402
from dstack_sdk import verify_env_encrypt_public_key  # noqa: E402
from dstack_sdk import verify_env_encrypt_public_key_legacy  # noqa: E402
from dstack_sdk.ethereum import to_account_secure  # noqa: E402
from dstack_sdk.solana import to_keypair_secure  # noqa: E402
from eth_account import Account  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from pydantic import BaseModel  # noqa: E402
from pydantic import Field  # noqa: E402
from solders.keypair import Keypair  # noqa: E402

SDK_VERSION = "0.6.0"
app = FastAPI(
    title="Phala Cloud Python starter",
    description=(
        "Reference app exercising every capability on dstack-sdk "
        f"{SDK_VERSION}. Each endpoint talks to /var/run/dstack.sock."
    ),
    version=SDK_VERSION,
    openapi_tags=[
        {
            "name": "v1",
            "description": (
                "dstack guest API v1 (`AsyncDstackClient`). Requires dstack "
                "OS >= 0.6.0."
            ),
        },
        {
            "name": "v0-legacy",
            "description": (
                "Legacy dstack guest API v0 (`AsyncDstackClientV0`). v0 keys "
                "differ from v1 keys for the same name."
            ),
        },
    ],
)


def _client() -> AsyncDstackClientV0:
    """Legacy v0 client. Built per request — the SDK is cheap to instantiate."""
    return AsyncDstackClientV0()


def _client_v1() -> AsyncDstackClient:
    """v1 client (dstack OS >= 0.6.0)."""
    return AsyncDstackClient()


@app.get("/", summary="Index", tags=["meta"])
async def index() -> dict[str, Any]:
    """Quick capability map so the demo is self-describing."""
    return {
        "sdk_version": SDK_VERSION,
        "endpoints": {
            "v1": [
                "/v1/version",
                "/v1/info",
                "/v1/keys/derive",
                "/v1/attestation/attest",
                "/v1/tls-key",
                "/v1/blockchain/ethereum",
                "/v1/blockchain/solana",
            ],
            "legacy_v0": {
                "diagnostics": ["/health", "/version", "/info"],
                "keys": ["/keys/derive", "/keys/derive/ed25519"],
                "attestation": ["/attestation/quote", "/attestation/attest"],
                "tls_key": ["/tls-key", "/tls-key/with-app-info"],
                "sign_verify": ["/sign", "/verify"],
                "events": ["/emit-event"],
                "blockchain": ["/blockchain/ethereum", "/blockchain/solana"],
            },
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


@app.get("/health", tags=["v0-legacy"])
async def health() -> dict[str, Any]:
    """Reachability probe — does not raise; mirrors `is_reachable()`."""
    reachable = await _client().is_reachable()
    return {"reachable": reachable}


@app.get("/version", tags=["v0-legacy"])
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


@app.get("/info", tags=["v0-legacy"])
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


@app.post("/keys/derive", tags=["v0-legacy"])
async def derive_key(params: GetKeyParams) -> dict[str, Any]:
    """secp256k1 key (default algorithm)."""
    result = await _client().get_key(params.path, params.purpose)
    return result.model_dump()


@app.post("/keys/derive/ed25519", tags=["v0-legacy"])
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


REPORT_DATA_TAG = "app-data"
REPORT_DATA_DERIVATION = 'sha512("app-data:" || utf8(user_input))'


def app_data_report_data(user_input: str) -> bytes:
    hasher = hashlib.sha512()
    hasher.update(REPORT_DATA_TAG.encode())
    hasher.update(b":")
    hasher.update(user_input.encode())
    return hasher.digest()


class ReportDataParams(BaseModel):
    report_data: str = Field(
        ...,
        max_length=4096,
        description=(
            "Caller input. Hashed as sha512('app-data:' || utf8(input)) before "
            "it is used as TDX report_data, so it cannot collide with RA-TLS."
        ),
    )


@app.post("/attestation/quote", tags=["v0-legacy"])
async def attestation_quote(params: ReportDataParams) -> dict[str, Any]:
    report_data = app_data_report_data(params.report_data)
    quote = await _client().get_quote(report_data)
    return {
        **quote.model_dump(),
        "user_input": params.report_data,
        "report_data_tag": REPORT_DATA_TAG,
        "report_data_hex": report_data.hex(),
        "report_data_derivation": REPORT_DATA_DERIVATION,
    }


@app.post("/attestation/attest", tags=["v0-legacy"])
async def attestation_attest(params: ReportDataParams) -> dict[str, Any]:
    """Versioned attestation envelope (preferred for new verifiers)."""
    report_data = app_data_report_data(params.report_data)
    result = await _client().attest(report_data)
    return {
        **result.model_dump(),
        "user_input": params.report_data,
        "report_data_tag": REPORT_DATA_TAG,
        "report_data_hex": report_data.hex(),
        "report_data_derivation": REPORT_DATA_DERIVATION,
    }


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


@app.post("/tls-key", tags=["v0-legacy"])
async def tls_key(params: TlsKeyParams) -> dict[str, Any]:
    result = await _client().get_tls_key(
        subject=params.subject,
        alt_names=params.alt_names,
        usage_ra_tls=params.usage_ra_tls,
        usage_server_auth=params.usage_server_auth,
        usage_client_auth=params.usage_client_auth,
    )
    return result.model_dump()


@app.post("/tls-key/with-app-info", tags=["v0-legacy"])
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


@app.post("/sign", tags=["v0-legacy"])
async def sign(params: SignParams) -> dict[str, Any]:
    result = await _client().sign(params.algorithm, params.data)
    return result.model_dump()


class VerifyParams(BaseModel):
    algorithm: str
    data: str
    signature: str = Field(..., description="Hex-encoded signature")
    public_key: str = Field(..., description="Hex-encoded public key")


@app.post("/verify", tags=["v0-legacy"])
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


@app.post("/emit-event", tags=["v0-legacy"])
async def emit_event(params: EmitEventParams) -> dict[str, str]:
    """Extends RTMR3. Side-effecting — every call mutates attestation."""
    await _client().emit_event(params.event, params.payload)
    return {"status": "emitted", "event": params.event}


# ---------------------------------------------------------------------------
# Blockchain helpers
# ---------------------------------------------------------------------------


class WalletPath(BaseModel):
    path: str = "wallet/default"


@app.post("/blockchain/ethereum", tags=["v0-legacy"])
async def ethereum_account(params: WalletPath) -> dict[str, str]:
    key = await _client().get_key(params.path)
    account = to_account_secure(key)
    return {"address": account.address}


@app.post("/blockchain/solana", tags=["v0-legacy"])
async def solana_keypair(params: WalletPath) -> dict[str, str]:
    key = await _client().get_key(params.path)
    keypair = to_keypair_secure(key)
    return {"address": str(keypair.pubkey())}


# ---------------------------------------------------------------------------
# dstack guest API v1 (dstack OS >= 0.6.0)
#
# v1 get_key derives different key material than v0 for the same name, and
# `algorithm` is required. Apps that already published v0-derived addresses
# must stay on the legacy v0 routes below.
# ---------------------------------------------------------------------------


@app.get("/v1/version", tags=["v1"])
async def v1_version() -> dict[str, Any]:
    """Guest-agent version. Also the cheapest probe for v1 support."""
    result = await _client_v1().version()
    return result.model_dump(mode="json")


@app.get("/v1/info", tags=["v1"])
async def v1_info() -> dict[str, Any]:
    """Application identity and configuration (not attestation)."""
    result = await _client_v1().info()
    return result.model_dump(mode="json")


class V1GetKeyParams(BaseModel):
    domain: str = Field(
        default="", description="Domain-separation string; flat, not a path"
    )
    algorithm: Literal["secp256k1", "ed25519"]


@app.post("/v1/keys/derive", tags=["v1"])
async def v1_derive_key(params: V1GetKeyParams) -> dict[str, Any]:
    """Deterministic key for (domain, algorithm), with its signature chain."""
    result = await _client_v1().get_key(params.domain, params.algorithm)
    return result.model_dump(mode="json")


@app.post("/v1/attestation/attest", tags=["v1"])
async def v1_attest(params: ReportDataParams) -> dict[str, Any]:
    """Versioned attestation; replaces v0 get_quote and attest."""
    report_data = app_data_report_data(params.report_data)
    result = await _client_v1().attest(report_data)
    return {
        **result.model_dump(mode="json"),
        "user_input": params.report_data,
        "report_data_tag": REPORT_DATA_TAG,
        "report_data_hex": report_data.hex(),
        "report_data_derivation": REPORT_DATA_DERIVATION,
    }


@app.post("/v1/tls-key", tags=["v1"])
async def v1_tls_key(params: TlsKeyWithAppInfoParams) -> dict[str, Any]:
    """Certificate with a fresh key (`issue_cert`, formerly get_tls_key)."""
    not_before = params.not_before or int(time.time())
    not_after = params.not_after or not_before + 30 * 86400
    result = await _client_v1().issue_cert(
        subject=params.subject,
        alt_names=params.alt_names,
        usage_ra_tls=params.usage_ra_tls,
        usage_server_auth=params.usage_server_auth,
        usage_client_auth=params.usage_client_auth,
        with_app_info=params.with_app_info,
        not_before=not_before,
        not_after=not_after,
    )
    return result.model_dump(mode="json")


# The SDK's ethereum/solana helpers only accept v0 responses, so v1 wallets
# are built straight from the 32 key bytes.


class V1WalletDomain(BaseModel):
    domain: str = "wallet/default"


@app.post("/v1/blockchain/ethereum", tags=["v1"])
async def v1_ethereum_account(params: V1WalletDomain) -> dict[str, str]:
    key = await _client_v1().get_key(params.domain, "secp256k1")
    return {"address": Account.from_key(key.key).address}


@app.post("/v1/blockchain/solana", tags=["v1"])
async def v1_solana_keypair(params: V1WalletDomain) -> dict[str, str]:
    key = await _client_v1().get_key(params.domain, "ed25519")
    return {"address": str(Keypair.from_seed(key.key).pubkey())}


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
