# PAS Audit System Architecture

## Overview

The PAS audit system is a sophisticated real-time protocol manipulation engine that performs active credential injection and semantic event recording across multiple protocols (SSH, RDP, VNC, Telnet, HTTP/HTTPS, Oracle, MySQL, FTP, MSDP, Horizon). This system is far more complex than passive byte recording - it understands protocol semantics and modifies data streams in real-time.

## Core Architecture Components

### Audit Service Listeners

Each protocol has a dedicated audit service listener that handles protocol-specific requirements:

**Current Protocol Support**:
- **SSH**: MITM proxy with credential injection (text-based audit)
- **RDP**: X.224 credential injection with binary audit format
- **VNC**: DES challenge/response injection with binary audit format
- **Telnet**: Terminal stream injection (text-based audit)
- **HTTP/HTTPS**: Regex-based credential replacement
- **Oracle**: SQL protocol injection
- **MySQL**: SQL protocol injection
- **FTP**: Command monitoring (no credential injection)
- **MSDP**: HTTP-based service discovery protocol
- **Horizon**: VMware Horizon protocol support

```
AuditServiceListenerFactory
├── SSH: MonitorSSHAudit (MITM proxy with key injection)
├── RDP: Rdp2AuditServerListener (X.224 credential injection)
├── VNC: MonitorVNCAudit (DES challenge/response injection)
├── HTTP: HttpAuditServiceListener (regex-based credential replacement)
├── Telnet: MonitorTelnetAudit (terminal stream injection)
├── Oracle: MonitorOracleAudit (SQL protocol injection)
└── MySQL: MonitorMySqlAudit (MySQL protocol injection)
```

### Protocol-Specific Credential Injection

#### SSH Credential Injection (MonitorSSHAudit)
- **Architecture**: Man-in-the-Middle (MITM) proxy using JSch library
- **Components**: SessionMITMServer and SessionMITMClient
- **Injection Points**: SSH authentication handshake, public key authentication
- **Credential Types**: Passwords, SSH private keys, certificates
- **Timing**: Must inject during SSH protocol negotiation phase

```java
// SSH credential lookup during authentication
@Override
public String passwordLookup(String token) {
    return credentialInjectionHandler.credentialLookupByToken(token)
        .map(Credential::getPassword)
        .orElse(null);
}
```

#### RDP Credential Injection (ProxyServerX224)
- **Architecture**: RDP proxy with X.224 connection layer interception
- **Injection Point**: RDP Client Info PDU during connection establishment
- **Credential Source**: RDP cookie parsing with token replacement
- **Protocol Phase**: X.224 connection request processing

```java
// RDP credential injection in connection phase
private void processCookie() {
    if (earlyCredentials.valid()) {
        Credential credential = CredentialUtils.getCredentialFromTokenString(
            getSessionInfo().getCredentialInjectionHandler(), 
            earlyCredentials.getPassword());
        // Inject real credentials into RDP stream
    }
}
```

#### VNC Credential Injection (MonitorVNCAudit)
- **Architecture**: VNC protocol interceptor with DES challenge handling
- **Injection Point**: VNC authentication challenge/response
- **Method**: DES cipher computation using actual password
- **Timing**: During VNC authentication handshake

```java
// VNC DES challenge credential injection
void substituteVncTokenForCred(InputStream clientInput, PipedOutputStream pos, 
                               ICredentialInjectionHandler handler) {
    if (enteredAuthentication.get()) {
        Credential cred = handler.credentialLookupByDesChallenge(buffer, plaintextChallenge);
        // Replace client's token-based response with computed DES response
    }
}
```

### Credential Injection Handler Integration

The audit system integrates with Parent's credential management through dependency injection:

```java
// Credential injection flow
Parent (CredentialInjectionService) 
    ↓ Spring injection
Audit Monitor (ICredentialInjectionHandler)
    ↓ Protocol-specific injection
Protocol Stream (SSH/RDP/VNC)
```

**Key Interfaces:**
- `ICredentialInjectionHandler`: Main credential lookup interface
- `IPrivateKeyMapService`: SSH key management
- `CredentialProvider`: Credential source abstraction

## Audit File Format and Management

### RDP Audit File Format

The audit system uses a custom binary format optimized for video reconstruction:

```c
// File header structure
#define FILE_HEADER_SIZE 32
#define RDP210_VERSION "RDP2.10"

struct rdp_event_header {
    BYTE type;           // Event type (CLIENT2SERVER, SERVER2CLIENT, etc.)
    UINT32 timestamp;    // Event timestamp in milliseconds
    UINT32 dataLength;   // Data payload length
    UINT32 dataOffset;   // Offset to data in file
};

// Event types
enum {
    CLIENT2SERVER = 2,
    SERVER2CLIENT = 3,
    CLIENTCURSORPOS = 5,
    CHANNEL = 6,
    SCREEN = 7,
    CREDENTIALS = 8,
    PDU_SERVER2CLIENT = 9
};
```

**Critical Dependencies:**
- **RDP2-Converter**: Requires exact binary format for video reconstruction
- **Channel Support**: Tracks up to 31 virtual channels
- **Semantic Events**: Records application-level events, not raw packets

### APORT Protocol Integration

LibRSSConnect reports session statistics to Parent via RSS protocol commands:

```cpp
// Session start notification
void AportMonitor::onOpen() {
    if (++openCount_ == 1) {
        const auto builder = createRssMessageBuilder(RSSCMD_APORTOPEN);
        rssMessageBuilderAddKeyValue(builder, "mappedPort", std::to_string(mappedPort_).c_str());
        rssMessageBuilderAddKeyValue(builder, "userId", userId_.c_str());
        // Send to Parent via RSS protocol
    }
}

// Session end with byte counts
void AportMonitor::onClose(boost::asio::ip::port_type port) {
    const auto builder = createRssMessageBuilder(RSSCMD_APORTCLOSE);
    rssMessageBuilderAddKeyValue(builder, "bytesUp", std::to_string(bytesUp_).c_str());
    rssMessageBuilderAddKeyValue(builder, "bytesDown", std::to_string(bytesDown_).c_str());
    // Send final statistics to Parent
}
```

## The 12-Year Audit Linking Race Condition

### Root Cause Analysis

The audit linking system suffers from a fundamental race condition between two asynchronous events:

1. **Audit Connection Creation**: When audit listener accepts connection (`IAuditServiceConnection#getCreateTime()`)
2. **Database Access Record Creation**: When Parent processes APORTOPEN command and creates `IHistServiceAccess`

### Current "Guessing" Algorithm

```java
// Time-based linking with 5-second window
private boolean isWithinAccessWindow(IAuditServiceConnection conn, AccessEntry entry) {
    return Math.abs(entry.createTime - conn.getCreateTime()) < 5000;
}
```

**Problems with Current Approach:**
- **Time-based guessing**: Fails under load when events exceed 5-second window
- **Multiple connections**: Cannot distinguish between multiple SSH sessions to same service
- **Network delays**: Variable latency pushes events outside time window
- **No deterministic identifier**: No guaranteed link between audit file and database record

### Audit-Link-Helper Workaround

The audit-link-helper system attempts to solve this through process tracking:

```
SSH Session → Process PID → User ID → Port Mapping → Deterministic Linking
```

**Limitations:**
- **SSH-only**: Doesn't work for RDP, VNC, HTTP protocols
- **External dependency**: Go service + systemd + IPC complexity
- **Single point of failure**: If helper dies, linking breaks
- **Latency overhead**: Additional lookup on every connection

## Performance Characteristics

### Current Bottlenecks

1. **Spring Bean Coupling**: All audit monitors are Spring beans in Parent JVM
2. **Synchronous Processing**: Credential injection blocks protocol flow
3. **Database Transactions**: Audit linking requires database writes
4. **Memory Usage**: 2000 connections × protocol state = significant heap pressure

### Protocol-Specific Overhead

- **SSH**: MITM proxy overhead + key lookup latency (~2-5ms per auth)
- **RDP**: X.224 parsing + credential injection in connection phase (~1-3ms)
- **VNC**: DES challenge computation for each authentication (~1-2ms)
- **HTTP**: Regex-based credential replacement in request/response bodies (~0.5-1ms)

## Integration Points with Parent

### Spring Configuration Dependencies

```java
// Audit monitors are Spring beans with injected dependencies
@Component
public class MonitorSSHAudit extends AbstractMonitor {
    @Autowired
    private ICredentialInjectionHandler credentialInjectionHandler;
    
    @Autowired
    private IPrivateKeyMapService privateKeyMapService;
    
    @Autowired
    private IAdminLogWriter adminLogWriter;
}
```

### Database Integration

- **Access Record Creation**: Parent creates `IHistServiceAccess` on APORTOPEN
- **Byte Count Updates**: Parent updates access record on APORTCLOSE
- **Audit File Linking**: GuessingConnectionLinker attempts to link files to access records
- **UI Integration**: Parent UI displays audit files based on database records

### RSS Protocol Commands

- **APORTOPEN**: LibRSSConnect → Parent when session starts
- **APORTCLOSE**: LibRSSConnect → Parent when session ends with byte counts
- **APORTFILE**: File transfer notifications
- **AUDITLOG**: Direct audit log messages

## Critical Constraints for Separation

### Must Preserve
1. **Real-time credential injection** across all protocols
2. **Exact file format compatibility** for RDP2-Converter
3. **Protocol semantic understanding** (not just byte recording)
4. **APORT protocol integration** for session statistics
5. **Database access record coordination** with Parent

### Cannot Simplify
1. **Credential injection timing** - must occur during protocol handshake
2. **Protocol awareness** - audit understands RDP PDUs, SSH messages, VNC challenges
3. **File format structure** - binary format optimized for video reconstruction
4. **Parent integration** - credential lookup and database coordination required

This architecture analysis reveals that audit separation must preserve sophisticated protocol manipulation capabilities while solving the fundamental race condition through deterministic session identification.
