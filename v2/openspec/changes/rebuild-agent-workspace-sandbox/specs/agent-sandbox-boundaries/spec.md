## Purpose

Define and verify filesystem, network, command-transport, runtime-file, and future interactive boundaries for pure sandbox and VM-backed agent execution.

## ADDED Requirements

### Requirement: Project mount boundary

The system SHALL preserve the existing project directory mount and SHALL expose no host path unless the execution mode explicitly mounts it.

#### Scenario: Project access

- **WHEN** an agent runs in either execution mode
- **THEN** the current project path is available with its configured write behavior

#### Scenario: Unmounted host path

- **WHEN** an agent accesses an unrelated host path
- **THEN** the path is unavailable inside the agent sandbox

### Requirement: Inner agent network sharing

The system SHALL run agent sandboxes with the parent agent network namespace shared.

#### Scenario: Nested agent networking

- **WHEN** an agent starts a sibling subagent
- **THEN** both agents can use the same network namespace and configured network access

### Requirement: Isolated outer networking

The system SHALL preserve isolated outer networking with explicit bidirectional TCP forwarding.

#### Scenario: Host connects to sandbox

- **WHEN** a configured host-to-sandbox forward targets a listening agent port
- **THEN** the host can connect through the configured host port

#### Scenario: Sandbox connects to host

- **WHEN** a configured sandbox-to-host forward targets a listening host port
- **THEN** the agent can connect through the configured sandbox port

#### Scenario: Unconfigured port

- **WHEN** no forward exists for a port
- **THEN** the port is not reachable across the outer boundary

### Requirement: Overlay persistence

The system SHALL persist copy-on-write upper and work state for each named workspace.

#### Scenario: Persist writes

- **WHEN** an agent writes a file in a named workspace and exits
- **THEN** the file remains available during the next execution of that workspace

#### Scenario: Preserve lower project

- **WHEN** an agent modifies or deletes a lower-layer project file in a named workspace
- **THEN** the main project file remains unchanged while the workspace records the change

### Requirement: Bounded VM command transport

The system SHALL pass long VM startup payloads through a temporary runtime script rather than embedding the full payload in the `chroot_vm` argument list.

#### Scenario: Long command

- **WHEN** the command payload exceeds safe argument or shell-string limits
- **THEN** the VM executes an equivalent temporary script and returns the command status

### Requirement: Runtime diagnostics isolation

The system SHALL store VM logs, status files, generated scripts, forwarding helpers, and control sockets outside project directories.

#### Scenario: Clean project tree

- **WHEN** an agent runs in VM mode
- **THEN** no `.agent_vm` runtime directory is created in the project

#### Scenario: Runtime cleanup

- **WHEN** an agent run exits
- **THEN** transient runtime files are removed while persistent workspace data remains

### Requirement: Future VM login interface

The VM runner SHALL reserve a host-accessible runtime interface for later interactive guest login without exposing arbitrary host paths.

#### Scenario: Runtime interface allocation

- **WHEN** a VM starts
- **THEN** its runtime directory contains an addressable control or console endpoint for future attach support

### Requirement: Boundary test coverage

The system SHALL provide automated tests for every supported execution mode and every configured exposure direction.

#### Scenario: Pure sandbox boundary suite

- **WHEN** boundary tests run in pure sandbox mode
- **THEN** tests verify mounts, inaccessible host paths, nested bwrap execution, forwarding, and workspace persistence

#### Scenario: VM boundary suite

- **WHEN** boundary tests run in `chroot_vm` mode
- **THEN** tests verify the same behavior across the VM boundary and verify runtime artifact placement
