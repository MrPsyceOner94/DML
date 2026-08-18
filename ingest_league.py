#!/usr/bin/env python3
"""
ingest_league.py

Usage:
  - Place league.json in same directory (or pass path as first arg).
  - Set DATABASE_URL env var, e.g.:
      export DATABASE_URL="postgresql://user:pass@localhost:5432/nrldb"
  - Install deps: pip install asyncpg
  - Run: python ingest_league.py [path/to/league.json]

What it does:
  - Creates import tables (if not exist).
  - Inserts the league as an imported_leagues row.
  - Upserts teams, ladder, fixtures, player ids, transactions.
  - Produces player_scores.json template with per-player per-round null values.
"""
import asyncio
import asyncpg
import json
import os
import sys
from pathlib import Path
from typing import Any

DEFAULT_LEAGUE_JSON = "league.json"
PLAYER_SCORES_OUT = "player_scores.json"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS imported_leagues (
    id SERIAL PRIMARY KEY,
    source_filename TEXT,
    teams_count INTEGER,
    rounds INTEGER,
    player_ids_count INTEGER,
    source_meta JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS league_teams (
    league_id INTEGER REFERENCES imported_leagues(id) ON DELETE CASCADE,
    source_team_id BIGINT NOT NULL,
    source_name TEXT,
    name TEXT,
    manager TEXT,
    user_id BIGINT,
    avatar_version INTEGER,
    total_points INTEGER,
    league_points INTEGER,
    rank INTEGER,
    rank_history JSONB,
    scoreflow JSONB,
    league_against JSONB,
    league_scoreflow JSONB,
    current_lineup JSONB,
    scoring_players JSONB,
    captain BIGINT,
    vice_captain BIGINT,
    PRIMARY KEY (league_id, source_team_id)
);

CREATE TABLE IF NOT EXISTS league_ladder (
    league_id INTEGER REFERENCES imported_leagues(id) ON DELETE CASCADE,
    rank INTEGER,
    team_id BIGINT,
    name TEXT,
    source_name TEXT,
    manager TEXT,
    league_points INTEGER,
    points_for INTEGER,
    points_against INTEGER,
    points_diff INTEGER,
    rank_history JSONB,
    PRIMARY KEY (league_id, team_id)
);

CREATE TABLE IF NOT EXISTS league_fixtures (
    league_id INTEGER REFERENCES imported_leagues(id) ON DELETE CASCADE,
    round INTEGER,
    home_team_id BIGINT,
    away_team_id BIGINT,
    home_score INTEGER,
    away_score INTEGER,
    home_result_points INTEGER,
    away_result_points INTEGER,
    source TEXT
);

CREATE TABLE IF NOT EXISTS league_player_ids (
    league_id INTEGER REFERENCES imported_leagues(id) ON DELETE CASCADE,
    player_id BIGINT,
    PRIMARY KEY (league_id, player_id)
);

CREATE TABLE IF NOT EXISTS league_transactions (
    league_id INTEGER REFERENCES imported_leagues(id) ON DELETE CASCADE,
    tx JSONB
);
"""

INSERT_LEAGUE_SQL = """
INSERT INTO imported_leagues(source_filename, teams_count, rounds, player_ids_count, source_meta)
VALUES($1, $2, $3, $4, $5)
RETURNING id
"""

UPSERT_TEAM_SQL = """
INSERT INTO league_teams (
  league_id, source_team_id, source_name, name, manager, user_id, avatar_version,
  total_points, league_points, rank, rank_history, scoreflow, league_against,
  league_scoreflow, current_lineup, scoring_players, captain, vice_captain
) VALUES (
  $1, $2, $3, $4, $5, $6, $7,
  $8, $9, $10, $11, $12, $13,
  $14, $15, $16, $17, $18
)
ON CONFLICT (league_id, source_team_id) DO UPDATE SET
  source_name = EXCLUDED.source_name,
  name = EXCLUDED.name,
  manager = EXCLUDED.manager,
  user_id = EXCLUDED.user_id,
  avatar_version = EXCLUDED.avatar_version,
  total_points = EXCLUDED.total_points,
  league_points = EXCLUDED.league_points,
  rank = EXCLUDED.rank,
  rank_history = EXCLUDED.rank_history,
  scoreflow = EXCLUDED.scoreflow,
  league_against = EXCLUDED.league_against,
  league_scoreflow = EXCLUDED.league_scoreflow,
  current_lineup = EXCLUDED.current_lineup,
  scoring_players = EXCLUDED.scoring_players,
  captain = EXCLUDED.captain,
  vice_captain = EXCLUDED.vice_captain
"""

INSERT_LADDER_SQL = """
INSERT INTO league_ladder (
  league_id, rank, team_id, name, source_name, manager, league_points,
  points_for, points_against, points_diff, rank_history
) VALUES (
  $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
)
ON CONFLICT (league_id, team_id) DO UPDATE SET
  rank = EXCLUDED.rank,
  name = EXCLUDED.name,
  source_name = EXCLUDED.source_name,
  manager = EXCLUDED.manager,
  league_points = EXCLUDED.league_points,
  points_for = EXCLUDED.points_for,
  points_against = EXCLUDED.points_against,
  points_diff = EXCLUDED.points_diff,
  rank_history = EXCLUDED.rank_history
"""

INSERT_FIXTURE_SQL = """
INSERT INTO league_fixtures (
  league_id, round, home_team_id, away_team_id, home_score, away_score,
  home_result_points, away_result_points, source
) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
"""

INSERT_PLAYER_ID_SQL = """
INSERT INTO league_player_ids (league_id, player_id)
VALUES ($1, $2)
ON CONFLICT DO NOTHING
"""

INSERT_TRANSACTION_SQL = """
INSERT INTO league_transactions (league_id, tx) VALUES ($1, $2)
"""

async def run(league_json_path: Path, database_url: str):
    print("Reading", league_json_path)
    data = json.loads(league_json_path.read_text(encoding="utf-8"))

    # Basic metadata
    source = data.get("source", {})
    src_filename = source.get("filename") or league_json_path.name
    teams_count = source.get("teams") or len(data.get("teams", []))
    rounds = source.get("rounds") or (max((f.get("round", 0) for f in data.get("fixtures", [])), default=0))
    player_ids_count = source.get("player_ids") or len(data.get("player_ids", []))

    conn = await asyncpg.connect(database_url)
    try:
        # Create tables if not exist
        print("Ensuring import tables exist...")
        await conn.execute(CREATE_TABLE_SQL)

        # Insert league metadata
        print("Inserting imported_leagues row...")
        league_row = await conn.fetchrow(INSERT_LEAGUE_SQL, src_filename, teams_count, rounds, player_ids_count, json.dumps(data.get("source", {})))
        league_id = league_row["id"]
        print(f"Inserted league id={league_id}")

        # Upsert teams
        teams = data.get("teams", [])
        print(f"Upserting {len(teams)} teams...")
        for t in teams:
            await conn.execute(
                UPSERT_TEAM_SQL,
                league_id,
                t.get("id"),
                t.get("source_name"),
                t.get("name"),
                t.get("manager"),
                t.get("user_id"),
                t.get("avatar_version"),
                t.get("total_points"),
                t.get("league_points"),
                t.get("rank"),
                json.dumps(t.get("rank_history") or {}),
                json.dumps(t.get("scoreflow") or {}),
                json.dumps(t.get("league_against") or {}),
                json.dumps(t.get("league_scoreflow") or {}),
                json.dumps(t.get("current_lineup") or {}),
                json.dumps(t.get("scoring_players") or {}),
                t.get("captain"),
                t.get("vice_captain")
            )

        # Insert ladder
        ladder = data.get("ladder", [])
        print(f"Inserting {len(ladder)} ladder rows...")
        for l in ladder:
            await conn.execute(
                INSERT_LADDER_SQL,
                league_id,
                l.get("rank"),
                l.get("team_id"),
                l.get("name"),
                l.get("source_name"),
                l.get("manager"),
                l.get("league_points"),
                l.get("points_for"),
                l.get("points_against"),
                l.get("points_diff"),
                json.dumps(l.get("rank_history") or {})
            )

        # Insert fixtures
        fixtures = data.get("fixtures", [])
        print(f"Inserting {len(fixtures)} fixtures...")
        for f in fixtures:
            await conn.execute(
                INSERT_FIXTURE_SQL,
                league_id,
                f.get("round"),
                f.get("home_team_id"),
                f.get("away_team_id"),
                f.get("home_score"),
                f.get("away_score"),
                f.get("home_result_points"),
                f.get("away_result_points"),
                f.get("source")
            )

        # Insert player ids
        pids = data.get("player_ids", [])
        print(f"Inserting {len(pids)} player ids...")
        for pid in pids:
            await conn.execute(INSERT_PLAYER_ID_SQL, league_id, pid)

        # Insert transactions
        txs = data.get("transactions", [])
        print(f"Inserting {len(txs)} transactions...")
        for tx in txs:
            await conn.execute(INSERT_TRANSACTION_SQL, league_id, json.dumps(tx))

        # Generate player_scores.json template
        print("Writing player_scores.json template...")
        rounds_count = rounds or 24
        player_scores = {}
        for pid in pids:
            per_round = {str(r): None for r in range(1, rounds_count + 1)}
            player_scores[str(pid)] = {"player_id": pid, "scores": per_round, "total": None}

        out_path = Path(PLAYER_SCORES_OUT)
        out_path.write_text(json.dumps(player_scores, indent=2), encoding="utf-8")
        print(f"Wrote {out_path.resolve()}")

        print("Ingestion completed successfully.")
        print(f"League imported as imported_leagues.id = {league_id}")

    finally:
        await conn.close()


def main():
    if "DATABASE_URL" not in os.environ:
        print("ERROR: DATABASE_URL env var not set. Example:")
        print('  export DATABASE_URL="postgresql://user:pass@localhost:5432/nrldb"')
        sys.exit(1)
    database_url = os.environ["DATABASE_URL"]

    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(DEFAULT_LEAGUE_JSON)
    if not path.exists():
        print(f"ERROR: league JSON not found at {path}. Provide path as first arg or place league.json next to this script.")
        sys.exit(1)

    asyncio.run(run(path, database_url))


if __name__ == "__main__":
    main()