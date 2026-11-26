# AI-agent-micro-VM

`agent_workspace` runs an AI agent in a sandbox.
The agent sees your project and little else.
It can run in a light sandbox or in a micro VM.

Example numbers (`exec -- echo hi`, 4-core laptop):

| Mode | Start and exit |
| --- | --- |
| `--shared-network` | 55 ms |
| default (isolated network) | 80 ms |
| `--vm --shared-network` | 200 ms |
| `--vm` | 240 ms |

An idle VM uses about 200 MB of host RAM.
A long Codex session in a VM used about 1.1 GB.
The VM sees 4 CPUs and 3.9 GB RAM.
Memory the VM frees goes back to the host.

## Requirements

Always:

- Python 3.11+
- `bwrap`
- `pasta` (from the passt package, for isolated network)
- `/dev/net/tun`

For `--vm`:

- `chroot_vm` on `PATH` (libkrun based)
- Access to `/dev/kvm`
- `/usr/bin/passt`
- `/usr/bin/setpriv`
- `ip` and `socat` (used inside the VM for port rules)
- `fuse-overlayfs`, `fusermount3` and `/dev/fuse` (for `--vm --workspace`)

Check that `chroot_vm` works:

```bash
chroot_vm / /bin/echo ok
```

## Usage

Run commands from your project directory.

```bash
agent_workspace shell                  # your shell in the sandbox
agent_workspace exec -- ls -la         # one command
agent_workspace exec --vm -- ls -la    # one command in a micro VM
agent_workspace configure              # edit project config
```

`shell` and `exec` accept these options:

- `--vm`: run in a micro VM.
- `--shared-network`: use the host network. No network isolation.
- `--workspace NAME`: work on a copy of the project. See below.

## What the agent sees

- The project directory, writable, at its real path.
- An empty `/tmp`.
- Paths you mount in config.
- `agent_workspace` itself, so the agent can start sub-workspaces.

Everything else is hidden.
The environment is cleared.
Only `HOME`, `PATH`, `USER`, `SHELL`, `LANG`, `TERM` and similar basics pass through.

## Workspaces

`--workspace NAME` gives the agent a private copy of the project.
The agent sees the project as usual.
Its changes are stored separately.
Your project files stay untouched.

```bash
agent_workspace exec --workspace review -- my-agent
```

Changes land in:

```text
~/.agent/workdirs/<project>/workspaces/review/upper/
```

Names may use letters, digits, `.`, `_` and `-`.

## Configuration

Two config files are merged.
The global file comes first, the project file second.

```text
~/.agent/config.toml                       # global
~/.agent/workdirs/<project>/config.toml    # project
```

`<project>` is the project path with dashes plus a short hash.
For example: `~-src-myapp-1a2b3c4d`.

The global file is created on first run.
It mounts system directories read-only.
The project file starts empty.

Set `AGENT_HOME` to use another directory than `~/.agent`.

### Mounts

```toml
[[mount]]
flag = "r"          # read-only
src = "/usr"
dst = "/usr"

[[mount]]
flag = "w"          # writable
src = "/home/user/.agent/npm"
dst = "/home/user/.npm"

[[mount]]
flag = "o"          # writable, changes vanish on exit
src = "/home/user/.gitconfig.d"
dst = "/home/user/.gitconfig.d"
```

Paths must be absolute.
Inside a read-only mount, like `/opt`, the destination must already exist.
Missing source paths are skipped.

### Environment

```toml
[env]
NPM_CONFIG_USERCONFIG = "/home/user/.npmrc"
CI = true           # becomes "1"
```

Values may be strings, numbers or booleans.
Project values override global values.

### Network

By default the network is isolated:

- Internet works.
- The agent cannot reach the host. Not localhost, not the host's LAN address.
- The host cannot reach the agent.

Open single TCP ports in the project config:

```toml
# Agent connects to 127.0.0.1:3306, reaches host 127.0.0.1:3306.
[[net]]
allow = "sandbox_connect_host"
host_port = 3306
sandbox_port = 3306

# Host connects to 127.0.0.1:8080, reaches agent port 80.
[[net]]
allow = "host_connect_sandbox"
host_port = 8080
sandbox_port = 80
```

Each rule opens one port in one direction.
All other ports stay closed, both ways.
Forwarded ports listen on host `127.0.0.1` only. Your LAN cannot reach them.
This works the same with and without `--vm`.
Only TCP is supported.

## Example: Codex in a VM

Install `codex-acp` into `~/.npm/bin/codex-acp`.
Copy the example config:

```bash
mkdir -p ~/.agent
cp example_dot_agent/config.toml ~/.agent/config.toml
cp example_dot_agent/npmrc ~/.agent/npmrc
```

Replace `/home/user` with your home directory in `~/.agent/config.toml`.
Then run [example-codex-acp_vm](example-codex-acp_vm):

```bash
agent_workspace exec --vm -- "$HOME/.npm/bin/codex-acp" "$@"
```

Neovim sample: [example_agentic_nvim_config.lua](example_agentic_nvim_config.lua).

## Security notes

- `--shared-network` removes the network boundary.
- A forwarded port gives the agent full access to that service.
- `w` mounts are writable by the agent.
- The agent sees its configs read-only. It cannot change its own mounts or ports.
