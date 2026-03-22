"""database.py — SQLite models and queries"""
import sqlite3, os
from datetime import datetime

DB_PATH = "campaigns.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS groups (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL UNIQUE,
            notes      TEXT DEFAULT '',
            active     INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS campaigns (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT NOT NULL,
            send_time    TEXT NOT NULL,
            send_days    TEXT DEFAULT 'everyday',
            repeat       TEXT DEFAULT 'once',
            status       TEXT DEFAULT 'active',
            created_at   TEXT DEFAULT (datetime('now','localtime'))
        );
        -- Each post = one image + its own caption, belongs to a campaign
        CREATE TABLE IF NOT EXISTS posts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id  INTEGER NOT NULL,
            banner_path  TEXT NOT NULL,
            caption      TEXT NOT NULL,
            sort_order   INTEGER DEFAULT 0,
            created_at   TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS campaign_groups (
            campaign_id INTEGER,
            group_id    INTEGER,
            PRIMARY KEY (campaign_id, group_id)
        );
        CREATE TABLE IF NOT EXISTS send_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            group_id    INTEGER,
            status      TEXT,
            error       TEXT,
            sent_at     TEXT DEFAULT (datetime('now','localtime'))
        );

        -- Tracks how many sends a campaign has done TODAY per group
        CREATE TABLE IF NOT EXISTS daily_send_tracker (
            campaign_id  INTEGER,
            group_id     INTEGER,
            send_date    TEXT,        -- "YYYY-MM-DD"
            send_count   INTEGER DEFAULT 0,
            PRIMARY KEY (campaign_id, group_id, send_date)
        );
    """)
    conn.commit(); conn.close()

# ── Groups ──────────────────────────────────────────────────
def add_group(name, notes=""):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO groups (name,notes) VALUES (?,?)", (name, notes))
        conn.commit(); return True, "Group added."
    except sqlite3.IntegrityError:
        return False, "Group already exists."
    finally:
        conn.close()

def get_groups(active_only=True):
    conn = get_conn()
    q = "SELECT * FROM groups" + (" WHERE active=1" if active_only else "") + " ORDER BY name"
    rows = [dict(r) for r in conn.execute(q).fetchall()]
    conn.close(); return rows

def toggle_group(gid, active):
    conn = get_conn()
    conn.execute("UPDATE groups SET active=? WHERE id=?", (1 if active else 0, gid))
    conn.commit(); conn.close()

def delete_group(gid):
    conn = get_conn()
    conn.execute("DELETE FROM groups WHERE id=?", (gid,))
    conn.commit(); conn.close()

# ── Campaigns ───────────────────────────────────────────────
def add_campaign(title, send_time, send_days, repeat, group_ids):
    """Create a campaign (no posts yet — add them separately via add_post)."""
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO campaigns (title,send_time,send_days,repeat) VALUES (?,?,?,?)",
        (title, send_time, send_days, repeat)
    )
    cid = cur.lastrowid
    for gid in group_ids:
        conn.execute("INSERT OR IGNORE INTO campaign_groups VALUES (?,?)", (cid, gid))
    conn.commit(); conn.close(); return cid

def get_campaigns(status=None):
    conn = get_conn()
    q = "SELECT * FROM campaigns"
    q += (" WHERE status=?" if status else "") + " ORDER BY id DESC"
    rows = conn.execute(q, (status,) if status else ()).fetchall()
    result = []
    for r in rows:
        cam = dict(r)
        # Linked groups
        gs = conn.execute("""
            SELECT g.* FROM groups g
            JOIN campaign_groups cg ON g.id=cg.group_id
            WHERE cg.campaign_id=?
        """, (cam["id"],)).fetchall()
        cam["groups"] = [dict(g) for g in gs]
        # Posts (image + caption pairs), in send order
        ps = conn.execute(
            "SELECT * FROM posts WHERE campaign_id=? ORDER BY sort_order, id",
            (cam["id"],)
        ).fetchall()
        cam["posts"] = [dict(p) for p in ps]
        result.append(cam)
    conn.close(); return result

def set_campaign_status(cid, status):
    conn = get_conn()
    conn.execute("UPDATE campaigns SET status=? WHERE id=?", (status, cid))
    conn.commit(); conn.close()

def delete_campaign(cid):
    conn = get_conn()
    conn.execute("DELETE FROM posts WHERE campaign_id=?", (cid,))
    conn.execute("DELETE FROM campaign_groups WHERE campaign_id=?", (cid,))
    conn.execute("DELETE FROM campaigns WHERE id=?", (cid,))
    conn.commit(); conn.close()

# ── Posts (image + caption pairs) ───────────────────────────
def add_post(campaign_id: int, banner_path: str, caption: str, sort_order: int = 0):
    """Add one image+caption post to a campaign."""
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO posts (campaign_id, banner_path, caption, sort_order) VALUES (?,?,?,?)",
        (campaign_id, banner_path, caption, sort_order)
    )
    pid = cur.lastrowid
    conn.commit(); conn.close(); return pid

def get_posts(campaign_id: int):
    """Return all posts for a campaign in send order."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM posts WHERE campaign_id=? ORDER BY sort_order, id",
        (campaign_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_post(post_id: int, banner_path: str = None, caption: str = None, sort_order: int = None):
    """Edit an existing post's image, caption or order."""
    conn = get_conn()
    if banner_path is not None:
        conn.execute("UPDATE posts SET banner_path=? WHERE id=?", (banner_path, post_id))
    if caption is not None:
        conn.execute("UPDATE posts SET caption=? WHERE id=?", (caption, post_id))
    if sort_order is not None:
        conn.execute("UPDATE posts SET sort_order=? WHERE id=?", (sort_order, post_id))
    conn.commit(); conn.close()

def delete_post(post_id: int):
    """Remove a single post from a campaign."""
    conn = get_conn()
    conn.execute("DELETE FROM posts WHERE id=?", (post_id,))
    conn.commit(); conn.close()

# ── Logs ────────────────────────────────────────────────────
def log_send(campaign_id, group_id, status, error=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO send_log (campaign_id,group_id,status,error) VALUES (?,?,?,?)",
        (campaign_id, group_id, status, error)
    )
    conn.commit(); conn.close()

def get_logs(limit=100):
    conn = get_conn()
    rows = conn.execute("""
        SELECT l.*, c.title as campaign, g.name as grp
        FROM send_log l
        JOIN campaigns c ON l.campaign_id=c.id
        JOIN groups g ON l.group_id=g.id
        ORDER BY l.sent_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Daily Send Tracker ──────────────────────────────────────
def get_daily_send_count(campaign_id: int, group_id: int) -> int:
    """How many times has this campaign been sent to this group TODAY?"""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_conn()
    row = conn.execute(
        "SELECT send_count FROM daily_send_tracker WHERE campaign_id=? AND group_id=? AND send_date=?",
        (campaign_id, group_id, today)
    ).fetchone()
    conn.close()
    return row["send_count"] if row else 0

def increment_daily_send_count(campaign_id: int, group_id: int):
    """Increment today's send count for this campaign+group by 1."""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_conn()
    conn.execute("""
        INSERT INTO daily_send_tracker (campaign_id, group_id, send_date, send_count)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(campaign_id, group_id, send_date)
        DO UPDATE SET send_count = send_count + 1
    """, (campaign_id, group_id, today))
    conn.commit(); conn.close()

def get_stats():
    conn = get_conn()
    stats = {
        "total_campaigns": conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0],
        "active_campaigns": conn.execute("SELECT COUNT(*) FROM campaigns WHERE status='active'").fetchone()[0],
        "total_groups":    conn.execute("SELECT COUNT(*) FROM groups WHERE active=1").fetchone()[0],
        "total_sent":      conn.execute("SELECT COUNT(*) FROM send_log WHERE status='sent'").fetchone()[0],
        "total_failed":    conn.execute("SELECT COUNT(*) FROM send_log WHERE status='failed'").fetchone()[0],
    }
    conn.close(); return stats
