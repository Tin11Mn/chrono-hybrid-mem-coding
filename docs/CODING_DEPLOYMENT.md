# Coding service deployment

This Compose profile runs Coding as a separate service beside any existing Textual deployment. It uses a distinct container, a persistent named volume, and a distinct database file. It binds to host port `18002` for direct NAT forwarding. The Textual container, database, and existing public listener are not changed.

## Prepare the server

Check out the fixed Coding commit that will be submitted. Do not deploy a moving branch reference:

```sh
git clone https://github.com/Tin11Mn/chrono-hybrid-mem-coding.git
cd chrono-hybrid-mem-coding
git checkout <fixed-coding-commit>
cp .env.coding.example .env.coding
chmod 600 .env.coding
```

Edit `.env.coding` on the server. Set `CODING_IMAGE_TAG` to the exact checked-out Git commit SHA, `OPENAI_API_KEY` to the runtime key for `gpt-4o-mini`, and `MEMORY_SYSTEM_KEY` to a long random API token. `PIP_INDEX_URL` selects the Python package index used during the image build; use an index reachable from the server. `OPENAI_BASE_URL` is optional. Configure the same system token in the evaluation request using Bearer authentication. The platform Eval Key is a separate credential. Never put any secret in Git, an image, or a URL.

## Start and inspect the Coding container

```sh
docker compose --env-file .env.coding -p chrono-coding -f compose.coding.yaml up -d --build
docker compose --env-file .env.coding -p chrono-coding -f compose.coding.yaml ps
```

For direct NAT access, add a TCP forwarding rule from a free public port to instance port `18002`. The endpoint is `http://<public-ip>:<public-port>`. This sends API traffic over plain HTTP; use TLS termination if the platform requires HTTPS or if the bearer token must be encrypted in transit. Check `GET /health`, then run an isolated Add → Search smoke using the same `user_id` and verify that Search returns the original message. Use the official platform Smoke after the endpoint and access request have been reviewed.

The named volume `chrono_hybrid_mem_coding_data` stores `/data/chrono_hybrid_mem_coding.db` independently from Textual. Preserve this volume when updating or restarting the container. `docker compose down` keeps it; avoid `docker compose down -v` and volume-pruning commands.

## Evaluation submission record

Before Full, record the fixed Git commit, image tag, public `/add` and `/search` URLs, HTTPS/auth scheme, Add/Search concurrency, capacity, timeout, rate limits, and operational constraints. The Coding endpoint must remain a participant-operated public API; a repository or image alone is not a deployment.

## Host-specific details still required

This profile assumes Docker Compose. For servers behind NAT, forward an external TCP port to instance port `18002`. Add a TLS proxy only when HTTPS is required; keep the Coding database and container separate from the existing Textual service.
