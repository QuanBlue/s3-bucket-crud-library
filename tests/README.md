# Running Tests

This suite exercises the library against two real local MinIO instances (via
`docker-compose.yml` at the repo root), standing in for two independent S3-compatible
providers (e.g. Viettel Cloud and MinIO) to validate the cross-instance sync feature,
same-instance sync regressions, and the full-pagination fix.

## Prerequisites

- Docker + Docker Compose
- Python environment with `requirements-dev.txt` installed

## Steps

```sh
# From the repo root
docker compose up -d
docker compose ps        # wait until both minio1/minio2 show "healthy"

pip install -r requirements-dev.txt
pytest -v

docker compose down      # tears down the containers (data is ephemeral, no volumes to prune)
```

## Notes

- MinIO credentials/ports are hardcoded in `tests/conftest.py` to match
  `docker-compose.yml` (`minio1` on `http://localhost:19000`, `minio2` on
  `http://localhost:19010`). Override via `MINIO1_ENDPOINT` / `MINIO1_ACCESS_KEY` /
  `MINIO1_SECRET_KEY` / `MINIO2_ENDPOINT` / `MINIO2_ACCESS_KEY` / `MINIO2_SECRET_KEY`
  env vars if you need different values (e.g. CI).
- Ports `19000`/`19010`/`19091`/`19092` were chosen instead of MinIO's usual
  `9000`/`9001` because `9000` may already be bound by something else on your machine
  (observed here: a stray `wslrelay.exe` listener on `127.0.0.1:9000`, which silently
  intercepts "localhost" connections ahead of Docker's own proxy). If those ports are
  also taken on your machine, edit both `docker-compose.yml` and the `MINIO*_ENDPOINT`
  values above/env vars to match.
- Each test creates its own uniquely-named bucket(s) and cleans them up afterward using
  the library's own `delete_objects`/`delete_bucket` methods - tests can run repeatedly
  without manual cleanup, and can run in parallel-safe fashion (unique bucket names).
