---
script_path: .claude/commands/info.md
description: >-
  Defines the procedure for running proto info and interpreting its output. It instructs the
  agent to check for errors or misconfigurations and suggest adding issues to MAINTENANCE.yaml.
  The command uses the docs maintenance tool to record new items with standard fields.
tags:
- cli
- docs
- infra
---

Run `proto info -v 1` and explain the output. Check for errors or misconfigurations.
If issues are found, suggest whether to add them to MAINTENANCE.yaml.
Use: `docs m a '{"op":"add","title":"...","priority":"...","status":"open","component":"...","owner":"lars","description":"...","action":"..."}'`
$ARGUMENTS
