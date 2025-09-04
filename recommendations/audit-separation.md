# Audit Architecture: Split into Separate Process

## Executive Summary

**Recommendation**: Split audit into a separate process with clean IPC mechanisms instead of merging with Parent.

**Priority**: HIGH  
**Effort**: 6-8 weeks  
**Risk**: Medium (IPC complexity, performance impact)

## Problem Statement

Current audit architecture is tightly coupled to Parent through Spring integration:
- Audit components are Spring beans within Parent JVM
- Audit failures can destabilize entire Parent application
- Independent testing of audit components is difficult
- HIPAA compliance requires cleaner audit boundaries

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
    // Session management
    void startAuditSession(String sessionId, AuditConfig config);
    void endAuditSession(String sessionId, SessionMetrics metrics);
    
    // Event recording
    void recordAuditEvent(String sessionId, AuditEvent event);
    void recordProtocolData(String sessionId, ProtocolData data);
    
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

## Benefits

### Technical Benefits
- **Fault Isolation**: Audit process crashes don't affect Parent
- **Independent Scaling**: Audit can scale based on session volume
- **Better Testing**: Audit can be tested independently with mock IPC
- **Performance Isolation**: Audit processing doesn't impact Parent performance

### Compliance Benefits
- **Cleaner Audit Boundaries**: Separate process provides clear audit trail
- **HIPAA Compliance**: Better separation of audit data and business logic
- **Security Isolation**: Audit process can run with different security context
- **Independent Monitoring**: Separate health checks and monitoring for audit

### Operational Benefits
- **Independent Deployment**: Audit updates don't require Parent restart
- **Specialized Configuration**: Audit-specific tuning and configuration
- **Better Debugging**: Isolated audit logs and debugging
- **Resource Management**: Dedicated resources for audit processing

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

### Phase 2: Audit Service Migration (Weeks 3-4)
1. Extract SSH audit service from Parent
2. Migrate HTTP audit service
3. Migrate RDP audit service
4. Implement audit coordinator

### Phase 3: Integration and Testing (Weeks 5-6)
1. Integrate IPC client into Parent
2. Implement error handling and resilience
3. Comprehensive testing with all protocols
4. Performance testing and optimization

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
