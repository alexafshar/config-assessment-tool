# High Level Architecture: MCP Client & Server Integration

This diagram illustrates how the `mcp_llm_client.py` acts as a bridge between the **User**, the internal **CIRCUIT AI**, and your local **Assessment Engine**.

```mermaid
graph TD
    %% Actors and External Systems
    User([User])
    style User fill:#fff,stroke:#333,stroke-width:2px
    
    subgraph External_Cloud [External Services]
        style External_Cloud fill:#eef,stroke:#333,stroke-dasharray: 5 5
        IdP[Identity Provider\nOAuth2]
        CIRCUIT[CIRCUIT LLM\nOpenAI Interface]
        AppD[AppDynamics Controller]
    end

    subgraph Local_Machine [Local Environment]
        style Local_Machine fill:#efe,stroke:#333
        
        subgraph MCP_Client_Process [Python: mcp_llm_client.py]
            ClientLogic[Client Logic]
            Pandas[Pandas Analysis]
        end
        
        subgraph MCP_Server_Process [Python: mcp_server.py]
            FastMCP[FastMCP Server]
        end
        
        subgraph CAT_Tool [Config Assessment Tool]
            Engine[Backend Engine]
        end
        
        FileSystem[(Local File System)]
    end

    %% Auth Flow
    ClientLogic -- 1. Authenticate --> IdP
    IdP -- Bearer Token --> ClientLogic

    %% Chat Flow
    User <-->| CLI Chat | ClientLogic
    ClientLogic <-->| 2. Send Prompt / Receive Tool Calls | CIRCUIT

    %% MCP Execution Flow
    ClientLogic <-->| 3. Stdio / JSON-RPC | FastMCP
    FastMCP -->| 4. Run Tool | Engine
    
    %% Engine Execution
    Engine -- Reads Job/Thresholds --> FileSystem
    Engine <-->| 5. API Extract Metrics | AppD
    Engine -- Writes Reports --> FileSystem
    
    %% Result Handling
    FastMCP -- Reads Report --> FileSystem
    FastMCP -- 6. Return EmbeddedResource Base64 --> ClientLogic
    
    %% Post Processing
    ClientLogic -- Decodes & Saves --> FileSystem
    FileSystem -- Reads Excel --> Pandas
    Pandas -- 7. Generates Summary --> ClientLogic
    ClientLogic -- 8. Sends Analysis Context --> CIRCUIT
    CIRCUIT -- 9. Final Answer --> ClientLogic
```

## Key Components

1.  **MCP Client (`mcp_llm_client.py`)**:
    *   The "Brain" of the operation locally.
    *   Authenticates with your internal IdP.
    *   Maintains the conversation history with CIRCUIT.
    *   Interprets tool calls from CIRCUIT and executes them on the local server via Stdio.
    *   **Crucial Step**: Intercepts the binary Excel response, saves it to disk, uses `pandas` to read it, and feeds a text summary back to the LLM so it can "see" the data.

2.  **MCP Server (`mcp_server.py`)**:
    *   The "Hands" of the operation.
    *   Run as a subprocess by the client.
    *   Exposes `run_assessment` and `list_jobs` as callable tools.
    *   Wraps the legacy `Engine` code.
    *   Encodes the resulting Excel report into a Base64 `EmbeddedResource` compliant with MCP.

3.  **CIRCUIT / LLM**:
    *   The "Intelligence".
    *   Doesn't run code itself; it just predicts which tool to call and interprets the text summaries provided by the client.

4.  **Local File System**:
    *   Acts as the persistent storage for the inputs (Jobs) and outputs (Reports), bridging the Engine's file-based operations with the Client's analysis logic.

