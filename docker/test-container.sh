#!/usr/bin/env bash
# Build the image, start a container, and check it from the outside:
# it becomes healthy, it answers on the published port, and it does not run as root.
# Needs Docker. Run from anywhere:  bash docker/test-container.sh
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
image="wre-docker-example:test"
name="wre-docker-example-$$"
port="${PORT:-8080}"

cleanup() { docker rm -f "$name" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "== build"
docker build -t "$image" "$here"

echo "== run"
docker run -d --name "$name" -p "127.0.0.1:$port:8080" "$image" >/dev/null

echo "== wait for the HEALTHCHECK to report healthy"
status=""
for _ in $(seq 1 30); do
  status="$(docker inspect --format '{{.State.Health.Status}}' "$name")"
  [[ "$status" == "healthy" ]] && break
  sleep 1
done
echo "health: $status"
[[ "$status" == "healthy" ]] || { docker logs "$name"; exit 1; }

echo "== request from the host"
body="$(curl -sS "http://127.0.0.1:$port/")"
echo "$body"
[[ "$body" == *"Hello from inside a container"* ]]

echo "== the container's user"
user="$(docker exec "$name" id -u)"
echo "uid: $user"
[[ "$user" != "0" ]]

echo "== image size"
docker image ls "$image" --format '{{.Repository}}:{{.Tag}}  {{.Size}}'

echo "all container checks passed"
