# First-party GoreeCloud Photos CLI

The `photosctl` Python executable is maintained in `api/app/cli.py`, installed from `api/pyproject.toml`, and covered by `api/tests/test_cli.py`. It complements (and does not bypass) the same private HTTP API used by web and native clients.

## Setup

From `api/` run `uv sync --frozen --group dev`, then:

```sh
uv run --frozen photosctl --version
uv run --frozen photosctl --help
uv run --frozen photosctl health
uv run --frozen photosctl list --limit 40 --page 1
uv run --frozen photosctl list --search vacation --favorites
uv run --frozen photosctl albums
uv run --frozen photosctl stats
uv run --frozen photosctl change-password
uv run --frozen photosctl create-album "Family"
uv run --frozen photosctl upload /path/to/selected/photo.jpg
uv run --frozen photosctl download 00000000-0000-4000-8000-000000000042 --output /private/photo.jpg
uv run --frozen photosctl favorite 00000000-0000-4000-8000-000000000042
uv run --frozen photosctl trash 00000000-0000-4000-8000-000000000042 --yes
uv run --frozen photosctl restore 00000000-0000-4000-8000-000000000042
```

Replace sample UUIDs with real IDs shown by `list`. For remote servers, add `--server https://your-private-server.example` **before** the command name. Plain HTTP is accepted only on the current device's loopback address. Redirects and environment HTTP proxies are not followed.

When `PHOTOS_ACCESS_TOKEN` is unset, the CLI prompts for the library password without shell-argument exposure and revokes the temporary session on exit. For an automated task you may supply a suitably protected short-lived session through the `PHOTOS_ACCESS_TOKEN` environment variable; environment variables may be visible to privileged local processes. Keep tokens out of shell history, CI logs and public workflows. No credentials are stored in a config file by the CLI.

Outputs are JSON and failures return nonzero exit status. Downloads refuse existing targets and write privately using a temporary file plus exclusive hard-link promotion. Uploads accept explicit regular files, stream their bytes, and are limited to 512 MiB.

## Offline backup and recovery commands

**Stop the API and all writers first.** Only the offline backup commands work without any running API or login.

```sh
uv run --frozen photosctl backup --data-dir /private/photos-data --output /separate-private-volume/photos.tar
uv run --frozen photosctl verify-backup --input /separate-private-volume/photos.tar
uv run --frozen photosctl restore-backup --input /separate-private-volume/photos.tar --data-dir /new/empty/restore-target
```

These archives are **unencrypted**; keep them in a restricted encrypted volume and independently test restoration before claiming recovery readiness. The CLI provides no scheduled backup, no remote off-site replication, no E2EE, and no silent media deletion. Android and browser application owners can use this supported companion CLI to administer their self-hosted API from a terminal; the mobile app itself does not expose a general shell.


## Changing the private library password

Run `uv run --frozen photosctl --server https://your-private-server.example change-password`. The CLI prompts for the **current**, **new** and **confirmed new** password without accepting secrets as command arguments. The authenticated API verifies the existing secret, updates the stored scrypt hash, and immediately revokes **every** active session across web, Linux, Android and CLI clients. All clients must log in again. Avoid rotation during active uploads or exports; the server may interrupt in-flight authenticated operations. The initial `PHOTOS_ADMIN_PASSWORD` environment variable does not override a rotated stored password on restart. Keep recovery documentation securely, and do not claim a lost password can be recovered without an existing authenticated recovery process.
