#!/bin/bash

OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

if [[ "$OS" == "darwin" ]]; then
  OS_TAG="macos"
elif [[ "$OS" == "linux" ]]; then
  OS_TAG="linux"
else
  echo "Unsupported OS: $OS"
  exit 1
fi

if [[ "$ARCH" == "arm64" || "$ARCH" == "aarch64" ]]; then
  ARCH_TAG="arm"
elif [[ "$ARCH" == "x86_64" ]]; then
  ARCH_TAG="amd64"
else
  echo "Unsupported architecture: $ARCH"
  exit 1
fi

# Detect Repo Owner from Git
if command -v git &> /dev/null; then
  GIT_ORIGIN=$(git config --get remote.origin.url)
  # Extract username from git@github.com:user/repo.git or https://github.com/user/repo.git
  if [[ "$GIT_ORIGIN" =~ github.com[:/]([^/]+)/ ]]; then
    REPO_OWNER="${BASH_REMATCH[1]}"
  fi
fi

# Default to appdynamics if detection failed or empty
REPO_OWNER="${REPO_OWNER:-appdynamics}"

# Convert to lowercase to be safe for docker images
REPO_OWNER=$(echo "$REPO_OWNER" | tr '[:upper:]' '[:lower:]')

REPO="ghcr.io/${REPO_OWNER}/config-assessment-tool-${OS_TAG}-${ARCH_TAG}"

if [[ -f VERSION ]]; then
  VERSION=$(cat VERSION)
else
  echo "VERSION file not found."
  exit 1
fi

check_available_images() {
  echo "  Checking available Docker images..."
  local found_images=false
  local repo_url="https://github.com/${REPO_OWNER}?tab=packages&repo_name=config-assessment-tool"

  # Check if curl is available
  if ! command -v curl &> /dev/null; then
    echo "    (curl not found, cannot automatically verify images)"
    echo "    Please check the repository manually for available packages at:"
    echo "    $repo_url"
    return
  fi

  # Query GitHub Packages page for this user/org
  local html_content
  if ! html_content=$(curl -s "$repo_url"); then
     echo "    (Failed to connect to GitHub to verify images)"
     echo "    Please check the repository manually for available packages at:"
     echo "    $repo_url"
     return
  fi

  echo "  Available Images (verified on GitHub for user '$REPO_OWNER'):"

  # Check Linux AMD64
  if echo "$html_content" | grep -q "config-assessment-tool-linux-amd64"; then
    echo "    ghcr.io/${REPO_OWNER}/config-assessment-tool-linux-amd64:$VERSION"
    found_images=true
  fi

  # Check Linux ARM
  if echo "$html_content" | grep -q "config-assessment-tool-linux-arm"; then
    echo "    ghcr.io/${REPO_OWNER}/config-assessment-tool-linux-arm:$VERSION"
    found_images=true
  fi

  # Check Windows
  if echo "$html_content" | grep -q "config-assessment-tool-windows-amd64"; then
    echo "    ghcr.io/${REPO_OWNER}/config-assessment-tool-windows-amd64:$VERSION"
    found_images=true
  fi

  if [ "$found_images" = false ]; then
    echo "    (No verified images found locally for version $VERSION)"
    # Fallback to listing expected ones if verify fails or none found?
    # Or just print what we expect.
    echo "    ghcr.io/${REPO_OWNER}/config-assessment-tool-linux-amd64:$VERSION"
    echo "    ghcr.io/${REPO_OWNER}/config-assessment-tool-windows-amd64:$VERSION"
  fi
  echo "  "
}

IMAGE="$REPO:$VERSION"
PORT="8501"
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/config-assessment-tool.log"
MOUNTS="-v $(pwd)/input/jobs:/app/input/jobs -v $(pwd)/input/thresholds:/app/input/thresholds -v $(pwd)/output/archive:/app/output/archive -v $(pwd)/$LOG_DIR:/app/$LOG_DIR"
CONTAINER_NAME="cat-tool-container"

mkdir -p "$LOG_DIR"

start_filehandler() {
  if [ ! -f "frontend/FileHandler.py" ]; then
    echo "Error: frontend/FileHandler.py not found."
    exit 1
  fi
  echo "Starting FileHandler service on host..."
  pkill -f "python.*FileHandler.py" 2>/dev/null
  pipenv run python frontend/FileHandler.py >> "$LOG_FILE" 2>&1 &
  echo "FileHandler.py started with PID $!"
  sleep 2
}

case "$1" in
  --start)
    if [[ "$2" == "docker" ]]; then
      export FILE_HANDLER_HOST=host.docker.internal
      start_filehandler
      docker stop $CONTAINER_NAME >/dev/null 2>&1
      docker rm $CONTAINER_NAME >/dev/null 2>&1

      if [[ $# -eq 2 ]]; then
        echo "Starting container in UI mode..."
        CONTAINER_ID=$(docker run --add-host=host.docker.internal:host-gateway -d --name $CONTAINER_NAME -e FILE_HANDLER_HOST=$FILE_HANDLER_HOST -p $PORT:$PORT $MOUNTS $IMAGE streamlit run frontend/frontend.py --server.headless=true)
        if [ $? -eq 0 ]; then
          echo "Container started successfully with ID: $CONTAINER_ID"
          echo "UI available at http://localhost:$PORT"
          docker logs -f $CONTAINER_ID
        else
          echo "Failed to start container."
          exit 1
        fi
      else
        echo "Starting container in backend mode with args: ${@:3}"
        docker run --add-host=host.docker.internal:host-gateway --rm --name $CONTAINER_NAME -e FILE_HANDLER_HOST=$FILE_HANDLER_HOST -p $PORT:$PORT $MOUNTS $IMAGE backend "${@:3}"
        EXIT_CODE=$?
        if [ $EXIT_CODE -ne 0 ]; then
          echo "Container failed with exit code: $EXIT_CODE"
          exit $EXIT_CODE
        fi
      fi
    else
      export PYTHONPATH="$(pwd):$(pwd)/backend"

      if ! command -v pipenv &> /dev/null; then
        echo "pipenv not found. Attempting to install via pip..."
        pip install pipenv
      fi

      # Ensure dependencies are installed before running
      echo "Checking/Installing dependencies..."
      pipenv install

      if [[ $# -eq 1 ]]; then
        echo "PYTHONPATH is: $PYTHONPATH"
        echo "Running application in UI mode from source..."
        echo "UI available at http://localhost:$PORT"
        pipenv run streamlit run frontend/frontend.py
      else
        echo "PYTHONPATH is: $PYTHONPATH"
        echo "Running application in backend mode from source with args: ${@:2}"
        pipenv run python backend/backend.py "${@:2}"
      fi
    fi
    ;;

  --plugin)
    if [[ "$2" == "list" ]]; then
       export PYTHONPATH="$(pwd):$(pwd)/backend"
       pipenv run python backend/plugin_manager.py list
       exit 0
    elif [[ "$2" == "docs" ]]; then
       PLUGIN_NAME="$3"
       if [[ -z "$PLUGIN_NAME" ]]; then
         echo "Error: Plugin name required."
         exit 1
       fi
       export PYTHONPATH="$(pwd):$(pwd)/backend"
       pipenv run python backend/plugin_manager.py docs "$PLUGIN_NAME"
       exit 0
    elif [[ "$2" == "start" ]]; then
       PLUGIN_NAME="$3"
       if [[ -z "$PLUGIN_NAME" ]]; then
         echo "Error: Plugin name required."
         exit 1
       fi
       export PYTHONPATH="$(pwd):$(pwd)/backend"
       # Pass remaining args to the plugin manager
       pipenv run python backend/plugin_manager.py start "$PLUGIN_NAME" "${@:4}"
       exit 0
    fi
    ;;

  shutdown)
    echo "Shutting down container: $CONTAINER_NAME"
    docker stop $CONTAINER_NAME >/dev/null 2>&1
    docker rm $CONTAINER_NAME >/dev/null 2>&1
    echo "Container stopped and removed."
    echo "Stopping FileHandler process..."
    pkill -f "python.*FileHandler.py" 2>/dev/null
    echo "FileHandler stopped."
    echo "Stopping backend process..."
    pkill -f "python.*backend.py" 2>/dev/null
    echo "Backend process stopped."
    echo "Stopping Streamlit process..."
    pkill -f "streamlit run frontend/frontend.py" 2>/dev/null
    echo "Streamlit stopped."
    ;;
  *)
    echo "Usage:"
    echo "  cat --start                # Starts CAT UI. Requires Python 3.12 and pipenv installed.  UI accessible at http://localhost:8501"
    echo "  cat --start [args]         # Starts CAT headless mode from source with [args].  Requires Python 3.12 & pipenv installed."
    echo "  cat --start docker         # Starts CAT UI using Docker. requires Docker. UI accessible at http://localhost:8501"
    echo "  cat --start docker [args]  # Starts CAT headless mode using Docker with [args]. Requires Docker installed."
    echo "  cat --plugin <list|start|docs> [name]    # list plugins | start plugin | show docs for plugin"
    echo "  cat shutdown               # Stop and remove the running container and FileHandler"
    echo ""
    echo "Arguments [args]:"
    echo "  -j, --job-file <name>             Job file name (default: DefaultJob)"
    echo "  -t, --thresholds-file <name>      Thresholds file name (default: DefaultThresholds)"
    echo "  -d, --debug                       Enable debug logging"
    echo "  -c, --concurrent-connections <n>  Number of concurrent connections"
    echo "  "
    echo "Direct Docker Usage:"
    echo "  You can also run the tool directly using Docker without this script."
    echo "  Ensure you mount the input, output, and logs directories."
    echo "  "
    echo "  # UI Mode:"
    echo "  docker run -p 8501:8501 \\"
    echo "    -v \$(pwd)/input:/app/input \\"
    echo "    -v \$(pwd)/output:/app/output \\"
    echo "    -v \$(pwd)/logs:/app/logs \\"
    echo "    $REPO:$VERSION"
    echo "  "
    echo "  # Headless Mode:"
    echo "  docker run --rm \\"
    echo "    -v \$(pwd)/input:/app/input \\"
    echo "    -v \$(pwd)/output:/app/output \\"
    echo "    -v \$(pwd)/logs:/app/logs \\"
    echo "    $REPO:$VERSION backend -j <job-file>"
    echo "  "

    check_available_images
    exit 1
    ;;
esac

