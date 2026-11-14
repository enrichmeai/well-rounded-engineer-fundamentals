#!/usr/bin/env bash
#
# logsum.sh: summarise a web server access log (Common Log Format).
#
# It prints how many requests there were, how many of each HTTP status code,
# and the most requested paths. The report goes to stdout; progress and errors
# go to stderr, so you can pipe the report somewhere without the noise.
#
# Exit codes:
#   0  success
#   2  usage error (bad option or missing argument)
#   3  the log file does not exist or cannot be read
#   4  the file has no lines that look like an access log

# Stop on errors (-e), on unset variables (-u) and on a failure anywhere in a pipe (pipefail).
set -euo pipefail

readonly PROG="${0##*/}"
readonly EXIT_USAGE=2
readonly EXIT_NO_FILE=3
readonly EXIT_NO_DATA=4

top=5
verbose=0
workdir=""

# Log to stderr, never stdout: stdout is for the report.
log() { printf '%s: %s\n' "$PROG" "$*" >&2; }
debug() { if [[ "$verbose" -eq 1 ]]; then log "$@"; fi; }
die() {
  local code="$1"
  shift
  log "error: $*"
  exit "$code"
}

usage() {
  cat <<EOF
Usage: $PROG [-n TOP] [-v] [-h] LOGFILE

Summarise an access log in Common Log Format.

Options:
  -n TOP   how many of the most requested paths to show (default: 5)
  -v       verbose: say what the script is doing (on stderr)
  -h       show this help and exit
EOF
}

# Runs on every exit, whether the script succeeds, fails or is interrupted.
cleanup() {
  if [[ -n "$workdir" && -d "$workdir" ]]; then
    rm -rf -- "$workdir"
    debug "removed temporary directory $workdir"
  fi
}
trap cleanup EXIT

parse_args() {
  local opt
  while getopts ":n:vh" opt; do
    case "$opt" in
      n) top="$OPTARG" ;;
      v) verbose=1 ;;
      h)
        usage
        exit 0
        ;;
      :)
        usage >&2
        die "$EXIT_USAGE" "option -$OPTARG needs a value"
        ;;
      *)
        usage >&2
        die "$EXIT_USAGE" "unknown option -$OPTARG"
        ;;
    esac
  done
  shift $((OPTIND - 1))

  if [[ ! "$top" =~ ^[1-9][0-9]*$ ]]; then
    die "$EXIT_USAGE" "-n must be a positive whole number, got '$top'"
  fi
  if [[ $# -ne 1 ]]; then
    usage >&2
    die "$EXIT_USAGE" "expected exactly one LOGFILE, got $#"
  fi
  logfile="$1"
}

main() {
  parse_args "$@"

  if [[ ! -f "$logfile" || ! -r "$logfile" ]]; then
    die "$EXIT_NO_FILE" "cannot read '$logfile'"
  fi

  workdir="$(mktemp -d)"
  debug "working in $workdir"

  # Keep only lines that look like Common Log Format:
  #   host ident user [date] "METHOD /path PROTOCOL" status size
  # and write "status path" for each one. The || true stops grep's
  # "no match" exit code from ending the script under set -e; we check
  # for an empty result just below instead.
  grep -E '^[^ ]+ [^ ]+ [^ ]+ \[[^]]+\] "[A-Z]+ [^ ]+ [^"]*" [0-9]{3} ' "$logfile" \
    | awk '{ print $9, $7 }' >"$workdir/parsed" || true

  local total skipped
  total="$(wc -l <"$workdir/parsed" | tr -d ' ')"
  skipped=$(($(wc -l <"$logfile" | tr -d ' ') - total))
  debug "parsed $total lines, skipped $skipped"

  if [[ "$total" -eq 0 ]]; then
    die "$EXIT_NO_DATA" "no access-log lines found in '$logfile'"
  fi

  echo "Requests: $total"
  if [[ "$skipped" -gt 0 ]]; then
    echo "Skipped (not access-log lines): $skipped"
  fi
  echo
  echo "By status code:"
  awk '{ print $1 }' "$workdir/parsed" | sort | uniq -c | sort -k2,2n \
    | awk '{ printf "  %s  %d\n", $2, $1 }'
  echo
  echo "Top $top paths:"
  awk '{ print $2 }' "$workdir/parsed" | sort | uniq -c | sort -k1,1nr -k2,2 \
    | awk -v top="$top" 'NR <= top { printf "  %5d  %s\n", $1, $2 }'
}

main "$@"
