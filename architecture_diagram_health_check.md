# Architecture: Health Check Job Execution Flow

This diagram illustrates the process of running a health check job via CIRCUIT and the MCP Server, focusing on the data flow and report generation.

```mermaid
graph TD
    %% Actors and Systems
    User([User])
    style User fill:#fff,stroke:#333,stroke-width:2px
    
    subgraph UI_Layer [CIRCUIT Interface]
        style UI_Layer fill:#eef,stroke:#333
        Prompt[Prompt: 'Run Health Check']
        Download[Download Attachments]
    end

    subgraph Execution_Layer [MCP Server Context]
        style Execution_Layer fill:#efe,stroke:#333
        Server[MCP Server]
        Logic[Health Check Logic]
        Processing[Data Extrapolation & Tabulation]
    end
    
    subgraph External_Systems
        style External_Systems fill:#fee,stroke:#333,stroke-dasharray: 5 5
        AppD[AppDynamics Controller API]
    end

    subgraph Output_Artifacts
        Reports[Excel & PowerPoint Reports]
    end

    %% Flow Steps
    User -->|1. Request Health Check| Prompt
    Prompt -->|2. Tool Execution Request| Server
    Server -->|Invokes| Logic
    Logic -->|3. Collect Meta-Metrics| AppD
    AppD -->|Return Metrics| Logic
    Logic -->|4. Process Data Best Practices| Processing
    Processing -->|Generate Customer Facing Reports| Reports
    Reports -->|5. Return as Attachments| Prompt
    Prompt -->|6. Available for Download| Download
    Download -->|User Downloads Files| User
```

