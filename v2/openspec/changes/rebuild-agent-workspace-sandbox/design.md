## Context

The current workspace tool already mounts the current project directory and supports pure `bwrap` and `chroot_vm` paths. Pure sandbox networking uses `pasta`; VM networking uses `passt` with explicit host-to-sandbox and sandbox-to-host forwarding. VM command execution currently builds a long shell command inline, and VM logs/status/helper files default to `<project>/.agent_vm`. This change adds a new executable, `agent_workspace_v2`, without modifying the existing workspace tool.

The new command runs inside one rootless `bwrap` in pure mode, or inside one rootless `bwrap` started by `chroot_vm` in VM mode.

## Goals / Non-Goals

**Goals:**

- Keep current project mount behavior.
- Provide flat persistent sibling workspaces without copying project files.
- Make all sibling workspaces visible at `/agent/workspaces`.
- Preserve pure sandbox mode, VM mode, isolated networking, and both forwarding directions.
- Make nested agents share their parent network namespace.
- Keep runtime artifacts out of project directories.
- Test positive exposure and negative isolation behavior.
- Reserve a runtime path for later VM console or control attachment.

**Non-Goals:**

- Add safety policy inside the VM beyond the rootless `bwrap` boundary.
- Add workspace process listing, activation, deactivation, or explicit removal commands.
- Copy project trees into workspace directories.
- Make subworkspaces recursive.
- Preserve existing configuration file syntax and default mount configuration.
- Implement persistent VM lifecycle or completed interactive login in this change.
- Modify the existing `agent_workspace` executable.
- Expose `/dev/kvm` to any new agent sandbox.

## Decisions

### One focused workspace command

Use `agent_workspace exec --workspace NAME -- COMMAND [ARGS...]`. Omitted workspace selects `main`. A missing named workspace is created on demand. The command surface drops unrelated lifecycle commands.

The workspace manager receives the outer project path and workspace registry path through the existing execution context. It does not need a new configuration format.

Initialize `~/.agent/config.toml` from the existing `DEFAULT_AGENT_CONFIG` when absent. Read its `[[mount]]` entries unchanged. Keep each project registry `config.toml` compatible with the existing `net` table format.

### Readable stable project directory names

Replace hash-only project registry names with a filesystem-safe readable slug containing a collision suffix. Normalize the project path before slugging. Keep `.path` as the authoritative original path. Use the `vim.fs.slug()` shape as the naming model, but do not require Neovim at runtime: implement the equivalent normalization, readable sanitization, length bound, and short hash behavior in the workspace tool.

### Overlay workspaces inside agent `bwrap`

Each named workspace uses bwrap native overlay mounting with the current project as lower layer and persistent `upper` and `work` directories. The overlay mount target is `/agent/workspaces/<name>`.

The launcher exposes the project and complete workspace registry to one rootless `bwrap` process in pure mode. That process performs overlay mounting inside its user and mount namespaces. VM mode adds `chroot_vm` outside that `bwrap`.

Alternative rejected: host-side overlay mounts. They create host mount state, complicate cleanup, and violate the requirement that mounting happen inside the sandbox.

The implementation must use bwrap native overlay mounting. This avoids `fuse-overlayfs` requiring a setuid helper after bwrap enables `no_new_privs`.

### Two-level sandbox execution

Pure mode is:

```text
host -> agent_workspace -> bwrap
```

VM mode is:

```text
host -> bwrap -> chroot_vm -> agent_workspace -> bwrap
```

The new executable is `agent_workspace_v2`. VM mode uses a host-side bwrap bootstrap that provides KVM to `chroot_vm`; inner agent bwrap receives a fresh `/dev` without `/dev/kvm`.

Nested agents force `--share-net`, so sibling agents share their parent agent network namespace. The top-level bwrap retains current network isolation and forwarding behavior.

### Preserve current network forwarding model

Pure mode continues using `pasta` to connect an isolated outer network namespace. VM mode continues using `passt` through the guest network path. Forward rules remain directional:

- host-to-sandbox: host port to agent port
- sandbox-to-host: agent port to host port

Forwarding configuration remains outside the agent workspace command. Nested agents inherit the already-configured namespace and do not create another network bridge.

### Script-based VM command transport

Generate a short-lived command script under runtime storage. For VM mode, stream a short bootstrap command into `chroot_vm`; the bootstrap recreates the command script inside guest `/tmp`. Preserve the command argument vector through shell quoting.

This avoids `ARG_MAX` and shell-string failures while keeping command execution semantics unchanged.

### Runtime artifact location

Use `${XDG_RUNTIME_DIR}/agent_workspace/<project-slug>/<run-id>/`, falling back to `/tmp/agent_workspace-<uid>/...`. Store logs, status files, command scripts, forwarding wrappers, and future console/control sockets there. Never create `.agent_vm` inside the project.

Use restrictive permissions for runtime directories. Remove scripts, status files, wrappers, and sockets on exit. Keep diagnostics only for the duration needed by the existing caller, subject to runtime-directory cleanup.

### Future VM attachment

Reserve a runtime socket path and libkrun device integration point for a console or control channel. The first implementation does not add an attach command or keep VMs alive after command exit. The interface must not expose arbitrary host filesystem paths.

### Boundary tests

Use subprocess integration tests. Run the same behavioral suite against pure mode and VM mode when KVM/libkrun dependencies are available. Mark VM-only tests skipped with an explicit reason when the host lacks prerequisites.

Tests assert both allowed and forbidden behavior. They must inspect paths from inside the agent, verify network connections in both directions, verify nested agent sharing, verify overlay persistence, and verify that runtime files never appear in the project.

## Risks / Trade-offs

- [Nested rootless overlay may fail on a guest kernel] -> Add a prerequisite probe and fail clearly; do not fall back to host mounting.
- [A shared workspace registry lets agents alter sibling workspaces] -> Accept this by design; agents operate in one collaboration domain.
- [Runtime cleanup can remove failure diagnostics] -> Keep libkrun logs until the process has returned its result, and preserve only explicitly retained diagnostics outside the project.
- [Readable slugs can collide] -> Append a short hash of the normalized path and test collision handling.
- [VM attach requires libkrun console/vsock support beyond current launcher] -> Reserve paths now and defer persistent VM lifecycle to a later change.
- [Pure mode shares the host kernel] -> Document pure mode as a sandbox mode, while VM mode remains the stronger boundary.

## Migration Plan

1. Add the new command path and compatibility-free workspace registry resolution.
2. Keep existing workspace data readable during transition where possible.
3. Move runtime artifacts to the runtime directory.
4. Remove obsolete command dispatch and project `.agent_vm` creation.
5. Run pure-mode tests first, then VM tests on a KVM-capable host.

Rollback means using the previous launcher and existing project directories. The change must not delete old workspace data automatically.
