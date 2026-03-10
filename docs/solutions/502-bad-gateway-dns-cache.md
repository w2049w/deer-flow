---
symptoms: ["Intermittent 502 Bad Gateway errors when accessing backend APIs through Nginx", "Nginx logs show 'connect() failed (111: Connection refused) while connecting to upstream'"]
root_cause: "Nginx caches upstream container IP addresses. When containers are recreated by Docker Compose, their internal IPs may change, but Nginx continues to use the stale (cached) IPs."
module: "docker-infrastructure"
severity: "high"
tags: ["nginx", "docker-compose", "502-bad-gateway", "dns-cache"]
---

# Solution: Recurring 502 Bad Gateway due to Nginx DNS Caching

## Problem Description
Users experience `502 Bad Gateway` when trying to access the application through the Nginx reverse proxy (port 2026). This usually happens after a deployment or a manual restart of backend services using `docker-compose`.

## Working Solution
The most direct fix is to restart the Nginx container to force it to re-resolve the service names (`gateway`, `langgraph`, etc.) and pick up the new container IPs.

### Manual Fix
Run the following command in the `docker/` directory:

```bash
docker restart deer-flow-nginx
```

### Verification
Check the Nginx logs for successful upstream connections:

```bash
docker logs deer-flow-nginx --tail 20
```

## Root Cause Analysis
Nginx resolves the hostnames specified in `proxy_pass` (like `http://gateway:8001`) to IP addresses. By default, it may cache these resolutions. When Docker Compose recreates a container, the internal IP address often changes. Since the Nginx container hasn't been restarted, it keeps trying to reach the old, now non-existent, IP address.

## Prevention
To prevent this in the future, one could use a variable for the `proxy_pass` directive combined with a short `resolver` timeout in the Nginx configuration, which forces Nginx to re-resolve the name on every (or frequent) request.

Example:
```nginx
resolver 127.0.0.11 valid=10s;
set $upstream_gateway gateway:8001;
proxy_pass http://$upstream_gateway;
```
Currently, mostly `server` blocks use the direct name which triggers the caching behavior.
