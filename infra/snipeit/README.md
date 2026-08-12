# Snipe-IT local test environment

This Docker Compose environment runs the application under test independently
from the legacy mock and datastore stack.

## Services

| Service | Host address |
| --- | --- |
| Snipe-IT | `http://localhost:8090` |
| MySQL | `127.0.0.1:13307` |

## First-time configuration

Copy `.env.example` to `.env`, replace every placeholder, and generate a unique
Laravel application key. The local `.env` file is ignored by Git.

## Commands

Run these commands from the repository root:

```powershell
docker compose --env-file .\infra\snipeit\.env -f .\infra\snipeit\docker-compose.yml up -d
docker compose --env-file .\infra\snipeit\.env -f .\infra\snipeit\docker-compose.yml ps
docker compose --env-file .\infra\snipeit\.env -f .\infra\snipeit\docker-compose.yml logs --tail 100 app
docker compose --env-file .\infra\snipeit\.env -f .\infra\snipeit\docker-compose.yml down
```

Do not use `down -v` during normal development because it deletes the Snipe-IT
database and uploaded-file volumes.
