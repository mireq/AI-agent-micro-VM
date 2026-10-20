## 1. Workspace registry and overlay storage

- [x] 1.1 Create new `agent_workspace_v2` executable with normalized readable slug generation and collision suffixes; verify equivalent paths resolve identically and distinct paths do not collide.
- [x] 1.2 Store registry metadata under `~/.agent/workdirs/<slug>/` and preserve the authoritative project path; verify no project-local configuration directory is created.
- [x] 1.3 Implement flat named workspace creation with persistent `upper` and `work` directories; verify missing workspace is created and existing workspace state is reused.
- [x] 1.4 Implement rootless bwrap native overlay mounting; verify a write persists in the workspace and does not modify the lower project.
- [x] 1.5 Add the prerequisite probe for nested rootless overlay mounting in pure and VM modes; verify unsupported environments fail clearly without host-side fallback.

## 2. Focused command and nested execution

- [x] 2.1 Implement `agent_workspace_v2 exec --workspace NAME -- COMMAND [ARGS...]` without modifying `agent_workspace`; verify omitted workspace selects `main`.
- [x] 2.2 Mount the complete sibling workspace registry at `/agent/workspaces`; verify every sibling is visible from each agent.
- [x] 2.3 Make workspace selection flat and non-recursive; verify an agent-created workspace appears beside the current workspace.
- [ ] 2.4 Run every selected workspace command through rootless `bwrap` in pure and VM modes; verify nested commands can create and execute sibling agents.
- [x] 2.5 Keep the new `agent_workspace_v2` interface limited to `exec`; verify obsolete process, activation, deactivation, and explicit lifecycle commands are unsupported.
- [x] 2.6 Preserve command argument vectors without shell reinterpretation; verify spaces, quotes, newlines, and metacharacters reach the target unchanged.

## 3. Outer sandbox and network integration

- [x] 3.1 Preserve project mounting for pure `bwrap` and VM launch paths; verify host-corresponding project path and no `/dev/kvm` inside agent sandbox.
- [x] 3.2 Keep agent bwraps on the parent network namespace with `--share-net`; verify sibling agents can communicate over the shared network.
- [x] 3.3 Preserve isolated pure-mode networking through `pasta`; verify unconfigured ports remain unreachable.
- [ ] 3.4 Preserve VM networking through `passt`; verify unconfigured ports remain unreachable inside the VM.
- [ ] 3.5 Test host-to-sandbox TCP forwarding in pure and VM modes; verify configured host ports reach agent listeners.
- [ ] 3.6 Test sandbox-to-host TCP forwarding in pure and VM modes; verify configured agent ports reach host listeners.
- [ ] 3.7 Verify forwarding helpers do not expose unrelated host paths or host ports.

## 4. VM command transport and runtime artifacts

- [ ] 4.1 Generate short-lived command scripts under runtime storage and pass short script paths to `chroot_vm`; verify commands exceeding shell argument limits execute successfully.
- [ ] 4.2 Move VM logs, status files, generated scripts, forwarding wrappers, and future control sockets under `${XDG_RUNTIME_DIR}` with a `/tmp` fallback; verify project trees contain no `.agent_vm` directory.
- [ ] 4.3 Apply restrictive runtime directory permissions and cleanup; verify transient files disappear after exit while workspace upper state remains.
- [ ] 4.4 Reserve runtime socket allocation for future VM console or control attachment; verify each VM run receives a unique endpoint path without exposing arbitrary host paths.

## 5. Boundary and regression tests

- [ ] 5.1 Add pure-mode filesystem boundary tests; verify project and `/agent/workspaces` are available while unrelated host paths and forbidden devices are unavailable.
- [ ] 5.2 Add VM-mode filesystem boundary tests with prerequisite-based skipping; verify the same contract across `chroot_vm`.
- [ ] 5.3 Add overlay persistence and lower-layer integrity tests; verify writes, deletes, and sibling workspace visibility.
- [ ] 5.4 Add nested-agent tests; verify flat workspace creation, shared network behavior, and persistent sibling changes.
- [ ] 5.5 Add long-command transport tests; verify exact command arguments and exit status in both execution modes.
- [ ] 5.6 Add runtime artifact placement tests; verify logs and helper files stay outside project directories.
- [ ] 5.7 Run the complete pure-mode suite and the VM-capable suite, recording explicit skips for unavailable KVM/libkrun prerequisites.
