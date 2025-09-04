# Configuration Management for RPM-Based Deployment

## Executive Summary

**Recommendation**: Implement hierarchical file-based configuration management with validation, hot reload, and customer override capabilities optimized for RPM deployment model.

**Priority**: MEDIUM  
**Effort**: 4-5 weeks  
**Risk**: Low (file-based, backward compatible)

## Problem Statement

Current configuration management has significant operational challenges:
- **Scattered configuration files** across multiple repositories and formats
- **No configuration validation** leading to runtime errors
- **Manual configuration synchronization** across components
- **Environment-specific configuration** requires manual management
- **RPM upgrade complexity** with configuration preservation
- **No hot reload capability** requiring service restarts for changes

## RPM-Compatible Configuration Strategy

### Hierarchical Configuration Structure
```bash
# RPM package structure for configuration
/etc/pas/
├── pas.conf                    # Main configuration file
├── conf.d/                     # Modular configuration directory
│   ├── 10-server.conf         # Server settings (lowest priority)
│   ├── 20-audit.conf          # Audit settings
│   ├── 30-gatekeeper.conf     # Gatekeeper settings
│   ├── 40-rss-protocol.conf   # RSS protocol settings
│   └── 99-customer.conf       # Customer overrides (highest priority)
├── templates/                  # Configuration templates
│   ├── pas.conf.template      # Base configuration template
│   ├── development.template   # Development environment
│   ├── staging.template       # Staging environment
│   └── production.template    # Production environment
├── validation/                 # Configuration validation
│   ├── pas-config-validator   # Validation script
│   └── schemas/               # Configuration schemas
│       ├── server.schema.json
│       ├── audit.schema.json
│       └── gatekeeper.schema.json
└── backup/                    # Configuration backups
    └── (automatic backups during upgrades)
```

### Main Configuration File Format
```yaml
# /etc/pas/pas.conf - Main configuration
pas:
  # Include modular configurations
  include:
    - "/etc/pas/conf.d/*.conf"
  
  # Global settings
  environment: production
  site_id: "customer_site_001"
  
  # Component configurations (can be overridden in conf.d/)
  server:
    host: "pas.customer.local"
    ports:
      https: 8443
      ssh: 22
      rss: 7894
    database:
      url: "jdbc:postgresql://localhost:5432/pas"
      username: "${PAS_DB_USER}"
      password: "${PAS_DB_PASSWORD}"
      pool_size: 20
    
  audit:
    enabled: true
    protocols: ["ssh", "rdp", "http", "vnc"]
    encryption:
      algorithm: "aes256"
      key_rotation_hours: 24
    retention:
      days: 90
      archive_location: "/var/pas/audit-archive"
    performance:
      max_concurrent_sessions: 1000
      buffer_size_mb: 64
    
  gatekeeper:
    poll_interval_seconds: 60
    key_rotation_hours: 24
    max_connections_per_gatekeeper: 100
    health_check_interval_seconds: 30
    
  rss_protocol:
    version: 110
    features:
      compression_enabled: true
      batching_enabled: false  # Can be enabled per customer
      async_errors_enabled: false
    timeout_seconds: 30
    
  monitoring:
    enabled: true
    metrics_port: 9090
    telemetry:
      enabled: true
      level: "basic"
      frequency: "daily"
```

### Modular Configuration Files
```yaml
# /etc/pas/conf.d/20-audit.conf - Audit-specific overrides
pas:
  audit:
    # Customer-specific audit settings
    retention:
      days: 180  # Override default 90 days
    protocols: ["ssh", "rdp", "http"]  # Disable VNC for this customer
    performance:
      max_concurrent_sessions: 500  # Lower limit for this customer
```

```yaml
# /etc/pas/conf.d/99-customer.conf - Customer-specific overrides
pas:
  server:
    host: "pas.healthcare-customer.com"
    database:
      pool_size: 50  # Higher pool size for this customer
  
  gatekeeper:
    max_connections_per_gatekeeper: 200  # Higher limit
  
  rss_protocol:
    features:
      batching_enabled: true  # Enable for this customer
```

## Configuration Management Tools

### Configuration Validation Script
```bash
#!/bin/bash
# /usr/bin/pas-config-validator

CONFIG_FILE="${1:-/etc/pas/pas.conf}"
SCHEMA_DIR="/etc/pas/validation/schemas"
TEMP_DIR="/tmp/pas-config-validation"

validate_configuration() {
    echo "Validating PAS configuration: $CONFIG_FILE"
    
    # Create temporary directory
    mkdir -p "$TEMP_DIR"
    
    # Parse and merge configuration files
    pas-config-parser "$CONFIG_FILE" > "$TEMP_DIR/merged-config.yaml"
    
    # Validate against schemas
    for schema in "$SCHEMA_DIR"/*.schema.json; do
        component=$(basename "$schema" .schema.json)
        echo "Validating $component configuration..."
        
        if ! yq eval ".pas.$component" "$TEMP_DIR/merged-config.yaml" | \
             jsonschema -i /dev/stdin "$schema"; then
            echo "ERROR: $component configuration validation failed"
            exit 1
        fi
    done
    
    # Cross-component validation
    validate_cross_component_constraints "$TEMP_DIR/merged-config.yaml"
    
    # Network validation
    validate_network_configuration "$TEMP_DIR/merged-config.yaml"
    
    echo "Configuration validation successful"
    cleanup_temp_files
}

validate_cross_component_constraints() {
    local config_file="$1"
    
    # Check port conflicts
    https_port=$(yq eval '.pas.server.ports.https' "$config_file")
    ssh_port=$(yq eval '.pas.server.ports.ssh' "$config_file")
    rss_port=$(yq eval '.pas.server.ports.rss' "$config_file")
    
    if [ "$https_port" = "$ssh_port" ] || [ "$https_port" = "$rss_port" ] || [ "$ssh_port" = "$rss_port" ]; then
        echo "ERROR: Port conflict detected in server configuration"
        exit 1
    fi
    
    # Check audit retention vs disk space
    retention_days=$(yq eval '.pas.audit.retention.days' "$config_file")
    if [ "$retention_days" -gt 365 ]; then
        echo "WARNING: Audit retention period is very long ($retention_days days)"
    fi
    
    # Check database connection settings
    db_pool_size=$(yq eval '.pas.server.database.pool_size' "$config_file")
    max_sessions=$(yq eval '.pas.audit.performance.max_concurrent_sessions' "$config_file")
    
    if [ "$db_pool_size" -lt $((max_sessions / 10)) ]; then
        echo "WARNING: Database pool size may be too small for max concurrent sessions"
    fi
}

validate_network_configuration() {
    local config_file="$1"
    
    # Check if ports are available
    https_port=$(yq eval '.pas.server.ports.https' "$config_file")
    if netstat -ln | grep -q ":$https_port "; then
        echo "WARNING: HTTPS port $https_port is already in use"
    fi
    
    # Validate hostname resolution
    hostname=$(yq eval '.pas.server.host' "$config_file")
    if ! nslookup "$hostname" >/dev/null 2>&1; then
        echo "WARNING: Hostname $hostname does not resolve"
    fi
}

# Run validation
validate_configuration "$@"
```

### Configuration Generator and Manager
```bash
#!/bin/bash
# /usr/bin/pas-configure - Configuration management utility

COMMAND="$1"
shift

case "$COMMAND" in
    "init")
        initialize_configuration "$@"
        ;;
    "set")
        set_configuration_value "$@"
        ;;
    "get")
        get_configuration_value "$@"
        ;;
    "validate")
        validate_configuration "$@"
        ;;
    "apply")
        apply_configuration "$@"
        ;;
    "backup")
        backup_configuration "$@"
        ;;
    "restore")
        restore_configuration "$@"
        ;;
    "environment")
        set_environment "$@"
        ;;
    *)
        show_usage
        ;;
esac

initialize_configuration() {
    local environment="${1:-production}"
    
    echo "Initializing PAS configuration for $environment environment..."
    
    # Copy base template
    cp "/etc/pas/templates/pas.conf.template" "/etc/pas/pas.conf"
    
    # Apply environment-specific settings
    if [ -f "/etc/pas/templates/$environment.template" ]; then
        echo "Applying $environment environment settings..."
        yq eval-all 'select(fileIndex == 0) * select(fileIndex == 1)' \
            "/etc/pas/pas.conf" "/etc/pas/templates/$environment.template" \
            > "/tmp/pas.conf.new"
        mv "/tmp/pas.conf.new" "/etc/pas/pas.conf"
    fi
    
    # Set appropriate permissions
    chmod 640 "/etc/pas/pas.conf"
    chown root:pas "/etc/pas/pas.conf"
    
    echo "Configuration initialized. Please review and customize /etc/pas/pas.conf"
}

set_configuration_value() {
    local key="$1"
    local value="$2"
    local config_file="${3:-/etc/pas/conf.d/99-customer.conf}"
    
    echo "Setting $key = $value in $config_file"
    
    # Backup current configuration
    backup_configuration
    
    # Create customer config if it doesn't exist
    if [ ! -f "$config_file" ]; then
        echo "pas:" > "$config_file"
        chmod 640 "$config_file"
        chown root:pas "$config_file"
    fi
    
    # Set the value using yq
    yq eval ".pas.$key = \"$value\"" -i "$config_file"
    
    # Validate the new configuration
    if pas-config-validator; then
        echo "Configuration updated successfully"
        
        # Trigger hot reload if service is running
        if systemctl is-active --quiet pas-server; then
            echo "Triggering configuration reload..."
            systemctl reload pas-server
        fi
    else
        echo "Configuration validation failed. Restoring backup..."
        restore_configuration
        exit 1
    fi
}

apply_configuration() {
    echo "Applying configuration changes..."
    
    # Validate configuration
    if ! pas-config-validator; then
        echo "Configuration validation failed. Aborting."
        exit 1
    fi
    
    # Backup current configuration
    backup_configuration
    
    # Reload services
    echo "Reloading PAS services..."
    systemctl reload pas-server
    systemctl reload pas-gatekeeper
    
    echo "Configuration applied successfully"
}

backup_configuration() {
    local backup_dir="/etc/pas/backup"
    local timestamp=$(date +%Y%m%d-%H%M%S)
    
    mkdir -p "$backup_dir"
    
    # Backup main configuration
    cp "/etc/pas/pas.conf" "$backup_dir/pas.conf.$timestamp"
    
    # Backup modular configurations
    tar -czf "$backup_dir/conf.d.$timestamp.tar.gz" -C "/etc/pas" conf.d/
    
    echo "Configuration backed up to $backup_dir"
}
```

## Hot Reload Implementation

### Configuration File Watcher
```java
@Component
public class ConfigurationWatcher {
    private final WatchService watchService;
    private final Path configDirectory = Paths.get("/etc/pas/conf.d");
    private final Path mainConfigFile = Paths.get("/etc/pas/pas.conf");
    private final ApplicationEventPublisher eventPublisher;
    private final ConfigurationLoader configurationLoader;
    
    @PostConstruct
    public void startWatching() throws IOException {
        watchService = FileSystems.getDefault().newWatchService();
        
        // Watch main config file directory
        mainConfigFile.getParent().register(watchService, ENTRY_MODIFY);
        
        // Watch modular config directory
        configDirectory.register(watchService, ENTRY_MODIFY, ENTRY_CREATE, ENTRY_DELETE);
        
        // Start watching in background thread
        CompletableFuture.runAsync(this::watchForChanges);
    }
    
    private void watchForChanges() {
        while (true) {
            try {
                WatchKey key = watchService.take();
                
                for (WatchEvent<?> event : key.pollEvents()) {
                    WatchEvent.Kind<?> kind = event.kind();
                    Path changedFile = (Path) event.context();
                    
                    if (kind == ENTRY_MODIFY && isConfigurationFile(changedFile)) {
                        log.info("Configuration file changed: {}", changedFile);
                        reloadConfiguration();
                    }
                }
                
                key.reset();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }
    
    private void reloadConfiguration() {
        try {
            // Load and validate new configuration
            Configuration newConfig = configurationLoader.loadConfiguration();
            
            // Publish configuration change event
            eventPublisher.publishEvent(new ConfigurationChangedEvent(newConfig));
            
            log.info("Configuration reloaded successfully");
        } catch (Exception e) {
            log.error("Failed to reload configuration", e);
            // Could send alert to operations team
        }
    }
}
```

### Configuration Change Handling
```java
@EventListener
public class ConfigurationChangeHandler {
    
    @EventListener
    public void handleConfigurationChange(ConfigurationChangedEvent event) {
        Configuration newConfig = event.getConfiguration();
        
        // Update component configurations
        updateServerConfiguration(newConfig.getServer());
        updateAuditConfiguration(newConfig.getAudit());
        updateGatekeeperConfiguration(newConfig.getGatekeeper());
        updateRssProtocolConfiguration(newConfig.getRssProtocol());
        
        log.info("Configuration changes applied successfully");
    }
    
    private void updateServerConfiguration(ServerConfig serverConfig) {
        // Update server settings that can be changed without restart
        if (serverConfig.getDatabase().getPoolSize() != currentPoolSize) {
            dataSource.setMaximumPoolSize(serverConfig.getDatabase().getPoolSize());
        }
        
        // Update monitoring settings
        if (serverConfig.getMonitoring().isEnabled() != monitoringEnabled) {
            if (serverConfig.getMonitoring().isEnabled()) {
                monitoringService.start();
            } else {
                monitoringService.stop();
            }
        }
    }
    
    private void updateAuditConfiguration(AuditConfig auditConfig) {
        // Update audit settings
        auditService.updateConfiguration(auditConfig);
        
        // Update retention policy
        auditArchivalService.updateRetentionPolicy(auditConfig.getRetention());
    }
}
```

## RPM Package Integration

### RPM Spec File Configuration Handling
```spec
# pas.spec - RPM specification
%pre
# Backup existing configuration before upgrade
if [ $1 -gt 1 ]; then
    # This is an upgrade
    /usr/bin/pas-configure backup
fi

%post
# Post-installation configuration setup
if [ $1 -eq 1 ]; then
    # This is a fresh installation
    echo "Initializing PAS configuration..."
    /usr/bin/pas-configure init production
    
    # Create pas user and group
    getent group pas >/dev/null || groupadd -r pas
    getent passwd pas >/dev/null || useradd -r -g pas -d /var/lib/pas -s /sbin/nologin pas
    
    # Set up configuration permissions
    chown -R root:pas /etc/pas/
    chmod -R 640 /etc/pas/*.conf
    chmod 755 /etc/pas/conf.d/
    chmod +x /usr/bin/pas-configure
    chmod +x /usr/bin/pas-config-validator
fi

# Validate configuration after install/upgrade
echo "Validating PAS configuration..."
if ! /usr/bin/pas-config-validator; then
    echo "WARNING: Configuration validation failed. Please check /var/log/pas/config-validation.log"
    echo "Run 'pas-configure validate' to see detailed validation errors"
fi

# Enable and start services
systemctl daemon-reload
systemctl enable pas-server
systemctl enable pas-gatekeeper

%postun
# Handle uninstall vs upgrade
if [ $1 -eq 0 ]; then
    # This is an uninstall
    echo "Removing PAS configuration..."
    rm -rf /etc/pas/
    userdel pas 2>/dev/null || true
    groupdel pas 2>/dev/null || true
else
    # This is an upgrade - preserve configuration
    echo "Configuration preserved during upgrade"
fi
```

## Implementation Plan

### Phase 1: Configuration Infrastructure (Weeks 1-2)
1. Design hierarchical configuration structure
2. Implement configuration parser and validator
3. Create configuration management scripts
4. Build configuration schemas

### Phase 2: Hot Reload Implementation (Weeks 2-3)
1. Implement file watching service
2. Create configuration change handlers
3. Update PAS components for hot reload
4. Test configuration changes without restart

### Phase 3: RPM Integration (Weeks 3-4)
1. Update RPM spec files for configuration handling
2. Create configuration templates for environments
3. Implement upgrade/downgrade configuration handling
4. Test RPM install/upgrade scenarios

### Phase 4: Production Readiness (Weeks 4-5)
1. Documentation and user guides
2. Configuration migration tools
3. Monitoring and alerting for config changes
4. Customer training materials

## Success Metrics

- **Configuration Errors**: Reduce configuration-related errors by 80%
- **Deployment Time**: Reduce configuration setup time by 60%
- **Hot Reload**: 95% of configuration changes applied without restart
- **Validation Coverage**: 100% of configuration parameters validated
- **Customer Satisfaction**: Simplified configuration management

This configuration management approach provides robust, validated, and maintainable configuration handling optimized for RPM-based deployment while supporting customer customization and operational requirements.
