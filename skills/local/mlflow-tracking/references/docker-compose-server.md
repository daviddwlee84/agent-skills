# Docker Compose server (PostgreSQL + MinIO)

> Authoritative source: https://mlflow.org/docs/latest/tracking/server.html
> Stack source: bundled in `assets/docker-compose-stack/` (also see its README)

The production deployment for teams. Battle-tested setup with PostgreSQL for
metadata and MinIO (S3-compatible) for artifacts.

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ PostgreSQL  │◄───│   MLflow     │───►│      MinIO      │
│ (metadata)  │    │   server     │    │  (artifacts)    │
│   :5432     │    │   :8000      │    │ :9000 / :9001   │
└─────────────┘    └──────────────┘    └─────────────────┘
       ▲                                        ▲
       └──────── docker network: mlflow ────────┘
```

The `create_s3_buckets` init container creates the artifact bucket once,
then exits. Healthchecks gate `tracking_server` start until DB and MinIO
are ready.

## One-time setup

```bash
# 1. Copy the stack into your project
bash skills/local/mlflow-tracking/scripts/start-mlflow-server.sh \
  --target-dir infra/mlflow

# OR manually:
cp -r skills/local/mlflow-tracking/assets/docker-compose-stack infra/mlflow
cd infra/mlflow
cp .env.example .env

# 2. Edit .env for non-local use:
#    - PG_PASSWORD          (rotate from default)
#    - MINIO_ACCESS_KEY     (rotate)
#    - MINIO_SECRET_ACCESS_KEY (rotate)
#    - MLFLOW_PORT          (if 8000 is taken)

# 3. Launch
docker compose up -d

# 4. Verify
curl http://localhost:8000/health    # → "OK"
```

## Daily ops

```bash
docker compose logs -f tracking_server   # tail logs
docker compose ps                         # check health
docker compose down                       # stop (data persists)
docker compose down -v                    # stop + delete data (irreversible)
docker compose pull && docker compose up -d   # upgrade MLflow (also bump pin in Dockerfile)
```

## Connecting clients

```bash
# Set on every machine that runs experiments:
export MLFLOW_TRACKING_URI=http://your-server:8000
export AWS_ACCESS_KEY_ID=<MINIO_ACCESS_KEY>
export AWS_SECRET_ACCESS_KEY=<MINIO_SECRET_ACCESS_KEY>
export MLFLOW_S3_ENDPOINT_URL=http://your-server:9000   # tells boto3 to hit MinIO
```

The **client uploads artifacts directly to MinIO** (the server only handles
metadata). This is why client-side AWS env vars are required.

For Python:

```python
import mlflow
mlflow.set_tracking_uri("http://your-server:8000")
# Registry inherits automatically — don't set MLFLOW_REGISTRY_URI separately.
```

## Customizing

### Use AWS S3 instead of MinIO

In `docker-compose.yaml`, remove the `s3` and `create_s3_buckets` services.
In `tracking_server`:

```yaml
environment:
  AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
  AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
  AWS_DEFAULT_REGION: us-east-1
command: >
  mlflow server
  --backend-store-uri postgresql://${PG_USER}:${PG_PASSWORD}@db:5432/${PG_DATABASE}
  --artifacts-destination s3://your-aws-bucket
  --serve-artifacts
  --host 0.0.0.0 --port 5000
```

Drop `MLFLOW_S3_ENDPOINT_URL` and `MLFLOW_S3_IGNORE_TLS`.

### Add basic auth

The bundled stack does NOT include auth. For internal-network deployments
that's often fine. If you need auth:

**Option 1 — MLflow built-in basic auth** (since 2.5):

```bash
command: >
  mlflow server
  --app-name basic-auth
  --backend-store-uri postgresql://...
  ...
```

Then `mlflow.set_tracking_uri("http://user:pass@host:8000")` from clients.

**Option 2 — Front with nginx + Auth0 / Authelia**: out of scope for this
skill. See https://mlflow.org/docs/latest/auth/.

### Run behind a reverse proxy

Set `MLFLOW_HOST` and `MLFLOW_PORT` for the server, and add an `X-Forwarded-Prefix`-aware
nginx location block. Standard nginx/traefik patterns apply.

### Pin the MLflow version

Edit `Dockerfile`:

```dockerfile
FROM ghcr.io/mlflow/mlflow:v3.6.0    # bump this to upgrade
RUN pip install --no-cache-dir psycopg2-binary boto3
```

Then `docker compose build --no-cache tracking_server && docker compose up -d`.
Always read the MLflow release notes before upgrading — schema migrations
happen between major versions.

## Backup strategy

- **Database**: `pg_dump -h localhost -U mlflow mlflow > mlflow.sql` (or `docker compose exec db pg_dump ...`)
- **Artifacts**: `mc mirror minio/mlflow s3://backup-bucket/mlflow/` (using MinIO client)
- **Config**: `infra/mlflow/.env` — store securely, NOT in git

For automated backups, run those two commands from cron and ship to off-host storage.

## Common pitfalls

- **macOS port 5000 conflict** — AirPlay Receiver. Default `MLFLOW_PORT` is 8000 to dodge this.
- **`database is locked` after migrating from SQLite** — You forgot to update `MLFLOW_TRACKING_URI` somewhere. SQLite errors should never appear once you're on the server.
- **Artifact upload fails with `Access Denied` or `NoSuchBucket`** — Either the client doesn't have AWS creds set, or `MLFLOW_S3_ENDPOINT_URL` is wrong. Test with `aws --endpoint-url http://server:9000 s3 ls s3://mlflow/`.
- **`Connection refused` on first boot** — Wait for healthchecks (~30s). `docker compose ps` should show all services as `healthy`. If `tracking_server` is `restarting`, check its logs — usually a DB password mismatch.
- **Artifacts visible in MinIO console but not in MLflow UI** — The artifact path stored in PostgreSQL must match what the server can resolve. Don't change `MLFLOW_BUCKET_NAME` mid-flight; old runs will point at the old bucket.
- **Forgot to commit `.env.example`** — `.env` itself is gitignored (and should be), but `.env.example` (template, no secrets) should be in git so collaborators know what env vars to set.

## When to outgrow this stack

Migrate to managed (Databricks, AWS managed MLflow, GCP Vertex MLflow) when:

- You need SSO / RBAC beyond basic auth
- You need geo-replication or HA
- You exceed ~100k runs and need per-experiment sharding
- Compliance requires audit logs you don't want to roll yourself

Below those thresholds, this stack scales to dozens of users on a single mid-sized VM.
