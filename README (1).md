# NRL Fantasy Matchup Extractor (GitHub Actions one-shot)

This repository contains a Playwright-based matchup extractor and a GitHub Actions workflow that runs it once and uploads the outputs as an artifact you can download on mobile.

Files:
- fetch_matchup_playwright.py — Playwright extractor (captures network JSON, embedded JSON, parsed fields)
- requirements.txt — Python deps
- .github/workflows/run-extract.yml — GitHub Actions workflow (workflow_dispatch)

How to use (mobile-friendly step-by-step)

1) Create a new GitHub repository
   - Open github.com in your mobile browser or GitHub app.
   - New → Create repository. Give it a name (e.g., nrl-extractor).
   - Create repo.

2) Add the files
   - In the repo, use "Add file" → "Create new file".
   - Create each file above one at a time (paste the contents) and commit.
     - fetch_matchup_playwright.py
     - requirements.txt
     - .github/workflows/run-extract.yml (ensure folder `.github/workflows/`)
     - README.md

3) Add secrets (Repository → Settings → Secrets & variables → Actions)
   - DATABASE_URL (if using stored team credentials; optional)
   - CRED_ENCRYPTION_KEY (Fernet key; required if using team creds)
   - ADMIN_USERNAME (if using admin login)
   - ADMIN_PASSWORD (if using admin login)
   - NRL_LOGIN_URL (typically `https://fantasy.nrl.com/login`)
   - Make sure values are exact and do NOT commit secrets in code.

4) Trigger the workflow
   - In the GitHub repo, go to Actions → Run Matchup Extractor → Run workflow.
   - Fill `url` (matchup URL). If you plan to use stored team credentials, set `use_team_creds=true` and fill league and team.
   - Start the workflow.

5) Download output
   - After the workflow completes, open the workflow run.
   - In the "Artifacts" section click `matchup-output` and download the ZIP to your phone.
   - Inside the ZIP you'll find:
     - raw_page_*.html (snapshot)
     - embedded_json_*.json (if any)
     - network_responses_*.json (captured API JSON)
     - parsed_matchup_*.json (consolidated parsed fields)

Notes & troubleshooting
- If Playwright fails due to missing libs, the workflow uses the `--with-deps` installer which generally resolves Linux library needs on GitHub runners.
- If the site blocks headless browsers, modify the extractor to run headful (set `--headful` and remove headless), but GitHub runners may not support displaying a browser. For debugging, run locally or use a remote headful runner.
- If parsing misses fields, paste the network_responses_*.json content (or upload) and I will tailor the parser to the exact JSON schema.

Security reminder
- Never commit credentials into the repo. Use GitHub Secrets only.
- Fernet key can be generated with:
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"