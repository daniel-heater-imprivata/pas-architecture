# PAS Server (Parent) Architecture

## Overview

The PAS Server, internally known as "Parent," is the central management component of the PAS system. It provides the web-based user interface, handles authentication and authorization, manages system configuration, and coordinates privileged access sessions across all system components.

## Core Responsibilities

### Web Interface and User Management
- **HTTPS Web Interface**: Primary user interface for access requests and system administration
- **User Authentication**: Integration with customer identity systems (LDAP, Active Directory, SAML)
- **Session Management**: Coordinate privileged access sessions across system components
- **Role-Based Access Control**: Fine-grained permissions based on user roles and departments

### System Coordination
- **Configuration Management**: Centralized configuration for all PAS components
- **Component Communication**: RSS protocol server for inter-component coordination
- **API Gateway**: REST APIs for programmatic access and third-party integration
- **Database Management**: PostgreSQL or MySQL database for system state and audit records

## Technical Architecture

### Technology Stack
- **Framework**: Java Spring Boot application
- **Database**: PostgreSQL (primary) or MySQL (legacy support)
- **Web Server**: Embedded Tomcat with HTTPS support
- **Frontend**: Mixed Angular/React components with legacy JSP pages
- **Build System**: Maven multi-module project

### Module Structure
```
parent/
├── api-request/          # API request objects and DTOs
├── api-response/         # API response objects and DTOs  
├── authorization/        # User permission and access control
├── connect-server/       # RSS protocol server implementation
├── domain-impl/          # Domain objects, repositories, DAOs
├── domain-interfaces/    # Domain interface definitions
├── service-impl/         # Business logic service implementations
├── rss-war/             # Main web application (legacy JSP)
├── rss-jetty-war/       # Jetty-based web application
└── text-provider/       # Internationalization and text resources
```

### Key Interfaces

#### RSS Protocol Server
- **Port**: 7894 (RSS protocol communication)
- **Purpose**: Coordinate with UCM clients and other components
- **Protocol**: Custom RSS protocol over SSH tunnels
- **Authentication**: Component-specific SSH keys and credentials

#### Web Interface
- **Port**: 8443 (HTTPS)
- **Purpose**: User interface and REST API access
- **Authentication**: Customer identity system integration
- **Session Management**: HTTP session with security controls

#### Database Integration
- **Supported Databases**: PostgreSQL 14+, MySQL 8+
- **Connection Pooling**: HikariCP for high-performance database access
- **Schema Management**: Flyway for database migrations
- **Audit Records**: Integration with audit system for session tracking

## Current Implementation Details

### Authentication and Authorization
- **LDAP/AD Integration**: Direct integration with customer directory services
- **SAML Support**: Enterprise SSO integration capabilities
- **Multi-Factor Authentication**: Integration with customer MFA systems
- **Session Security**: Secure session management with timeout controls

### Configuration Management
- **Database-Driven**: System configuration stored in database
- **Hot Reload**: Configuration changes without service restart
- **Environment-Specific**: Support for development, staging, production configurations
- **Audit Trail**: All configuration changes logged and tracked

### API Architecture
- **REST APIs**: JSON-based APIs for programmatic access
- **GraphQL**: Modern query interface for reporting and analytics
- **Legacy APIs**: Backward compatibility with existing integrations
- **Rate Limiting**: API throttling and abuse protection

## Integration Points

### Audit System Integration
- **Spring Integration**: Direct Spring bean integration (current coupling)
- **Session Coordination**: Audit session lifecycle management
- **Credential Injection**: Coordinate credential injection for audited sessions
- **File Discovery**: Audit file location and metadata management

### Component Communication
- **RSS Protocol**: Primary communication with UCM clients
- **SSH Tunneling**: Secure communication channels
- **Database Sharing**: Shared database access with audit components
- **Configuration Distribution**: Push configuration to remote components

## Performance Characteristics

### Scalability
- **Concurrent Users**: Supports 500+ concurrent web users
- **Session Management**: Handles 1000+ simultaneous privileged sessions
- **Database Performance**: Optimized queries with connection pooling
- **Memory Management**: JVM tuning for enterprise workloads

### Reliability
- **High Availability**: Supports active-passive clustering
- **Graceful Degradation**: Continues operation during component failures
- **Error Recovery**: Automatic retry and recovery mechanisms
- **Health Monitoring**: Comprehensive health checks and metrics

## Security Model

### Network Security
- **TLS Encryption**: All web traffic encrypted with TLS 1.2+
- **Certificate Management**: Customer-provided or self-signed certificates
- **Network Isolation**: DMZ deployment with controlled network access
- **Firewall Integration**: Minimal required port exposure

### Application Security
- **Input Validation**: Comprehensive input sanitization and validation
- **SQL Injection Protection**: Parameterized queries and ORM protection
- **XSS Prevention**: Output encoding and Content Security Policy
- **CSRF Protection**: Token-based CSRF protection for state-changing operations

### Audit and Compliance
- **Access Logging**: Comprehensive logging of all user actions
- **Configuration Auditing**: All system changes tracked and logged
- **Compliance Reporting**: Multi-regulatory compliance report generation
- **Data Protection**: No PII/PHI in system logs or monitoring data

## Deployment Model

### RPM-Based Deployment
- **Package Management**: Standard RPM package for Linux distributions
- **Service Management**: systemd service integration
- **Configuration Files**: Standard Linux configuration file locations
- **Log Management**: Integration with system logging (rsyslog, journald)

### Database Setup
- **Schema Creation**: Automated database schema creation and migration
- **Initial Data**: Default configuration and administrative users
- **Backup Integration**: Database backup and recovery procedures
- **Performance Tuning**: Database-specific optimization recommendations

## Current Challenges

### Technical Debt
- **Legacy JSP Pages**: Mixed modern and legacy web technologies
- **Audit Coupling**: Tight Spring integration with audit system
- **Build Complexity**: Large multi-module Maven project with long build times
- **Database Migrations**: Complex schema evolution and upgrade procedures

### Performance Issues
- **Memory Usage**: High JVM memory requirements for large deployments
- **Startup Time**: Long application startup due to Spring context initialization
- **Database Queries**: Some inefficient queries under high load
- **Session Management**: Memory-based session storage limits scalability

### Operational Complexity
- **Configuration Management**: Complex configuration with many interdependencies
- **Troubleshooting**: Difficult to isolate issues across tightly coupled components
- **Upgrade Procedures**: Complex upgrade process with database migrations
- **Monitoring**: Limited observability into internal component interactions

---

*This document describes the current implementation of the PAS Server (Parent) component. For proposed improvements and modernization strategies, see the [recommendations](../recommendations/) section.*
