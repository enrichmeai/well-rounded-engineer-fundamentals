#!/usr/bin/env bash
# Show HTTP caching with curl: a 200, then a 304 Not Modified.
# Start the server first, in another terminal:  python3 server.py
set -euo pipefail

url="${1:-http://127.0.0.1:8000/}"

echo "1) First request. Note the ETag and Cache-Control headers."
echo "   \$ curl -sS -i $url"
curl -sS -i "$url"
echo

etag="$(curl -sS -I "$url" | tr -d '\r' | awk 'tolower($1) == "etag:" { print $2 }')"
echo "2) Ask again, sending the ETag back in If-None-Match."
echo "   \$ curl -sS -i -H 'If-None-Match: $etag' $url"
curl -sS -i -H "If-None-Match: $etag" "$url"
echo
echo "The second answer is 304 Not Modified with no body: the copy you already have is still good."
