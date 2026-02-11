#!/bin/bash

# If no arguments are provided, print usage instructions
if [ $# -eq 0 ]; then
  echo ""
  echo "Usage: docker run [OPTIONS] <docker-image> [COMMAND]"
  echo ""
  echo "To run the Backend (CLI):"
  echo "  docker run --rm \\"
  echo "    -v \$(pwd)/input:/app/input \\"
  echo "    -v \$(pwd)/output:/app/output \\"
  echo "    -v \$(pwd)/logs:/app/logs \\"
  echo "    <docker-image> backend -j <job-file>"
  echo ""
  echo "To run the Frontend (Web UI):"
  echo "  docker run --rm -p 8501:8501 \\"
  echo "    -v \$(pwd)/input:/app/input \\"
  echo "    -v \$(pwd)/output:/app/output \\"
  echo "    -v \$(pwd)/logs:/app/logs \\"
  echo "    <docker-image> ui"
  echo ""
  exit 0
fi

if [ "$1" = "backend" ]; then
  shift
  exec python backend/backend.py "$@"
elif [ "$1" = "ui" ]; then
  shift
  exec streamlit run frontend/frontend.py "$@"
else
  # Fallback for backward compatibility or direct commands
  # If the first arg is not 'backend' or 'ui', assume it's a command for the default entrypoint
  # Previously, default was UI. Now we made specific 'ui' command.
  # But assuming running 'streamlit' if args are passed might be wrong if they passed flags for backend without 'backend' keyword.
  # However, let's stick to the structure:
  # If they pass arguments that look like they want to run UI?
  # The previous script defaulted to UI.

  # For safety, let's keep the old default behavior if it's not 'backend',
  # BUT since we are handling empty args above, this else block handles non-empty args.

  # If user types `docker run img some-flag`, previously it ran `streamlit run frontend.py some-flag`.
  # Unlikely useful for streamlit unless they are passing streamlit args.

  # If user previously ran `docker run img` (no args), it ran UI. Now it prints help.

  exec streamlit run frontend/frontend.py "$@"
fi