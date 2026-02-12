#!/bin/bash

# If no arguments are provided, print usage instructions
if [ $# -eq 0 ]; then
  echo ""
  echo "Usage: docker run [DOCKER_OPTIONS] <docker-image> [ --ui | ARGS ]"
  echo ""
  echo "This container requires volume mounts for input, output, and logs."
  echo ""
  echo "Volume Mounts:"
  echo "  -v <local_input>:/app/input       Required. Must contain 'jobs' and 'thresholds' subfolders."
  echo "  -v <local_output>:/app/output     Required. Destination for generated reports."
  echo "  -v <local_logs>:/app/logs         Recommended. Access logs outside the container."
  echo ""
  echo "  --ui              Start the Web UI"
  echo "  [ARGS]            Start the Backend (Headless) without UI (see below for options)"
  echo ""
  echo "[ARGS]:"
  echo "  -j, --job-file <name>               Job file name (default: DefaultJob)"
  echo "  -t, --thresholds-file <name>        Thresholds file name (default: DefaultThresholds)"
  echo "  -d, --debug                         Enable debug logging"
  echo "  -c, --concurrent-connections <n>    Number of concurrent connections"
  echo ""
  echo "Examples:"
  echo "1. Run the Web UI:"
  echo "   docker run --rm -p 8501:8501 \\"
  echo "     -v \$(pwd)/input:/app/input \\"
  echo "     -v \$(pwd)/output:/app/output \\"
  echo "     -v \$(pwd)/logs:/app/logs \\"
  echo "     <docker-image> --ui"
  echo ""
  echo "2. Run the Backend (Headless):"
  echo "   docker run --rm \\"
  echo "     -v \$(pwd)/input:/app/input \\"
  echo "     -v \$(pwd)/output:/app/output \\"
  echo "     -v \$(pwd)/logs:/app/logs \\"
  echo "     <docker-image> -j <job-file>"
  echo ""
  echo "for more help run:"
  echo "   docker run <docker-image> --help"
  echo ""
  exit 0
fi

# Fix ModuleNotFoundError: Add current dir (/app) to path
# This allows 'import backend' to work from bin/bundle_main.py
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Delegate ALL argument handling to bundle_main.py
# This script handles --ui, --run, --help, and backend [options]
exec python bin/bundle_main.py "$@"
