# agent_vm

`agent_vm` runs an agent command inside a lightweight `bubblewrap` sandbox while keeping the current working tree mounted and preserving the calling user identity.

This repository includes:

- `agent_vm`: the main launcher
- `example-codex-acp_vm`: wrapper for running `codex-acp` through `agent_vm`
- `example_agentic_nvim_config.lua`: example ACP provider configuration
- `example_dot_agent/`: example `~/.agent` files for binds and npm config

## What It Does

`agent_vm` starts a process with:

- a clean environment created with `env -i`
- the current directory mounted read-write
- host `/usr`, `/bin`, `/lib`, `/lib64`, `/opt`, and `/usr/local` mounted read-only
- `/tmp` as tmpfs
- network access enabled with `--share-net`
- the calling user and group IDs preserved via `setpriv`
- selected `/etc` files mounted read-only for name resolution, TLS, and locale/time support

It also loads optional user-defined bind mounts from `~/.agent/binds` and writes a per-run log file to `.agent_vm/` in the working directory by default.

## Requirements

The launcher expects these host tools to exist:

- `bwrap`
- `/usr/bin/setpriv`
- `chroot_vm`
- standard POSIX user utilities such as `id`, `getent`, `cut`, and `env`

## Usage

Run any command through the sandbox:

```bash
./agent_vm <command> [args...]
```

Example:

```bash
./agent_vm /bin/sh -lc 'pwd && id && env'
```

The sandbox working directory defaults to the current directory. Override it with:

```bash
SANDBOX_WORKDIR=/path/to/project ./agent_vm <command>
```

## Configuration

### `~/.agent/binds`

`agent_vm` reads bind definitions from `${AGENT_HOME:-$HOME/.agent}/binds`.

Supported formats:

```text
w /host/path /guest/path
r /host/path /guest/path
/host/path:/guest/path
```

Rules:

- `w` creates a read-write bind
- `r` creates a read-only bind
- `source:target` is shorthand for a read-write bind
- `~` is expanded against the host user's home directory
- missing source paths are ignored
- invalid lines are skipped with an error message

Example from [example_dot_agent/binds](/home/mirec/a/example_dot_agent/binds):

```text
r /home/user/.agent/npmrc /home/user/.npmrc
w /home/user/.agent/npm /home/user/.npm
w /home/user/.codex /home/user/.codex
```

### Environment Variables

`agent_vm` exposes a small set of knobs:

- `SANDBOX_WORKDIR`: directory mounted and used as the initial working directory
- `AGENT_HOME`: directory that contains the `binds` file; defaults to `$HOME/.agent`
- `AGENT_SANDBOX_INCLUDE_ENV_VARS`: comma-separated list of host env vars to copy into the sandbox; default is `HOME,LOGNAME,PATH,SHELL,USER`
- `AGENT_SANDBOX_OVERRIDE_ENV_VARS`: comma-separated `KEY=VALUE` assignments injected into the sandbox
- `AGENT_VM_LOG_DIR`: directory for `krun` logs; defaults to `<workdir>/.agent_vm`
- `AGENT_VM_LOG_BASENAME`: basename used for the current run log file

Example:

```bash
AGENT_SANDBOX_INCLUDE_ENV_VARS=HOME,PATH,SSH_AUTH_SOCK \
AGENT_SANDBOX_OVERRIDE_ENV_VARS='NPM_CONFIG_USERCONFIG=/home/mirec/.npmrc,CI=1' \
./agent_vm my-agent
```

## Example Agent Setup

This repository includes a minimal example for running `codex-acp` inside the sandbox.

### 1. Install `codex-acp`

The wrapper expects the binary at:

```text
$HOME/.npm/bin/codex-acp
```

### 2. Create `~/.agent`

Copy the example files:

```bash
mkdir -p ~/.agent
cp example_dot_agent/binds ~/.agent/binds
cp example_dot_agent/npmrc ~/.agent/npmrc
mkdir -p ~/.agent/npm
```

Adjust the hard-coded `/home/user/...` paths in `~/.agent/binds` for your account.

The sample npm config in [example_dot_agent/npmrc](/home/mirec/a/example_dot_agent/npmrc) sets:

```text
prefix="/home/user/.npm/"
ignore-scripts=true
```

### 3. Use the wrapper

Run:

```bash
./example-codex-acp_vm --help
```

The wrapper is only:

```bash
NODE_PATH="$HOME/.npm"
agent_vm "$NODE_PATH/bin/codex-acp" "$@"
```

### 4. Point your editor or agent host at it

Example Neovim ACP config from [example_agentic_nvim_config.lua](/home/mirec/a/example_agentic_nvim_config.lua):

```lua
opts = {
	provider = "codex-acp",
	debug = false,
	acp_providers = {
		["codex-acp"] = {
			command = "example-codex-acp_vm",
			args = {
				"-c", "sandbox_mode=danger-full-access"
			}
		}
	}
}
```

## Logs

Each run creates a log file in:

```text
${AGENT_VM_LOG_DIR:-$PWD/.agent_vm}/<timestamp-and-pid>.krun.log
```

These logs are useful when the sandbox boots but the agent process fails later.

## Warnings

- `agent_vm` currently uses `bwrap --share-net`, so it does not isolate networking on its own. Processes inside the sandbox can use the same network namespace as the process that launched `agent_vm`.
- The example bind file mounts the host `.codex` directory read-write into the sandbox. That is convenient for agent state and credentials, but it also means the sandboxed process can read and modify the same Codex config, caches, and tokens as the host user.
- The example bind file should be treated as a convenience starting point, not a hardened default. Remove any mounts you do not want the agent to access.

## Network Namespace

If you want network isolation or custom routing, `agent_vm` can be launched from an existing Linux network namespace. This is applicable here because `agent_vm` shares the caller's network namespace instead of creating its own.

Example:

```bash
sudo ip netns add agentns
sudo ip netns exec agentns /home/mirec/a/agent_vm <command>
```

In practice you would usually need to configure interfaces, routes, and DNS inside that namespace before the command is useful.

The important detail is:

- `agent_vm` will stay in whatever network namespace it starts in
- `agent_vm` will not override that with separate network isolation because it uses `--share-net`
- `ip netns exec` is therefore a valid outer wrapper if you want to control networking externally

## Notes

- Network is enabled by design with `bwrap --share-net`.
- Only paths explicitly mounted into the sandbox are available for read/write access.
