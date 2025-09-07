# Gatekeeper Architecture

## Overview

Gatekeeper is the service proxy component of the PAS system, responsible for enforcing access policies, proxying connections to target services, and coordinating with the audit system for session recording. It operates in the customer's internal network and serves as the enforcement point for privileged access policies.

## Core Responsibilities

### Access Enforcement
- **Policy Enforcement**: Apply time-based restrictions and access policies
- **Service Proxying**: Proxy connections to target services (SSH, RDP, HTTP, databases)
- **Session Coordination**: Coordinate with audit process for session recording
- **Application Management**: Manage application-specific configurations and policies

### Protocol Support
- **SSH Services**: Proxy SSH connections to Linux/Unix systems
- **RDP Services**: Proxy RDP connections to Windows systems
- **HTTP/HTTPS**: Proxy web-based applications and services
- **Database Protocols**: Support for various database connection protocols
- **Custom Applications**: Configurable support for proprietary applications

## Technical Architecture

### Technology Stack
- **Language**: Go (Gatekeeper 2.0) / Java (Legacy Gatekeeper)
- **Deployment**: Native binary or containerized deployment
- **Configuration**: YAML-based configuration with hot reload
- **Logging**: Structured logging with configurable output formats
- **Monitoring**: Prometheus metrics and health check endpoints

### Current Implementation (Gatekeeper 2.0)
```
gatekeeper2/
├── backend/              # Go backend implementation
├── frontend/            # Web-based configuration interface
├── platforms/           # Platform-specific build configurations
├── rpm/                # RPM packaging for Linux deployment
└── upgrade/            # Upgrade scripts and procedures
```

### Key Components

#### Proxy Engine
- **Connection Handling**: High-performance connection proxying
- **Protocol Detection**: Automatic protocol detection and routing
- **Load Balancing**: Basic load balancing across multiple target services
- **Connection Pooling**: Efficient connection reuse and management

#### Policy Engine
- **Time-Based Access**: Enforce access windows and time restrictions
- **User-Based Policies**: Apply policies based on user roles and permissions
- **Service-Based Rules**: Service-specific access controls and restrictions
- **Emergency Access**: Break-glass procedures for emergency access

#### Configuration Management
- **Hot Reload**: Configuration changes without service restart
- **Validation**: Configuration validation and error reporting
- **Templating**: Support for environment-specific configuration templates
- **Backup/Restore**: Configuration backup and restore capabilities

## Integration Points

### PAS Server Integration
- **RSS Protocol**: Communication with Parent for session coordination
- **Configuration Sync**: Receive configuration updates from Parent
- **Status Reporting**: Report service status and health metrics
- **User Authentication**: Validate user permissions and access rights

### Audit System Integration
- **Session Coordination**: Coordinate audit session creation and management
- **Traffic Routing**: Route traffic through audit system for recording
- **Metadata Collection**: Collect session metadata for audit records
- **Compliance Reporting**: Provide data for compliance and audit reports

### Target Service Integration
- **Service Discovery**: Automatic discovery of available target services
- **Health Monitoring**: Monitor target service availability and health
- **Connection Management**: Manage connections to target services
- **Error Handling**: Handle target service failures and recovery

## Deployment Models

### Network Placement
- **Internal Network**: Deployed in customer's internal network
- **DMZ Access**: Controlled access from DMZ components
- **Service Proximity**: Close network proximity to target services
- **Firewall Integration**: Minimal firewall rule requirements

### High Availability
- **Active-Passive**: Support for active-passive clustering
- **Load Distribution**: Distribute load across multiple Gatekeeper instances
- **Failover**: Automatic failover to backup instances
- **Session Persistence**: Maintain session state during failover

### Security Model
- **Network Isolation**: Isolated network segments for different service types
- **Credential Management**: Secure storage and management of service credentials
- **Encryption**: Encrypted communication with all system components
- **Audit Trail**: Comprehensive logging of all access attempts and activities

## Performance Characteristics

### Scalability
- **Concurrent Connections**: Supports 1000+ concurrent proxied connections
- **Throughput**: High-throughput data proxying with minimal latency overhead
- **Resource Efficiency**: Low memory and CPU footprint
- **Connection Limits**: Configurable connection limits per user/service

### Reliability
- **Fault Tolerance**: Continues operation during partial system failures
- **Recovery**: Automatic recovery from transient failures
- **Monitoring**: Comprehensive health monitoring and alerting
- **Graceful Degradation**: Maintains core functionality during component failures

## Configuration Management

### Service Configuration
```yaml
services:
  - name: "production-db"
    type: "mysql"
    host: "db.internal.company.com"
    port: 3306
    policies:
      - time_windows: ["09:00-17:00"]
      - user_groups: ["dba", "developers"]
      - max_connections: 10
```

### Policy Configuration
```yaml
policies:
  time_based:
    business_hours: "09:00-17:00"
    maintenance_window: "02:00-04:00"
  user_based:
    emergency_access: ["admin", "oncall"]
    restricted_access: ["contractor", "temp"]
```

## Current Implementation Status

### Gatekeeper 2.0 (Current)
- **Language**: Go implementation for improved performance
- **Features**: Enhanced policy engine and configuration management
- **Deployment**: Native binary with systemd integration
- **Monitoring**: Prometheus metrics and structured logging
- **Status**: Production deployment in progress

### Legacy Gatekeeper (Deprecated)
- **Language**: Java implementation
- **Status**: Being phased out in favor of Gatekeeper 2.0
- **Migration**: Automated migration tools available
- **Support**: Limited support for critical bug fixes only

## Operational Procedures

### Installation and Setup
1. **Package Installation**: Install RPM package on target systems
2. **Configuration**: Configure services and policies via YAML files
3. **Network Setup**: Configure firewall rules and network access
4. **Integration**: Connect to PAS Server and audit system
5. **Validation**: Verify connectivity and policy enforcement

### Monitoring and Maintenance
- **Health Checks**: Regular health check endpoints for monitoring
- **Log Analysis**: Structured logs for troubleshooting and analysis
- **Performance Metrics**: Prometheus metrics for performance monitoring
- **Configuration Validation**: Automated configuration validation and testing

### Troubleshooting
- **Connection Issues**: Diagnostic tools for connection troubleshooting
- **Policy Debugging**: Tools for debugging policy enforcement issues
- **Performance Analysis**: Performance profiling and analysis tools
- **Log Correlation**: Correlation with audit and Parent logs for issue resolution

## Future Enhancements

### Planned Improvements
- **Enhanced Policy Engine**: More sophisticated policy rules and conditions
- **Service Discovery**: Automatic discovery and registration of target services
- **Load Balancing**: Advanced load balancing and failover capabilities
- **Container Support**: Native container deployment and orchestration

### Integration Enhancements
- **Cloud Integration**: Support for cloud-based target services
- **API Gateway**: Enhanced API gateway functionality
- **Monitoring Integration**: Integration with enterprise monitoring systems
- **Compliance Automation**: Automated compliance checking and reporting

---

*This document describes the current implementation of the Gatekeeper component. For proposed improvements and future enhancements, see the [recommendations](../recommendations/) section.*
