#!/usr/bin/env python3
"""
Generate proposed separated MITM + Audit architecture diagram
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

# Set up the figure
fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 12)
ax.set_ylim(0, 10)
ax.axis('off')

# Define colors
rust_color = '#CE422B'
java_color = '#FF6B35'
ipc_color = '#96CEB4'
web_color = '#45B7D1'
unchanged_color = '#4ECDC4'

# Title
ax.text(6, 9.5, 'Proposed Separated Architecture: Rust MITM + Java Audit', 
        fontsize=18, fontweight='bold', ha='center')

# Rust MITM Process (Left side)
rust_box = FancyBboxPatch((0.5, 5), 4.5, 3.5, 
                         boxstyle="round,pad=0.1", 
                         facecolor=rust_color, 
                         edgecolor='black', 
                         linewidth=2, 
                         alpha=0.3)
ax.add_patch(rust_box)
ax.text(2.75, 8.2, 'Rust MITM Process', fontsize=16, fontweight='bold', ha='center', color='white')

# Rust components
rust_components = [
    ('SSH MITM\n(russh)', 1.5, 7.5),
    ('RDP MITM\n(IronRDP)', 4, 7.5),
    ('WebSocket\nStreaming', 1.5, 6.5),
    ('Credential Lookup\nvia IPC', 4, 6.5),
    ('Protocol State\nManagement', 2.75, 5.5)
]

for comp, x, y in rust_components:
    comp_box = FancyBboxPatch((x-0.4, y-0.25), 0.8, 0.5, 
                             boxstyle="round,pad=0.02", 
                             facecolor='white', 
                             edgecolor='black', 
                             linewidth=0.5)
    ax.add_patch(comp_box)
    ax.text(x, y, comp, fontsize=9, ha='center', va='center')

# Java Audit Process (Right side)
java_box = FancyBboxPatch((7, 5), 4.5, 3.5, 
                         boxstyle="round,pad=0.1", 
                         facecolor=java_color, 
                         edgecolor='black', 
                         linewidth=2, 
                         alpha=0.3)
ax.add_patch(java_box)
ax.text(9.25, 8.2, 'Java Audit Process', fontsize=16, fontweight='bold', ha='center')

# Java components (UNCHANGED)
java_components = [
    ('AuditFile.java\n(UNCHANGED)', 8, 7.5),
    ('DatabaseAuditWriter.java\n(UNCHANGED)', 10.5, 7.5),
    ('TerminalAuditWriter.java\n(UNCHANGED)', 8, 6.5),
    ('GuessingConnectionLinker.java\n(UNCHANGED)', 10.5, 6.5),
    ('CredentialInjectionService.java\n(UNCHANGED)', 9.25, 5.5)
]

for comp, x, y in java_components:
    comp_box = FancyBboxPatch((x-0.4, y-0.25), 0.8, 0.5, 
                             boxstyle="round,pad=0.02", 
                             facecolor=unchanged_color, 
                             edgecolor='black', 
                             linewidth=0.5,
                             alpha=0.8)
    ax.add_patch(comp_box)
    ax.text(x, y, comp.split('\n')[0], fontsize=8, ha='center', va='center')
    ax.text(x, y-0.15, '(UNCHANGED)', fontsize=7, ha='center', va='center', 
            style='italic', color='green', fontweight='bold')

# IPC Interface (Center)
ipc_box = FancyBboxPatch((5.25, 6), 1.5, 2, 
                        boxstyle="round,pad=0.05", 
                        facecolor=ipc_color, 
                        edgecolor='black', 
                        linewidth=2, 
                        alpha=0.8)
ax.add_patch(ipc_box)
ax.text(6, 7.5, 'IPC Interface', fontsize=12, fontweight='bold', ha='center')

ipc_components = [
    'Credential Lookup',
    'Audit Events',
    'Session Lifecycle',
    'WebSocket Data'
]

for i, comp in enumerate(ipc_components):
    ax.text(6, 7.2 - i*0.2, f'• {comp}', fontsize=8, ha='center')

# Bidirectional IPC arrows
ipc_arrow1 = ConnectionPatch((5, 7), (5.25, 7), "data", "data",
                           arrowstyle="->", shrinkA=5, shrinkB=5, 
                           mutation_scale=20, fc="green", ec="green", linewidth=3)
ax.add_artist(ipc_arrow1)

ipc_arrow2 = ConnectionPatch((6.75, 7), (7, 7), "data", "data",
                           arrowstyle="->", shrinkA=5, shrinkB=5, 
                           mutation_scale=20, fc="green", ec="green", linewidth=3)
ax.add_artist(ipc_arrow2)

ipc_arrow3 = ConnectionPatch((7, 6.5), (6.75, 6.5), "data", "data",
                           arrowstyle="->", shrinkA=5, shrinkB=5, 
                           mutation_scale=20, fc="green", ec="green", linewidth=3)
ax.add_artist(ipc_arrow3)

ipc_arrow4 = ConnectionPatch((5.25, 6.5), (5, 6.5), "data", "data",
                           arrowstyle="->", shrinkA=5, shrinkB=5, 
                           mutation_scale=20, fc="green", ec="green", linewidth=3)
ax.add_artist(ipc_arrow4)

# Client connections
ax.text(0.2, 7, 'Native\nClients', fontsize=10, ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.2", facecolor='lightblue'))

ax.text(0.2, 5.5, 'Web\nClients', fontsize=10, ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.2", facecolor=web_color))

# Client arrows to Rust MITM
client_arrow1 = ConnectionPatch((0.8, 7), (0.5, 7), "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5, 
                              mutation_scale=20, fc="blue", ec="blue")
ax.add_artist(client_arrow1)

client_arrow2 = ConnectionPatch((0.8, 5.5), (0.5, 6), "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5, 
                              mutation_scale=20, fc=web_color, ec=web_color)
ax.add_artist(client_arrow2)

# External systems
ax.text(9.25, 4.5, 'Database', fontsize=10, ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.2", facecolor='lightgray'))

ax.text(11, 4.5, 'Audit Files', fontsize=10, ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.2", facecolor='lightgray'))

# Arrows to external systems
db_arrow = ConnectionPatch((9.25, 5), (9.25, 4.7), "data", "data",
                          arrowstyle="->", shrinkA=5, shrinkB=5, 
                          mutation_scale=20, fc="gray", ec="gray")
ax.add_artist(db_arrow)

file_arrow = ConnectionPatch((10.5, 5), (11, 4.7), "data", "data",
                           arrowstyle="->", shrinkA=5, shrinkB=5, 
                           mutation_scale=20, fc="gray", ec="gray")
ax.add_artist(file_arrow)

# Benefits annotation
benefits_text = """Benefits of Separated Architecture:
• Loose coupling via IPC interface
• Independent failure domains
• Web client support built-in
• Rust memory safety and performance
• Preserved audit architecture (95% unchanged)
• Minimal risk to existing functionality"""

ax.text(0.5, 3.5, benefits_text, fontsize=11, va='top',
        bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.7))

# Technical details
tech_text = """Technical Implementation:
• IPC: Unix Domain Sockets / Named Pipes
• Serialization: MessagePack (binary)
• Error Handling: Timeout + Retry + Fallback
• Performance: <10ms IPC overhead
• Compatibility: 100% audit format preservation"""

ax.text(6.5, 3.5, tech_text, fontsize=11, va='top',
        bbox=dict(boxstyle="round,pad=0.3", facecolor='lightyellow', alpha=0.7))

# Data flow indicators
ax.text(6, 8.7, '↕ Bidirectional IPC', fontsize=10, ha='center', 
        bbox=dict(boxstyle="round,pad=0.2", facecolor='green', alpha=0.3))

# Process separation indicator
separation_line = ConnectionPatch((5.75, 4.5), (5.75, 8.5), "data", "data",
                                linestyle="--", linewidth=3, color="red", alpha=0.7)
ax.add_artist(separation_line)
ax.text(5.75, 4.2, 'Process Boundary', fontsize=10, ha='center', color='red', fontweight='bold')

plt.tight_layout()
plt.savefig('docs/analysis/proposed-architecture.png', dpi=300, bbox_inches='tight')
plt.close()

print("Proposed architecture diagram saved as: docs/analysis/proposed-architecture.png")
