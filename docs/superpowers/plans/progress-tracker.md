# xjskp Progress Tracker

## Current Milestone
M1 (In Progress)

## Done
- M0 baseline scaffold completed
- M1 local service + minimal UI + SSE logs completed
- M2 minimal runtime and demo branch task flow completed
- M1 packaging scripts (Task 4) completed, pending local PyInstaller build validation

## Risks/Blockers
- Local environment may miss PyInstaller or macOS packaging prerequisites
- `.cursor/` remains untracked and should stay excluded from release commits

## Next
- run `bash scripts/build-macos.sh` and verify `artifacts/xjskp.dmg`
- if build succeeds, mark M1 done and proceed with stabilization tasks
