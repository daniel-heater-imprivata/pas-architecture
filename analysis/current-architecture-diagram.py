#!/usr/bin/env python3
"""
Generate current monolithic audit system architecture diagram
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

# Set up the figure
fig, ax = plt.subplots(1, 1, figsize=(14, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# Define colors
java_color = '#FF6B35'
mitm_color = '#F7931E'
audit_color = '#4ECDC4'
credential_color = '#45B7D1'
interface_color = '#96CEB4'

# Title
ax.text(5, 9.5, 'Current Monolithic Java Audit System', 
        fontsize=18, fontweight='bold', ha='center')

# Main container - Java Audit System
main_box = FancyBboxPatch((0.5, 1), 9, 7.5, 
                         boxstyle="round,pad=0.1", 
                         facecolor=java_color, 
                         edgecolor='black', 
                         linewidth=2, 
                         alpha=0.3)
ax.add_patch(main_box)
ax.text(5, 8.2, 'Java Audit System', fontsize=16, fontweight='bold', ha='center')

# MITM Proxy Layer
mitm_box = FancyBboxPatch((1, 6), 8, 1.8, 
                         boxstyle="round,pad=0.05", 
                         facecolor=mitm_color, 
                         edgecolor='black', 
                         linewidth=1, 
                         alpha=0.7)
ax.add_patch(mitm_box)
ax.text(5, 7.5, 'MITM Proxy Layer', fontsize=14, fontweight='bold', ha='center')

# MITM components
mitm_components = [
    ('MonitorSSHAudit.java', 1.5, 6.8),
    ('MonitorVNCAudit.java', 3.5, 6.8),
    ('Rdp2ProxyHandler.java', 5.5, 6.8),
    ('SessionInfo.java', 7.5, 6.8)
]

for comp, x, y in mitm_components:
    comp_box = FancyBboxPatch((x-0.4, y-0.15), 0.8, 0.3, 
                             boxstyle="round,pad=0.02", 
                             facecolor='white', 
                             edgecolor='black', 
                             linewidth=0.5)
    ax.add_patch(comp_box)
    ax.text(x, y, comp.split('.')[0], fontsize=8, ha='center', va='center')

# Audit Logging Layer
audit_box = FancyBboxPatch((1, 3.5), 8, 1.8, 
                          boxstyle="round,pad=0.05", 
                          facecolor=audit_color, 
                          edgecolor='black', 
                          linewidth=1, 
                          alpha=0.7)
ax.add_patch(audit_box)
ax.text(5, 5, 'Audit Logging Layer', fontsize=14, fontweight='bold', ha='center')

# Audit components
audit_components = [
    ('AuditFile.java', 1.5, 4.3),
    ('DatabaseAuditWriter.java', 3.5, 4.3),
    ('TerminalAuditWriter.java', 5.5, 4.3),
    ('GuessingConnectionLinker.java', 7.5, 4.3)
]

for comp, x, y in audit_components:
    comp_box = FancyBboxPatch((x-0.4, y-0.15), 0.8, 0.3, 
                             boxstyle="round,pad=0.02", 
                             facecolor='white', 
                             edgecolor='black', 
                             linewidth=0.5)
    ax.add_patch(comp_box)
    ax.text(x, y, comp.split('.')[0], fontsize=8, ha='center', va='center')

# Credential Injection Service
cred_box = FancyBboxPatch((1, 1.5), 8, 1.2, 
                         boxstyle="round,pad=0.05", 
                         facecolor=credential_color, 
                         edgecolor='black', 
                         linewidth=1, 
                         alpha=0.7)
ax.add_patch(cred_box)
ax.text(5, 2.5, 'Credential Injection Service', fontsize=14, fontweight='bold', ha='center')
ax.text(5, 1.9, 'CredentialInjectionService.java (Parent Integration)', fontsize=10, ha='center')

# Connection arrows showing tight coupling
# MITM to Audit
arrow1 = ConnectionPatch((5, 6), (5, 5.3), "data", "data",
                        arrowstyle="->", shrinkA=5, shrinkB=5, 
                        mutation_scale=20, fc="red", ec="red", linewidth=2)
ax.add_artist(arrow1)

# MITM to Credential
arrow2 = ConnectionPatch((5, 6), (5, 2.7), "data", "data",
                        arrowstyle="->", shrinkA=5, shrinkB=5, 
                        mutation_scale=20, fc="red", ec="red", linewidth=2)
ax.add_artist(arrow2)

# Audit to Credential
arrow3 = ConnectionPatch((5, 3.5), (5, 2.7), "data", "data",
                        arrowstyle="->", shrinkA=5, shrinkB=5, 
                        mutation_scale=20, fc="red", ec="red", linewidth=2)
ax.add_artist(arrow3)

# Add coupling indicators
ax.text(5.5, 5.7, 'Tight\nCoupling', fontsize=10, ha='center', 
        bbox=dict(boxstyle="round,pad=0.3", facecolor='red', alpha=0.3))

# External connections
ax.text(0.2, 7, 'Client\nConnections', fontsize=10, ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.2", facecolor='lightblue'))

# Arrow from client to MITM
client_arrow = ConnectionPatch((0.8, 7), (1, 7), "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5, 
                              mutation_scale=20, fc="blue", ec="blue")
ax.add_artist(client_arrow)

# Problems annotation
problems_text = """Problems with Current Architecture:
• Tight coupling between MITM and audit
• Single point of failure
• Difficult to add web client support
• Complex threading model
• Data loss risk from coupling"""

ax.text(0.5, 0.5, problems_text, fontsize=10, va='bottom',
        bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.7))

plt.tight_layout()
plt.savefig('docs/analysis/current-architecture.png', dpi=300, bbox_inches='tight')
plt.close()

print("Current architecture diagram saved as: docs/analysis/current-architecture.png")
