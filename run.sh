#!/usr/bin/env bash
# Human-facing launcher. A reserved verb runs a built-in action; anything else is treated as
# the name of a tool under ./tools (tools/<name>/<name>.py). Run with no arguments to list both.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tools_dir="$repo_root/tools"
venv="$repo_root/.venv"
py="$venv/bin/python"
verbs=(
    setup
    test
    lint
    format
    typecheck
    build
)

list() {
    echo "Verbs:"
    printf '  %s\n' "${verbs[@]}"
    echo
    echo "Tools:"
    if [ -d "$tools_dir" ] && [ -n "$(find "$tools_dir" -mindepth 1 -maxdepth 1 -type d)" ]; then
        find "$tools_dir" -mindepth 1 -maxdepth 1 -type d -printf '  %f\n' | sort
    else
        echo "  (none yet)"
    fi
    echo
    echo "Usage: $0 <verb|tool> [args...]"
}

setup() {
    if [ ! -x "$py" ]; then
        python3 -m venv "$venv"
    fi
    "$py" -m pip install --quiet --upgrade pip
    "$py" -m pip install --quiet -e "$repo_root[dev,pdf,svg,diagrams]"
    # mermaid-cli for mermaid blocks (E06-S03), repo-local in a fixed version; only with Node.js.
    if command -v npm >/dev/null 2>&1; then
        (cd "$repo_root/tools/mermaid" && npm ci --no-audit --no-fund --silent) \
            || echo "npm ci in tools/mermaid failed; mermaid blocks stay code." >&2
    else
        echo "Node.js not found: mermaid blocks stay code (see docs/verwendung.md, Mermaid)."
    fi
    # Playwright and its Chromium for ./run.sh preview (E10-S02); without them only preview stops.
    if "$py" -m pip install --quiet -e "$repo_root[preview]"; then
        if ! "$py" "$tools_dir/preview/preview.py" --check-browser; then
            "$py" -m playwright install chromium \
                || echo "Chromium for Playwright could not be installed; ./run.sh preview will not work." >&2
        fi
    else
        echo "Playwright could not be installed; ./run.sh preview will not work." >&2
    fi
}

ensure() {
    [ -x "$py" ] || setup
}

command="${1:-}"
[ -z "$command" ] && { list; exit 0; }
shift

cd "$repo_root"
case "$command" in
    setup) setup ;;
    test) ensure; exec "$py" -m pytest "$@" ;;
    lint) ensure; exec "$py" -m ruff check "$@" ;;
    format) ensure; "$py" -m ruff check --fix --select I "$@" && exec "$py" -m ruff format "$@" ;;
    typecheck) ensure; exec "$py" -m pyright "$@" ;;
    build) ensure; exec "$py" -m pip wheel --quiet --no-deps --wheel-dir "$repo_root/dist" "$repo_root" ;;
    *)
        entry="$tools_dir/$command/$command.py"
        if [ ! -f "$entry" ]; then
            echo "Unknown verb or tool '$command'. Run $0 with no arguments to list both." >&2
            exit 1
        fi
        ensure
        exec "$py" "$entry" "$@"
        ;;
esac
