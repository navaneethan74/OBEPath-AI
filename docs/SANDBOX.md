# OBEPath AI — Secure Code Execution Sandbox Architecture

## 1. Security Overview & Threat Model

In outcome-based education (OBE) programming assignments, students submit untrusted Python code for automated testing. 

### Why String & AST Blacklists Fail
Previously, code execution attempted to enforce security boundaries using string pattern matching and AST node filtering. Attackers and researchers proved this boundary escapable using dynamic attribute access and string concatenation:

```python
# Escaping traditional blacklist filters via runtime reflection:
getattr(__builtins__, chr(95)+chr(95)+'import'+chr(95)+chr(95))('os').system('cat .env')
```

**Security Mandate:** Blacklists are utilized solely as a fast, friendly early-rejection UX helper to inform students about prohibited standard library functions. **The container boundary is the sole authoritative security perimeter.**

---

## 2. Container Isolation Boundary

Every code submission executes in a fresh, isolated, single-use Docker container spawned dynamically via `code_runner.py`. Code and test cases are piped directly via `stdin`—**no host folders, project directories, database files, or `.env` secrets are ever mounted.**

### Execution Flags

| Flag | Value | Security Purpose |
| :--- | :--- | :--- |
| `--network` | `none` | Blocks all outbound & inbound network traffic. Prevents SSRF, port scanning, data exfiltration, and socket connections to `localhost:8000`. |
| `--read-only` | Active | Root filesystem is mounted strictly read-only. Prevents persistence, binary replacement, and file tampering. |
| `--tmpfs` | `/tmp:rw,noexec,nosuid,size=16m` | Restricted in-memory temporary scratchpad capped at 16 MB with binaries blocked from executing (`noexec`). |
| `--memory` | `128m` | Limits container RAM to 128 MB. Memory bombs are killed cleanly via OOM (exit code 137) without affecting the host. |
| `--memory-swap` | `128m` | Disallows additional swap space, enforcing a hard 128 MB ceiling. |
| `--cpus` | `0.5` | Restricts CPU usage to half a core, preventing CPU starvation. |
| `--pids-limit` | `64` | Restricts process count to 64, completely neutralizing fork bombs. |
| `--cap-drop` | `ALL` | Drops all Linux kernel capabilities (including `CAP_NET_RAW`, `CAP_SYS_ADMIN`, `CAP_DAC_OVERRIDE`). |
| `--security-opt` | `no-new-privileges` | Prevents sub-processes from acquiring additional privileges via setuid/setgid binaries. |
| `--user` | `sandboxuser` | Forces execution under non-root unprivileged account (UID 1000). |
| `--rm` | Active | Automatically purges container filesystem upon process exit. |
| Stdin Passing | Direct Pipe | Code and test harness are passed via standard input directly to `python3 -u -`. No temporary files exist on host disk. |

---

## 3. How to Build the Sandbox Image

The sandbox image `obepath-sandbox:1` is based on minimal `python:3.11-slim` with no package managers, no extra dependencies, and no compilers (`gcc`/`g++`).

### Build via PowerShell (Windows)
```powershell
.\sandbox\build.ps1
```

### Build via Bash (Linux / macOS)
```bash
./sandbox/build.sh
```

### Manual Docker CLI Build
```bash
docker build -t obepath-sandbox:1 ./sandbox
```

---

## 4. Fail-Closed Policy & Dev Fallback

### Fail-Closed in Production
If the Docker daemon is unreachable, offline, or Docker is not installed:
* The backend **FAILS CLOSED** immediately.
* `/api/assessment/compile-code` returns **HTTP 503 Service Unavailable**:
  ```json
  {
    "detail": "Code execution temporarily unavailable"
  }
  ```
* Under no circumstances will the system fall back to host subprocess execution in production.

### Dev-Only Unsafe Fallback (`SANDBOX_ALLOW_UNSAFE_LOCAL`)
For local workstation development on machines where Docker Desktop is not installed:
* Set `SANDBOX_ALLOW_UNSAFE_LOCAL=true` in `.env`.
* When active, a loud security warning is logged at runtime:
  `CRITICAL SECURITY WARNING: Docker is unavailable. Running code in UNSAFE host mode because SANDBOX_ALLOW_UNSAFE_LOCAL=true. THIS MUST NEVER BE USED IN PRODUCTION!`
* **Production Guard:** If `ENV=production` or `ENVIRONMENT=production`, the `SANDBOX_ALLOW_UNSAFE_LOCAL` flag is **strictly ignored**, and the server fails closed with HTTP 503.

---

## 5. Concurrency & Rate Limiting

To prevent Denial of Service (DoS) attacks on compute resources:

1. **Global Concurrency Semaphore:**
   * Maximum **4 simultaneous container executions** across the entire backend instance.
   * If all 4 slots are busy and a new request cannot acquire a slot within 1.0 second, the request is rejected with **HTTP 429 Too Many Requests**:
     `"Compiler busy. Maximum concurrent execution limit reached. Please retry in a few moments."`

2. **Per-User Rate Limiting:**
   * Maximum **10 execution runs per minute** per user ID.
   * Attempting an 11th run within 60 seconds returns **HTTP 429 Too Many Requests** with standard `Retry-After: <seconds>` response header.

3. **Input and Output Caps:**
   * **Code Length:** Capped at 10,000 characters (returns HTTP 400 if exceeded).
   * **Test Cases:** Maximum 20 test cases per submission (returns HTTP 400 if exceeded).
   * **Execution Timeout:** Clamped between 0.5s and 5.0s (client requests for larger values are clamped to 5.0s).
   * **Output Truncation:** Stdout and Stderr are capped at 64 KB inside the harness and runner.

---

## 6. Deployment Requirements & Platform Limitations

### Serverless & PaaS Limitations
Common serverless and lightweight PaaS hosts do not support running arbitrary Docker containers from within containerized apps:
* **Render Web Services:** Does not provide access to the host Docker daemon or Docker-in-Docker (DinD).
* **Railway:** Shared ephemeral runtimes do not expose Docker daemon socket `/var/run/docker.sock`.
* **Vercel / AWS Lambda:** Serverless functions cannot run nested Docker containers.

### Recommended Production Architectures

#### Architecture A: Dedicated Virtual Private Server (VPS)
Deploy the backend on a dedicated cloud instance (e.g. AWS EC2, DigitalOcean Droplet, Hetzner Cloud, GCP Compute Engine):
1. Install Docker: `apt update && apt install -y docker.io`.
2. Add backend service user to docker group: `usermod -aG docker appuser`.
3. Build the sandbox image: `docker build -t obepath-sandbox:1 ./sandbox`.
4. Start backend: Backend can directly spawn ephemeral sandbox containers via `/var/run/docker.sock`.

#### Architecture B: External Sandbox Microservice (Judge0 / Remote Runner)
For serverless or multi-tenant deployments, route code execution to a dedicated external microservice:
1. Deploy Judge0 or an isolated runner cluster on a dedicated worker node.
2. Direct `/api/assessment/compile-code` calls to the worker cluster via mutual TLS.

---

## 7. Environment Variables Reference

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `SANDBOX_DOCKER_IMAGE` | `obepath-sandbox:1` | Docker image tag utilized for sandbox execution. |
| `SANDBOX_ALLOW_UNSAFE_LOCAL` | `false` | Development-only fallback flag allowing local host subprocess execution when Docker is absent. Strictly ignored in production. |
| `ENV` / `ENVIRONMENT` | `development` | Deployment environment indicator (`production` / `development`). When `production`, forces fail-closed 503 behavior. |
