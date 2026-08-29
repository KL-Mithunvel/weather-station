---
name: prod-vm
description: Rules and protocol for Claude Code when connecting to and operating on production VMs.
---

When the user asks Claude Code to connect to a production VM and perform actions, the following rules apply.

## Connection

- Connections are typically made using `plink` with named saved sessions (e.g., `plink "ERP Kerberos Server" <command>`).
- **Never try to guess** or try to deduce the saved session name or hostname / ip.
- If the saved session name or hostname / ip is not known, ask the user to provide it.

## Machine Identity Verification
Machine Identity Verification
- After every successful plink connection to a production VM, immediately perform identity verification using only existing system state.
- Never proceed with other commands until verification is complete and acceptable.
- Acceptable: The combination of hostname + /etc/machine-id + running containers/services clearly matches the expected machine for that session.

## Announcement

**Make it clear that you are connecting to a production VM, announce the machine name and intent.**

## Command Authorization
- **Rules**:
  - **Every command must be printed before execution**, along with the reason it is being run.
  - **Stick to Authorized Actions only** - Do only the actions that are authorized by the user. Do not try to execute commands that are not explicitly authorized.
  - If a command’s impact is unclear, treat it as Tier 4
- **Tiers**:
All commands must be classified into one of the categories below **before** execution. The agent must state the category and reasoning.
  - **Tier 1 - Diagnostic / read-only commands**: viewing logs, checking processes, disk usage, service status, diagnostic etc. are permitted without explicit authorization. `sudo` with a read-only payload is also permitted.
  - **Tier 2 - Config Change**: Any command that alters machine configuration or files requires explicit user authorization before execution. Authorization may be granted for a single command, a batch of commands, or a class of commands.
  - **Tier 3 - Service Control**: Requires pre-approved class **or** explicit per-command authorization. Common safe operations can be pre-authorized for a session.
  - **Tier 4 - Destructive / High-risk commands**: (e.g., `rm`, `mv` on important paths, database drops/migrations, mass file operations, `fdisk`, `mkfs`) - Fresh explicit approval **every time**, never pre-authorize. Always confirm impact first 

## CRITICAL 
- **Never run commands that could potentially cause credentials to be exfiliated to including the cloud.**

## Logging

Maintain a session log at `~/.claude/logs/prod-vm/<machine-name>.cc.log` on the dev machine (never on the prod VM). Log
each command executed, the reason it was run, and a summary of its output.

## Data / File Downloads

Any files or data downloaded from the session must be listed at the end of the session for proper handling and securing.

## Sub-commands

If the user specifies `clean-logs`, delete all log files under `~/.claude/logs/prod-vm/`.

If the user specifies `help`, display the available sub-commands and a summary of the rules above.
