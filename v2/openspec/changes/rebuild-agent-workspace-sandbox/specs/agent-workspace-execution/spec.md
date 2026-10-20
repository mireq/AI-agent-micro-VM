## Purpose

Provide lightweight persistent project workspaces and a single command path for running agents and sibling subagents inside rootless sandboxes.

## ADDED Requirements

### Requirement: Existing configuration compatibility

The system SHALL preserve existing `DEFAULT_AGENT_CONFIG` mount syntax and existing project `config.toml` network syntax.

#### Scenario: Initialize agent configuration

- **WHEN** `~/.agent/config.toml` does not exist
- **THEN** the system creates it with existing `DEFAULT_AGENT_CONFIG` content

#### Scenario: Read configured mounts

- **WHEN** an agent starts
- **THEN** the launcher applies valid `[[mount]]` entries from existing agent and project configuration files

### Requirement: Project workspace registry

The system SHALL store per-project workspace metadata below `~/.agent/workdirs/` using a readable stable project identifier.

#### Scenario: Resolve project registry

- **WHEN** an agent command starts from a project directory
- **THEN** the system resolves one registry directory for that normalized project path and stores its metadata there

#### Scenario: Preserve readable project identity

- **WHEN** two project paths have different normalized identities
- **THEN** their registry directory names remain distinguishable and collision-safe

### Requirement: Main workspace

The system SHALL expose `main` as the current project directory without copying or overlaying its files.

#### Scenario: Execute in main

- **WHEN** the command omits `--workspace`
- **THEN** the command runs with the current project directory as its working directory

### Requirement: Persistent sibling workspaces

The system SHALL create named sibling workspaces as persistent copy-on-write views of the project without copying project contents.

#### Scenario: Create workspace on first use

- **WHEN** `agent_workspace exec --workspace feature-a -- command` targets a missing workspace
- **THEN** the system creates `feature-a` and runs the command against its writable copy-on-write view

#### Scenario: Reuse workspace

- **WHEN** a later command targets existing `feature-a`
- **THEN** the system reuses its persisted changes

#### Scenario: Flat workspace names

- **WHEN** an agent creates a workspace while running in another workspace
- **THEN** the new workspace is a sibling under the project registry and is not nested under the current workspace

### Requirement: Workspace visibility

The system SHALL make all project sibling workspaces available inside each agent at `/agent/workspaces`.

#### Scenario: Read sibling workspace

- **WHEN** an agent lists `/agent/workspaces`
- **THEN** it can see every existing sibling workspace, including workspaces created by other agents

#### Scenario: Modify sibling workspace

- **WHEN** an agent runs `agent_workspace exec --workspace other -- command`
- **THEN** the command runs against the selected sibling workspace and persists its changes

### Requirement: Agent execution

The system SHALL run every agent command through rootless `bwrap` in both pure sandbox mode and `chroot_vm` mode.

#### Scenario: Pure sandbox execution

- **WHEN** the host selects pure sandbox mode
- **THEN** the host starts one rootless `bwrap` sandbox and agent commands run inside it

#### Scenario: VM execution

- **WHEN** the host selects `chroot_vm` mode
- **THEN** the VM starts first and agent commands run in one rootless `bwrap` sandbox inside the VM

### Requirement: Focused command interface

The system SHALL support `agent_workspace exec --workspace NAME -- COMMAND [ARGS...]` and SHALL remove obsolete workspace process, activation, and lifecycle commands from the new command surface.

#### Scenario: Preserve command arguments

- **WHEN** an agent command contains spaces, quotes, newlines, or shell metacharacters
- **THEN** the target command receives the original argument vector without shell reinterpretation

#### Scenario: Unknown workspace

- **WHEN** a workspace name is invalid or cannot be created
- **THEN** the command fails with a nonzero status and an actionable error
