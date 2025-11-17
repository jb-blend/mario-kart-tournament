import os
import base64
from pathlib import Path

import pandas as pd
from PIL import Image
import streamlit as st
import re
import streamlit.components.v1 as components

# ---------- CONFIG ----------
DATA_FILE = Path("data/results.xlsx")
RESULTS_SHEET = "results"
PLAYERS_SHEET = "players"

PLAYER_PIC_DIR = Path("player_pics")
CHARACTER_PIC_DIR = Path("character_pics")
BACKGROUND_IMG = Path("assets/mario_bg.jpg")       # you choose
MARIO_FONT = Path("assets/MarioFont.ttf")          # optional; you supply

AUTOREFRESH_SECONDS = 5

CHARACTER_COLORS = {
    "mario": "#ff4b4b",
    "luigi": "#4caf50",
    "peach": "#ffb6c1",
    "toad": "#f5e050",
    "yoshi": "#7ed957",
    "bowser": "#ff9f00",
    "donkey kong": "#a56b46",
    "wario": "#fdda24",
    "rosalina": "#66d3ff",
    "default": "#ffffff"
}

from PIL import Image
for img_path in CHARACTER_PIC_DIR.glob("*.png"):
    img = Image.open(img_path)
    if img.mode != "RGBA":
        print(img_path.name, "→ not transparent")

# ---------- PAGE SETUP ----------
# Must come BEFORE any Streamlit elements render
st.set_page_config(
    page_title="Mario Kart Tournament Leaderboard",
    layout="wide",
    page_icon="🏎️",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* Fix broken Material icon text that leaks as 'keyboard_double_arrow_left/right' */

/* Target the specific span used for the icon */
span[data-testid="stIconMaterial"] {
    font-family: 'Material Symbols Outlined' !important;
    font-feature-settings: 'liga';
}

/* If the Material font still fails, hide the raw fallback text */
span[data-testid="stIconMaterial"]:not(:has(svg)) {
    font-family: 'Material Symbols Outlined', sans-serif !important;
    color: transparent !important;
}

/* Optionally, replace with your own small MENU text */
span[data-testid="stIconMaterial"]:not(:has(svg))::before {
    content: "MENU";
    font-family: 'Press Start 2P', cursive !important;
    font-size: 0.6rem;
    color: #ffcc00;
    text-shadow: 1px 1px 0 #000;
    position: relative;
    top: 1px;
}
</style>
""", unsafe_allow_html=True)

# 🎨 Apply Mario-style Google Font (Press Start 2P)
# 🎨 Apply Mario-style Google Font via @import
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

/* Hit everything inside the Streamlit app */
html, body, .stApp, .block-container,
h1, h2, h3, h4, h5, h6,
p, span, div, button,
[class*="css"] {
    font-family: 'Press Start 2P', cursive !important;
    letter-spacing: 0.03em;
}
</style>
""", unsafe_allow_html=True)


# ---------- STYLING HELPERS ----------

def get_base64(file_path: Path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def inject_theme():
    """Inject background and card styling into the Streamlit app."""
    # ---------- BACKGROUND ----------
    bg_css = ""
    if BACKGROUND_IMG.exists():
        import base64
        bg = base64.b64encode(BACKGROUND_IMG.read_bytes()).decode()
        bg_css = f"""
        .stApp {{
            background-image: url("data:image/jpg;base64,{bg}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        """

    # ⚠️ No font_css here – Google font handles that

    custom_css = f"""
    {bg_css}

    /* ===== LEADERBOARD CARD ===== */
    .leaderboard-card {{
        background: rgba(255, 255, 255, 0.92);
        border-radius: 1.5rem;
        padding: 1rem 1.5rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.35);
        backdrop-filter: blur(6px);
        display: flex;
        align-items: center;
        gap: 1rem;
        border: 3px solid #ffcc00;
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }}
    .leaderboard-card:hover {{
        transform: scale(1.02);
        box-shadow: 0 1rem 2rem rgba(255, 204, 0, 0.7);
    }}

    /* ===== GLOBAL FONT ===== */
    html, body, .stApp, h1, h2, h3, h4, h5, h6, p, span, div, button {{
        font-family: 'Press Start 2P', cursive !important;
        letter-spacing: 0.04em;
    }}

    /* ===== SECTION HEADERS ===== */
    h1, h2, h3 {{
        color: #ffcc00 !important;
        text-shadow:
            -2px -2px 0 #000,
            2px 2px 0 #000,
            0 0 10px #ff0000,
            0 0 15px #00ccff;
    }}
    h2 {{
        color: #00ffff !important;
        text-shadow:
            -2px -2px 0 #000,
            2px 2px 0 #000,
            0 0 8px #0077ff;
    }}

    /* ===== LEADERBOARD TEXT (simplified for readability) ===== */
    .leaderboard-rank {{
        font-size: 1.6rem;
        font-weight: 900;
        color: #ff2d2d;
        text-shadow:
            1px 1px 0 #fff,
            -1px -1px 0 #fff,
            2px 2px 4px rgba(0,0,0,0.3);
    }}

    .leaderboard-time {{
        font-size: 1.3rem;
        font-weight: 800;
        color: #111;
        text-shadow:
            1px 1px 0 #fff,
            -1px -1px 0 #fff;
    }}

    .player-name {{
        font-size: 0.9rem;
        font-weight: 700;
        color: #222;
        text-shadow:
            1px 1px 0 #fff;
    }}

    .character-name {{
        font-size: 0.9rem;
        font-weight: 800;
        color: #d49b00;
        text-shadow:
            1px 1px 0 #fff;
    }}

    /* ===== PLAYER IMAGES ===== */
    .img-round {{
        border-radius: 20%;
        border: 4px solid #ffdc00;
        box-shadow:
            0 0 10px #ff0000,
            0 0 20px #ffdc00,
            0 0 30px #00ffff;
        object-fit: cover;
        width: 70px;
        height: 100px;
        image-rendering: pixelated;
        background: rgba(255, 255, 255, 0.25);
    }}

    /* ===== ENTRY ANIMATION ===== */
    @keyframes riseUp {{
        0% {{ transform: translateY(40px); opacity: 0; }}
        100% {{ transform: translateY(0); opacity: 1; }}
    }}
    .new-entry {{
        animation: riseUp 0.7s ease-out;
    }}
    """




    st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

inject_theme()

# ---------- DATA HELPERS ----------

@st.cache_data(ttl=5)
def load_data():
    if not DATA_FILE.exists():
        return pd.DataFrame(), pd.DataFrame()

    xls = pd.ExcelFile(DATA_FILE)
    results = pd.read_excel(xls, sheet_name=RESULTS_SHEET)
    players = pd.read_excel(xls, sheet_name=PLAYERS_SHEET)

    # Normalise column names just in case (lowercase)
    results.columns = [c.strip().lower() for c in results.columns]
    players.columns = [c.strip().lower() for c in players.columns]

    # Parse time
    if "time" in results.columns:
        results["time_seconds"] = results["time"].apply(parse_time_to_seconds)
    else:
        results["time_seconds"] = None

    return results, players


def parse_time_to_seconds(val):
    if pd.isna(val):
        return None
    s = str(val).strip()

    # Direct numeric values
    try:
        return float(s)
    except ValueError:
        pass

    # Accept "mm:ss", "m:ss", "hh:mm:ss", with optional decimals
    match = re.match(r'(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)$', s)  # hh:mm:ss or mm:ss
    if match:
        h, m, sec = match.groups()
        h = int(h) if h else 0
        m = int(m)
        sec = float(sec)
        return h * 3600 + m * 60 + sec

    # Accept "m:ss" or "mm:ss"
    if ":" in s:
        try:
            parts = s.split(":")
            parts = [float(p) for p in parts]
            if len(parts) == 2:
                return parts[0]*60 + parts[1]
            elif len(parts) == 3:
                return parts[0]*3600 + parts[1]*60 + parts[2]
        except Exception:
            pass

    # fallback: no parse
    return None


def format_seconds(t):
    if t is None or pd.isna(t):
        return "-"
    t = float(t)
    m = int(t // 60)
    s = t % 60
    return f"{m}:{s:05.2f}" if m > 0 else f"{s:05.2f}"


def build_long_entries(results, players):
    """
    Turn results (p1, p2, time, character, date) into one row per player:
    columns: player, time_seconds, character, date, picture, service line, location
    """
    if results.empty or players.empty:
        return pd.DataFrame()

    # Make long format: one row per player per entry
    cols = ["time_seconds", "character"]
    if "date" in results.columns:
        cols.append("date")  # include date if present

    long_p1 = results[["p1"] + cols].rename(columns={"p1": "player"})
    long_p2 = results[["p2"] + cols].rename(columns={"p2": "player"})
    long_all = pd.concat([long_p1, long_p2], ignore_index=True)

    # Merge player info
    players = players.rename(columns={"service line": "service_line"})
    merged = long_all.merge(players, on="player", how="left")

    return merged



def load_image_safe(path: Path, size=None):
    try:
        img = Image.open(path).convert("RGBA")  # 🔹 Force RGBA to preserve transparency
        if size is not None:
            img = img.resize(size, Image.LANCZOS)
        return img
    except Exception:
        return None



def get_player_image(filename):
    if pd.isna(filename):
        return None
    path = PLAYER_PIC_DIR / str(filename)
    # Taller rectangle for passport-photo look
    return load_image_safe(path, size=(70, 100))


def get_character_image(character):
    if pd.isna(character):
        return None
    name = str(character).strip().lower().replace(" ", "_")
    path = CHARACTER_PIC_DIR / f"{name}.png"
    if not path.exists():
        st.warning(f"⚠️ Missing character image: {path}")
        print("⚠️ Missing character image:", path)
        return None
    img = Image.open(path).convert("RGBA")
    img = img.resize((80, 80), Image.LANCZOS)
    return img


# ---------- STATE FOR ANIMATIONS ----------

if "known_entry_keys" not in st.session_state:
    st.session_state["known_entry_keys"] = set()


def get_entry_key(row):
    # Unique-ish ID for a result row
    return f"{row.get('p1','')}-{row.get('p2','')}-{row.get('character','')}-{row.get('time_seconds','')}"


# ---------- MAIN UI ----------

# Simple autorefresh by re-running with a changing widget value
# (This trick uses an empty selectbox that changes every X seconds)
st.markdown(
    f"""
    <script>
    function reload() {{
        window.location.reload();
    }}
    setTimeout(reload, {AUTOREFRESH_SECONDS * 1000});
    </script>
    """,
    unsafe_allow_html=True,
)

st.title("🏁 Mario Kart Tournament Leaderboard")

page = st.sidebar.radio("Page", ["Leaderboard", "Service line stats"])

results_df, players_df = load_data()
long_df = build_long_entries(results_df, players_df)


# ---------- LEADERBOARD PAGE ----------

if page == "Leaderboard":
    st.subheader("Live Leaderboard")
    if results_df.empty:
        st.info("No results yet – add rows to the Excel file to get started.")
    else:
        # Sort by time ascending (fastest at top)
        results_sorted = results_df.sort_values("time_seconds", ascending=True).reset_index(drop=True)

        # Determine which entries are new
        current_keys = []
        for _, row in results_sorted.iterrows():
            current_keys.append(get_entry_key(row))

        previous_keys = st.session_state["known_entry_keys"]
        new_keys = set(current_keys) - previous_keys

        # Render cards
        for idx, row in results_sorted.iterrows():
            rank = idx + 1
            p1 = row["p1"]
            p2 = row["p2"]
            char = row["character"]
            time_str = format_seconds(row["time_seconds"])

            # Player info
            p1_info = players_df[players_df["player"] == p1].iloc[0] if (players_df["player"] == p1).any() else None
            p2_info = players_df[players_df["player"] == p2].iloc[0] if (players_df["player"] == p2).any() else None

            # Images
            p1_img = get_player_image(p1_info["picture"]) if p1_info is not None else None
            p2_img = get_player_image(p2_info["picture"]) if p2_info is not None else None
            char_img = get_character_image(char)

            # Colours + encode images
            bg_color = CHARACTER_COLORS.get(char.lower(), CHARACTER_COLORS["default"])
            def img_to_b64(img):
                if img is None: return ""
                import io, base64
                buf = io.BytesIO(); img.save(buf, format="PNG")
                return base64.b64encode(buf.getvalue()).decode()
            p1_b64, p2_b64, char_b64 = map(img_to_b64, [p1_img, p2_img, char_img])
            font_import = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
html, body, * {
    font-family: 'Press Start 2P', cursive !important;
    letter-spacing: 0.03em;
}
</style>
"""
            
            # --- Build the HTML string ---
            # --- Choose podium style based on rank ---
            def podium_style(rank):
                if rank == 1:
                    return "#FFD700", "0 0 15px #FFD700, 0 0 30px #FFF176"
                elif rank == 2:
                    return "#C0C0C0", "0 0 15px #C0C0C0, 0 0 30px #E0E0E0"
                elif rank == 3:
                    return "#CD7F32", "0 0 15px #CD7F32, 0 0 30px #FFB266"
                else:
                    return "#FF4B4B", "0 0 15px #FF4B4B, 0 0 30px #FF9999"

            border_col, glow = podium_style(rank)
            crown_b64 = get_base64(Path("assets/crown.png"))

            # --- Build the HTML string ---
            html = f"""
<div class="leaderboard-card" style="
  position: relative;
  border-radius: 1.25rem;
  border: 4px solid {border_col};
  background: linear-gradient(135deg, {bg_color}ee, #ffffffdd);
  overflow: hidden;
  animation: riseUp 0.7s ease-out;
  font-family: 'Press Start 2P', cursive;
  color: #fff;
  letter-spacing: 0.03em;
">
  <style>
  .leaderboard-card::before {{
      content: '';
      position: absolute;
      inset: -4px;
      border-radius: 1.25rem;
      background: radial-gradient(circle at center, {border_col}55 0%, transparent 70%);
      box-shadow: {glow};
      filter: blur(8px);
      z-index: -1;
  }}
  </style>

  <div style="display:flex;align-items:center;justify-content:space-between;width:100%;padding:1rem 1.5rem;">
    <!-- Rank -->
    <div style="flex:1;min-width:5rem;text-align:center;">
      <div style="font-size:1.2rem;color:#fff;
        filter: drop-shadow(1px 1px 0 #000) drop-shadow(-1px 1px 0 #000)
                drop-shadow(1px -1px 0 #000) drop-shadow(-1px -1px 0 #000);">
        #{rank}
      </div>
    </div>

    <!-- Time -->
    <div style="flex:2;text-align:center;">
      <div style="font-size:1rem;color:#fff;
        filter: drop-shadow(1px 1px 0 #000) drop-shadow(-1px 1px 0 #000)
                drop-shadow(1px -1px 0 #000) drop-shadow(-1px -1px 0 #000);">
        {time_str}
      </div>
    </div>

    <!-- Players -->
    <div style="flex:5;display:flex;align-items:center;justify-content:center;gap:2rem;">
      {"".join([
        f'''
        <div style="position:relative;text-align:center;">
          <div style="border-radius:20%;border:4px solid {border_col};
                      box-shadow:{glow};
                      display:inline-block;position:relative;">
            <img src="data:image/png;base64,{b64}" style="border-radius:16%;
                     width:70px;height:100px;object-fit:cover;display:block;">
            {f'<img src="data:image/png;base64,{crown_b64}" style="position:absolute;top:-10px;right:-8px;width:35px;transform:rotate(20deg);">' if rank == 1 else ''}
          </div>
          <div style="font-size:0.8rem;color:#fff;
              filter: drop-shadow(1px 1px 0 #000) drop-shadow(-1px 1px 0 #000)
                      drop-shadow(1px -1px 0 #000) drop-shadow(-1px -1px 0 #000);
              margin-top:4px;">{name}</div>
        </div>
        ''' for name, b64 in [(p1, p1_b64), (p2, p2_b64)] if b64
      ])}
    </div>

    <!-- Character -->
    <div style="flex:2;text-align:center;">
      {f'<img src="data:image/png;base64,{char_b64}" width="90" style="filter:drop-shadow(0 0 6px #000) drop-shadow(0 0 10px {bg_color});">' if char_b64 else ''}
      <div style="font-size:0.9rem;font-weight:800;color:#fff;
        filter: drop-shadow(1px 1px 0 #000) drop-shadow(-1px 1px 0 #000)
                drop-shadow(1px -1px 0 #000) drop-shadow(-1px -1px 0 #000);">
        {char}
      </div>
    </div>
  </div>
</div>
"""


            components.html(html, height=230, scrolling=False)

        # Update known keys AFTER rendering so the animation only fires once per new row
        st.session_state["known_entry_keys"] = set(current_keys)


# ---------- SERVICE LINE STATS PAGE ----------

if page == "Service line stats":
    st.subheader("Service line stats")

    if long_df.empty:
        st.info("No entries yet – add results to the Excel file.")
    else:
        # Guarantee consistent naming
        if "service_line" not in long_df.columns and "service line" in long_df.columns:
            long_df = long_df.rename(columns={"service line": "service_line"})

        # ---- Total entries by service line ----
        counts = (
            long_df.groupby("service_line")
            .size()
            .reset_index(name="total_entries")
            .sort_values("total_entries", ascending=False)
        )

        # ---- Average speed (time) by service line ----
        avg_times = (
            long_df.groupby("service_line")["time_seconds"]
            .mean()
            .reset_index(name="avg_time_seconds")
            .sort_values("avg_time_seconds", ascending=True)
        )
        avg_times["avg_time_str"] = avg_times["avg_time_seconds"].apply(format_seconds)

        col1, col2 = st.columns(2)

        # with col1:
        #     st.markdown("### 🧮 Entries by service line")
        #     st.bar_chart(
        #         counts.set_index("service_line")["total_entries"],
        #         height=400,
        #     )
        #     st.dataframe(counts.reset_index(drop=True), use_container_width=True)

        # with col2:
        #     st.markdown("### ⚡ Fastest service lines (average time)")
        #     st.dataframe(
        #         avg_times[["service_line", "avg_time_str", "avg_time_seconds"]],
        #         use_container_width=True,
        #     )

            # Little leaderboard-style printout
        # 🟨 Mario-style section title
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #ff0000cc, #ffcc00cc);
            border: 3px solid #fff200;
            box-shadow: 0 0 12px #ff0000, 0 0 20px #00ffff, 0 0 30px #ffcc00;
            color: #fff;
            padding: 0.8rem 1.2rem;
            border-radius: 1rem;
            font-family: 'Press Start 2P', cursive;
            font-size: 0.8rem;
            text-align: center;
            text-shadow: 2px 2px 0 #000, -2px -2px 0 #000;
            letter-spacing: 0.05em;
            margin-top: 1rem;
            margin-bottom: 1rem;
        ">
            ⭐ Leaderboard by Service Line ⭐
        </div>
        """, unsafe_allow_html=True)

        # 🧱 Mario-style glowing boxes (no ranks)
        colors = [
            ("#FFD700", "#fff8e1"),  # gold
            ("#C0C0C0", "#f0f0f0"),  # silver
            ("#CD7F32", "#ffe0b2"),  # bronze
        ]

        # Cycle through defined colors and fall back to red if >3
        for i, row in avg_times.iterrows():
            main_col, light_col = colors[i] if i < 3 else ("#ff4b4b", "#ffe5e5")
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {main_col}, {light_col});
                border: 3px solid #fff;
                box-shadow: 0 0 10px {main_col}, 0 0 20px {light_col}, 0 0 30px #ffffff88;
                color: #000;
                padding: 0.8rem 1.2rem;
                border-radius: 1rem;
                font-family: 'Press Start 2P', cursive;
                font-size: 0.7rem;
                text-align: center;
                text-shadow: 1px 1px 0 #fff, -1px -1px 0 #fff, 0 0 6px #00000055;
                letter-spacing: 0.04em;
                margin: 0.5rem 0;
            ">
                <b>{row['service_line']}</b><br>
                <span style="color:#000; font-size:0.75rem;">⏱ {row['avg_time_str']}</span>
            </div>
            """, unsafe_allow_html=True)



        # ---- Cumulative entries over time ----
        if "date" in long_df.columns:
            st.markdown("### 📈 Cumulative Entries Over Time")

            # Parse safely (dd/mm/yyyy) and strip time-of-day
            long_df["date"] = pd.to_datetime(
                long_df["date"], errors="coerce", dayfirst=True
            ).dt.date

            # Drop missing and group by day + service line
            df_time = (
                long_df.dropna(subset=["date", "service_line"])
                .groupby(["date", "service_line"])
                .size()
                .reset_index(name="entries")
                .sort_values("date")
            )

            # Compute cumulative counts per service line
            df_time["cumulative_entries"] = (
                df_time.groupby("service_line")["entries"].cumsum()
            )

            # Pivot for plotting
            df_pivot = (
                df_time.pivot(
                    index="date", 
                    columns="service_line", 
                    values="cumulative_entries"
                )
                .fillna(method="ffill")
            )

            # Force integer values (removes decimals on y-axis)
            df_pivot = df_pivot.astype(int)

            # Force plain string x-axis so Streamlit doesn't show time
            df_pivot.index = df_pivot.index.astype(str)

            st.line_chart(df_pivot, height=400, use_container_width=True)

        else:
            st.info("No 'date' column found in the data — add it to plot cumulative entries over time.")



