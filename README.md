# AI-agent-micro-VM

Lightweight wrappers for running agent tooling inside a `bubblewrap` sandbox while keeping your current project directory mounted.

This repository provides two launchers:

- `agent_vm`: sandbox + `chroot_vm` + `setpriv` (preserves caller UID/GID and supplementary groups)
- `agent_sandbox`: direct `bwrap` launcher (simpler, no `chroot_vm`)

Also included:

- `example-codex-acp_vm`: wrapper that runs `codex-acp` through `agent_vm`
- `example_dot_agent/`: example `~/.agent` bind and npm config
- `example_agentic_nvim_config.lua`: example ACP provider config

## What Gets Isolated

Both launchers use `bwrap` with:

- `--unshare-all` and `--new-session`
- host network namespace sharing (`--share-net`)
- writable bind mount of the chosen workdir
- `tmpfs` at `/tmp`
- clean environment (`--clearenv`) with explicit variables re-added
- bind mounts loaded from `${AGENT_HOME:-$HOME/.agent}/binds`
- special built-in mounts only for `proc` and `dev`

## Requirements

Common:

- `bwrap`
- standard utilities: `id`, `getent`, `cut`, `date`, `env`

`agent_vm` only:

- `/usr/bin/setpriv`
- `chroot_vm`

## Usage

Run a command in the sandbox:

```bash
./agent_vm <command> [args...]
# or
./agent_sandbox <command> [args...]
```

Example:

```bash
./agent_vm /bin/sh -lc 'pwd && id && env'
```

Set the sandbox working directory:

```bash
SANDBOX_WORKDIR=/path/to/project ./agent_vm <command>
```

## Configuration

### Bind File

Both scripts read binds from:

```text
${AGENT_HOME:-$HOME/.agent}/binds
```

Optional extra bind file:

```text
${AGENT_BIND_CONFIG_EXTRA_PATH}
```

Supported entries:

```text
w /host/path /guest/path
r /host/path /guest/path
/host/path:/guest/path
```

Rules:

- `w` = read-write bind
- `r` = read-only bind
- `source:target` defaults to read-write
- `~` expands to host home
- missing source paths are ignored
- malformed lines are skipped with a warning
- non-special mounts are no longer hardcoded in launchers; provide required runtime mounts in this file
- if `AGENT_BIND_CONFIG_EXTRA_PATH` is set, that file loads after default binds and entries are additive

See [example_dot_agent/binds](/home/mirec/AI-agent-micro-VM/example_dot_agent/binds).

### Environment Variables

- `SANDBOX_WORKDIR`: mounted project directory and initial cwd inside sandbox
- `AGENT_HOME`: location of `binds` file (default `$HOME/.agent`)
- `AGENT_BIND_CONFIG_EXTRA_PATH`: optional extra binds file loaded in addition to `$AGENT_HOME/binds`
- `AGENT_SANDBOX_INCLUDE_ENV_VARS`: comma-separated vars copied in (default `HOME,LOGNAME,PATH,SHELL,USER`)
- `AGENT_SANDBOX_OVERRIDE_ENV_VARS`: comma-separated `KEY=VALUE` pairs injected in sandbox

`agent_vm` only:

- `AGENT_VM_LOG_DIR`: directory for `chroot_vm` log file (default `<workdir>/.agent_vm`)
- `AGENT_VM_LOG_BASENAME`: log basename (default `<utc-timestamp>-<pid>`)

Example:

```bash
AGENT_SANDBOX_INCLUDE_ENV_VARS=HOME,PATH,SSH_AUTH_SOCK \
AGENT_SANDBOX_OVERRIDE_ENV_VARS='NPM_CONFIG_USERCONFIG=/home/mirec/.npmrc,CI=1' \
./agent_vm my-agent
```

## Example `codex-acp` Setup

1. Install `codex-acp` under `~/.npm/bin/codex-acp`.
2. Create `~/.agent` and copy the examples:

```bash
mkdir -p ~/.agent ~/.agent/npm
cp example_dot_agent/binds ~/.agent/binds
cp example_dot_agent/npmrc ~/.agent/npmrc
```

3. Keep the runtime/system bind lines in `~/.agent/binds`
4. Run the wrapper:

```bash
./example-codex-acp_vm --help
```

Wrapper contents:

```bash
NODE_PATH="$HOME/.npm"
agent_vm "$NODE_PATH/bin/codex-acp" "$@"
```

Neovim ACP sample: [example_agentic_nvim_config.lua](/home/mirec/AI-agent-micro-VM/example_agentic_nvim_config.lua)

## Logs (`agent_vm`)

`agent_vm` writes one log file per run to:

```text
${AGENT_VM_LOG_DIR:-$PWD/.agent_vm}/<timestamp-and-pid>.krun.log
```

Use these logs when sandbox bootstrap succeeds but command execution fails later.

## Security Notes

- Networking is shared with the caller (`--share-net`), so there is no network isolation by default.
- Any bind-mounted path is accessible to the sandboxed process with the permissions you grant (`r`/`w`).
- The example bind file includes runtime/system binds needed by the launchers plus a writable `.codex` mount for convenience; remove the `.codex` line if you do not want shared agent state/credentials.

## Network Namespace Integration

Because launchers use `--share-net`, they remain in whichever network namespace launched them. You can wrap with `ip netns exec` if you want external network control:

```bash
sudo ip netns add agentns
sudo ip netns exec agentns /home/mirec/AI-agent-micro-VM/agent_vm <command>
```
