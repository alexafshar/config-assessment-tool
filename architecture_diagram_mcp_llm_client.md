# Architecture: MCP LLM Client Integration Flow

This diagram illustrates the internal architecture and flow of the `mcp_llm_client.py` application, highlighting how it orchestrates interactions between the User, the Local MCP Server, and the remote CIRCUIT LLM service.

```mermaid
graph TD
    %% Nodes
    User([User])
    
    subgraph LocalMachine [Local Machine]
        style LocalMachine fill:#f9f9f9,stroke:#333,stroke-width:2px
        
        subgraph ClientApp ["MCP LLM Client (mcp_llm_client.py)"]
            style ClientApp fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
            Orchestrator[Main Chat Loop]
            Auth[Auth Handler]
            FileProc["File Processor / Pandas"]
        end
        
        subgraph MCPServer [MCP Server Process]
            style MCPServer fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
            ServerScript[mcp_server.py]
        end
        
        FileSystem[(Local File System)]
        style FileSystem fill:#fff3e0,stroke:#ef6c00
    end
    
    subgraph RemoteServices ["Remote Services / Cloud"]
        style RemoteServices fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
        IDP["Identity Provider (OAuth)"]
        CIRCUIT[CIRCUIT LLM API]
    end

    %% Edge connections
    
    %% Startup & Auth
    Orchestrator -- "1. Start Subprocess stdio" --> ServerScript
    Auth -- "2. Get Access Token" --> IDP
    Auth -.->|Token| Orchestrator
    
    %% Chat Flow
    User -- "3. Chat Input" --> Orchestrator
    Orchestrator -- "4. Send Prompt + Tool Definitions" --> CIRCUIT
    
    %% Tool Execution
    CIRCUIT -.->|"5. JSON: Tool Call Request"| Orchestrator
    Orchestrator -- "6. Execute Tool" --> ServerScript
    ServerScript -- "7. Return Result (Embedded File/Text)" --> Orchestrator
    
    %% File Handling (The specific part of this client)
    Orchestrator -- "8. If File Resource Detected" --> FileProc
    FileProc -- "9. Save .xlsx" --> FileSystem
    FileProc -- "10. Read & Summarize (df.head)" --> Orchestrator
    
    %% Final Response
    Orchestrator -- "11. Feed Tool Output/Summary" --> CIRCUIT
    CIRCUIT -- "12. Final Natural Language Response" --> Orchestrator
    Orchestrator -- "13. Display Response" --> User
```

