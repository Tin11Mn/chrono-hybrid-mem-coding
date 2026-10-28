# Coding service deployment

This Compose profile runs Coding as a separate service beside any existing Textual deployment. It uses a distinct container, a persistent named volume, and a distinct database file. It binds only to `127.0.0.1:8001`; an HTTPS reverse proxy on the host can route a Coding subdomain to that local port. The Textual container, database, and public listener are not changed.

## Prepare the server

Check out the fixed Coding commit that will be submitted. Do not deploy a moving branch reference:

```sh
git clone https://github.com/Tin11Mn/chrono-hybrid-mem-coding.git
cd chrono-hybrid-mem-coding
git checkout <fixed-coding-commit>
cp .env.coding.example .env.coding
chmod 600 .env.coding
```

Edit `.env.coding` on the server. Set `CODING_IMAGE_TAG` to the exact checked-out Git commit SHA, `OPENAI_API_KEY` to the runtime key for `gpt-4o-mini`, and `MEMORY_SYSTEM_KEY` to a long random API token. `OPENAI_BASE_URL` is optional. Configure the same system token in the evaluation request using Bearer authentication. The platform Eval Key is a separate credential. Never put any secret in Git, an image, or a URL.

## Start and inspect the Coding container

```sh
docker compose --env-file .env.coding -p chrono-coding -f compose.coding.yaml up -d --build
docker compose --env-file .env.coding -p chrono-coding -f compose.coding.yaml ps
```

Configure the host's existing HTTPS reverse proxy to forward the Coding hostname to `http://127.0.0.1:8001` without changing the Textual virtual host. Keep the service port loopback-only; do not expose port 8001 directly to the internet. Check `GET /health`, then run an isolated Add → Search smoke using the same `user_id` and verify that Search returns the original message. Use the official platform Smoke after the endpoint and access request have been reviewed.

The named volume `chrono_hybrid_mem_coding_data` stores `/data/chrono_hybrid_mem_coding.db` independently from Textual. Preserve this volume when updating or restarting the container. `docker compose down` keeps it; avoid `docker compose down -v` and volume-pruning commands.

## Evaluation submission record

Before Full, record the fixed Git commit, image tag, public `/add` and `/search` URLs, HTTPS/auth scheme, Add/Search concurrency, capacity, timeout, rate limits, and operational constraints. The Coding endpoint must remain a participant-operated public API; a repository or image alone is not a deployment.

## Host-specific details still required

This profile assumes Docker Compose and a host-level HTTPS reverse proxy. Confirm the server OS, Compose availability, proxy type, DNS name, and the existing Textual launch method before applying it. If the server uses a containerized reverse proxy or NAT-generated external ports, adapt the network/port mapping without sharing the Textual database or replacing its service.
