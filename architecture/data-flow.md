# PAS System Data Flow Architecture

## Executive Summary

This document describes the end-to-end data flow patterns within the PAS system, covering user authentication, session establishment, privileged access, and audit data collection. Understanding these flows is critical for security analysis, performance optimization, and compliance validation.

## High-Level Data Flow Overview

```mermaid
graph TB
    subgraph "User Domain"
        User[👤 Healthcare User]
        UCM[🖥️ UCM Client]
        App[📱 Target Application<br/>RDP, SSH, etc.]
    end
    
    subgraph "PAS Management Domain"
        WebUI[🌐 Web Interface]
        AuthSvc[🔐 Auth Service]
        SessionMgr[📋 Session Manager]
        AuditCoord[📊 Audit Coordinator]
    end
    
    subgraph "Audit Domain"
        AuditProc[📊 Audit Process]
        AuditStore[(💾 Audit Storage)]
    end
    
    subgraph "Service Domain"
        Gatekeeper[🚪 Gatekeeper]
        TargetSvc[⚙️ Target Service]
    end
    
    User -->|1. Access Request| WebUI
    WebUI -->|2. Authentication| AuthSvc
    AuthSvc -->|3. Session Creation| SessionMgr
    SessionMgr -->|4. Audit Setup| AuditCoord
    AuditCoord -.->|5. IPC| AuditProc
    UCM -.->|6. SSH Tunnel| AuditProc
    AuditProc -.->|7. Proxy Control| Gatekeeper
    Gatekeeper -->|8. Service Access| TargetSvc
    App -.->|9. Application Data| UCM
    AuditProc -->|10. Audit Data| AuditStore
    
    classDef user fill:#E3F2FD,stroke:#1976D2
    classDef management fill:#FFF3E0,stroke:#F57C00
    classDef audit fill:#F3E5F5,stroke:#7B1FA2
    classDef service fill:#E8F5E8,stroke:#388E3C
    
    class User,UCM,App user
    class WebUI,AuthSvc,SessionMgr,AuditCoord management
    class AuditProc,AuditStore audit
    class Gatekeeper,TargetSvc service
```

## Detailed Data Flow Patterns

### 1. User Authentication Flow

#### Web-Based Authentication
```mermaid
sequenceDiagram
    participant U as User
    participant W as Web UI
    participant A as Auth Service
    participant L as LDAP/AD
    participant S as Session Manager
    
    U->>W: Login request (username/password)
    W->>A: Authenticate user
    A->>L: LDAP/AD lookup
    L->>A: User attributes + groups
    A->>A: Validate credentials
    A->>S: Create session token
    S->>W: Session token + permissions
    W->>U: Authentication success + token
    
    Note over U,S: Session established with RBAC permissions
```

#### Multi-Factor Authentication Flow
```mermaid
sequenceDiagram
    participant U as User
    participant W as Web UI
    participant A as Auth Service
    participant M as MFA Provider
    participant S as Session Manager
    
    U->>W: Primary authentication
    W->>A: Validate primary credentials
    A->>M: Request MFA challenge
    M->>U: MFA challenge (SMS, app, etc.)
    U->>M: MFA response
    M->>A: MFA validation result
    A->>S: Create authenticated session
    S->>W: Full session token
    W->>U: Complete authentication
```

### 2. Session Establishment Flow

#### End-to-End Session Setup
```mermaid
sequenceDiagram
    participant U as User
    participant UCM as UCM Client
    participant PS as PAS Server
    participant AC as Audit Coordinator
    participant AP as Audit Process
    participant GK as Gatekeeper
    participant TS as Target Service
    
    U->>UCM: Request access to service
    UCM->>PS: RSS INIT + session request
    PS->>AC: Initialize audit session
    AC->>AP: Start audit session (IPC)
    AP->>AP: Setup protocol handlers
    PS->>UCM: Session approved + SSH keys
    UCM->>AP: Establish SSH tunnel
    AP->>GK: Coordinate proxy session
    GK->>TS: Establish service connection
    AP->>PS: Session ready notification
    PS->>UCM: Session established
    UCM->>U: Ready for application launch
    
    Note over U,TS: Secure audited session active
```

### 3. Application Data Flow

#### SSH Session Data Flow
```mermaid
graph LR
    subgraph "SSH Session Flow"
        A[SSH Client] -->|Encrypted SSH| B[UCM Port Forward]
        B -->|SSH Tunnel| C[Audit Process]
        C -->|SSH Proxy| D[Gatekeeper]
        D -->|SSH Connection| E[SSH Server]
    end
    
    subgraph "Audit Capture"
        C -->|Session Recording| F[SSH Audit Handler]
        F -->|Encrypted Logs| G[Audit Storage]
    end
    
    classDef dataflow fill:#E3F2FD,stroke:#1976D2
    classDef audit fill:#F3E5F5,stroke:#7B1FA2
    
    class A,B,C,D,E dataflow
    class F,G audit
```

#### RDP Session Data Flow
```mermaid
graph LR
    subgraph "RDP Session Flow"
        A[RDP Client] -->|RDP Protocol| B[UCM Port Forward]
        B -->|SSH Tunnel| C[Audit Process]
        C -->|RDP Proxy| D[Gatekeeper]
        D -->|RDP Connection| E[RDP Server]
    end
    
    subgraph "Audit Capture"
        C -->|Screen Recording| F[RDP Audit Handler]
        F -->|Video + Metadata| G[Audit Storage]
    end
    
    classDef dataflow fill:#E3F2FD,stroke:#1976D2
    classDef audit fill:#F3E5F5,stroke:#7B1FA2
    
    class A,B,C,D,E dataflow
    class F,G audit
```

#### HTTP/HTTPS Session Data Flow
```mermaid
graph LR
    subgraph "HTTP Session Flow"
        A[Web Browser] -->|HTTP/HTTPS| B[UCM Port Forward]
        B -->|SSH Tunnel| C[Audit Process]
        C -->|HTTP Proxy| D[Gatekeeper]
        D -->|HTTP/HTTPS| E[Web Server]
    end
    
    subgraph "Audit Capture"
        C -->|Request/Response| F[HTTP Audit Handler]
        F -->|HTTP Logs| G[Audit Storage]
    end
    
    classDef dataflow fill:#E3F2FD,stroke:#1976D2
    classDef audit fill:#F3E5F5,stroke:#7B1FA2
    
    class A,B,C,D,E dataflow
    class F,G audit
```

### 4. Audit Data Flow

#### Real-Time Audit Processing
```mermaid
sequenceDiagram
    participant AP as Audit Process
    participant SSH as SSH Handler
    participant RDP as RDP Handler
    participant HTTP as HTTP Handler
    participant AS as Audit Storage
    participant AR as Audit Reporting
    
    Note over AP: Session traffic flows through audit process
    
    AP->>SSH: SSH packet received
    SSH->>SSH: Parse and analyze
    SSH->>AS: Store session data
    
    AP->>RDP: RDP frame received
    RDP->>RDP: Screen capture + analysis
    RDP->>AS: Store video frame
    
    AP->>HTTP: HTTP request received
    HTTP->>HTTP: Parse request/response
    HTTP->>AS: Store HTTP transaction
    
    AS->>AR: Periodic audit report generation
    AR->>AR: Compliance report creation
```

#### Audit Data Storage Pattern
```mermaid
graph TB
    subgraph "Audit Data Pipeline"
        A[Live Session Data] -->|Real-time| B[Protocol Handlers]
        B -->|Parsed Data| C[Audit Processor]
        C -->|Encrypted| D[Primary Storage]
        D -->|Backup| E[Secondary Storage]
        D -->|Reporting| F[Compliance Reports]
    end
    
    subgraph "Data Retention"
        D -->|7 Years| G[Long-term Archive]
        E -->|Disaster Recovery| H[Offsite Backup]
    end
    
    classDef processing fill:#E3F2FD,stroke:#1976D2
    classDef storage fill:#F3E5F5,stroke:#7B1FA2
    classDef retention fill:#FFF3E0,stroke:#F57C00
    
    class A,B,C processing
    class D,E,F storage
    class G,H retention
```

## Data Security and Encryption

### Encryption in Transit
```mermaid
graph TB
    subgraph "Encryption Layers"
        A[User Application] -->|TLS 1.2+| B[UCM Client]
        B -->|SSH Tunnel| C[Audit Process]
        C -->|mTLS| D[Gatekeeper]
        D -->|Protocol Native| E[Target Service]
    end
    
    subgraph "Key Management"
        F[Key Management Service] -.->|Session Keys| B
        F -.->|Component Keys| C
        F -.->|Service Keys| D
    end
    
    classDef encryption fill:#E8F5E8,stroke:#388E3C
    classDef keymanagement fill:#F3E5F5,stroke:#7B1FA2
    
    class A,B,C,D,E encryption
    class F keymanagement
```

### Encryption at Rest
```yaml
# Data encryption configuration
encryption_at_rest:
  audit_logs:
    algorithm: "AES-256-GCM"
    key_source: "Customer HSM"
    rotation_frequency: "Annual"
    
  database:
    method: "Transparent Data Encryption (TDE)"
    key_management: "Customer-controlled"
    backup_encryption: "Same as primary"
    
  configuration:
    sensitive_values: "AES-256 encrypted"
    key_derivation: "PBKDF2 with customer passphrase"
    access_control: "Role-based decryption"
```

## Performance and Scalability Patterns

### Data Flow Optimization
```mermaid
graph TB
    subgraph "Performance Optimization"
        A[Connection Pooling] -->|Reuse| B[Database Connections]
        C[Session Caching] -->|Memory| D[Active Sessions]
        E[Audit Buffering] -->|Batch| F[Audit Writes]
        G[Protocol Optimization] -->|Compression| H[Network Traffic]
    end
    
    subgraph "Scalability Patterns"
        I[Load Balancing] -->|Distribute| J[Multiple PAS Servers]
        K[Audit Partitioning] -->|Shard| L[Multiple Audit Processes]
        M[Database Clustering] -->|Replicate| N[Read Replicas]
    end
    
    classDef optimization fill:#E3F2FD,stroke:#1976D2
    classDef scalability fill:#E8F5E8,stroke:#388E3C
    
    class A,C,E,G optimization
    class I,K,M scalability
```

### Throughput Characteristics
```yaml
# Performance metrics and limits
performance_characteristics:
  session_establishment:
    target_latency: "< 500ms"
    current_latency: "< 2000ms"
    throughput: "100 sessions/minute"
    
  audit_processing:
    ssh_sessions: "500 concurrent"
    rdp_sessions: "100 concurrent"
    http_sessions: "1000 concurrent"
    storage_rate: "1GB/hour typical"
    
  database_operations:
    read_queries: "1000 QPS"
    write_queries: "100 QPS"
    connection_pool: "50 connections"
    
  network_utilization:
    audit_overhead: "< 5% of session traffic"
    compression_ratio: "3:1 for text protocols"
    bandwidth_efficiency: "95% effective utilization"
```

## HIPAA Compliance Data Handling

### PHI Data Flow Controls
```mermaid
graph TB
    subgraph "PHI Protection Boundaries"
        A[User Input] -->|Sanitized| B[PAS Processing]
        B -->|No PHI| C[Audit Logs]
        B -->|No PHI| D[Monitoring Data]
        B -->|Encrypted| E[Session Content]
    end
    
    subgraph "Compliance Controls"
        F[Data Minimization] -->|Limit Collection| A
        G[Access Controls] -->|Restrict Access| C
        H[Encryption] -->|Protect Data| E
        I[Audit Trail] -->|Track Access| G
    end
    
    classDef protection fill:#F3E5F5,stroke:#7B1FA2
    classDef compliance fill:#FFF3E0,stroke:#F57C00
    
    class A,B,C,D,E protection
    class F,G,H,I compliance
```

### Data Retention and Disposal
```yaml
# HIPAA-compliant data lifecycle
data_lifecycle:
  collection:
    principle: "Minimum necessary"
    authorization: "Role-based access"
    logging: "All access logged"
    
  storage:
    encryption: "AES-256 at rest"
    access_controls: "Multi-factor authentication"
    backup: "Encrypted offsite backup"
    
  retention:
    audit_logs: "7 years minimum"
    session_recordings: "7 years minimum"
    configuration: "Lifecycle of system"
    monitoring_data: "1 year maximum"
    
  disposal:
    method: "Cryptographic erasure"
    verification: "Certificate of destruction"
    documentation: "Disposal audit trail"
```

## Monitoring and Observability Data Flow

### Metrics Collection Flow
```mermaid
sequenceDiagram
    participant C as Components
    participant P as Prometheus
    participant G as Grafana
    participant A as AlertManager
    participant O as Operations Team
    
    C->>P: Metrics scraping (30s interval)
    P->>P: Store time-series data
    G->>P: Query metrics for dashboards
    P->>A: Evaluate alert rules
    A->>O: Send alerts (email/SMS)
    O->>G: View dashboards for analysis
    
    Note over C,O: All metrics are HIPAA-compliant (no PHI)
```

### Telemetry Data Flow
```yaml
# Anonymized telemetry configuration
telemetry:
  local_collection:
    metrics: "System and application metrics"
    retention: "30 days local storage"
    access: "Customer-controlled only"
    
  vendor_telemetry:
    enabled: false  # Customer controlled
    data_type: "Aggregated, anonymized only"
    frequency: "Weekly if enabled"
    content:
      - deployment_health_score
      - feature_usage_statistics
      - performance_percentiles
      - error_category_counts
    
  privacy_protection:
    no_phi: "Zero PHI in any telemetry"
    anonymization: "Site IDs hashed"
    aggregation: "Individual data points removed"
    customer_control: "Complete opt-out capability"
```

This data flow architecture ensures secure, compliant, and efficient handling of all data within the PAS system while maintaining the performance and reliability required for healthcare environments.
