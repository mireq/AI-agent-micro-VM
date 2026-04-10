opts = {
	provider = "codex-acp",
	debug = false,
	acp_providers = {
		["codex-acp"] = {
			command = 'example-codex-acp_vm',
			args = {
				'-c', "sandbox_mode=danger-full-access"
			}
		}
	}
}
