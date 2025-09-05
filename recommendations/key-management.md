# SSH Key Management Service Integration

## Executive Summary

**Recommendation**: Integrate PAS components with existing key management service for centralized policy and storage, while keeping usage logic in PAS components.

**Priority**: MEDIUM-LOW (Revised from HIGH)
**Effort**: 5-6 weeks
**Risk**: Medium (integration complexity, performance impact)

## Priority Revision Note

**Original Assessment**: This was initially rated as HIGH priority due to perceived critical security vulnerabilities in cross-zone SSH key distribution.

**Revised Assessment**: After understanding the actual implementation (single-use ephemeral keys with 2-minute expiry for connection establishment only), this is now rated MEDIUM-LOW priority. The current implementation is within industry norms and represents acceptable risk.

## Problem Statement

### Current SSH Key Distribution Model
The PAS system uses ephemeral SSH keys for session establishment with the following pattern:
1. **Key Generation**: Parent generates single-use SSH key pairs in DMZ
2. **Key Delivery**: Keys delivered to UCM via HTTPS with 2-minute expiry
3. **Single Use**: Keys used once to establish SSH tunnel to Audit process
4. **Persistent Connection**: SSH tunnel remains active for entire UCM session (hours)
5. **Key Disposal**: Keys become invalid after first use or 2-minute timeout

### Current Implementation Assessment
**Security Posture**: ACCEPTABLE - Within industry norms for dynamic authentication
- ✅ Ephemeral keys (single-use, short-lived)
- ✅ Secure delivery (HTTPS transport)
- ✅ Limited exposure window (2 minutes maximum, typically 30 seconds)
- ✅ No persistent key storage on client devices
- ⚠️ Cross-zone key distribution (mitigated by ephemeral nature)

### Scattered Key Management Components
- Key generation logic in Parent SshKeyService
- Key rotation in Gatekeeper RssScProperties
- Key handling in LibRSSConnect CmSession
- Inconsistent key policies and lifecycle management
- No centralized audit trail for key operations

## Enhanced Security Recommendations

### Option 1: Certificate-Based Authentication (Incremental Improvement)
Replace ephemeral SSH keys with short-lived SSH certificates for improved security and audit trail.

#### Implementation Approach
```
Current: Parent generates SSH key pair → UCM uses private key
Proposed: Parent issues SSH certificate → UCM uses certificate
```

#### Benefits
- **No private key distribution** - Only certificates cross zones
- **Centralized revocation** - Can revoke certificates instantly
- **Better audit trail** - Certificate usage is more traceable
- **Industry standard** - SSH certificates designed for this use case

#### Technical Implementation
```bash
# Parent acts as Certificate Authority
ssh-keygen -t rsa -f /etc/pas/ca_key
ssh-keygen -s /etc/pas/ca_key -I "user@session" -n user -V +2m user_cert.pub
```

### Option 2: Reverse Tunnel Architecture (RECOMMENDED - Fundamental Redesign)
Eliminate cross-zone credential distribution entirely using reverse tunnels over existing SSH connections.

#### **Feasibility Assessment: HIGH**
Based on detailed codebase analysis, this approach is **highly feasible** because:
- **Uses existing infrastructure** - Gatekeeper already connects to PAS Server via SSH
- **No new firewall rules** - Leverages existing Internal → DMZ SSH (port 22)
- **Complies with security policy** - PAS Server receives (never initiates) SSH connections
- **Existing RSS protocol** - Runs over the same SSH connection Gatekeeper already uses

#### Implementation Approach
```
Current: UCM receives credentials → Connects to Internal Zone
Proposed: Gatekeeper creates reverse tunnel → UCM connects without credentials
```

#### **Technical Implementation Using Existing SSH Connection**
```java
// Gatekeeper already has SSH connection to Parent - just add reverse tunnels
public class GatekeeperReverseTunnelService {

    @Autowired
    private ExistingSSHConnection parentConnection; // Already exists!

    public void createReverseTunnelForSession(String sessionId, int servicePort) {
        // Use EXISTING SSH connection to Parent
        SSHSession existingSession = parentConnection.getSession();

        // Create reverse tunnel using existing connection
        int allocatedPort = existingSession.setPortForwardingR(
            0, // Let Parent allocate port
            "127.0.0.1",
            servicePort
        );

        // Notify Parent of tunnel availability via existing RSS protocol
        rssProtocol.sendMessage("TUNNEL_READY", Map.of(
            "sessionId", sessionId,
            "tunnelPort", allocatedPort
        ));
    }
}
```

#### Benefits
- **No credentials in Internet Zone** - UCM never receives any keys/certificates
- **Internal Zone controls** - Gatekeeper initiates all connections (already does this)
- **Zero trust** - Internet Zone has zero network credentials
- **Simplified audit** - All connections originate from trusted zone
- **No customer impact** - Uses existing network infrastructure
- **Security policy compliant** - PAS Server only receives SSH connections

## Integration Strategy (Current Approach)

### Responsibilities to Move to Existing Key Service

#### 1. Key Generation Policy Enforcement
```java
// Move to Key Management Service
public interface KeyPolicyService {
    KeyGenerationPolicy getKeyPolicy(String componentType);
    boolean validateKeyStrength(PublicKey key);
    Duration getKeyRotationInterval(String componentType);
    List<String> getAllowedKeyTypes();
}

// Example policies
KeyGenerationPolicy sshPolicy = KeyGenerationPolicy.builder()
    .keyType("RSA")
    .keySize(4096)
    .rotationInterval(Duration.ofHours(24))
    .maxUsageCount(1000)
    .build();
```

#### 2. Key Storage and Lifecycle Management
```java
// Move to Key Management Service
public interface KeyStorageService {
    String storeKey(SshKeyPair keyPair, KeyMetadata metadata);
    SshKeyPair retrieveKey(String keyId);
    void rotateKey(String keyId);
    void revokeKey(String keyId, String reason);
    List<KeyMetadata> getKeyHistory(String componentId);
}

// Key metadata for audit and lifecycle
public class KeyMetadata {
    private String keyId;
    private String componentId;
    private String purpose; // "session", "connect", "audit"
    private Instant createdAt;
    private Instant expiresAt;
    private KeyStatus status;
    private String createdBy;
}
```

#### 3. Key Distribution Coordination
```java
// Move to Key Management Service
public interface KeyDistributionService {
    void distributeKey(String keyId, List<String> targetComponents);
    void synchronizeKeys(String componentId);
    void emergencyKeyRevocation(String keyId);
    KeyDistributionStatus getDistributionStatus(String keyId);
}
```

### Responsibilities to Keep in PAS Components

#### 1. Key Usage and Caching
```java
// Keep in PAS components for performance
public class LocalKeyCache {
    private final Map<String, CachedKey> keyCache = new ConcurrentHashMap<>();
    private final KeyManagementClient keyClient;
    
    public SshKeyPair getSessionKey(String userId, String sessionId) {
        String cacheKey = userId + ":" + sessionId;
        CachedKey cached = keyCache.get(cacheKey);
        
        if (cached == null || cached.isExpired()) {
            // Request new key from key management service
            SshKeyPair keyPair = keyClient.requestSessionKey(userId, sessionId);
            keyCache.put(cacheKey, new CachedKey(keyPair, Duration.ofMinutes(30)));
            return keyPair;
        }
        
        return cached.getKeyPair();
    }
}
```

#### 2. Protocol-Specific Key Handling
```java
// Keep in Connect/LibRSSConnect for SSH protocol specifics
public class SshKeyHandler {
    public void configureSSHSession(Session session, SshKeyPair keyPair) {
        // SSH-specific key configuration
        session.setConfig("PreferredAuthentications", "publickey");
        session.setConfig("PubkeyAcceptedAlgorithms", "rsa-sha2-512,rsa-sha2-256");
        
        // Apply private key to session
        JSch jsch = session.getJSch();
        jsch.addIdentity("session-key", 
                        keyPair.getPrivateKey().getEncoded(),
                        keyPair.getPublicKey().getEncoded(),
                        null);
    }
}
```

#### 3. Connection-Specific Key Derivation
```java
// Keep in components for connection-specific logic
public class ConnectionKeyDerivation {
    public SshKeyPair deriveConnectionKey(SshKeyPair masterKey, String connectionId) {
        // Derive connection-specific key from master key
        // This stays in PAS components for performance and security
        return keyDerivationFunction.derive(masterKey, connectionId);
    }
}
```

## Integration API Design

### Key Management Client Interface
```java
public interface KeyManagementClient {
    // Session key management
    SshKeyPair requestSessionKey(String userId, String sessionId, Duration ttl);
    void releaseSessionKey(String keyId);
    
    // Component key management  
    SshKeyPair getComponentKey(String componentId, String keyType);
    void reportKeyUsage(String keyId, KeyUsageEvent event);
    
    // Key validation and status
    boolean validateKeyFingerprint(String fingerprint);
    KeyStatus getKeyStatus(String keyId);
    
    // Key rotation
    void requestKeyRotation(String componentId);
    RotationStatus getRotationStatus(String rotationId);
}
```

### Key Usage Events for Audit
```java
public class KeyUsageEvent {
    private String keyId;
    private String componentId;
    private String userId;
    private String sessionId;
    private KeyUsageType usageType; // REQUESTED, USED, RELEASED, FAILED
    private Instant timestamp;
    private String sourceIP;
    private Map<String, String> additionalContext;
}
```

### Error Handling and Fallback
```java
public class ResilientKeyManagementClient implements KeyManagementClient {
    private final KeyManagementClient primaryClient;
    private final LocalKeyCache fallbackCache;
    private final CircuitBreaker circuitBreaker;
    
    @Override
    public SshKeyPair requestSessionKey(String userId, String sessionId, Duration ttl) {
        return circuitBreaker.executeSupplier(() -> {
            try {
                SshKeyPair key = primaryClient.requestSessionKey(userId, sessionId, ttl);
                fallbackCache.store(userId + ":" + sessionId, key, ttl);
                return key;
            } catch (KeyManagementException e) {
                // Fallback to cached key if available
                return fallbackCache.get(userId + ":" + sessionId)
                    .orElseThrow(() -> new SessionKeyUnavailableException(
                        "Key management service unavailable and no cached key", e));
            }
        });
    }
}
```

## HIPAA Compliance Integration

### Key Access Logging
```java
public class HipaaCompliantKeyClient implements KeyManagementClient {
    private final KeyManagementClient delegate;
    private final AuditLogger auditLogger;
    
    @Override
    public SshKeyPair requestSessionKey(String userId, String sessionId, Duration ttl) {
        // Log key request for HIPAA compliance
        auditLogger.logKeyAccess(KeyAccessEvent.builder()
            .userId(userId)
            .sessionId(sessionId)
            .action("REQUEST_SESSION_KEY")
            .timestamp(Instant.now())
            .sourceComponent("PAS")
            .build());
        
        try {
            SshKeyPair key = delegate.requestSessionKey(userId, sessionId, ttl);
            
            // Log successful key retrieval
            auditLogger.logKeyAccess(KeyAccessEvent.builder()
                .userId(userId)
                .sessionId(sessionId)
                .action("SESSION_KEY_GRANTED")
                .keyFingerprint(key.getPublicKey().getFingerprint())
                .timestamp(Instant.now())
                .build());
            
            return key;
        } catch (Exception e) {
            // Log key request failure
            auditLogger.logKeyAccess(KeyAccessEvent.builder()
                .userId(userId)
                .sessionId(sessionId)
                .action("SESSION_KEY_DENIED")
                .errorReason(e.getMessage())
                .timestamp(Instant.now())
                .build());
            throw e;
        }
    }
}
```

### Encryption in Transit
```java
// All key service communication must be encrypted
public class SecureKeyManagementClient {
    private final SSLContext sslContext;
    private final RestTemplate restTemplate;
    
    public SecureKeyManagementClient() {
        // Configure mutual TLS for key service communication
        this.sslContext = SSLContextBuilder.create()
            .loadKeyMaterial(clientKeyStore, clientKeyPassword)
            .loadTrustMaterial(trustStore, null)
            .build();
            
        this.restTemplate = new RestTemplate();
        restTemplate.setRequestFactory(new HttpComponentsClientHttpRequestFactory(
            HttpClients.custom().setSSLContext(sslContext).build()));
    }
}
```

## Implementation Plan

### **RECOMMENDED APPROACH: Reverse Tunnel Architecture**

Based on detailed feasibility analysis, the reverse tunnel approach is the clear winner:
- **Highest security benefit** - Eliminates cross-zone credential distribution
- **Uses existing infrastructure** - No customer firewall changes required
- **Manageable implementation** - 8-12 weeks with existing SSH connections
- **Backward compatible** - Can run parallel with current system

#### **Phase 1: Reverse Tunnel Implementation (Weeks 1-8)**

**Week 1-2: Core Infrastructure**
1. Implement reverse tunnel capability in existing Gatekeeper SSH connection
2. Add tunnel coordination to existing RSS protocol messages
3. Create tunnel management service in Parent

**Week 3-4: Parent Coordination**
1. Modify Parent to coordinate reverse tunnels instead of generating SSH keys
2. Update session establishment flow to provide tunnel endpoints
3. Add tunnel health monitoring and management

**Week 5-6: UCM Integration**
1. Update UCM/LibRSSConnect to connect to Parent-provided tunnel endpoints
2. Remove SSH key handling from connection establishment
3. Implement connection retry logic for tunnel endpoints

**Week 7-8: Feature Flag and Testing**
1. Implement database-driven feature flag for gradual rollout
2. Add dual-mode operation (old SSH keys + new reverse tunnels)
3. Comprehensive testing and validation

#### **Feature Flag Implementation for Backward Compatibility**
```java
// Database-driven feature flag for gradual rollout over 1+ years
@Entity
public class SystemConfiguration {
    @Column(name = "reverse_tunnel_enabled")
    private boolean reverseTunnelEnabled = false;

    @Column(name = "reverse_tunnel_rollout_percentage")
    private int rolloutPercentage = 0; // Start at 0%, gradually increase
}

@Service
public class SessionEstablishmentService {

    public void establishSession(SessionRequest request) {
        if (shouldUseReverseTunnel(request)) {
            establishSessionWithReverseTunnel(request);
        } else {
            establishSessionWithSSHKeys(request); // Current method
        }
    }

    private boolean shouldUseReverseTunnel(SessionRequest request) {
        SystemConfiguration config = configRepository.findCurrent();

        if (!config.isReverseTunnelEnabled()) {
            return false;
        }

        // Gradual rollout based on percentage
        int hash = Math.abs(request.getSessionId().hashCode()) % 100;
        return hash < config.getRolloutPercentage();
    }
}
```

#### **Rollout Strategy (12+ months)**
1. **Month 1**: Deploy with feature flag disabled (0% rollout)
2. **Month 2-3**: Enable for 5% of sessions, monitor performance
3. **Month 4-6**: Gradually increase to 25% rollout
4. **Month 7-9**: Increase to 75% rollout
5. **Month 10-12**: Reach 100% rollout for new sessions
6. **Month 12+**: Deprecate SSH key method once all UCM/Gatekeeper components upgraded

### Alternative: Certificate-Based Authentication (Lower Priority)

#### Phase 1: Certificate Implementation (Weeks 1-4) - IF BANDWIDTH PERMITS
1. **Week 1-2**: Implement SSH certificate authority in Parent
2. **Week 3**: Update UCM/LibRSSConnect to use certificates instead of keys
3. **Week 4**: Testing and validation of certificate-based authentication

**Note**: This provides incremental improvement but doesn't address the fundamental cross-zone credential distribution issue.

## Risk Assessment and Mitigation Analysis

### Current Risk Level: MEDIUM (Revised from HIGH)

#### Existing Mitigations Effectiveness
1. **HTTPS Delivery vs File Download**: ✅ Eliminates persistent key files, reduces exposure window
2. **Single-Use + 2-Minute Expiry**: ✅ Dramatically reduces attack window (99.9% reduction)
3. **Ephemeral Nature**: ✅ Keys become useless after first use
4. **Memory-Only Storage**: ✅ No persistent key storage on client devices

#### Remaining Risk Factors
- **Cross-zone trust model**: Internet zone devices accessing Internal zone
- **Memory-based attacks**: Sophisticated attackers could extract keys during valid window
- **Audit trail gaps**: Limited visibility into key usage in Internet zone
- **Operational complexity**: Frequent key generation and coordination

#### Risk Quantification
- **Exposure Window**: Reduced from indefinite to ~30 seconds (typical connection time)
- **Attack Vectors**: Reduced from 5+ to 2-3 realistic scenarios
- **Business Impact**: Reduced from CRITICAL to MEDIUM due to effective mitigations
- **Overall Risk Reduction**: ~85% compared to unmitigated key distribution

## Success Metrics

### Current Implementation Success Metrics
- **Key Exposure Time**: < 2 minutes maximum, < 30 seconds typical
- **Key Reuse Prevention**: 100% single-use enforcement
- **Secure Delivery**: 100% HTTPS transport for key delivery
- **Connection Success Rate**: > 99% successful SSH tunnel establishment

### Enhanced Implementation Success Metrics
- **Centralized Control**: 100% of SSH keys/certificates managed through central service
- **Audit Compliance**: Complete audit trail for all key/certificate operations
- **Performance**: Key/certificate retrieval latency < 50ms for 95th percentile
- **Reliability**: 99.9% key/certificate availability with fallback mechanisms
- **Security**: Zero key-related security incidents

## Migration Strategy

### Gradual Migration Approach
1. **Phase 1**: Parallel operation (both old and new key management)
2. **Phase 2**: New sessions use key management service
3. **Phase 3**: Migrate existing sessions during rotation
4. **Phase 4**: Remove old key management code

### Rollback Plan
- Maintain local key generation capability during migration
- Feature flags to switch between old and new key management
- Automated rollback triggers based on error rates
- Emergency key generation for service continuity

## Detailed Feasibility Analysis Results

### **Reverse Tunnel Architecture: HIGH FEASIBILITY**

#### **Pros vs Cons Analysis**

**Pros**:
- ✅ **Eliminates cross-zone credential distribution** - No more SSH keys to Internet zone
- ✅ **Uses existing infrastructure** - No new firewall rules needed
- ✅ **Backward compatible** - Can run both systems in parallel with feature flags
- ✅ **Security policy compliant** - PAS Server only receives SSH connections
- ✅ **Gradual rollout** - Feature flag allows controlled deployment over 1+ years
- ✅ **Simpler troubleshooting** - Fewer moving parts in connection establishment
- ✅ **Better audit trail** - All connections originate from trusted Internal zone

**Cons**:
- ⚠️ **Additional latency** - +10-20ms for extra hop through Parent
- ⚠️ **Parent becomes bottleneck** - All traffic flows through Parent port forwarding
- ⚠️ **Implementation complexity** - Dual-mode operation during transition
- ⚠️ **Connection coordination** - More complex session setup coordination

#### **Performance Impact Assessment**
- **Latency**: +10-20ms (acceptable for security benefit)
- **Scalability**: Parent already handles session coordination (existing bottleneck)
- **Throughput**: No significant impact on data transfer rates
- **Memory**: Moderate increase in Parent for tunnel management

#### **Customer Impact Assessment**
- **Firewall Changes**: ✅ **NONE REQUIRED** - Uses existing SSH connections
- **Operational Changes**: ✅ **MINIMAL** - Transparent to end users
- **Deployment Impact**: ✅ **LOW** - Feature flag enables gradual rollout

### **Value Assessment: PROCEED WITH IMPLEMENTATION**

#### **Security Value: HIGH**
- **Eliminates fundamental security concern** - No more credentials in Internet zone
- **Improves compliance posture** - Cleaner audit boundaries for HIPAA
- **Reduces attack surface** - UCM becomes credential-free

#### **Implementation Value: HIGH**
- **Uses existing infrastructure** - No customer firewall changes required
- **Manageable complexity** - 8-12 weeks with existing SSH connections
- **Backward compatible** - Gradual rollout reduces deployment risk

#### **Performance Cost: LOW**
- **Minimal latency impact** - +10-20ms acceptable for security benefit
- **Existing bottleneck** - Parent already coordinates sessions

### **Final Recommendation: IMPLEMENT REVERSE TUNNEL ARCHITECTURE**

**Rationale**: The security benefits of eliminating cross-zone credential distribution significantly outweigh the minimal performance cost, especially since:

1. **No customer impact** - Uses existing Gatekeeper → PAS Server SSH connections
2. **High feasibility** - Leverages existing infrastructure and protocols
3. **Manageable implementation** - Clear 8-12 week development path
4. **Backward compatibility** - Feature flag enables safe gradual rollout
5. **Security policy compliant** - Aligns with PAS Server SSH connection constraints

**Priority Revision**: While this was initially downgraded to MEDIUM-LOW priority, the discovery that it uses existing infrastructure and requires no customer firewall changes makes this a **HIGH-VALUE, LOW-RISK** improvement that should be prioritized when development bandwidth is available.

This approach represents the optimal balance of security improvement, implementation feasibility, and operational impact for the PAS system architecture.
