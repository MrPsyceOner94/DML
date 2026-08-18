# DML League Hub — 2026

Production-oriented DML Draft Premiership command centre built from the supplied `fantasy.nrl(1).PDF` export.

## Included

- 14-team DML league dataset imported from the supplied PDF.
- Complete ladder with rank, H2H points, points for, points against and differential.
- Round 1–24 team score history and historical rank.
- Current roster structures, captain and vice-captain IDs for every team.
- 285 unique player IDs with round-by-round scoring-lineup participation.
- 161 reconstructed H2H fixtures for Rounds 1–23 from the two sides' score fields.
- Round 24 team scores preserved; opponent identities are not fabricated because the PDF does not contain them.
- Transaction engine for verified trade/waiver/RFA/FA imports.
- PDF re-import endpoint and UI.
- DRAFT360 data-driven newsroom layer.
- PWA manifest/service worker.
- Docker + Procfile deployment configuration.

## Important data-integrity note

The supplied PDF does **not** contain individual player fantasy-point values. It contains player IDs in each team's scoring lineups and team-level `scoreflow`. The app therefore does not invent player scores. Individual player score fields remain explicitly marked as unavailable until an export containing those values is imported.

The supplied PDF also contains no trade/transaction records. The transaction log therefore starts empty and can be populated with verified records through the UI/API.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DML_ADMIN_PASSWORD='choose-a-password'
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## Docker

```bash
docker build -t dml-league-hub .
docker run -p 8000:8000 -e DML_ADMIN_PASSWORD='choose-a-password' dml-league-hub
```

## Railway / Render / similar

Use the Procfile or Dockerfile. Set `DML_ADMIN_PASSWORD` in the service environment. If you need transactions to persist across restarts, attach persistent storage or move the transaction store to PostgreSQL.

## API

- `GET /api/health`
- `POST /api/auth/login`
- `GET /api/league`
- `GET /api/standings?round=23`
- `GET /api/teams/{team_id}`
- `GET /api/teams/{team_id}/rounds`
- `GET /api/fixtures?round=23`
- `GET /api/players`
- `GET /api/transactions`
- `POST /api/transactions`
- `POST /api/import/pdf`
- `GET /api/draft360/round/{round}`
