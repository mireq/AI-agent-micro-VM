import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "agent_workspace_v2"


class AgentWorkspaceV2Tests(unittest.TestCase):
	def run_agent(
		self,
		home: Path,
		project: Path,
		*args: str,
		env_overrides: dict[str, str] | None = None,
	) -> subprocess.CompletedProcess[str]:
		env = os.environ.copy()
		env["AGENT_HOME"] = str(home / ".agent")
		env.update(env_overrides or {})
		return subprocess.run(
			[str(COMMAND), "--workdir", str(project), "exec", *args],
			env=env,
			text=True,
			capture_output=True,
			check=False,
		)

	def test_main_exposes_project_and_workspace_root_without_kvm(self) -> None:
		with tempfile.TemporaryDirectory() as temporary:
			root = Path(temporary)
			project = root / "project"
			project.mkdir()
			(project / "marker").write_text("ok", encoding="utf-8")

			result = self.run_agent(
				root,
				project,
				"--workspace",
				"main",
				"--shared-network",
				"--",
				"/bin/sh",
				"-c",
				"test -f marker && test -d /agent/workspaces && test \"$TERM\" = test-term && test ! -e /dev/kvm",
			env_overrides={"TERM": "test-term"},
			)

			self.assertEqual(result.returncode, 0, result.stderr)
			self.assertFalse((project / ".agent_vm").exists())

	def test_invalid_workspace_name_fails(self) -> None:
		with tempfile.TemporaryDirectory() as temporary:
			root = Path(temporary)
			project = root / "project"
			project.mkdir()

			result = self.run_agent(
				root,
				project,
				"--workspace",
				"../escape",
				"--",
				"/bin/true",
			)

			self.assertNotEqual(result.returncode, 0)
			self.assertIn("invalid workspace name", result.stderr)

	def test_initializes_compatible_default_agent_config(self) -> None:
		with tempfile.TemporaryDirectory() as temporary:
			root = Path(temporary)
			project = root / "project"
			project.mkdir()

			result = self.run_agent(
				root,
				project,
				"--workspace",
				"main",
				"--shared-network",
				"--",
				"/bin/true",
			)

			self.assertEqual(result.returncode, 0, result.stderr)
			agent_config = root / ".agent" / "config.toml"
			config = agent_config.read_text(encoding="utf-8")
			self.assertIn("[[mount]]", config)
			self.assertIn('flag = "r"', config)
			self.assertIn('src = "/usr"', config)
			self.assertIn('dst = "/usr"', config)

	def test_configure_updates_project_config(self) -> None:
		with tempfile.TemporaryDirectory() as temporary:
			root = Path(temporary)
			project = root / "project"
			project.mkdir()

			result = subprocess.run(
				[
					str(COMMAND),
					"--workdir",
					str(project),
					"configure",
					"example",
					"value",
				],
				env={**os.environ, "AGENT_HOME": str(root / ".agent")},
				text=True,
				capture_output=True,
				check=False,
			)

			self.assertEqual(result.returncode, 0, result.stderr)
			config = (root / ".agent" / "workdirs").glob("*/config.toml")
			self.assertEqual(next(config).read_text(encoding="utf-8").strip(), 'example = "value"')

	def test_custom_mount_source_is_available_to_inner_bwrap(self) -> None:
		with tempfile.TemporaryDirectory() as temporary:
			root = Path(temporary)
			project = root / "project"
			source = root / "machine-id"
			project.mkdir()
			source.write_text("test-machine-id\n", encoding="utf-8")
			env = {**os.environ, "AGENT_HOME": str(root / ".agent")}

			initialize = subprocess.run(
				[
					str(COMMAND),
					"--workdir",
					str(project),
					"exec",
					"--workspace",
					"main",
					"--shared-network",
					"--",
					"/bin/true",
				],
				env=env,
				check=False,
			)
			self.assertEqual(initialize.returncode, 0)
			config_path = next((root / ".agent" / "workdirs").glob("*/config.toml"))
			config_path.write_text(
				f'[[mount]]\nflag = "r"\nsrc = "{source}"\ndst = "/etc/test-machine-id"\n',
				encoding="utf-8",
			)

			result = subprocess.run(
				[
					str(COMMAND),
					"--workdir",
					str(project),
					"exec",
					"--workspace",
					"main",
					"--shared-network",
					"--",
					"/bin/sh",
					"-c",
					'test "$(cat /etc/test-machine-id)" = test-machine-id',
				],
				env=env,
				text=True,
				capture_output=True,
				check=False,
			)
			self.assertEqual(result.returncode, 0, result.stderr)

	def test_agent_can_start_nested_main_agent(self) -> None:
		with tempfile.TemporaryDirectory() as temporary:
			root = Path(temporary)
			project = root / "project"
			project.mkdir()

			result = self.run_agent(
				root,
				project,
				"--workspace",
				"main",
				"--shared-network",
				"--",
				COMMAND.name,
				"exec",
				"--workspace",
				"main",
				"--",
				"/bin/sh",
				"-c",
				f'test "$AGENT_HOME" = /agent/agent-home && test -x /agent/bin/{COMMAND.name} && test "$AGENT_WORKSPACE_COMMAND" = /agent/bin/{COMMAND.name}',
			)
			self.assertEqual(result.returncode, 0, result.stderr)

	def test_named_workspace_persists_overlay_write(self) -> None:
		with tempfile.TemporaryDirectory() as temporary:
			root = Path(temporary)
			project = root / "project"
			project.mkdir()
			(project / "lower-only").write_text("lower", encoding="utf-8")

			first = self.run_agent(
				root,
				project,
				"--workspace",
				"feature-a",
				"--shared-network",
				"--",
				"/bin/sh",
				"-c",
				"printf upper > new-file",
			)
			self.assertEqual(first.returncode, 0, first.stderr)
			self.assertFalse((project / "new-file").exists())

			second = self.run_agent(
				root,
				project,
				"--workspace",
				"feature-a",
				"--shared-network",
				"--",
				"/bin/sh",
				"-c",
				"test \"$(cat new-file)\" = upper",
			)
			self.assertEqual(second.returncode, 0, second.stderr)


if __name__ == "__main__":
	unittest.main()
