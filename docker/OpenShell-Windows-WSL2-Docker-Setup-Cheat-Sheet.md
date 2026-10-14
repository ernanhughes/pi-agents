# OpenShell on Windows + WSL2 + Docker Desktop

These environment notes support the [PI Agents book development repository](../README.md).
For the prerequisites to run the chapter tests, start with [the examples guide](../examples/README.md).

**Setup cheat sheet: Docker gateway, sandbox JWT, Landlock, host networking, and a working smoke test**

> **Known-good result:** This procedure was validated end-to-end on Windows with WSL 3.0.1 / Linux 6.18, Docker Desktop, and OpenShell 0.1.2. The final smoke-test sandbox created successfully after using a Docker named volume for gateway JWT keys, Landlock ABI 3+, Docker host networking, and `grpc_endpoint = "http://127.0.0.1:8080"`.

> **Security scope:** This configuration is for trusted local development. TLS is disabled and unauthenticated user access is enabled, so ports 8080/8081 are deliberately published only on `127.0.0.1`. Do not expose this configuration directly to a LAN or the Internet.

## 1. What you are building

```text
Windows
├─ Docker Desktop (Linux engine on WSL2)
│  ├─ OpenShell gateway container
│  │  ├─ host 127.0.0.1:8080  -> gateway API
│  │  ├─ host 127.0.0.1:8081  -> health API
│  │  └─ Docker socket -> creates sibling sandbox/supervisor containers
│  └─ OpenShell sandbox + host-networked supervisor
└─ Ubuntu WSL
   └─ openshell CLI -> http://localhost:8080
```

## 2. Tested stack and hard requirements

| Item | Tested value / requirement |
|---|---|
| PowerShell | 7.6.6 tested |
| WSL | 3.0.1.0 tested |
| Linux kernel | 6.18.40.1 tested; use a kernel that exposes Landlock ABI 3 or newer |
| Landlock | ABI 7 tested; OpenShell requires ABI 3+ for its mandatory baseline |
| Docker Desktop | 4.92.0 tested |
| Docker Engine | 29.8.0 tested |
| OpenShell CLI / gateway | 0.1.2 tested |

## 3. Update WSL first

Run in an elevated PowerShell:

```powershell
wsl --update
wsl --shutdown
wsl --version
```

A known-good result was:

```text
WSL version: 3.0.1.0
Kernel version: 6.18.40.1-1
```

An older 5.15 WSL kernel exposed only Landlock ABI 1. OpenShell failed with `Refer | Truncate` and `Landlock allow/deny probe`. Updating WSL raised the tested environment to Landlock ABI 7.

## 4. Configure Docker Desktop

- Start Docker Desktop after the WSL update.
- Enable **host networking**.
- Disable **Enhanced Container Isolation (ECI)** for this OpenShell Docker setup.
- Restart Docker Desktop.

Verify the kernel:

```powershell
docker info --format "{{.KernelVersion}}"
wsl -d docker-desktop uname -a
```

Probe Landlock directly:

```powershell
docker run --rm python:3.13-slim `
  python -c "import ctypes,errno,platform; libc=ctypes.CDLL(None,use_errno=True); r=libc.syscall(444,None,0,1); e=ctypes.get_errno(); print('kernel=',platform.release()); print('landlock_abi=',r); print('errno=',e,errno.errorcode.get(e))"
```

**Pass condition:** `landlock_abi` must be **3 or greater**. The tested system returned `7`.

## 5. Create the local gateway files

Example directory:

```text
C:\Projects\pi-agents\docker\
├─ docker-compose.yml
└─ gateway.toml
```

## 6. Generate gateway JWT credentials in a Docker volume

Do **not** generate the keys into a Windows NTFS bind mount. Use a Docker named volume:

```powershell
docker volume create openshell-auth

docker run --rm --user 0 `
  -v openshell-auth:/out `
  ghcr.io/nvidia/openshell/gateway:latest `
  generate-certs `
  --output-dir /out `
  --server-san 127.0.0.1 `
  --server-san localhost `
  --server-san host.openshell.internal
```

Verify with a helper image (the gateway image is distroless and does not contain `ls`):

```powershell
docker run --rm `
  -v openshell-auth:/out `
  alpine `
  sh -c "ls -la /out/jwt"
```

Expected files:

```text
kid
public.pem
signing.pem
```

If `generate-certs` against a `C:\...` bind mount reports `failed to set permissions on /out` / `Operation not permitted`, that is the Windows NTFS bind-mount permission mismatch. The named-volume method avoids it.

## 7. `docker-compose.yml`

```yaml
services:
  gateway:
    image: ghcr.io/nvidia/openshell/gateway:${IMAGE_TAG:-latest}
    restart: unless-stopped
    user: "0"

    ports:
      - "127.0.0.1:${OPENSHELL_PORT:-8080}:8080"
      - "127.0.0.1:${OPENSHELL_HEALTH_PORT:-8081}:8081"

    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

      # Must remain a bind mount at the same absolute path.
      - type: bind
        source: /var/lib/openshell
        target: /var/lib/openshell
        bind:
          create_host_path: true

      - type: bind
        source: ./gateway.toml
        target: /etc/openshell/gateway.toml
        read_only: true

      # JWT signing material. Named volume avoids Windows NTFS chmod issues.
      - type: volume
        source: openshell-auth
        target: /etc/openshell/auth
        read_only: true

    environment:
      OPENSHELL_GATEWAY_CONFIG: /etc/openshell/gateway.toml
      OPENSHELL_DB_URL: "sqlite:/var/lib/openshell/gateway.db?mode=rwc"
      XDG_DATA_HOME: /var/lib/openshell
      HOME: /var/lib/openshell

volumes:
  openshell-auth:
    external: true
    name: openshell-auth
```

Create the external volume before `docker compose up`:

```powershell
docker volume create openshell-auth
```

## 8. `gateway.toml`

```toml
[openshell]
version = 2

[openshell.gateway]
bind_address        = "127.0.0.1:8080"
health_bind_address = "127.0.0.1:8081"
log_level           = "info"
compute_driver      = "docker"
disable_tls         = true

[openshell.gateway.auth]
allow_unauthenticated_users = true

[openshell.gateway.gateway_jwt]
signing_key_path = "/etc/openshell/auth/jwt/signing.pem"
public_key_path  = "/etc/openshell/auth/jwt/public.pem"
kid_path         = "/etc/openshell/auth/jwt/kid"
gateway_id       = "openshell-docker"

[openshell.drivers.docker]
default_image          = "nvcr.io/nvidia/base/ubuntu:24.04"
sandbox_runtime_image  = "ghcr.io/nvidia/openshell/sandbox:latest"
supervisor_image       = "ghcr.io/nvidia/openshell/supervisor:latest"
image_pull_policy      = "if_not_present"
sandbox_label          = "openshell"
grpc_endpoint          = "http://127.0.0.1:8080"
app_armor_profile      = "Unconfined"
```

> **Critical Docker Desktop detail:** In this tested host-networked setup, use `grpc_endpoint = "http://127.0.0.1:8080"`. Using `host.openshell.internal` caused the supervisor to start but repeatedly fail to fetch its policy from the gateway.

## 9. Start and verify the gateway

From PowerShell in the `docker` directory:

```powershell
docker compose config
docker compose up -d --force-recreate
docker compose ps
docker compose logs --tail=100 gateway
```

Look for:

```text
gateway-minted sandbox JWT enabled gateway_id=openshell-docker
```

Check health:

```powershell
curl.exe -i http://localhost:8081/healthz
curl.exe -i http://localhost:8081/readyz
```

Check host-network reachability:

```powershell
docker run --rm --network host curlimages/curl:latest `
  -sS -o /dev/null -w "%{http_code}`n" `
  http://127.0.0.1:8080/
```

Expected result:

```text
404
```

`404` is a **PASS** here: it proves the host-networked container reached the gateway. Port 8080 is an API endpoint, not a web UI.

## 10. Install and register the OpenShell CLI in WSL

```bash
curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh
openshell --version

openshell gateway add http://localhost:8080 --name openshell-docker
openshell gateway select
openshell status
```

Expected status includes:

```text
Gateway: openshell-docker
Server: http://localhost:8080
Status: Connected
```

`Authentication: Not required (gateway)` is expected for this local config. The sandbox launch JWT is a separate mechanism.

## 11. Create the smoke-test sandbox

```bash
openshell sandbox create --name smoke-test
```

Useful checks:

```bash
openshell sandbox list
openshell sandbox connect smoke-test
```

Inside the sandbox:

```bash
uname -a
cat /etc/os-release
pwd
id
```

Cleanup:

```bash
exit
openshell sandbox delete smoke-test
```

## 12. Troubleshooting map

| Symptom | Meaning | Fix |
|---|---|---|
| `generate-certs: failed to set permissions on /out` | Windows NTFS bind mount cannot satisfy Linux chmod semantics | Generate certs into Docker named volume `openshell-auth` |
| `docker exec ... ls: executable file not found` | Gateway image is distroless | Use an Alpine helper container to inspect the named volume |
| `docker sandboxes require launch-scoped gateway authentication` | Gateway has no sandbox JWT authority | Mount JWT volume and configure `[openshell.gateway.gateway_jwt]` |
| `Refer \| Truncate` / `Landlock allow/deny probe` | Kernel Landlock ABI too old | `wsl --update`; restart Docker; require `landlock_abi >= 3` |
| Supervisor starts but policy fetch fails | Supervisor cannot reach gateway | Enable Docker host networking, disable ECI, verify `--network host` curl, use `grpc_endpoint=http://127.0.0.1:8080` |
| Browser shows 404 on `localhost:8080` | Normal: 8080 is the control-plane API | Use `8081/healthz` and `8081/readyz` for health checks |
| Docker API pipe missing after `wsl --shutdown` | Docker Desktop backend was stopped | Restart Docker Desktop, then rerun `docker info` |

## 13. Final validation checklist

- [ ] WSL kernel is modern and Docker Desktop uses the updated kernel.
- [ ] Landlock probe reports ABI 3 or greater.
- [ ] Docker Desktop host networking is enabled and ECI is disabled.
- [ ] `openshell-auth` contains `kid`, `public.pem`, and `signing.pem`.
- [ ] Gateway log says `gateway-minted sandbox JWT enabled`.
- [ ] Host-network curl to `127.0.0.1:8080` returns `404`.
- [ ] `openshell status` reports `Connected`.
- [ ] `openshell sandbox create --name smoke-test` succeeds.

## 14. Upstream references

- NVIDIA OpenShell: https://github.com/NVIDIA/OpenShell
- Docker gateway example: https://github.com/NVIDIA/OpenShell/tree/main/deploy/docker
- OpenShell Docker driver: https://github.com/NVIDIA/OpenShell/blob/main/crates/openshell-driver-docker/README.md
- OpenShell support matrix: https://github.com/NVIDIA/OpenShell/blob/main/docs/about/support-matrix.mdx
- Docker host networking: https://docs.docker.com/engine/network/drivers/host/
- Microsoft WSL commands: https://learn.microsoft.com/windows/wsl/basic-commands

> **Version note:** OpenShell is moving quickly. Treat this as a tested baseline, not a permanent substitute for release notes. If a later release changes Docker driver endpoint behavior or authentication defaults, re-check the upstream `deploy/docker` example and Docker driver README.
