# Phala Cloud Python Starter

[![](https://cloud.phala.network/deploy-button.svg)](https://cloud.phala.network/templates/python-starter)

FastAPI reference app that exercises `dstack-sdk` 0.6.0, led by the dstack guest API v1. Use it as a copy/paste source for your own dstack-deployed service. The container is built and published to GHCR automatically.

## Requirements

The `/v1/` routes use the current dstack guest API (`AsyncDstackClient`) and need dstack OS >= 0.6.0 (guest agent 0.6.0+). On Phala Cloud, CPU images `dstack-0.6.x` have it. GPU images are still 0.5.15 and only speak v0, so use the legacy routes there.

## Endpoint Map

### Guest API v1 (primary, tag `v1`)

| Endpoints | What it shows |
|---|---|
| `GET /v1/version`, `GET /v1/info` | `version()` and `info()`. `/v1/version` is also the cheapest probe for v1 support. |
| `POST /v1/keys/derive` | `get_key(domain, algorithm)` for `secp256k1` or `ed25519`. `algorithm` is required; `domain` is a flat domain-separation string. |
| `POST /v1/attestation/attest` | `attest(report_data)`, which returns the versioned attestation (quote and event log). Caller input is hashed as `sha512("app-data:" \|\| utf8(input))` into 64 bytes of `report_data`; the response includes `user_input`, `report_data_hex`, and `report_data_derivation` so a verifier can recompute it. |
| `POST /v1/tls-key` | `issue_cert()` (v0 `get_tls_key`), with `not_before` / `not_after` / `with_app_info` |
| `POST /v1/blockchain/ethereum`, `POST /v1/blockchain/solana` | Wallets built from `get_key` bytes: `Account.from_key` (secp256k1) and `Keypair.from_seed` (ed25519). The SDK's `to_account_secure` / `to_keypair_secure` helpers accept v0 responses only. |

v1 has no `sign`, `verify`, `get_quote`, or `emit_event`. Sign locally with the key from `get_key`, and use `attest()` instead of `get_quote()`.

Do not hold assets in a wallet derived from `get_key`: the key is a function of the KMS root, so these wallets suit demos and low-value or rotatable signing only. See the [dstack SDK warning](https://github.com/Dstack-TEE/dstack/blob/next/sdk/js/README.md#blockchain-helpers).

### Utilities (no socket required)

`POST /utils/compose-hash`, `POST /utils/encrypt-env-vars`, `POST /utils/verify-env-encrypt-public-key`, `POST /utils/verify-env-encrypt-public-key/legacy`: compose hash, ECIES env-var encryption, and KMS env-encrypt key verification (signature_v1 with timestamp, plus the deprecated legacy path).

### Legacy guest API v0 (tag `v0-legacy`)

The routes below call the frozen v0 API through `AsyncDstackClientV0`. They are kept for apps already running on v0.

> **Warning:** v1 `get_key` derives different key material than v0 for the same name. An app that already published v0-derived addresses or keys must stay on v0; switching to v1 changes them.

| Group | Endpoints |
|---|---|
| Diagnostics | `GET /health`, `GET /version`, `GET /info` |
| Keys | `POST /keys/derive`, `POST /keys/derive/ed25519` |
| Attestation | `POST /attestation/quote`, `POST /attestation/attest` |
| TLS Keys | `POST /tls-key`, `POST /tls-key/with-app-info` |
| Sign / Verify | `POST /sign`, `POST /verify` |
| Events | `POST /emit-event` |
| Blockchain | `POST /blockchain/ethereum`, `POST /blockchain/solana` |

Interactive Swagger UI is available at `/docs` once the server is up.

## Run Locally

Clone and set up a venv:

```shell
git clone --depth 1 https://github.com/Phala-Network/phala-cloud-python-starter.git
cd phala-cloud-python-starter
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
cp env.example .env
```

The SDK auto-discovers `/var/run/dstack.sock`. The `/v1/` routes use `AsyncDstackClient`; the legacy routes use `AsyncDstackClientV0`. Local development needs a running dstack guest-agent simulator (Linux). See [sdk/simulator](https://github.com/Dstack-TEE/dstack/tree/next/sdk/simulator).

Point the SDK at it with `DSTACK_SIMULATOR_ENDPOINT` — a unix socket path, or an `http://` / `https://` URL (both clients accept both). Set it in `.env` (see `env.example`) or export it:

```shell
export DSTACK_SIMULATOR_ENDPOINT=/path/to/dstack.sock
# or: export DSTACK_SIMULATOR_ENDPOINT=http://127.0.0.1:8090
```

Then in another terminal:

```shell
source venv/bin/activate
python -m fastapi dev
```

Visit http://127.0.0.1:8000/ for the endpoint map or http://127.0.0.1:8000/docs for Swagger.

## Container Image

Every push to `main` rebuilds and publishes a multi-tagged image to GHCR:

```
ghcr.io/phala-network/phala-cloud-python-starter:latest
ghcr.io/phala-network/phala-cloud-python-starter:main
ghcr.io/phala-network/phala-cloud-python-starter:sha-<short>
```

Build locally (optional):

```shell
docker build -t phala-cloud-python-starter .
```

## Deploy

`docker-compose.yml` already points at the published GHCR image and mounts `/var/run/dstack.sock` so the SDK can talk to the host guest-agent.
