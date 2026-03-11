# circuit-a2a-agent-sample
## 🌟 Purpose

This version demonstrates a **minimal  setup** using Anthropic's [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol) via the official **`mcp` SDK**.

It includes:
- A single **Weather server** that returns the weather alerts and forecasts
- A single **MCP client** that sends messages and receives responses

---

## 🚀 Features

- ✅ Minimal working server.
- ✅ Fully async MCP client using the SDK

---

## 📦 Project Structure

```bash
circuit-mcp-server-sample/
→ app/
    weather.py                 # Weather tools logic
    fastmcp_instantiator.py    # Initialize MCP server and connect to tools

→ client/
    client.py               # MCP SDK client that discovers tools and streams messages to the tool

main.py                    # Starts the MCP server (entry point)
README.md                  # You're reading it!
requirements.txt           # Python dependencies
````

---

## 🛠️ Prerequisites

* Python 3.12+
* `pip install -r requirements.txt` to install dependencies

---

## ⚙️ Setup & Installation

```bash
git clone https://github.com/cisco-dd-enterprise-aiml-eng/circuit-mcp-server-sample
cd circuit-mcp-server-sample
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
## 🧪 Running the Project

### 🔧 Environment Variables
Set the following environment variables in `properties.py` file (you will receive these when registering your MCP server in the registry):
```bash
JWKS_URI = os.environ.get('JWKS_URI', "<your-jwks-value-here>")
AUDIENCE = os.environ.get('AUDIENCE', "<your-aud-here>")
ISSUER = os.environ.get('ISSUER', "<your-iss-here>")
CIRCUIT_CLIENT_ID = os.environ.get('CIRCUIT_CLIENT_ID', "<your-clientid-here>")
```

If you want to run the weather app as is, also update these values with your llm details.
```bash
CIRCUIT_LLM_API_APP_KEY = os.environ.get('CIRCUIT_LLM_API_APP_KEY', "<your-llm-appkey-here>")
CIRCUIT_LLM_API_CLIENT_ID = os.environ.get('CIRCUIT_LLM_API_CLIENT_ID', "<your-llm-clientid-here>")
CIRCUIT_LLM_API_CLIENT_SECRET = os.environ.get('CIRCUIT_LLM_API_CLIENT_SECRET', "<your-llm-secret-here>")
CIRCUIT_LLM_API_MODEL_NAME = os.environ.get('CIRCUIT_LLM_API_MODEL_NAME', "<your-llm-model-here>") 
CIRCUIT_LLM_API_ENDPOINT = os.environ.get('CIRCUIT_LLM_API_ENDPOINT', "<your-llm-endpoint-here>")
CIRCUIT_LLM_API_VERSION = os.environ.get('CIRCUIT_LLM_API_VERSION', "<your-llm-version-here>")
```

### 🟢 Step 1: Start the Weather MCP Server

```bash
python3 app --host 0.0.0.0 --port 8006
```

This launches the agent server at `http://localhost:8006`.

### 🟡 Step 2: Run the MCP Client

```bash
cd circuit-mcp-server-sample
source .venv/bin/activate
python3 client/client.py
```

This will connect to the MCP server and send a message. You should see the response in the terminal. You can update the example values to get weather in your location.

### 🔴 Step 3: Stop the MCP Server
Press `Ctrl+C` in the terminal where the agent server is running to stop it.
---

## 📜 Notes
- This is a minimal example to demonstrate the MCP protocol using the `mcp` SDK.
- After registering an MCP server on CIRCUIT UI, enable the OAuth code flow i.e un-comment the lines from 140 to 159 in `oauth2_middleware.py`.
