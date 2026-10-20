## Why

Current workspace execution mixes host-side workspace preparation, VM execution, and agent execution. It also builds long shell commands inline, stores VM runtime files in project directories, and lacks tests proving filesystem, network, and nested-agent boundaries.

Agents need persistent lightweight workspaces that use overlay storage without copying projects. Agents must run sibling subagents through rootless `bwrap` while preserving both pure sandbox and `chroot_vm` launch modes.

## What Changes

- Replace workspace command surface with a focused `agent_workspace exec --workspace NAME -- COMMAND` flow.
- Keep `main` mapped to current project directory.
- Store project workspace metadata under `~/.agent/workdirs/<readable-slug>/`.
- Create flat persistent subworkspaces with rootless bwrap native overlays; do not copy project files.
- Mount all sibling workspaces inside agents at `/agent/workspaces`.
- Run every agent, including nested agents, through rootless `bwrap`.
- Preserve pure host `bwrap` mode and `chroot_vm` mode.
- Preserve isolated networking and bidirectional explicit TCP forwarding.
- Make nested agents share their parent agent network namespace.
- Pass long VM startup commands through temporary scripts instead of inline command strings.
- Move VM logs, status files, scripts, and helper sockets to runtime temporary storage.
- Reserve a VM console or control interface for later interactive login.
- Add boundary tests for filesystem mounts, workspace persistence, network forwarding, nested agents, command transport, and runtime-file placement.
- Remove obsolete workspace process and lifecycle commands.

## Capabilities

### New Capabilities

- `agent-workspace-execution`: Execute commands in persistent named workspaces through rootless agent sandboxes.
- `agent-sandbox-boundaries`: Define and verify filesystem, network, runtime-file, and nested-agent isolation behavior.

### Modified Capabilities

<!-- No existing capabilities are defined in this repository. -->

## Impact

- Replaces the current workspace CLI implementation and its command dispatch.
- Changes workspace storage from hash-only directories to readable stable slugs.
- Uses bwrap native overlay mounting as the workspace storage mechanism.
- Changes VM command startup to use runtime scripts.
- Changes VM diagnostics location from project `.agent_vm` directories to runtime storage.
- Requires integration tests that execute both pure `bwrap` and `chroot_vm` paths.
- Keeps existing project mounts and network forwarding concepts compatible where possible.
