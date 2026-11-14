#!/usr/bin/env bash
# Plain-shell tests for logsum.sh. No test framework needed.
# Run from anywhere:  bash linux/tests/test_logsum.sh
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
script="$here/../logsum.sh"
sample="$here/../sample-access.log"

passed=0
failed=0
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT

pass() { passed=$((passed + 1)); printf 'ok    %s\n' "$1"; }
fail() { failed=$((failed + 1)); printf 'FAIL  %s\n' "$1"; }

# run ARGS...: runs the script, saving stdout, stderr and the exit code.
run() {
  set +e
  "$script" "$@" >"$tmp/out" 2>"$tmp/err"
  status=$?
  set -e
}

expect_status() { # NAME WANT
  if [[ "$status" -eq "$2" ]]; then pass "$1 (exit $2)"; else fail "$1: wanted exit $2, got $status"; fi
}
expect_out() { # NAME TEXT
  if grep -qF -- "$2" "$tmp/out"; then pass "$1"; else fail "$1: stdout lacks '$2'"; fi
}
expect_err() { # NAME TEXT
  if grep -qF -- "$2" "$tmp/err"; then pass "$1"; else fail "$1: stderr lacks '$2'"; fi
}

# --- success ---
run "$sample"
expect_status "summarises the sample log" 0
expect_out "counts requests" "Requests: 9"
expect_out "reports skipped lines" "Skipped (not access-log lines): 1"
expect_out "counts status 200" "  200  5"
expect_out "counts status 500" "  500  1"
expect_out "most requested path first" "      3  /"
if [[ ! -s "$tmp/err" ]]; then pass "quiet on stderr without -v"; else fail "stderr not empty without -v"; fi

run -n 1 "$sample"
expect_status "-n 1 works" 0
if [[ "$(sed -n '/^Top 1 paths:/,$p' "$tmp/out" | wc -l | tr -d ' ')" -eq 2 ]]; then
  pass "-n 1 shows exactly one path"
else
  fail "-n 1 did not show exactly one path"
fi

run -h
expect_status "-h shows help" 0
expect_out "help mentions usage" "Usage:"

# --- the trap cleans up, on success and on failure ---
run -v "$sample"
workdir="$(sed -n 's/^logsum.sh: working in //p' "$tmp/err")"
if [[ -n "$workdir" && ! -e "$workdir" ]]; then pass "temp dir removed after success"; else fail "temp dir left behind: '$workdir'"; fi

printf 'not a log line\nnor this one\n' >"$tmp/junk.log"
run -v "$tmp/junk.log"
expect_status "file with no log lines" 4
expect_err "explains no log lines" "no access-log lines found"
workdir="$(sed -n 's/^logsum.sh: working in //p' "$tmp/err")"
if [[ -n "$workdir" && ! -e "$workdir" ]]; then pass "temp dir removed after failure"; else fail "temp dir left behind: '$workdir'"; fi

# --- bad input ---
run
expect_status "no arguments" 2
expect_err "says a file is expected" "expected exactly one LOGFILE"

run "$sample" "$sample"
expect_status "two files" 2

run -x "$sample"
expect_status "unknown option" 2
expect_err "names the unknown option" "unknown option -x"

run -n
expect_status "-n without a value" 2

run -n zero "$sample"
expect_status "-n not a number" 2
run -n 0 "$sample"
expect_status "-n zero" 2

run "$tmp/does-not-exist.log"
expect_status "missing file" 3
expect_err "names the missing file" "cannot read"

: >"$tmp/empty.log"
run "$tmp/empty.log"
expect_status "empty file" 4

echo
echo "$passed passed, $failed failed"
[[ "$failed" -eq 0 ]]
