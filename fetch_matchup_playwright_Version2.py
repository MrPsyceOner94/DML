#!/usr/bin/env python3
"""
Playwright matchup extractor (headless) - writes outputs to ./output/

Usage (workflow will call it):
  python fetch_matchup_playwright.py "<matchup_url>" --outdir ./output --use-team-creds --league 60018 --team 68

Environment variables (set as GitHub Secrets):
  DATABASE_URL - postgres DSN (if using stored team creds)
  CRED_ENCRYPTION_KEY - Fernet key to decrypt stored team creds (if using team creds)
  ADMIN_USERNAME, ADMIN_PASSWORD - admin login (if using admin login)
  NRL_LOGIN_URL - login page URL (e.g. https://fantasy.nrl.com/login)

This script uses Playwright to capture network JSON, embedded JSON and parse matchup fields.
"""
import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Response, Browser

try:
    import asyncpg
    from cryptography.fernet import Fernet
except Exception:
    asyncpg = None
    Fernet = None

def fernet_from_env() -> Optional[Fernet]:
    key = os.environ.get("CRED_ENCRYPTION_KEY")
    if not key:
        return None
    if Fernet is None:
        raise RuntimeError("cryptography required but not installed")
    return Fernet(key.encode())

def save_json(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    print("WROTE:", path)

def save_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print("WROTE:", path)

async def get_team_credentials(db_url: str, league_id: int, team_id: int):
    if not asyncpg:
        raise RuntimeError("asyncpg not installed")
    pool = await asyncpg.create_pool(dsn=db_url, min_size=1, max_size=2)
    try:
        row = await pool.fetchrow("SELECT encrypted_blob, owner_user_id FROM team_credentials WHERE league_id=$1 AND team_source_id=$2", league_id, team_id)
        return row
    finally:
        await pool.close()

def decrypt_blob(encrypted_blob: bytes) -> Dict:
    f = fernet_from_env()
    if not f:
        raise RuntimeError("CRED_ENCRYPTION_KEY missing")
    plain = f.decrypt(bytes(encrypted_blob))
    return json.loads(plain.decode("utf-8"))

def recursive_find(obj: Any, key_patterns: List[str]) -> List[Any]:
    found = []
    def _walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                lk = str(k).lower()
                for pat in key_patterns:
                    if pat in lk:
                        found.append({k: v})
                _walk(v)
        elif isinstance(o, list):
            for it in o:
                _walk(it)
    _walk(obj)
    return found

def find_first_matching(obj: Any, key_names: List[str]):
    key_names_lower = [k.lower() for k in key_names]
    result = None
    def _walk(o):
        nonlocal result
        if result is not None:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                if k.lower() in key_names_lower:
                    result = v
                    return
            for v in o.values():
                _walk(v)
        elif isinstance(o, list):
            for it in o:
                _walk(it)
    _walk(obj)
    return result

def parse_matchup_from_embedded_json(embedded: Dict) -> Dict:
    out = {}
    out['matchup'] = find_first_matching(embedded, ["matchup", "match", "fixture", "game"])
    out['teams'] = find_first_matching(embedded, ["teams", "team", "fantasy_teams"])
    out['lineups'] = find_first_matching(embedded, ["lineup", "lineups", "current_lineup"])
    out['scoring'] = find_first_matching(embedded, ["scoring", "scores", "player_scores"])
    out['draft'] = find_first_matching(embedded, ["draft", "drafts", "draft_order"])
    out['players'] = find_first_matching(embedded, ["players", "playerList", "player_ids"])
    out['events'] = find_first_matching(embedded, ["timeline", "events", "live", "matchEvents"])
    if out['matchup'] and isinstance(out['matchup'], dict):
        m = out['matchup']
        for k in ("league_id", "leagueId", "competitionId", "competition_id"):
            if k in m:
                out.setdefault("metadata", {})["league_id"] = m[k]
        for k in ("round", "round_id"):
            if k in m:
                out.setdefault("metadata", {})["round"] = m[k]
        for k in ("home_team_id", "homeId", "homeTeamId", "home_team"):
            if k in m:
                if isinstance(m[k], dict) and m[k].get("id"):
                    out.setdefault("metadata", {})["home_team_id"] = m[k]["id"]
                else:
                    out.setdefault("metadata", {})["home_team_id"] = m[k]
        for k in ("away_team_id", "awayId", "awayTeamId", "away_team"):
            if k in m:
                if isinstance(m[k], dict) and m[k].get("id"):
                    out.setdefault("metadata", {})["away_team_id"] = m[k]["id"]
                else:
                    out.setdefault("metadata", {})["away_team_id"] = m[k]
        for k in ("kickoff", "kickoff_time", "start_time", "startAt", "kickoff_at"):
            if k in m:
                out.setdefault("metadata", {})["kickoff"] = m[k]
    return out

async def handle_response(resp: Response, collected: List[Dict]):
    try:
        url = str(resp.url)
        headers = dict(resp.headers)
        ct = headers.get("content-type", "")
        if "application/json" in ct or "/api/" in url:
            try:
                body = await resp.json()
            except Exception:
                try:
                    text = await resp.text()
                    body = text if len(text) < 500000 else text[:500000]
                except Exception:
                    body = None
            collected.append({"url": url, "status": resp.status, "headers": headers, "body": body})
    except Exception as e:
        print("response handler error:", e)

async def attempt_login_with_form(page: Page, login_url: str, username: str, password: str) -> bool:
    await page.goto(login_url, wait_until="networkidle")
    html = await page.content()
    soup = BeautifulSoup(html, "lxml")
    uname_selectors = [
        "input[name='username']", "input[name='email']", "input[type='email']",
        "input[id*='user']", "input[id*='email']"
    ]
    pwd_selectors = [
        "input[name='password']", "input[type='password']", "input[id*='pass']"
    ]
    filled_uname = False
    filled_pwd = False
    for sel in uname_selectors:
        try:
            await page.fill(sel, username)
            filled_uname = True
            break
        except Exception:
            continue
    for sel in pwd_selectors:
        try:
            await page.fill(sel, password)
            filled_pwd = True
            break
        except Exception:
            continue
    submitted = False
    try:
        await page.click("button[type='submit']", timeout=3000)
        submitted = True
    except Exception:
        try:
            if filled_pwd:
                await page.keyboard.press("Enter")
                submitted = True
        except Exception:
            pass
    try:
        await page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    content = (await page.content()).lower()
    if "logout" in content or "sign out" in content or "my account" in content:
        return True
    return submitted

async def fetch_matchup_playwright(url: str, outdir: Path, args):
    outdir.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    raw_html_path = outdir / f"raw_page_{timestamp}.html"
    embedded_json_path = outdir / f"embedded_json_{timestamp}.json"
    network_json_path = outdir / f"network_responses_{timestamp}.json"
    parsed_path = outdir / f"parsed_matchup_{timestamp}.json"

    collected_responses: List[Dict] = []

    username = None
    password = None
    if args.use_team_creds:
        if not args.league or not args.team:
            raise SystemExit("--use-team-creds requires --league and --team")
        if not os.environ.get("DATABASE_URL"):
            raise SystemExit("DATABASE_URL env var required for team creds")
        if not os.environ.get("CRED_ENCRYPTION_KEY"):
            raise SystemExit("CRED_ENCRYPTION_KEY required to decrypt team creds")
        row = await get_team_credentials(args.database_url or os.environ.get("DATABASE_URL"), int(args.league), int(args.team))
        if not row:
            raise SystemExit("no team credentials found for league/team")
        encrypted_blob = row["encrypted_blob"]
        cred = decrypt_blob(encrypted_blob)
        username = cred.get("username")
        password = cred.get("password")
    else:
        username = args.admin_username or os.environ.get("ADMIN_USERNAME")
        password = args.admin_password or os.environ.get("ADMIN_PASSWORD")

    playwright = await async_playwright().start()
    browser: Browser = await playwright.chromium.launch(headless=not args.headful, args=["--no-sandbox"], slow_mo=args.slow_mo)
    context = await browser.new_context()
    page = await context.new_page()

    page.on("response", lambda r: asyncio.create_task(handle_response(r, collected_responses)))

    if username and password and args.login_url:
        try:
            ok = await attempt_login_with_form(page, args.login_url, username, password)
            if ok:
                print("Login (heuristic) appears successful")
            else:
                print("Login attempt complete (could not detect success heuristically). Continue to page.")
        except Exception as e:
            print("Login attempt threw:", e)

    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
    except Exception as e:
        print("Goto error:", e)
    await asyncio.sleep(args.post_wait)

    page_html = await page.content()
    save_text(raw_html_path, page_html)

    embedded = None
    try:
        try:
            next_data = await page.evaluate("window.__NEXT_DATA__ ? window.__NEXT_DATA__ : null")
            if next_data:
                embedded = next_data
        except Exception:
            pass
        if not embedded:
            try:
                initial = await page.evaluate("window.__INITIAL_STATE__ ? window.__INITIAL_STATE__ : null")
                if initial:
                    embedded = initial
            except Exception:
                pass
        if not embedded:
            scripts = await page.query_selector_all('script[type="application/json"]')
            for s in scripts:
                txt = await s.text_content()
                if txt:
                    try:
                        parsed = json.loads(txt)
                        embedded = parsed
                        break
                    except Exception:
                        continue
    except Exception as e:
        print("embedded JSON extraction error:", e)

    if embedded:
        save_json(embedded_json_path, embedded)
    else:
        try:
            heur = await page.evaluate("document.documentElement.innerHTML")
            candidate = extract_json_from_html_heuristic(heur)
            if candidate:
                embedded = candidate
                save_json(embedded_json_path, embedded)
            else:
                print("No embedded JSON found via heuristics.")
        except Exception:
            pass

    save_json(network_json_path, collected_responses)

    parsed = {"url": url, "extracted_at": timestamp, "sources": {}}
    if embedded:
        parsed_from_embedded = parse_matchup_from_embedded_json(embedded)
        parsed["sources"]["embedded_json"] = parsed_from_embedded
    parsed_network = {}
    for resp in collected_responses:
        body = resp.get("body")
        if not body:
            continue
        if isinstance(body, (dict, list)):
            mf = find_first_matching(body, ["matchup", "home_team", "away_team", "lineup", "player_scores", "draft"])
            if mf:
                parsed_network.setdefault("found_items", []).append({"url": resp["url"], "match": mf})
    if parsed_network:
        parsed["sources"]["network_responses"] = parsed_network

    consolidated = {}
    def pick(*keys):
        for k in keys:
            if embedded and isinstance(embedded, dict) and k in embedded:
                return embedded[k]
        if embedded:
            res = recursive_find(embedded, [k.lower() for k in keys])
            if res:
                return res
        for resp in collected_responses:
            b = resp.get("body")
            if isinstance(b, dict):
                for k in keys:
                    if k in b:
                        return b[k]
        return None

    metadata = {}
    for cand in ("matchup", "fixture", "game"):
        block = pick(cand)
        if isinstance(block, dict):
            for lk in ("league_id","leagueId","competitionId","competition_id"):
                if lk in block:
                    metadata["league_id"] = block[lk]
            for rk in ("round","round_id"):
                if rk in block:
                    metadata["round"] = block[rk]
            for hk in ("home_team_id","homeId","homeTeamId"):
                if hk in block:
                    metadata["home_team_id"] = block[hk]
            for ak in ("away_team_id","awayId","awayTeamId"):
                if ak in block:
                    metadata["away_team_id"] = block[ak]
            for tk in ("kickoff","kickoff_time","start_time","startAt","kickoff_at"):
                if tk in block:
                    metadata["kickoff"] = block[tk]
            if metadata:
                break
    if not metadata.get("league_id"):
        m = re.search(r"/league/(\d+)", url)
        if m:
            metadata["league_id"] = int(m.group(1))
    if not metadata.get("home_team_id") or not metadata.get("away_team_id") or not metadata.get("round"):
        m = re.search(r"/matchup/(\d+)/(\d+)/(\d+)", url)
        if m:
            metadata.setdefault("home_team_id", int(m.group(1)))
            metadata.setdefault("away_team_id", int(m.group(2)))
            metadata.setdefault("round", int(m.group(3)))
    consolidated["metadata"] = metadata

    lineups = find_first_matching(embedded, ["lineup", "current_lineup", "team_lineup"]) if embedded else None
    scoring = find_first_matching(embedded, ["scoring", "player_scores", "scores"]) if embedded else None
    captain = find_first_matching(embedded, ["captain", "captainId", "captain_player"]) if embedded else None
    draft = find_first_matching(embedded, ["draft", "drafts", "draft_order"]) if embedded else None
    events = find_first_matching(embedded, ["timeline", "events", "matchEvents", "live"]) if embedded else None
    statuses = find_first_matching(embedded, ["player_status", "status", "availability"]) if embedded else None
    totals = find_first_matching(embedded, ["totals", "summary", "matchup_summary", "team_totals"]) if embedded else None

    if not lineups:
        for resp in collected_responses:
            b = resp.get("body")
            if isinstance(b, dict):
                l = find_first_matching(b, ["lineup", "current_lineup"])
                if l:
                    lineups = l
                    break
    if not scoring:
        for resp in collected_responses:
            b = resp.get("body")
            if isinstance(b, dict):
                s = find_first_matching(b, ["player_scores", "scoring", "scores"])
                if s:
                    scoring = s
                    break
    if not events:
        for resp in collected_responses:
            b = resp.get("body")
            if isinstance(b, dict):
                e = find_first_matching(b, ["timeline", "events", "live"])
                if e:
                    events = e
                    break
    if not draft:
        for resp in collected_responses:
            b = resp.get("body")
            if isinstance(b, dict):
                d = find_first_matching(b, ["draft", "drafts", "draft_order"])
                if d:
                    draft = d
                    break

    consolidated["lineups"] = lineups
    consolidated["scoring"] = scoring
    consolidated["captain"] = captain
    consolidated["events"] = events
    consolidated["statuses"] = statuses
    consolidated["totals"] = totals
    consolidated["draft"] = draft

    parsed["consolidated"] = consolidated
    save_json(parsed_path, parsed)

    await context.close()
    await browser.close()
    await playwright.stop()
    return parsed_path

def extract_json_from_html_heuristic(html: str) -> Optional[Dict]:
    m = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, flags=re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, flags=re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    soup = BeautifulSoup(html, "lxml")
    for script in soup.find_all("script"):
        if script.string and len(script.string) > 200 and ("matchup" in script.string.lower() or "lineup" in script.string.lower()):
            text = script.string.strip()
            m = re.search(r'({.*})', text, flags=re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    continue
    return None

def cli_args():
    import argparse
    p = argparse.ArgumentParser(description="Playwright-enhanced matchup extractor")
    p.add_argument("url", help="matchup URL to fetch")
    p.add_argument("--outdir", "-o", default="./output", help="output directory")
    p.add_argument("--login-url", default=os.environ.get("NRL_LOGIN_URL"), help="NRL login URL (env NRL_LOGIN_URL)")
    p.add_argument("--admin-username", help="Admin username (or set ADMIN_USERNAME env var)")
    p.add_argument("--admin-password", help="Admin password (or set ADMIN_PASSWORD env var)")
    p.add_argument("--use-team-creds", action="store_true", help="Use stored team credentials from DB (requires --league and --team and env DATABASE_URL & CRED_ENCRYPTION_KEY)")
    p.add_argument("--league", type=int, help="league id (used with --use-team-creds)")
    p.add_argument("--team", type=int, help="team source id (used with --use-team-creds)")
    p.add_argument("--database-url", help="override DATABASE_URL (optional)")
    p.add_argument("--headful", action="store_true", help="Run browser visible (not headless) - useful for debugging")
    p.add_argument("--slow-mo", type=int, default=0, help="slow motion ms for Playwright (0 = none)")
    p.add_argument("--post-wait", type=int, default=2, help="seconds to wait after page loads to capture network activity")
    return p.parse_args()

async def main():
    args = cli_args()
    outdir = Path(args.outdir)
    if not args.admin_username:
        args.admin_username = os.environ.get("ADMIN_USERNAME")
    if not args.admin_password:
        args.admin_password = os.environ.get("ADMIN_PASSWORD")
    try:
        parsed_path = await fetch_matchup_playwright(args.url, outdir, args)
        print("Parsed result saved to:", parsed_path)
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())