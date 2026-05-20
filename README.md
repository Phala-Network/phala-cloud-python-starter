# Phala Cloud Python Starter

[![](https://cloud.phala.network/deploy-button.svg)](https://cloud.phala.network/templates/python-starter)

FastAPI reference app that exercises every capability on `dstack-sdk` 0.5.4b1. Use it as a copy/paste source for your own dstack-deployed service. The container is built and published to GHCR automatically.

## Endpoint Map

| Group | Endpoints | What it shows |
|---|---|---|
| Diagnostics | `GET /health`, `GET /version`, `GET /info` | `is_reachable()`, `version()`, `info()` (including `cloud_vendor` / `cloud_product` on 0.5.7+) |
| Keys | `POST /keys/derive`, `POST /keys/derive/ed25519` | Deterministic secp256k1 and ed25519 derivation (the latter gated to dstack OS >= 0.5.7) |
| Attestation | `POST /attestation/quote`, `POST /attestation/attest` | `get_quote()` (with RTMR replay) and the versioned `attest()` envelope |
| TLS Keys | `POST /tls-key`, `POST /tls-key/with-app-info` | Legacy fields plus the 0.5.7-only `not_before` / `not_after` / `with_app_info` opts |
| Sign / Verify | `POST /sign`, `POST /verify` | `sign()` + `verify()` |
| Events | `POST /emit-event` | `emit_event()` — appends to RTMR3 |
| Blockchain | `POST /blockchain/ethereum`, `POST /blockchain/solana` | `to_account_secure` / `to_keypair_secure` |
| Utilities | `POST /utils/compose-hash`, `POST /utils/encrypt-env-vars`, `POST /utils/verify-env-encrypt-public-key`, `POST /utils/verify-env-encrypt-public-key/legacy` | Deployment helpers — compose hash, ECIES env-var encryption, KMS env-encrypt key verification (signature_v1 with timestamp, plus the deprecated legacy path) |

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

The SDK auto-discovers `/var/run/dstack.sock`. For local development without a CVM, run the dstack simulator and point `DSTACK_SIMULATOR_ENDPOINT` at it:

```shell
# Linux
wget https://github.com/Leechael/tappd-simulator/releases/download/v0.1.4/tappd-simulator-0.1.4-x86_64-linux-musl.tgz
tar -xvf tappd-simulator-0.1.4-x86_64-linux-musl.tgz
cd tappd-simulator-0.1.4-x86_64-linux-musl
./tappd-simulator -l unix:/tmp/tappd.sock

# macOS
wget https://github.com/Leechael/tappd-simulator/releases/download/v0.1.4/tappd-simulator-0.1.4-aarch64-apple-darwin.tgz
tar -xvf tappd-simulator-0.1.4-aarch64-apple-darwin.tgz
cd tappd-simulator-0.1.4-aarch64-apple-darwin
./tappd-simulator -l unix:/tmp/tappd.sock
```

`env.example` already sets `DSTACK_SIMULATOR_ENDPOINT=/tmp/tappd.sock` to match. Then in another terminal:

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
