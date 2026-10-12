"""HTTP entry point for the XArcanoid leaderboard.

The canvas game stays in the XArcanoid repo. This process only stores and
reads finished runs. PostgreSQL is reached over the Docker network.
"""

import os
import re
import time

import psycopg2
from flask import Flask, jsonify, request
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ["DATABASE_URL"]
PORT = int(os.environ.get("PORT", "8080"))

PLAYER_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
DIFFICULTIES = ("standard", "overdrive")
MODES = ("campaign", "survival")

SCORE_COLUMNS = """
    id, player, score, level, max_combo, difficulty, mode,
    played_at::text AS played_at
"""

app = Flask(__name__)


def wait_for_database() -> None:
    for attempt in range(1, 31):
        try:
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            print(f"database is ready (attempt {attempt})", flush=True)
            return
        except psycopg2.OperationalError as exc:
            print(f"waiting for database ({attempt}/30): {exc}", flush=True)
            time.sleep(1)
    raise SystemExit("database did not become ready")


def run_query(sql, params=None):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if cur.description is None:
                return []
            return list(cur.fetchall())


def as_int(value):
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


@app.get("/")
def index():
    return jsonify(
        service="xarcanoid-entrypoint",
        game="XArcanoid",
        endpoints={
            "health": "GET /health",
            "board": "GET /leaderboard?mode=survival|campaign",
            "runs": "GET /scores",
            "one": "GET /scores/<id>",
            "submit": "POST /scores  {player, score, level, max_combo, difficulty, mode}",
        },
    )


@app.get("/health")
def health():
    try:
        run_query("SELECT 1")
    except psycopg2.Error:
        return jsonify(status="error", database="down"), 503
    return jsonify(status="ok", database="up")


@app.get("/leaderboard")
def leaderboard():
    mode = (request.args.get("mode") or "survival").strip()
    if mode not in MODES:
        return jsonify(error="mode must be campaign or survival"), 400
    rows = run_query(
        f"""
        SELECT {SCORE_COLUMNS}
        FROM scores AS s
        WHERE s.mode = %s
          AND s.id = (
              SELECT s2.id
              FROM scores AS s2
              WHERE s2.player = s.player
                AND s2.mode = s.mode
              ORDER BY s2.score DESC, s2.id DESC
              LIMIT 1
          )
        ORDER BY s.score DESC, s.level DESC, s.player ASC
        LIMIT 10
        """,
        (mode,),
    )
    return jsonify(mode=mode, entries=rows)


@app.get("/scores")
def list_scores():
    return jsonify(run_query(f"SELECT {SCORE_COLUMNS} FROM scores ORDER BY id"))


@app.get("/scores/<int:score_id>")
def get_score(score_id):
    rows = run_query(
        f"SELECT {SCORE_COLUMNS} FROM scores WHERE id = %s",
        (score_id,),
    )
    if not rows:
        return jsonify(error="not found"), 404
    return jsonify(rows[0])


@app.post("/scores")
def submit_score():
    body = request.get_json(silent=True) or {}
    player = str(body.get("player") or "").strip()
    score = as_int(body.get("score"))
    level = as_int(body.get("level"))
    max_combo = as_int(body.get("max_combo"))
    difficulty = str(body.get("difficulty") or "").strip()
    mode = str(body.get("mode") or "").strip()

    if not PLAYER_RE.fullmatch(player):
        return jsonify(error="player must be 3-20 letters, digits, or underscores"), 400
    if score is None or not 0 <= score <= 999_999:
        return jsonify(error="score must be an integer from 0 to 999999"), 400
    if level is None or not 1 <= level <= 9999:
        return jsonify(error="level must be an integer from 1 to 9999"), 400
    if max_combo is None or not 0 <= max_combo <= 9999:
        return jsonify(error="max_combo must be an integer from 0 to 9999"), 400
    if difficulty == "practice":
        return jsonify(error="practice runs are not saved"), 400
    if difficulty not in DIFFICULTIES:
        return jsonify(error="difficulty must be standard or overdrive"), 400
    if mode not in MODES:
        return jsonify(error="mode must be campaign or survival"), 400

    rows = run_query(
        f"""
        INSERT INTO scores (player, score, level, max_combo, difficulty, mode)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING {SCORE_COLUMNS}
        """,
        (player, score, level, max_combo, difficulty, mode),
    )
    return jsonify(rows[0]), 201


if __name__ == "__main__":
    wait_for_database()
    app.run(host="0.0.0.0", port=PORT)
