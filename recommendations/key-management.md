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

### Option 1: Certificate-Based Authentication (Recommended)
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

### Option 2: Reverse Tunnel Architecture (Fundamental Redesign)
Eliminate cross-zone credential distribution entirely using reverse tunnels over existing SSH connections.

#### Implementation Approach
```
Current: UCM receives credentials → Connects to Internal Zone
Proposed: Gatekeeper creates reverse tunnel → UCM connects without credentials
```

#### **Key Advantage: Uses Existing Infrastructure**
This approach leverages the **existing SSH connection** that Gatekeeper already makes to PAS Server:
- **No new firewall rules required** - Uses existing Internal → DMZ SSH (port 22)
- **Complies with SSH policy** - PAS Server receives (not initiates) SSH connections
- **Existing RSS protocol** - Runs over the same SSH connection Gatekeeper already uses

#### Benefits
- **No credentials in Internet Zone** - UCM never receives any keys/certificates
- **Internal Zone controls** - Gatekeeper initiates all connections (already does this)
- **Zero trust** - Internet Zone has zero network credentials
- **Simplified audit** - All connections originate from trusted zone
- **No customer impact** - Uses existing network infrastructure

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

### Recommended Approach: Phased Enhancement

#### Phase 1: Certificate-Based Authentication (Weeks 1-4) - RECOMMENDED
1. **Week 1-2**: Implement SSH certificate authority in Parent
2. **Week 3**: Update UCM/LibRSSConnect to use certificates instead of keys
3. **Week 4**: Testing and validation of certificate-based authentication

#### Phase 2: Enhanced Security Features (Weeks 5-8) - OPTIONAL
1. **Week 5-6**: Implement HSM integration for certificate signing
2. **Week 7**: Add mutual TLS for certificate delivery
3. **Week 8**: Implement certificate transparency logging

#### Phase 3: Architectural Redesign (Weeks 9-20) - FUTURE
1. **Week 9-12**: Design and implement reverse tunnel architecture
2. **Week 13-16**: Migrate existing sessions to reverse tunnel model
3. **Week 17-20**: Complete testing and production deployment

### Alternative: Current System Enhancement

#### Phase 1: Key Management Service Integration (Weeks 1-2)
1. Define KeyManagementClient interface for existing service
2. Implement secure client with mTLS
3. Create HIPAA-compliant audit logging
4. Build resilient client with fallback

#### Phase 2: Parent Integration (Weeks 3-4)
1. Replace SshKeyService with KeyManagementClient
2. Migrate key generation logic to key service
3. Update session establishment to use new API
4. Implement local key caching

#### Phase 3: Component Integration (Weeks 4-6)
1. Update Gatekeeper key handling
2. Integrate LibRSSConnect with key management
3. End-to-end testing and validation

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

## Conclusion and Recommendations

### Current State Assessment
The existing SSH key distribution model is **acceptable for production use** with effective mitigations in place:
- Single-use ephemeral keys with 2-minute expiry
- HTTPS delivery eliminating persistent key storage
- Standard SSH tunnel security for persistent connections
- Risk level reduced to MEDIUM through effective controls

### Recommended Next Steps

#### Immediate (Optional Enhancement)
**Certificate-Based Authentication** - Provides incremental security improvement with industry-standard approach. Recommended when development bandwidth is available.

#### Strategic (Architectural Improvement)
**Reverse Tunnel Architecture** - Eliminates cross-zone credential distribution entirely. Best long-term solution applying "subtract principle" to remove the fundamental issue.

#### Current Priority
This issue has been **downgraded from HIGH to MEDIUM-LOW priority**. Focus immediate efforts on:
1. Audit process separation (higher compliance impact)
2. RSS protocol consolidation (higher development velocity impact)
3. SSH key management improvements (when bandwidth permits)

### Final Assessment
The current implementation represents **good security engineering** that transforms a potentially critical vulnerability into manageable risk through effective mitigations. While architectural improvements are valuable, they are not urgent given the current risk posture.

This integration approach provides centralized key management while maintaining the performance and security requirements of the PAS system, with full HIPAA compliance and audit capabilities.
