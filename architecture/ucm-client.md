# UCM Client Architecture

## Overview

The UCM (Unified Connection Manager) Client is the desktop application that provides users with access to privileged resources through the PAS system. It handles user authentication, displays available resources, and establishes secure connections to target systems through the PAS infrastructure.

## Core Responsibilities

### User Interface
- **Resource Discovery**: Display available privileged resources based on user permissions
- **Connection Management**: Initiate and manage connections to target systems
- **Session Monitoring**: Display active session status and connection health
- **User Authentication**: Handle user login and credential management

### Connection Handling
- **Protocol Support**: Support for SSH, RDP, VNC, HTTP, and custom protocols
- **Secure Tunneling**: Establish secure tunnels through PAS infrastructure
- **Session Coordination**: Coordinate with audit system for session recording
- **Application Integration**: Launch appropriate client applications for different protocols

## Technical Architecture

### Technology Stack
- **Language**: C++ with Qt framework for cross-platform GUI
- **Networking**: LibRSSConnect library for RSS protocol communication
- **Deployment**: Native installers for Windows, macOS, and Linux
- **Configuration**: Local configuration files with server-side policy enforcement
- **Updates**: Automatic update mechanism with digital signature verification

### Module Structure
```
ucm-client/
├── src/
│   ├── core/           # Core application logic and RSS protocol handling
│   ├── gui/            # Qt-based user interface components
│   ├── protocols/      # Protocol-specific connection handlers
│   ├── security/       # Authentication and encryption components
│   └── utils/          # Utility functions and helper classes
├── resources/          # UI resources, icons, and configuration templates
├── installers/         # Platform-specific installer configurations
└── tests/             # Unit tests and integration tests
```

### Key Components

#### RSS Protocol Client
- **Server Communication**: Communicate with PAS Server using RSS protocol
- **Authentication**: Handle user authentication and session management
- **Resource Enumeration**: Retrieve available resources based on user permissions
- **Connection Coordination**: Coordinate connection establishment with server components

#### Protocol Handlers
- **SSH Handler**: Launch SSH clients with appropriate connection parameters
- **RDP Handler**: Launch RDP clients with credential injection support
- **VNC Handler**: Launch VNC clients with secure connection setup
- **HTTP Handler**: Launch web browsers with SSO integration
- **Custom Handlers**: Support for customer-specific application protocols

#### Security Components
- **Certificate Management**: Handle SSL/TLS certificates for secure communication
- **Credential Storage**: Secure storage of user credentials and connection parameters
- **Encryption**: End-to-end encryption for sensitive data transmission
- **Digital Signatures**: Verify application and update integrity

## Platform Support

### Windows
- **Supported Versions**: Windows 10, Windows 11, Windows Server 2016+
- **Installation**: MSI installer with Group Policy deployment support
- **Integration**: Windows credential manager integration
- **Client Applications**: Built-in RDP client, PuTTY, custom SSH clients

### macOS
- **Supported Versions**: macOS 10.15+, Apple Silicon support
- **Installation**: DMG installer with notarization
- **Integration**: Keychain integration for credential storage
- **Client Applications**: Built-in SSH, Microsoft Remote Desktop, VNC clients

### Linux
- **Supported Distributions**: RHEL/CentOS 7+, Ubuntu 18.04+, SUSE Linux
- **Installation**: RPM and DEB packages
- **Integration**: System credential managers (GNOME Keyring, KWallet)
- **Client Applications**: OpenSSH, Remmina, TigerVNC, custom clients

## Connection Workflow

### Resource Discovery
1. **Authentication**: User authenticates with PAS Server
2. **Permission Retrieval**: Server returns available resources based on user roles
3. **Resource Display**: Client displays categorized list of available resources
4. **Policy Enforcement**: Apply client-side policy restrictions and time windows

### Connection Establishment
1. **Resource Selection**: User selects target resource from available list
2. **Connection Request**: Client sends connection request to PAS Server
3. **Audit Coordination**: Server coordinates with audit system for session recording
4. **Tunnel Establishment**: Secure tunnel established through PAS infrastructure
5. **Client Launch**: Appropriate client application launched with connection parameters

### Session Management
1. **Session Monitoring**: Monitor connection status and health
2. **Audit Integration**: Coordinate with audit system for session recording
3. **Policy Enforcement**: Enforce session time limits and access restrictions
4. **Session Termination**: Clean termination and audit record completion

## Configuration Management

### Client Configuration
```json
{
  "server": {
    "hostname": "pas.company.com",
    "port": 7894,
    "ssl_verify": true
  },
  "ui": {
    "theme": "corporate",
    "auto_connect": false,
    "remember_credentials": true
  },
  "protocols": {
    "ssh": {
      "client": "putty",
      "options": "-load corporate_profile"
    },
    "rdp": {
      "client": "mstsc",
      "fullscreen": false
    }
  }
}
```

### Policy Enforcement
- **Server-Side Policies**: Policies enforced by PAS Server
- **Client-Side Validation**: Additional validation and user experience improvements
- **Time-Based Restrictions**: Enforce access windows and time limits
- **Application Restrictions**: Control which client applications can be used

## Security Model

### Authentication
- **Multi-Factor Support**: Integration with customer MFA systems
- **Certificate-Based**: Support for certificate-based authentication
- **SSO Integration**: Single sign-on with enterprise identity systems
- **Credential Caching**: Secure local credential caching with encryption

### Communication Security
- **TLS Encryption**: All communication encrypted with TLS 1.2+
- **Certificate Pinning**: Server certificate validation and pinning
- **Protocol Security**: RSS protocol with built-in encryption and authentication
- **Man-in-the-Middle Protection**: Protection against network-based attacks

### Local Security
- **Credential Protection**: Encrypted storage of cached credentials
- **Application Integrity**: Digital signature verification for application updates
- **Process Isolation**: Isolation between UCM client and launched applications
- **Audit Trail**: Local audit trail of user actions and connection attempts

## Performance Characteristics

### Resource Usage
- **Memory Footprint**: Minimal memory usage (typically <100MB)
- **CPU Usage**: Low CPU usage during normal operation
- **Network Efficiency**: Efficient protocol usage with minimal bandwidth overhead
- **Startup Time**: Fast application startup and resource discovery

### Scalability
- **Concurrent Connections**: Support for multiple simultaneous connections
- **Resource Limits**: Configurable limits on concurrent sessions
- **Performance Monitoring**: Built-in performance monitoring and reporting
- **Resource Cleanup**: Automatic cleanup of terminated sessions and resources

## Deployment and Management

### Installation
- **Automated Deployment**: Support for enterprise deployment tools
- **Silent Installation**: Command-line installation with configuration parameters
- **Group Policy**: Windows Group Policy deployment and configuration
- **Package Management**: Linux package manager integration

### Updates and Maintenance
- **Automatic Updates**: Configurable automatic update mechanism
- **Digital Signatures**: Cryptographic verification of updates
- **Rollback Support**: Ability to rollback to previous versions
- **Configuration Migration**: Automatic configuration migration during updates

### Troubleshooting
- **Diagnostic Tools**: Built-in diagnostic and troubleshooting tools
- **Log Collection**: Comprehensive logging with configurable verbosity
- **Support Information**: Automatic collection of support information
- **Remote Assistance**: Support for remote troubleshooting and assistance

## Current Challenges

### Technical Debt
- **Legacy Qt Version**: Older Qt framework version with security and compatibility issues
- **C++ Complexity**: Complex C++ codebase with maintenance challenges
- **Platform Differences**: Platform-specific code paths and behaviors
- **Update Mechanism**: Complex update mechanism with reliability issues

### User Experience
- **Interface Modernization**: Outdated user interface design and usability
- **Performance Issues**: Slow resource discovery and connection establishment
- **Error Handling**: Poor error messages and user feedback
- **Configuration Complexity**: Complex configuration with limited user guidance

### Operational Issues
- **Deployment Complexity**: Complex deployment and configuration procedures
- **Troubleshooting Difficulty**: Limited diagnostic capabilities and error reporting
- **Platform Support**: Challenges maintaining support across multiple platforms
- **Update Reliability**: Update failures and rollback issues

---

*This document describes the current implementation of the UCM Client component. For proposed improvements and modernization strategies, see the [recommendations](../recommendations/) section.*
