#!/bin/bash
# Wrapper script to launch Python with correct env (used by VS Code)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$DIR/settings.sh"
exec python "$@"
