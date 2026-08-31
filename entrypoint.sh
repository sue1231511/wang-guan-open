#!/bin/bash
# Run the realtime gateway process and the periodic/background process together.
# If either exits, stop the other and let the container platform restart both.

python background_main.py &
BG_PID=$!

python main.py &
MAIN_PID=$!

EXIT_CODE=0
wait -n "$BG_PID" "$MAIN_PID" || EXIT_CODE=$?
kill "$BG_PID" "$MAIN_PID" 2>/dev/null || true
wait "$BG_PID" "$MAIN_PID" 2>/dev/null || true
exit "$EXIT_CODE"
