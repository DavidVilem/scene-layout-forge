# Runtime discovery before execution

On Windows, run the bundled `scripts/resolve_python.ps1` with PowerShell before creating images. Pass `-Project` with the project root. The script checks an explicit `-Python` argument or `INDUSTRIAL_LAYOUT_PYTHON` override, otherwise the project virtual environment, executable commands, Python registry registrations and per-user Python installation directories. Store aliases are skipped. It probes the actual executable and imports NumPy and Pillow. It never installs software or changes environment settings.

Parse its JSON, retain it in the execution history, and use `executable` as an absolute command with argument arrays for every Python command below. Examples that say `python` are shorthand for this verified executable. A missing command on PATH is not proof that Python is absent. An explicit override is authoritative: if it fails, report that failure rather than silently selecting another environment.

```powershell
$runtime = & $resolver -Project $project | ConvertFrom-Json
if (-not $runtime.ready) { throw 'Runtime preflight failed; inspect rejected candidates.' }
$layoutPython = $runtime.executable
& $layoutPython -B $pipelineScript next $pipeline
# Exit 2 means pending work. Continue the returned next_action.
```

Resolve `$resolver` and `$pipelineScript` against the loaded skill directory, not the current working directory. On other platforms probe Python 3.11+ and dependency imports using the platform shell, then retain the resolved absolute interpreter similarly.

If no runtime passes, preserve the exact preflight failure and resolve the missing runtime before beginning the multi-output chain. Do not generate images outside the coordinator and call them accepted. Dependency installation, if needed, belongs in an isolated environment with the bundled requirements, never an unrequested global change. Python discovery does not prove availability of the image tool, browser or Node: check those capabilities separately when requested. Browser test helpers take a runtime directory argument; locate its installed dependencies in the current environment, never copy a personal runtime path into this package.

Environment parity tests must include an empty PATH, a project path containing spaces, a broken explicit override and the actual coordinator executed with the resolved interpreter. Record whether these were shell simulations or tests inside the user's VS Code session. Unit tests and a desktop end-to-end run do not prove another agent's behavior in VS Code.
