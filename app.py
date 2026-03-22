"""
app.py — Streamlit dashboard for WhatsApp Marketing Scheduler
Run: streamlit run app.py
"""
import streamlit as st
import os, time, shutil, subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd
from database import (
    init_db, add_group, get_groups, toggle_group, delete_group,
    add_campaign, get_campaigns, set_campaign_status, delete_campaign,
    add_post, get_posts, update_post, delete_post,
    get_logs, get_stats
)

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title="WA Marketing Scheduler",
    page_icon="📲",
    layout="wide",
    initial_sidebar_state="expanded"
)

BANNER_DIR = "./banners"
os.makedirs(BANNER_DIR, exist_ok=True)
init_db()

# ── Custom CSS ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --green:   #25D366;
    --dkgreen: #128C7E;
    --teal:    #075E54;
    --bg:      #0f1117;
    --card:    #1a1d27;
    --border:  #2a2d3a;
    --text:    #e8eaf6;
    --muted:   #8b8fa8;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

h1,h2,h3 { font-family: 'Syne', sans-serif !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1f1a 0%, #0f1117 100%) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .stRadio label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    padding: 0.4rem 0;
}

/* Metric cards */
.metric-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: var(--green); }
.metric-num {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    color: var(--green);
    line-height: 1;
}
.metric-label {
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 6px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Section header */
.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text);
    border-left: 4px solid var(--green);
    padding-left: 12px;
    margin: 1.5rem 0 1rem 0;
}

/* Campaign card */
.campaign-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.status-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}
.dot-active   { background: var(--green); box-shadow: 0 0 6px var(--green); }
.dot-paused   { background: #f59e0b; }
.dot-done     { background: var(--muted); }

/* Status badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.badge-active  { background: #0d3320; color: var(--green); border: 1px solid var(--green); }
.badge-paused  { background: #2d1f00; color: #f59e0b;  border: 1px solid #f59e0b; }
.badge-done    { background: #1e1e2e; color: var(--muted); border: 1px solid var(--border); }
.badge-sent    { background: #0d3320; color: var(--green); border: 1px solid var(--green); }
.badge-failed  { background: #3d0a0a; color: #f87171;  border: 1px solid #f87171; }

/* Form inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--green) !important;
    box-shadow: 0 0 0 2px rgba(37,211,102,0.15) !important;
}

/* Buttons */
.stButton > button {
    background: var(--green) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.4rem !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: var(--dkgreen) !important;
    color: #fff !important;
}

/* Divider */
hr { border-color: var(--border) !important; }

/* Multiselect */
.stMultiSelect div[data-baseweb="tag"] {
    background: var(--teal) !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1rem 0 1.5rem'>
        <div style='font-size:2.5rem'>📲</div>
        <div style='font-family:Syne; font-size:1.1rem; font-weight:700; color:#25D366'>WA Scheduler</div>
        <div style='font-size:0.75rem; color:#8b8fa8; margin-top:2px'>Marketing Automation</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("Navigation", [
        "🏠  Dashboard",
        "👥  Groups",
        "📢  Campaigns",
        "➕  New Campaign",
        "📜  Logs",
        "🤖  Bot Control",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown(f"<div style='font-size:0.75rem; color:#8b8fa8; text-align:center'>{datetime.now().strftime('%a %b %d, %Y %H:%M')}</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════
if page == "🏠  Dashboard":
    st.markdown("<div class='section-header'>Dashboard</div>", unsafe_allow_html=True)
    stats = get_stats()

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, num, label in zip(
        [c1, c2, c3, c4, c5],
        [stats["total_campaigns"], stats["active_campaigns"],
         stats["total_groups"], stats["total_sent"], stats["total_failed"]],
        ["Total Campaigns","Active","Groups","Sent","Failed"]
    ):
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-num'>{num}</div>
                <div class='metric-label'>{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("<div class='section-header' style='font-size:1.1rem'>Active Campaigns</div>", unsafe_allow_html=True)
        campaigns = get_campaigns(status="active")
        if not campaigns:
            st.info("No active campaigns. Create one in ➕ New Campaign.")
        for cam in campaigns[:5]:
            groups_str = ", ".join(g["name"] for g in cam["groups"]) or "—"
            st.markdown(f"""
            <div class='campaign-card'>
                <div class='status-dot dot-active'></div>
                <div style='flex:1'>
                    <div style='font-family:Syne; font-weight:600'>{cam['title']}</div>
                    <div style='font-size:0.8rem; color:#8b8fa8'>⏰ {cam['send_time']} &nbsp;·&nbsp; 🔁 {cam['repeat']} &nbsp;·&nbsp; 👥 {groups_str}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    with col_b:
        st.markdown("<div class='section-header' style='font-size:1.1rem'>Recent Activity</div>", unsafe_allow_html=True)
        logs = get_logs(10)
        if not logs:
            st.info("No send history yet.")
        for l in logs:
            badge = f"<span class='badge badge-{l['status']}'>{l['status'].upper()}</span>"
            st.markdown(f"""
            <div style='padding:0.6rem 0; border-bottom:1px solid #2a2d3a; display:flex; justify-content:space-between; align-items:center'>
                <div>
                    <div style='font-size:0.85rem; font-weight:500'>{l['campaign']}</div>
                    <div style='font-size:0.75rem; color:#8b8fa8'>→ {l['grp']} &nbsp;·&nbsp; {l['sent_at']}</div>
                </div>
                {badge}
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# PAGE: GROUPS
# ══════════════════════════════════════════════════════════
elif page == "👥  Groups":
    st.markdown("<div class='section-header'>WhatsApp Groups</div>", unsafe_allow_html=True)

    with st.expander("➕ Add New Group", expanded=False):
        with st.form("add_group_form"):
            g_name  = st.text_input("Group Name (exact, as in WhatsApp)")
            g_notes = st.text_input("Notes (optional)")
            if st.form_submit_button("Add Group"):
                if g_name.strip():
                    ok, msg = add_group(g_name.strip(), g_notes.strip())
                    st.success(msg) if ok else st.error(msg)
                    st.rerun()
                else:
                    st.warning("Group name is required.")

    st.markdown("---")
    groups = get_groups(active_only=False)
    if not groups:
        st.info("No groups yet. Add your first group above.")
    else:
        for grp in groups:
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            with c1:
                st.markdown(f"**{grp['name']}**")
                if grp["notes"]:
                    st.caption(grp["notes"])
            with c2:
                st.caption(f"Added: {grp['created_at'][:10]}")
            with c3:
                active = bool(grp["active"])
                if st.toggle("Active", value=active, key=f"tgl_{grp['id']}"):
                    if not active:
                        toggle_group(grp["id"], True); st.rerun()
                else:
                    if active:
                        toggle_group(grp["id"], False); st.rerun()
            with c4:
                if st.button("🗑", key=f"del_grp_{grp['id']}"):
                    delete_group(grp["id"]); st.rerun()
            st.divider()


# ══════════════════════════════════════════════════════════
# PAGE: CAMPAIGNS
# ══════════════════════════════════════════════════════════
elif page == "📢  Campaigns":
    st.markdown("<div class='section-header'>All Campaigns</div>", unsafe_allow_html=True)

    tab_active, tab_paused, tab_done = st.tabs(["✅ Active", "⏸ Paused", "✔️ Done"])

    def render_campaigns(status):
        cams = get_campaigns(status=status)
        if not cams:
            st.info(f"No {status} campaigns.")
            return
        for cam in cams:
            with st.container():
                c1, c3 = st.columns([5, 2])
                with c1:
                    st.markdown(f"### {cam['title']}")
                    st.caption(f"⏰ {cam['send_time']}  ·  📅 {cam['send_days']}  ·  🔁 {cam['repeat']}")
                    groups_str = " · ".join(f"👥 {g['name']}" for g in cam["groups"]) or "No groups"
                    st.caption(groups_str)
                    # Show posts as a mini table
                    posts = cam.get("posts", [])
                    if posts:
                        st.markdown(f"**{len(posts)} post(s):**")
                        for i, p in enumerate(posts):
                            pc1, pc2, pc3 = st.columns([1, 3, 1])
                            with pc1:
                                if os.path.exists(p["banner_path"]):
                                    st.image(p["banner_path"], width=70)
                                else:
                                    st.caption("⚠️ missing")
                            with pc2:
                                st.caption(f"**Post {i+1}:** {p['caption'][:120]}{'...' if len(p['caption'])>120 else ''}")
                            with pc3:
                                if st.button("🗑", key=f"del_post_{p['id']}"):
                                    delete_post(p["id"]); st.rerun()
                    else:
                        st.warning("⚠️ No posts added yet.")
                with c3:
                    if status == "active":
                        if st.button("⏸ Pause", key=f"pause_{cam['id']}"):
                            set_campaign_status(cam["id"], "paused"); st.rerun()
                    elif status == "paused":
                        if st.button("▶️ Resume", key=f"resume_{cam['id']}"):
                            set_campaign_status(cam["id"], "active"); st.rerun()
                    if st.button("🗑 Delete", key=f"del_cam_{cam['id']}"):
                        delete_campaign(cam["id"]); st.rerun()
                    st.caption(f"Created: {cam['created_at'][:10]}")

                    # Quick add post inline
                    with st.expander("➕ Add Post"):
                        up = st.file_uploader("Image", type=["jpg","jpeg","png","webp"],
                                              key=f"up_{cam['id']}")
                        cap = st.text_area("Caption", key=f"cap_{cam['id']}", height=80)
                        if st.button("Add", key=f"addpost_{cam['id']}"):
                            if up and cap.strip():
                                dest = os.path.join(BANNER_DIR, up.name)
                                with open(dest,"wb") as f: f.write(up.getbuffer())
                                add_post(cam["id"], dest, cap.strip(),
                                         sort_order=len(cam.get("posts",[])))
                                st.success("Post added!"); st.rerun()
                            else:
                                st.warning("Upload an image and write a caption.")
                st.divider()

    with tab_active: render_campaigns("active")
    with tab_paused: render_campaigns("paused")
    with tab_done:   render_campaigns("done")


# ══════════════════════════════════════════════════════════
# PAGE: NEW CAMPAIGN
# ══════════════════════════════════════════════════════════
elif page == "➕  New Campaign":
    st.markdown("<div class='section-header'>Create Campaign</div>", unsafe_allow_html=True)

    groups = get_groups(active_only=True)
    if not groups:
        st.warning("⚠️ You need at least one group. Go to 👥 Groups first.")
        st.stop()

    # ── Step 1: Campaign info ──────────────────────────────
    st.markdown("#### 📋 Step 1 — Campaign Details")
    with st.form("new_campaign_form"):
        title = st.text_input("Campaign Title", placeholder="e.g. Weekend Flash Sale")

        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            send_time = st.text_input("Send Time", placeholder="e.g. 20:15",
                help="Type any time in HH:MM format (24-hour). Examples: 09:00, 14:30, 20:15")
        with sc2:
            repeat = st.selectbox("Repeat", ["once","daily","weekly"])
        with sc3:
            send_days = st.multiselect("Days (optional — leave empty = everyday)",
                ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"],
                help="Pick specific days to send. Leave empty to send every day.")
            send_days_str = ",".join(send_days) if send_days else "everyday"

        group_map = {g["name"]: g["id"] for g in groups}
        selected_names = st.multiselect("Target Groups", options=list(group_map.keys()))

        step1 = st.form_submit_button("✅ Create Campaign & Add Posts →", use_container_width=True)

    if step1:
        import re
        errors = []
        if not title.strip():   errors.append("Title is required.")
        if not selected_names:  errors.append("Select at least one group.")
        if not send_time.strip():
            errors.append("Send time is required.")
        elif not re.match(r"^\d{1,2}:\d{2}$", send_time.strip()):
            errors.append("Invalid time format. Use HH:MM — e.g. 09:00 or 20:15")
        else:
            # Normalise to zero-padded HH:MM
            h, m = send_time.strip().split(":")
            if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
                errors.append("Invalid time. Hours 0-23, minutes 0-59.")
            else:
                send_time = f"{int(h):02d}:{int(m):02d}"

        if errors:
            for e in errors: st.error(e)
        else:
            group_ids  = [group_map[n] for n in selected_names]
            cid = add_campaign(title.strip(), send_time, send_days_str, repeat, group_ids)
            st.session_state["new_campaign_id"] = cid
            st.success(f"✅ Campaign **{title}** created (ID: {cid}). Now add your posts below.")
            st.rerun()

    # ── Step 2: Add posts to the just-created campaign ─────
    cid = st.session_state.get("new_campaign_id")
    if cid:
        st.markdown("---")
        st.markdown("#### 🖼️ Step 2 — Add Posts (Image + Caption)")
        st.caption("Each post = one image with its own caption. Add as many as you need.")

        # Show already-added posts
        existing = get_posts(cid)
        if existing:
            st.markdown(f"**{len(existing)} post(s) added so far:**")
            for i, p in enumerate(existing):
                col_img, col_txt, col_del = st.columns([1, 4, 1])
                with col_img:
                    if os.path.exists(p["banner_path"]):
                        st.image(p["banner_path"], width=80)
                with col_txt:
                    st.markdown(f"**Post {i+1}**")
                    st.caption(p["caption"])
                with col_del:
                    if st.button("🗑", key=f"rm_{p['id']}"):
                        delete_post(p["id"]); st.rerun()
            st.markdown("---")

        # Add new post form
        with st.form("add_post_form", clear_on_submit=True):
            col_a, col_b = st.columns([1, 2])
            with col_a:
                new_img = st.file_uploader("Upload Image",
                    type=["jpg","jpeg","png","webp"])
                existing_banners = ["— pick existing —"] + [
                    f for f in os.listdir(BANNER_DIR)
                    if f.lower().endswith((".jpg",".jpeg",".png",".webp"))
                ]
                pick_existing = st.selectbox("Or pick from banners/", existing_banners)
            with col_b:
                new_caption = st.text_area("Caption for this image", height=150,
                    placeholder="🔥 Flash Sale!\n50% OFF today only.\nShop now 👇")
                sort_ord = st.number_input("Send order (0 = first)", min_value=0,
                    value=len(existing))

            add_btn = st.form_submit_button("➕ Add This Post", use_container_width=True)

        if add_btn:
            banner_path = None
            if new_img:
                dest = os.path.join(BANNER_DIR, new_img.name)
                with open(dest, "wb") as f: f.write(new_img.getbuffer())
                banner_path = dest
            elif pick_existing != "— pick existing —":
                banner_path = os.path.join(BANNER_DIR, pick_existing)

            if not banner_path:
                st.error("Upload or select an image.")
            elif not new_caption.strip():
                st.error("Caption cannot be empty.")
            else:
                add_post(cid, banner_path, new_caption.strip(), sort_order=int(sort_ord))
                st.success("Post added!")
                st.rerun()

        col_done, col_clear = st.columns(2)
        with col_done:
            if st.button("🎉 Done — View Campaign", use_container_width=True):
                del st.session_state["new_campaign_id"]
                st.rerun()
        with col_clear:
            if st.button("🗑 Discard Campaign", use_container_width=True):
                from database import delete_campaign
                delete_campaign(cid)
                del st.session_state["new_campaign_id"]
                st.rerun()


# ══════════════════════════════════════════════════════════
# PAGE: LOGS
# ══════════════════════════════════════════════════════════
elif page == "📜  Logs":
    st.markdown("<div class='section-header'>Send Logs</div>", unsafe_allow_html=True)

    logs = get_logs(200)
    if not logs:
        st.info("No logs yet. Logs appear after campaigns are sent.")
    else:
        df = pd.DataFrame(logs)[["sent_at","campaign","grp","status","error"]]
        df.columns = ["Sent At","Campaign","Group","Status","Error"]

        # Color map
        def style_status(val):
            if val == "sent":   return "background-color:#0d3320; color:#25D366"
            if val == "failed": return "background-color:#3d0a0a; color:#f87171"
            return ""

        styled = df.style.map(style_status, subset=["Status"])
        st.dataframe(styled, use_container_width=True, height=500)

        col1, col2 = st.columns(2)
        total = len(logs)
        sent  = sum(1 for l in logs if l["status"] == "sent")
        with col1:
            st.metric("Total Sends", total)
        with col2:
            rate = round(sent/total*100) if total else 0
            st.metric("Success Rate", f"{rate}%")


# ══════════════════════════════════════════════════════════
# PAGE: BOT CONTROL
# ══════════════════════════════════════════════════════════
elif page == "🤖  Bot Control":
    st.markdown("<div class='section-header'>Bot Control</div>", unsafe_allow_html=True)

    st.info("The scheduler runs as a **separate process**. Use the commands below to start/stop it.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class='campaign-card' style='flex-direction:column; align-items:flex-start; gap:0.5rem'>
            <div style='font-family:Syne; font-weight:700; font-size:1.1rem'>▶️ Start Scheduler</div>
            <div style='font-size:0.85rem; color:#8b8fa8'>Opens Chrome, scan QR once, then runs in background</div>
            <code style='background:#0d1f1a; padding:6px 12px; border-radius:6px; color:#25D366; font-size:0.9rem'>
                python scheduler_worker.py
            </code>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='campaign-card' style='flex-direction:column; align-items:flex-start; gap:0.5rem'>
            <div style='font-family:Syne; font-weight:700; font-size:1.1rem'>🧪 Test Send Now</div>
            <div style='font-size:0.85rem; color:#8b8fa8'>Immediately send a campaign to verify it works</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("#### 🧪 Manual Test Send")
    campaigns = get_campaigns(status="active")
    if not campaigns:
        st.warning("No active campaigns to test.")
    else:
        cam_map = {c["title"]: c for c in campaigns}
        sel = st.selectbox("Select Campaign to Test", list(cam_map.keys()))
        if st.button("Send Now (Test)", type="primary"):
            cam = cam_map[sel]
            st.info(f"Connecting to WhatsApp Web...")

            try:
                from whatsapp_bot import get_bot
                bot = get_bot(headless=False)
                if not bot.ready:
                    bot.start()

                if bot.ready:
                    for grp in cam["groups"]:
                        with st.spinner(f"Sending to {grp['name']}..."):
                            ok, info = bot.send_image_to_group(
                                grp["name"], cam["banner_path"], cam["message"])
                            if ok:
                                st.success(f"✅ Sent to {grp['name']}")
                            else:
                                st.error(f"❌ Failed: {grp['name']} — {info}")
                        time.sleep(3)
                else:
                    st.error("Bot not ready. Make sure Chrome opened and QR was scanned.")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    st.markdown("#### 📋 Scheduler Log (live)")
    if os.path.exists("scheduler.log"):
        with open("scheduler.log") as f:
            lines = f.readlines()[-30:]
        st.code("".join(lines), language="bash")
    else:
        st.caption("scheduler.log not found. Start the scheduler first.")

    if st.button("🔄 Refresh Logs"):
        st.rerun()
