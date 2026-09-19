# Security notes

- Keep `config.py` and `adel_smart_bot.db` local; both are ignored by Git.
- Use `config.example.py` only as a safe starting template.
- Before a commit, run `python scripts/security_scan.py` after staging intended files.
- Historical Telegram Bot Token Rotation = **REQUIRED MANUAL ACTION**. No credentials were changed by this batch.
