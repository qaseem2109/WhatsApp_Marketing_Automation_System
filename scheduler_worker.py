"""
scheduler_worker.py
Runs as a SEPARATE PROCESS (python scheduler_worker.py)
Reads campaigns from DB every minute, fires ones due right now.
"""
import time, logging, os
from datetime import datetime
from database import get_campaigns, log_send, set_campaign_status, init_db, get_daily_send_count, increment_daily_send_count, get_posts
from whatsapp_bot import get_bot

# ── CONFIG ─────────────────────────────────────────────────
DAILY_SEND_LIMIT = 2   # max sends per campaign per group per day
                        # ← change this number to adjust the limit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SCHEDULER] %(message)s",
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("scheduler")

DAYS = {"monday":0,"tuesday":1,"wednesday":2,"thursday":3,
        "friday":4,"saturday":5,"sunday":6}


def is_due(campaign: dict) -> bool:
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_day  = now.weekday()  # 0=Mon

    if campaign["send_time"] != current_time:
        return False

    days = campaign["send_days"].lower()  # "everyday" or "mon,wed,fri" etc.
    if days == "everyday":
        return True

    # Parse day list
    day_list = [d.strip() for d in days.split(",")]
    for d in day_list:
        if d in DAYS and DAYS[d] == current_day:
            return True
        if d == ["mon","tue","wed","thu","fri","sat","sun"][current_day]:
            return True
    return False


def run_campaign(bot, campaign: dict):
    log.info(f"🚀 Running campaign [{campaign['id']}]: {campaign['title']}")
    groups = campaign.get("groups", [])
    posts  = get_posts(campaign["id"])   # each post has its own banner + caption

    if not groups:
        log.warning("  No groups linked. Skipping."); return
    if not posts:
        log.warning("  No posts added. Skipping."); return

    for grp in groups:
        # ── Check daily limit for this group ──────────────
        count_today = get_daily_send_count(campaign["id"], grp["id"])
        if count_today >= DAILY_SEND_LIMIT:
            log.info(f"  ⏭ Skipping {grp['name']} — daily limit reached ({count_today}/{DAILY_SEND_LIMIT})")
            continue

        log.info(f"  Sending to {grp['name']} (send {count_today + 1}/{DAILY_SEND_LIMIT} today)...")

        # Send every post (image + its own caption) one by one
        all_ok = True
        for i, post in enumerate(posts):
            banner  = post["banner_path"]
            caption = post["caption"]

            log.info(f"    Post {i+1}/{len(posts)}: {os.path.basename(banner)}")

            if os.path.exists(banner):
                success, info = bot.send_image_to_group(grp["name"], banner, caption)
            else:
                log.warning(f"    Banner missing: {banner} — sending caption as text")
                success, info = bot.send_text_to_group(grp["name"], caption)

            log_send(campaign["id"], grp["id"],
                     "sent" if success else "failed",
                     None if success else info)

            if not success:
                log.info(f"    ❌ Failed: {info}")
                all_ok = False
            else:
                log.info(f"    ✅ Sent")

            time.sleep(3)   # short gap between posts in same group

        if all_ok:
            increment_daily_send_count(campaign["id"], grp["id"])
            new_count = count_today + 1
            if new_count >= DAILY_SEND_LIMIT:
                log.info(f"  ✅ {grp['name']}: done ({new_count}/{DAILY_SEND_LIMIT}) — pausing 24h")
            else:
                log.info(f"  ✅ {grp['name']}: done ({new_count}/{DAILY_SEND_LIMIT})")

        time.sleep(5)   # gap between groups

    if campaign["repeat"] == "once":
        set_campaign_status(campaign["id"], "done")
        log.info("  Campaign marked as done (one-time).")


def main():
    init_db()
    log.info("="*50)
    log.info("  WhatsApp Scheduler Worker")
    log.info("="*50)

    bot = get_bot(headless=False)   # visible so you can scan QR
    bot.start()

    if not bot.ready:
        log.error("Bot not ready. Exiting.")
        return

    log.info("✅ Bot ready. Checking campaigns every minute...")
    fired_this_minute = set()  # track (campaign_id, minute) to avoid double-fire

    while True:
        try:
            now_key = datetime.now().strftime("%Y-%m-%d %H:%M")
            campaigns = get_campaigns(status="active")

            for cam in campaigns:
                key = (cam["id"], now_key)
                if key in fired_this_minute:
                    continue
                if is_due(cam):
                    fired_this_minute.add(key)
                    run_campaign(bot, cam)

            # Cleanup old keys (keep memory small)
            cutoff = datetime.now().strftime("%Y-%m-%d %H:%M")
            fired_this_minute = {k for k in fired_this_minute if k[1] >= cutoff}

        except KeyboardInterrupt:
            log.info("Shutting down...")
            bot.quit()
            break
        except Exception as e:
            log.error(f"Loop error: {e}")

        time.sleep(30)  # check every 30s


if __name__ == "__main__":
    main()
