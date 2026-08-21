# AI-agent-micro-VM

Workspace manager for agent processes. `agent_workspace` creates per-project,
per-branch workspaces under `${AGENT_HOME:-$HOME/.agent}`, then runs commands in
an isolated `bwrap` environment. It can optionally run the command through
`chroot_vm`.

## Requirements

- `bwrap`
- `fuse-overlayfs`
- `bindfs`
- `fusermount3`
- `pasta`
- Python 3.11+

VM mode additionally needs:

- `chroot_vm`
- `/usr/bin/setpriv`
- `/dev/kvm`

## Layout

Global agent config:

```text
${AGENT_HOME:-$HOME/.agent}/config.toml
```

Per-project state:

```text
${AGENT_HOME:-$HOME/.agent}/workdirs/<workdir-hash>/
```

Each project directory contains:

```text
config.toml
.path
scripts/workspace_post_create
scripts/workspace_pre_enter
scripts/workspace_pre_remove
workspaces/<branch>/
```

## Basic Usage

Set the current project branch:

```bash
./agent_workspace branch develop
```

Edit the current project config:

```bash
./agent_workspace configure
```

Run a shell in the current branch workspace:

```bash
./agent_workspace shell
```

Run a command in the current branch workspace:

```bash
./agent_workspace exec -- ls
```

Run through `chroot_vm`:

```bash
./agent_workspace exec --vm -- ls
./agent_workspace shell --vm
```

Create a subagent workspace and run a command:

```bash
./agent_workspace subagent reviewer -- my-agent review
```

List known workspaces:

```bash
./agent_workspace ls
./agent_workspace ls -a
```

Unmount current branch mounts:

```bash
./agent_workspace umount
```

Remove current branch workspace:

```bash
./agent_workspace rm
./agent_workspace rm --yes
```

Mount the current branch workspace over the project path with `bindfs`:

```bash
./agent_workspace activate
./agent_workspace deactivate
```

Use another project directory:

```bash
./agent_workspace --workdir /path/to/project shell
```

## Configuration

`agent_workspace` creates a default global config at:

```text
${AGENT_HOME:-$HOME/.agent}/config.toml
```

The project config starts as:

```toml
branch = "main"
```

Set the branch without opening an editor:

```bash
./agent_workspace configure branch develop
./agent_workspace branch develop
```

`AGENT_BRANCH` overrides the configured branch for the current process.

## Mounts

Mounts are configured with `[[mount]]` entries in TOML:

```toml
[[mount]]
flag = "r"
src = "/usr"
dst = "/usr"

[[mount]]
flag = "w"
src = "/home/user/.codex"
dst = "/home/user/.codex"

[[mount]]
flag = "o"
src = "/path/to/source"
dst = "/path/in/sandbox"
```

Flags:

- `r`: read-only bind
- `w`: read-write bind
- `o`: overlay using `fuse-overlayfs`

The project workdir is mounted as an overlay by default.

Global mounts from `$AGENT_HOME/config.toml` are combined with project mounts
from `workdirs/<hash>/config.toml`.

See [example_dot_agent/config.toml](example_dot_agent/config.toml).

## Activation

`activate` prepares the configured branch workspace, then mounts it with
`bindfs`:

```text
${AGENT_HOME:-$HOME/.agent}/workdirs/<workdir-hash>/workspaces/<branch>/root/<project-path>
```

over the original project path. This lets host tools such as editors keep using
normal project paths while seeing the same workspace files as the agent.

`deactivate` checks `/proc/self/mountinfo` and only unmounts the project path
with `fusermount3` when the top mount matches a workspace branch for this
project.

## Environment

Add environment variables with an `[env]` table:

```toml
[env]
NPM_CONFIG_USERCONFIG = "/home/user/.npmrc"
CI = true
```

`[env]` from the global config is loaded first. `[env]` from the project config
overrides global values.

## Network

Network isolation is enabled by default for `shell`, `exec`, and `subagent`.

Use host networking:

```bash
./agent_workspace shell --shared-network
./agent_workspace exec --shared-network -- curl https://example.com/
```

Allowed port mappings are configured in project `config.toml`:

```toml
[[net]]
allow = "sandbox_connect_host"
host_port = 3306
sandbox_port = 3306

[[net]]
allow = "host_connect_sandbox"
host_port = 8080
sandbox_port = 80
```

Rules:

- `sandbox_connect_host`: sandbox connects to a selected host localhost port
- `host_connect_sandbox`: host connects to a selected sandbox localhost port

Only TCP is supported.

Print network setup details:

```bash
./agent_workspace shell --verbose
```

## Workspace Hooks

These executable scripts are created for every project if missing:

```text
scripts/workspace_post_create
scripts/workspace_pre_enter
scripts/workspace_pre_remove
```

`workspace_post_create` and `workspace_pre_remove` receive:

```text
AGENT_BRANCH
AGENT_WORKSPACE_DIR
```

`workspace_pre_enter` receives the same environment and is also called with the
workspace path and branch as positional arguments for compatibility.

## Example `codex-acp` Setup

Install `codex-acp` under `~/.npm/bin/codex-acp`.

Create agent config from the example:

```bash
mkdir -p ~/.agent
cp example_dot_agent/config.toml ~/.agent/config.toml
cp example_dot_agent/npmrc ~/.agent/npmrc
```

Edit `~/.agent/config.toml` and replace `/home/user` with your home directory.

Run the wrapper:

```bash
./example-codex-acp_vm --help
```

Wrapper contents:

```bash
NODE_PATH="$HOME/.npm"
agent_workspace exec --vm -- "$NODE_PATH/bin/codex-acp" "$@"
```

Neovim ACP sample:
[example_agentic_nvim_config.lua](example_agentic_nvim_config.lua)

## Logs

VM mode writes one log file per run to:

```text
${AGENT_VM_LOG_DIR:-$PWD/.agent_vm}/<timestamp-and-pid>.krun.log
```

`AGENT_VM_LOG_BASENAME` can override the generated log basename.

## Security Notes

- Default networking is isolated.
- `--shared-network` intentionally removes the network boundary.
- Any `w` mount is writable by the sandboxed process.
- VM mode exposes `/dev/kvm` to bwrap, but does not bind the whole host `/dev`.
