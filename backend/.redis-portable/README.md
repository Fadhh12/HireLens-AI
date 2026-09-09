# Portable Redis (Windows dev)

Redis has no official Windows build, and the usual native options
(Memurai, tporadowski/redis MSI) install as a Windows **service**,
which needs a UAC prompt — fine on a normal desktop, but it hung here
because this session can't click "Yes" on that dialog.

The workaround: `tporadowski/redis`'s **zip** release (not the MSI) —
just `redis-server.exe` + friends, no installer, no admin rights, no
Windows service. Still "native" per the project brief (no Docker),
just run directly instead of installed as a service.

## Setup

Nothing in this folder except this README is committed (gitignored —
third-party redistributable binaries, not project source). To set it
up:

1. Download the `.zip` asset (not `.msi`) from
   https://github.com/tporadowski/redis/releases — e.g.
   `Redis-x64-5.0.14.1.zip`.
2. Unzip its contents directly into this folder, so you end up with
   `redis-server.exe`, `redis-cli.exe`, `redis.windows.conf`, etc.
   sitting next to this README.

## Run it

```bash
cd backend/.redis-portable
./redis-server.exe redis.windows.conf --port 6379
```

Leave that running in its own terminal (or `&` it in the background).
Check it's alive:

```bash
./redis-cli.exe ping   # -> PONG
```

`backend/.env`'s `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND`
already point at `redis://localhost:6379` — nothing else to configure.

If you'd rather have Redis run automatically as a proper background
service, install Memurai Developer (`winget install
Memurai.MemuraiDeveloper`) or the Redis MSI from a normal interactive
terminal where you can approve the UAC prompt yourself.
