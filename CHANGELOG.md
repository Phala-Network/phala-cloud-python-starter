## v0.2.0 (2026-11-24)

- Merge pull request #8 from Phala-Network/feat/dstack-v1-examples (84c73f7)
- feat: add dstack guest API v1 examples and mark v0 as legacy (dca18be)
- Merge pull request #7 from Phala-Network/chore/dstack-sdk-0.6 (c9c28de)
- docs: describe the simulator without build steps (437614a)
- chore: drop the stale tappd-simulator gitignore entry (08cbcc1)
- docs: switch to the dstack simulator and dstack sdk 0.6 (bde7741)
- chore(deps): bump dstack sdk to 0.6 and pin the v0 client (ecaf708)
- Merge pull request #5 from Phala-Network/chore/update-deps-and-base-image (f7f5882)
- Merge pull request #6 from Phala-Network/chore/gha-node24-ubuntu-pin (24cf0b5)
- chore(ci): bump GitHub Actions to Node 24 runtimes (ca6af31)
- chore(release): update docker-compose.yml and CHANGELOG.md for v0.1.0 (a08c077)
- chore: bump Python deps and pin 3.12.16-slim-trixie (fec1274)

## Unreleased

- feat: add dstack guest API v1 routes under `/v1/` (info, version, key derivation, attest, TLS cert, Ethereum and Solana wallets) as the primary example; requires dstack OS >= 0.6.0
- docs: label the existing v0 routes as legacy and document that v1 `get_key` derives different keys than v0

## v0.1.0 (2026-11-10)

- Merge pull request #4 from Phala-Network/fix/hash-quote-report-data (f2d29ec)
- fix: hash quote report_data under the app-data tag (19033c3)
- chore(release): update docker-compose.yml and CHANGELOG.md for v0.0.1 (6c43f9c)

# Changelog

## v0.0.1 (2026-06-02)

- Align CI workflows with other starter projects (f9b6b69)
- Update dstack-sdk to 0.5.4 (b7a6b8c)
- ci: build and publish image to GHCR + refresh README (0e4b4cf)
- chore: switch image distribution to GHCR (ca67e90)
- feat: rewrite demo against dstack-sdk 0.5.4b1 (e36c775)
- Merge pull request #3 from Phala-Network/dependabot/pip/urllib3-2.6.0 (c79fc84)
- Bump urllib3 from 2.3.0 to 2.6.0 (c95d8e6)
- update docker-compose.yml (c4a8ec5)
- update demo with latest version of sdk (e975463)
- update example with SDK v0.2.1 (44c72c4)
- update dependencies & build docker image (ea901d6)
- Merge pull request #2 from Phala-Network/dependabot/pip/jinja2-3.1.6 (71faea0)
- Bump jinja2 from 3.1.5 to 3.1.6 (85753a8)
- Merge pull request #1 from Phala-Network/dependabot/pip/h11-0.16.0 (c924d91)
- Bump h11 from 0.14.0 to 0.16.0 (a06a202)
- fix: demo (66779f0)
- llm auto-completion import JSONResponse wrong, so human fix it (facbf38)
- update sdk (7664c0c)
- add .dockerignore (ee86a25)
- docs (885fd8b)
- update docker-compose.yml & env.example (a263613)
- init everything for test (0966362)
