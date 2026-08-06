# c0admin

Suggests GNU/Linux terminal commands from natural language using AI, with an AI-assisted sysadmin toolkit.

![c0admin Banner](c0admin-banner.png)

> [!WARNING]
> For the automatic copy to clipboard feature to work, you must have the ‘xsel’ and ‘xclip’ packages installed on your system.

[How to get personal Google Gemini API key?](https://github.com/ufuayk/c0admin/blob/main/how-to-get-gemini-api-key.md)

## Installation

To install `c0admin` system-wide with the universal installer:

```bash
curl -s https://raw.githubusercontent.com/ufuayk/c0admin/main/install.sh -o install.sh && bash install.sh
```

This will:

- Download and install c0admin to ~/.c0admin/
- Set up a Python virtual environment
- Install dependencies
- Make c0admin available as a global terminal command

After installation, you can start the app anytime by simply typing:

```bash
c0admin
```

## Commands

- `/help` — Display help information.
- `/del` — Delete the GEMINI API KEY.
- `/exit` — Exit the app safely.
- `/history` — Displays the command history (history.txt).
- `/clear` — Clear the current session conversation history.
- `/setinst <url>` — Set a custom system instruction from a given URL.
- `/resetinst` — Reset system instruction to the default one.
- `/theme [name|list]` — Show or set the color theme.
- `/json [on|off]` — Toggle machine-readable JSON output.
- `/debug [on|off]` — Toggle verbose debug output.
- `/health` — AI-analyzed system health report (CPU, memory, disks, network).
- `/ps top|list|kill|analyze` — Process manager with AI analysis.
- `/net ping|trace|dns|check` — Network diagnostics.
- `/run <command>` — Run a command after an AI safety check.

Up/down arrow keys recall your previous inputs, like a normal terminal.

## Models

c0admin routes different tasks to different models:

- `main_model` — the main command-suggestion chat (`gemini-2.5-flash`).
- `report_model` — lighter model for system reports and analysis (`gemini-2.5-flash-lite`).

Both are configurable in `config.json`. Deprecated model IDs (e.g. `gemini-2.0-flash-lite`, shut down June 2026) are migrated automatically.

## Custom System Instructions

From the [system-instructions](https://github.com/ufuayk/c0admin-system-instructions) repo you can see all the community-created system instructions.

We welcome your contributions on this issue.

## Security & Legality

`/run` asks the AI to audit a command before executing it; `DANGEROUS` commands are blocked.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Disclaimer

This software (c0admin) and toolkit are provided "as is" without warranty of any kind, express or implied. The code, commands, or AI-generated outputs—especially system health reports and actions executed via `/run`—may lead to system instability, data loss, or unexpected behavior.

Use this tool entirely at your own risk. The developers assume no responsibility or liability for any direct or indirect damages resulting from its use. Don't go running random commands blindly; you are completely on your own, my friend. :P