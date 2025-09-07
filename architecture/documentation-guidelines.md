# Documentation Guidelines for PAS Architecture

## Core Principle: Present Current State Cleanly

Documentation should present the current state of the system as authoritative truth, not as a journey of discovery. Git maintains the historical record - documentation should focus on clarity and utility for current readers.

## Language to Avoid

### Historical Discovery Language
❌ **Avoid these phrases:**
- "After analysis, we discovered..."
- "Further investigation revealed..."
- "Newly discovered complexity..."
- "Critical findings show..."
- "Deep-dive analysis indicates..."
- "This analysis incorporates..."
- "We found that..."
- "Investigation shows..."

### Temporal Qualification Language
❌ **Avoid these phrases:**
- "Initially we thought..."
- "Previous assessment missed..."
- "Updated understanding shows..."
- "Revised analysis indicates..."
- "Current findings suggest..."

### Uncertainty and Hedging Language
❌ **Avoid these phrases:**
- "It appears that..."
- "Seems to indicate..."
- "Suggests that..."
- "May be the case..."
- "Potentially shows..."

## Language to Use

### Direct Statements
✅ **Use these approaches:**
- "The audit system performs..."
- "The race condition occurs because..."
- "PCAP is unsuitable because..."
- "The system requires..."
- "Performance characteristics include..."

### Present Tense Authority
✅ **Write as current truth:**
- "The system includes X, Y, and Z"
- "Performance requirements are..."
- "The architecture consists of..."
- "Integration points include..."

### Clear Problem Statements
✅ **State problems directly:**
- "The audit linking system suffers from a race condition"
- "PCAP captures network packets while audit requires application semantics"
- "The current coupling creates development bottlenecks"

## Document Structure Guidelines

### Executive Summaries
- Lead with clear recommendation
- State rationale directly
- Avoid discovery narrative

**Example:**
```markdown
## Executive Summary

**Recommendation**: Reject PCAP-based audit capture.

**Rationale**: PCAP captures network packets while PAS audit requires application semantics.
```

### Problem Statements
- State the problem as current reality
- Describe impact without discovery language
- Focus on what needs to be solved

**Example:**
```markdown
## Problem Statement

The audit system is tightly coupled with Parent through Spring configuration, creating development bottlenecks. The system performs real-time protocol manipulation with credential injection.
```

### Technical Analysis
- Present findings as facts
- Use technical precision
- Avoid narrative of how information was obtained

**Example:**
```markdown
## Credential Injection Architecture

The audit system modifies protocol streams in real-time:
- SSH uses MITM proxy with key injection
- RDP injects credentials during X.224 connection phase
- VNC computes DES responses using actual passwords
```

## Revision Guidelines

### When Updating Documentation
1. **Remove discovery language** from existing content
2. **Rewrite as current state** without historical context
3. **Preserve technical accuracy** while improving clarity
4. **Let git track changes** - don't document the documentation process

### Version Control Philosophy
- **Git commits** record what changed and when
- **Documentation** presents current authoritative state
- **No need** to document the evolution within the documents themselves

### Review Checklist
Before publishing documentation, verify:
- [ ] No "discovery" or "analysis" language
- [ ] No temporal qualifiers about previous understanding
- [ ] Direct statements about current system state
- [ ] Clear problem statements without narrative
- [ ] Technical facts presented authoritatively

## Examples of Good vs Bad Documentation

### Bad Example
```markdown
After comprehensive analysis of the audit system, we discovered that the complexity far exceeds initial assessment. Further investigation revealed that the audit system performs real-time protocol manipulation with credential injection, not simple byte recording. This analysis incorporates critical findings about protocol awareness.
```

### Good Example
```markdown
The audit system performs real-time protocol manipulation with credential injection, not simple byte recording. The system includes protocol awareness, credential injection requirements, and a persistent audit linking race condition.
```

### Bad Example
```markdown
**Discovery**: Audit system performs real-time protocol manipulation, not passive recording:
- **Credential injection**: Active modification of SSH, RDP, VNC protocol streams

**Implication**: Audit separation must preserve protocol manipulation capabilities.
```

### Good Example
```markdown
The audit system performs real-time protocol manipulation, not passive recording:
- **Credential injection**: Active modification of SSH, RDP, VNC protocol streams

Audit separation must preserve protocol manipulation capabilities.
```

## Rationale

### Why This Approach Works
1. **Clarity**: Readers get authoritative information without narrative noise
2. **Maintainability**: Updates focus on content, not discovery stories
3. **Professionalism**: Documentation reads as expert knowledge, not investigation notes
4. **Efficiency**: Faster to read and understand current state

### What Git Provides
- **Historical context**: Commit messages and diffs show evolution
- **Change tracking**: When and why documentation changed
- **Blame/annotation**: Who made specific changes and when
- **Branching**: Experimental documentation approaches

### Division of Responsibility
- **Git**: Historical record, change tracking, evolution narrative
- **Documentation**: Current authoritative state, clear technical facts
- **Comments**: Implementation details and rationale in code
- **Commit messages**: Context for why changes were made

This approach ensures documentation serves its primary purpose: clearly communicating the current state of the system to people who need to understand and work with it.
