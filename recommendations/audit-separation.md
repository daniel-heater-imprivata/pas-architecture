# Audit Architecture: Split into Separate Process

## Executive Summary

**Recommendation**: Split audit into a separate process with clean IPC mechanisms instead of merging with Parent.

**Priority**: HIGHEST - Critical Infrastructure Investment
**Effort**: 6-8 weeks
**Risk**: Medium (IPC complexity, credential injection preservation, performance impact)

## Why This is Priority #1: Developer Productivity Crisis

**The Real Problem**: Audit coupling is killing development velocity. Every audit change requires:
- Full Parent rebuild (3-5 minutes)
- Complete Parent restart with database, Spring context, web stack
- Integration testing with entire monolith
- Coordinated deployments across audit and business logic

**The Hidden Cost**: Audit changes are frequent (compliance updates, new event types, formatting fixes) but each change has a 5-minute feedback loop. This compounds into hours of lost productivity per week.

**The Strategic Value**: This is infrastructure work that makes everything else possible. Every future audit change becomes a 30-second test cycle instead of 5-minute rebuild cycle.

## Problem Statement: Development Velocity Killer

Current audit architecture creates a development bottleneck:

### **Immediate Pain Points**
- **Slow feedback loop**: 3-5 minute rebuild cycle for any audit change
- **Monolith coupling**: Can't test audit logic without full Parent stack
- **Deployment coupling**: Audit fixes require Parent downtime
- **Testing complexity**: Audit integration tests require database, Spring, web stack

### **Operational Pain Points**
- **Audit failures destabilize Parent**: Single audit bug can crash entire application
- **Debugging complexity**: Audit issues mixed with business logic in same process
- **Resource contention**: Audit processing competes with Parent for CPU/memory
- **HIPAA compliance**: Unclear audit boundaries within monolith

### **System Complexity**
- **Real-time credential injection**: SSH, RDP, VNC require active protocol stream modification
- **Protocol awareness**: Audit understands RDP PDUs, SSH handshakes, VNC DES challenges
- **Semantic event recording**: Records application events, not raw network packets
- **File format dependencies**: RDP2-Converter requires exact binary format preservation
- **Persistent race condition**: Audit linking uses time-based guessing with 5-second windows
- **APORT protocol integration**: LibRSSConnect reports session statistics via RSS protocol

### **Strategic Pain Points**
- **Innovation blocking**: Complex audit changes avoided due to testing overhead
- **Technical debt accumulation**: Quick fixes preferred over proper solutions
- **Team productivity**: Developers avoid audit work due to friction

## Recommended Architecture

### Current State
```
Parent JVM
├── Web Controllers
├── Business Services
└── Audit Spring Beans ← Tightly coupled
    ├── AuditService
    ├── MonitorSSHAudit
    ├── HttpAuditServiceListener
    └── RdpAuditServerListener
```

### Proposed State
```
Parent Process ↔ IPC ↔ Audit Process
                      ├── AuditCoordinator
                      ├── SshAuditService
                      ├── HttpAuditService
                      └── RdpAuditService
```

## Technical Implementation

### IPC Interface Design
```java
// Core audit IPC interface
public interface AuditIPC {
    // Session management with credential injection
    void startAuditSession(String sessionId, AuditConfig config, CredentialInjectionHandler handler);
    void endAuditSession(String sessionId, SessionMetrics metrics);

    // Credential injection requests
    String injectCredential(String sessionId, String token, ProtocolType protocol);
    KeyPair injectKeyPair(String sessionId, String token, ProtocolType protocol);

    // Event recording
    void recordAuditEvent(String sessionId, AuditEvent event);
    void recordProtocolData(String sessionId, ProtocolData data);

    // File management
    void notifyAuditFileCreated(String sessionId, String filePath);
    void linkAuditFile(String sessionId, String accessId);

    // Status and health
    AuditStatus getAuditStatus();
    List<ActiveSession> getActiveSessions();

    // Configuration
    void updateAuditConfig(AuditConfig config);
    AuditConfig getCurrentConfig();
}
```

### IPC Implementation Options

#### Option 1: Unix Domain Sockets (Recommended)
```java
// Lowest latency, most secure for on-premises deployment
public class UnixSocketAuditIPC implements AuditIPC {
    private final String socketPath = "/var/run/pas/audit.sock";
    private final UnixDomainSocketChannel channel;
    
    public void startAuditSession(String sessionId, AuditConfig config) {
        AuditMessage message = new AuditMessage(START_SESSION, sessionId, config);
        sendMessage(message);
    }
    
    private void sendMessage(AuditMessage message) {
        byte[] serialized = messageSerializer.serialize(message);
        ByteBuffer buffer = ByteBuffer.wrap(serialized);
        channel.write(buffer);
    }
}
```

#### Option 2: Named Pipes (Windows Compatibility)
```java
// For Windows environments
public class NamedPipeAuditIPC implements AuditIPC {
    private final String pipeName = "\\\\.\\pipe\\pas-audit";
    private final RandomAccessFile pipe;
    
    // Similar implementation using named pipes
}
```

### Audit Process Architecture
```java
// Main audit process
public class AuditProcess {
    private final AuditCoordinator coordinator;
    private final Map<String, AuditService> protocolServices;
    private final IPCServer ipcServer;
    
    public static void main(String[] args) {
        AuditProcess process = new AuditProcess();
        process.start();
    }
    
    public void start() {
        // Initialize protocol-specific audit services
        protocolServices.put("ssh", new SshAuditService());
        protocolServices.put("http", new HttpAuditService());
        protocolServices.put("rdp", new RdpAuditService());
        
        // Start IPC server
        ipcServer.start();
        
        // Start audit coordinator
        coordinator.start();
    }
}
```

### Error Handling and Resilience
```java
// Handle audit process failures gracefully
public class AuditIPCClient {
    private final CircuitBreaker circuitBreaker;
    private final RetryTemplate retryTemplate;
    
    public void recordAuditEvent(String sessionId, AuditEvent event) {
        circuitBreaker.executeSupplier(() -> {
            return retryTemplate.execute(context -> {
                auditIPC.recordAuditEvent(sessionId, event);
                return null;
            });
        });
    }
    
    // Fallback when audit process is unavailable
    private void handleAuditFailure(String sessionId, AuditEvent event) {
        // Log locally for later replay
        localAuditBuffer.store(sessionId, event);
        
        // Alert operations team
        alertService.sendAlert("Audit process unavailable", AlertLevel.CRITICAL);
        
        // Consider terminating session if audit is mandatory
        if (auditConfig.isAuditMandatory()) {
            sessionManager.terminateSession(sessionId, "Audit unavailable");
        }
    }
}
```

## Benefits: Why This Investment Pays Off

### **Developer Productivity Benefits (Primary Value)**
- **30-second feedback loop**: Test audit changes without Parent rebuild
- **Independent testing**: Unit test audit logic with simple mocks
- **Isolated debugging**: Audit issues don't get mixed with Parent complexity
- **Parallel development**: Audit team can work independently of Parent team
- **Rapid iteration**: Compliance updates and audit fixes deploy in minutes, not hours

### **Technical Benefits (Secondary Value)**
- **Fault isolation**: Audit crashes don't affect Parent uptime
- **Performance isolation**: Audit processing doesn't impact session performance
- **Independent scaling**: Audit can scale based on session volume
- **Clean interfaces**: Forces well-defined audit API design

### **Operational Benefits (Tertiary Value)**
- **Independent deployment**: Audit updates don't require Parent downtime
- **Better monitoring**: Separate health checks and metrics for audit
- **Specialized configuration**: Audit-specific tuning without Parent impact
- **HIPAA compliance**: Cleaner audit boundaries for compliance audits

## Risks and Mitigation

### Performance Impact
**Risk**: IPC adds 50-100μs latency per audit call  
**Mitigation**: 
- Use Unix domain sockets for lowest latency
- Implement message batching for high-volume events
- Async IPC for non-critical audit events

### Complexity Increase
**Risk**: IPC adds operational complexity  
**Mitigation**:
- Comprehensive monitoring of IPC health
- Automatic process restart on failure
- Clear documentation and runbooks

### State Synchronization
**Risk**: Audit process restart loses active session state  
**Mitigation**:
- Persist active session state to disk
- Parent re-sends session state on audit process restart
- Implement session state recovery protocol

## Implementation Plan

### Phase 1: IPC Infrastructure (Weeks 1-2)
1. Implement Unix domain socket IPC layer
2. Create audit message protocol and serialization
3. Build basic audit process skeleton
4. Implement process lifecycle management

### Phase 2: Credential Injection Migration (Weeks 3-4)
1. Extract SSH audit service with MITM credential injection
2. Implement credential injection IPC protocol
3. Migrate RDP audit service with X.224 credential handling
4. Migrate VNC audit service with DES challenge injection
5. Preserve exact file format for RDP2-Converter compatibility

### Phase 3: Integration and Testing (Weeks 5-6)
1. Integrate IPC client into Parent with credential injection callbacks
2. Implement deterministic audit linking to solve 12-year race condition
3. Comprehensive testing with all protocols and credential injection
4. Validate RDP2-Converter compatibility with new audit files
5. Performance testing and optimization for 2000 connection target

### Phase 4: Production Readiness (Weeks 7-8)
1. Monitoring and alerting setup
2. Documentation and runbooks
3. Deployment automation
4. Production validation

## Success Metrics

- **Fault Isolation**: Audit process crashes don't affect Parent uptime
- **Performance**: IPC latency < 100μs for 95th percentile
- **Reliability**: 99.9% audit event capture rate
- **Testing**: Independent audit testing reduces test time by 50%
- **Compliance**: Pass HIPAA audit with cleaner audit boundaries

## HIPAA Compliance Considerations

- **Process Isolation**: Separate audit process provides cleaner compliance boundary
- **Access Controls**: Audit process runs with minimal required privileges
- **Audit Trail**: All IPC communication logged for compliance
- **Data Protection**: Audit data encrypted in transit and at rest
- **Monitoring**: Comprehensive audit of audit system access and operations

This separation provides the foundation for better testing, compliance, and operational excellence while maintaining the security and reliability requirements of the PAS system.
