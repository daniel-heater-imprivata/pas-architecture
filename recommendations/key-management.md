# SSH Key Management Service Integration

## Executive Summary

**Recommendation**: Integrate PAS components with existing key management service for centralized policy and storage, while keeping usage logic in PAS components.

**Priority**: HIGH  
**Effort**: 5-6 weeks  
**Risk**: Medium (integration complexity, performance impact)

## Problem Statement

SSH key management is currently scattered across multiple PAS components:
- Key generation logic in Parent SshKeyService
- Key rotation in Gatekeeper RssScProperties  
- Key handling in LibRSSConnect CmSession
- Inconsistent key policies and lifecycle management
- No centralized audit trail for key operations

## Integration Strategy

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

### Phase 1: API Design and Client Implementation (Weeks 1-2)
1. Define KeyManagementClient interface
2. Implement secure client with mTLS
3. Create HIPAA-compliant audit logging
4. Build resilient client with fallback

### Phase 2: Parent Integration (Weeks 3-4)
1. Replace SshKeyService with KeyManagementClient
2. Migrate key generation logic to key service
3. Update session establishment to use new API
4. Implement local key caching

### Phase 3: Gatekeeper Integration (Weeks 4-5)
1. Remove key rotation logic from RssScProperties
2. Integrate with key management client
3. Update RSS protocol to use managed keys
4. Test key rotation scenarios

### Phase 4: LibRSSConnect Integration (Weeks 5-6)
1. Update CmSession to use key management API
2. Implement C++ client wrapper for key service
3. Update UCM to handle key management integration
4. End-to-end testing

## Success Metrics

- **Centralized Control**: 100% of SSH keys managed through central service
- **Audit Compliance**: Complete audit trail for all key operations
- **Performance**: Key retrieval latency < 50ms for 95th percentile
- **Reliability**: 99.9% key availability with fallback mechanisms
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

This integration provides centralized key management while maintaining the performance and security requirements of the PAS system, with full HIPAA compliance and audit capabilities.
