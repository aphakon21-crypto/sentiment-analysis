# src/dashboard/app.py
# -*- coding: utf-8 -*-

# ============================== IMPORTS ==============================

from __future__ import annotations
import os
from pathlib import Path
from datetime import datetime

import hashlib
import pandas as pd
import plotly.express as px
import streamlit as st



import sys, os
from pathlib import Path
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import base64

import requests

def fetch_facebook_comments(post_url: str) -> list[str]:
    """
    ดึงคอมเมนต์จาก Facebook Post
    (ตอนนี้เป็น mock เพื่อทดสอบระบบ)
    """
    # TODO: เชื่อม Facebook Graph API จริงในอนาคต
    return [
        "สินค้าคุณภาพแย่มาก",
        "บริการดี ประทับใจ",
        "เฉย ๆ ยังไม่แน่ใจ",
        "ส่งของช้า ไม่โอเคเลย",
    ]


def export_df_to_gsheet(df, spreadsheet_id: str, worksheet_name: str, clear_first=True):
    """
    ส่งออก DataFrame ไปยัง Google Sheets
    """
    # ตั้งค่า scope สำหรับ Google Sheets + Drive
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]

    import streamlit as st
from google.oauth2 import service_account

# โหลด credentials จาก Streamlit Secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)


    # เปิด Spreadsheet
    sh = client.open_by_key(spreadsheet_id)

    try:
        worksheet = sh.worksheet(worksheet_name)
        if clear_first:
            worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title=worksheet_name, rows="100", cols="20")

    # แปลง df → list of lists
    values = [df.columns.values.tolist()] + df.values.tolist()
    worksheet.update(values)

    return True

def test_gsheet_connection(spreadsheet_url_or_id, worksheet_name=None):
    try:
        # ถ้าเป็น URL → ดึง ID ออกมา
        if "docs.google.com" in spreadsheet_url_or_id:
            spreadsheet_id = spreadsheet_url_or_id.split("/d/")[1].split("/")[0]
        else:
            spreadsheet_id = spreadsheet_url_or_id

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "src/dashboard/credentials.json",
            scope
        )

        client = gspread.authorize(creds)
        client.open_by_key(spreadsheet_id)

        return True, "เชื่อมต่อ Google Sheets สำเร็จ ✅"

    except Exception as e:
        return False, f"เชื่อมต่อไม่สำเร็จ ❌ : {e}"



# บังคับให้ Python เห็น root ของโปรเจกต์
ROOT = Path(__file__).resolve().parents[2]   # 2 ขั้นเพราะไฟล์อยู่ใน src/dashboard/app.py
sys.path.append(str(ROOT))

# โหลดตัวทำนาย (โมเดลไฮบริด / rule / ML / LLM ได้หมด ตามไฟล์ของเรา)
from src.infer.predictor import predict_smart


# ============================== PAGE CONFIG ==============================
st.set_page_config(
    page_title="Retail Sentiment",
    page_icon="🛍️",
    layout="wide",
)

# เตรียม path หลัก + โฟลเดอร์ข้อมูล
ROOT = Path(__file__).resolve().parents[2]   # project root
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = DATA_DIR / "log.csv"


# ============================== LOAD CSS (UTF-8) ==============================
def inject_css(relative_path: str):
    """
    โหลดไฟล์ CSS ที่ assets/style.css (เข้ารหัส UTF-8)
    """
    here = Path(__file__).resolve()
    root = here.parents[2]           # project root
    css_path = (root / relative_path).resolve()
    if not css_path.exists():
        st.warning(f"ไม่พบไฟล์ CSS: {css_path}")
        return
    css = css_path.read_text(encoding="utf-8", errors="ignore")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# เรียกใช้ CSS (อย่าลืมสร้าง/แก้ใน assets/style.css)
inject_css("assets/style.css")

# Tab Animation (เพิ่มคลาสให้คอนเทนเนอร์หลักเพื่อช่วยให้เกิด effect เวลาเปลี่ยนแท็บ)
st.markdown(
    """
    <style>
      .tab-fade-in { animation: tabfade .35s ease both; }
      @keyframes tabfade { from {opacity:0; transform: translateY(6px);} to {opacity:1; transform:none;} }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================== USER AUTH (SHA-256 + SALT) ==============================
def _get_users_from_secrets() -> dict[str, dict]:
    """
    โครงสร้าง .streamlit/secrets.toml ที่คาดหวัง:

    [users.alice]
    display_name = "Alice"
    role  = "admin"
    salt  = "Z3N8Q9"
    hash  = "2e4128bb-7051-40b3-a29b-d1f6699569e8"  # <== sha256((salt + password).encode()).hexdigest()

    [users.bob]
    display_name = "Bob"
    role  = "user"
    salt  = "A1B2C3"
    hash  = "....."
    """
    users = st.secrets.get("users", {})
    return users


def _verify_password(password_plain: str, salt: str, hash_hex: str) -> bool:
    return hashlib.sha256((salt + password_plain).encode("utf-8")).hexdigest() == hash_hex


def login_form():
    st.markdown(
        """
        <div class="login-wrapper">
          <div class="login-card">
            <div class="login-left">
              <h1>Retail Sentiment</h1>
              <p>
                วิเคราะห์ความคิดเห็นลูกค้าด้วย AI<br>
                โมเดลอัจฉริยะ • Dashboard ทันสมัย<br>
                เชื่อมต่อ Google Sheets
              </p>
            </div>
            <div class="login-right">
              <div class="login-title">เข้าสู่ระบบ</div>
              <div class="login-sub">ยินดีต้อนรับ 👋 กรุณาเข้าสู่ระบบ</div>
        """,
        unsafe_allow_html=True
    )

    # ===== ฟอร์มจริง (ต้องเป็น Streamlit) =====
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("ชื่อผู้ใช้")
        password = st.text_input("รหัสผ่าน", type="password")

        submit = st.form_submit_button("เข้าสู่ระบบ", use_container_width=True)

    st.markdown(
        """
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if submit:
        users = _get_users_from_secrets()
        u = users.get(username)

        if not u:
            st.error("ไม่พบผู้ใช้นี้")
            return False

        if _verify_password(password, u["salt"], u["hash"]):
            st.session_state.auth = {
                "logged_in": True,
                "username": username,
                "display_name": u.get("display_name", username),
                "role": u.get("role", "user"),
            }
            st.success("เข้าสู่ระบบสำเร็จ")
            st.rerun()
        else:
            st.error("รหัสผ่านไม่ถูกต้อง")

    st.markdown(
        "<div style='text-align:center;margin-top:1rem;'>"
        "ยังไม่มีบัญชี? <a href='#'>สมัครสมาชิก</a>"
        "</div>",
        unsafe_allow_html=True
    )

    return False
def require_login():
    if "auth" not in st.session_state or not st.session_state.auth.get("logged_in"):
        login_form()
        st.stop()




# ============================== LOGGING HELPERS ==============================
def append_log(text: str, label: str):
    row = {"timestamp": datetime.now().isoformat(timespec="seconds"), "text": text, "label": label}
    if LOG_PATH.exists():
        df = pd.read_csv(LOG_PATH)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df.to_csv(LOG_PATH, index=False, encoding="utf-8-sig")


def load_log() -> pd.DataFrame:
    if LOG_PATH.exists():
        df = pd.read_csv(LOG_PATH)
        if "date" not in df.columns and "timestamp" in df.columns:
            df["date"] = pd.to_datetime(df["timestamp"]).dt.date.astype(str)
        return df
    return pd.DataFrame(columns=["timestamp", "text", "label", "date"])


def make_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame({"label": ["pos", "neu", "neg"], "count": [0, 0, 0]})
    cnt = df["label"].value_counts().reindex(["pos", "neu", "neg"], fill_value=0)
    return pd.DataFrame({"label": cnt.index, "count": cnt.values})


# ============================== NAV / HERO ==============================
def banner():
    banner_path = ROOT / "assets" / "banner.png"
    if not banner_path.exists():
        return

    encoded = base64.b64encode(banner_path.read_bytes()).decode()

    st.markdown(
        f"""
        <div style="margin-bottom:20px;">
            <img src="data:image/png;base64,{encoded}"
                 style="
                    width:100%;
                    max-height:360px;
                    object-fit:cover;
                    border-radius:18px;
                    box-shadow:0 10px 30px rgba(0,0,0,.08);
                 ">
        </div>
        """,
        unsafe_allow_html=True
    )

def navbar():
    with st.container():
        st.markdown(
            """
            <div class="navbar">
              <div class="brand">
                <span class="dot"></span>
                <span>Retail Sentiment</span>
              </div>
              <div class="nav-actions">
                <a href="#" onclick="window.location.reload()">Refresh</a>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def hero():
    st.markdown(
        """
        <div class="hero">
          <h1>🛍️ Retail Sentiment Dashboard</h1>
          <p style="margin-top:6px;color:var(--muted)">
            วิเคราะห์ความรู้สึกลูกค้าด้วย AI • โมเดลไฮบริด • ส่งออก Google Sheets
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================== PAGES ==============================
def page_analyze():
    st.markdown("<div class='tab-fade-in'>", unsafe_allow_html=True)

    st.markdown("<h3 class='section-title'>🔎 วิเคราะห์ข้อความ</h3>", unsafe_allow_html=True)

    # ===================== MODE 1: ข้อความเดียว =====================
    st.subheader("📝 วิเคราะห์จากข้อความเดียว")
    txt = st.text_area(
        "ข้อความลูกค้า / คอมเมนต์",
        placeholder="เช่น: อาหารอร่อยมาก บริการดี",
        height=120,
    )

    c1, c2 = st.columns([0.25, 0.75])
    if c1.button("วิเคราะห์ข้อความ", use_container_width=True):
        if not txt.strip():
            st.warning("กรุณาพิมพ์ข้อความก่อน")
        else:
            label = predict_smart(txt)
            append_log(txt, label)
            st.markdown(
                f"""
                <div class="pill {label} fade-in">
                  <span class="dot"></span> ผลลัพธ์: {label}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ===================== MODE 2: Facebook Post =====================
    st.subheader("🔗 วิเคราะห์จากลิงก์ Facebook Post")
    post_url = st.text_input(
        "วางลิงก์โพสต์ Facebook",
        placeholder="https://www.facebook.com/...",
    )

    if st.button("ดึงคอมเมนต์และวิเคราะห์", use_container_width=True):
        if not post_url.strip():
            st.warning("กรุณาใส่ลิงก์โพสต์")
        else:
            with st.spinner("กำลังดึงคอมเมนต์จากโพสต์..."):
                comments = fetch_facebook_comments(post_url)

            if not comments:
                st.info("ไม่พบคอมเมนต์ในโพสต์นี้")
            else:
                results = []
                for c in comments:
                    label = predict_smart(c)
                    append_log(c, label)
                    results.append({
                        "comment": c,
                        "label": label
                    })

                df = pd.DataFrame(results)

                st.success(f"วิเคราะห์ทั้งหมด {len(df)} คอมเมนต์แล้ว ✅")
                st.dataframe(df, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)



def page_summary():
    st.markdown("<div class='tab-fade-in'>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-title'>📊 สรุปภาพรวม</h3>", unsafe_allow_html=True)

    df_log = load_log()
    df_sum_all = make_summary(df_log)

    # === Filters ===
    colF1, colF2, colF3 = st.columns([0.35, 0.35, 0.3])
    if not df_log.empty:
        dmin = pd.to_datetime(df_log["timestamp"]).min().date()
        dmax = pd.to_datetime(df_log["timestamp"]).max().date()
    else:
        dmin = dmax = datetime.now().date()

    with colF1:
        date_from = st.date_input("จากวันที่", value=dmin, min_value=dmin, max_value=dmax)
    with colF2:
        date_to = st.date_input("ถึงวันที่", value=dmax, min_value=dmin, max_value=dmax)
    with colF3:
        label_filter = st.multiselect("กรองด้วยผลลัพธ์", ["pos", "neu", "neg"], default=["pos", "neu", "neg"])

    # apply filters
    if not df_log.empty:
        dfl = df_log.copy()
        dfl["dt"] = pd.to_datetime(dfl["timestamp"]).dt.date
        dfl = dfl[(dfl["dt"] >= date_from) & (dfl["dt"] <= date_to) & (dfl["label"].isin(label_filter))]
    else:
        dfl = df_log

    # KPI Cards
    df_sum_f = make_summary(dfl)
    total = len(dfl)
    pos = int(df_sum_f.loc[df_sum_f["label"] == "pos", "count"].values[0]) if not df_sum_f.empty else 0
    neu = int(df_sum_f.loc[df_sum_f["label"] == "neu", "count"].values[0]) if not df_sum_f.empty else 0
    neg = int(df_sum_f.loc[df_sum_f["label"] == "neg", "count"].values[0]) if not df_sum_f.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    for c, t, v in [(c1, "ทั้งหมด", total), (c2, "บวก (pos)", pos), (c3, "กลาง (neu)", neu), (c4, "ลบ (neg)", neg)]:
        with c:
            st.markdown(
                f"""
                <div class="card">
                  <div style="color:var(--muted)">{t}</div>
                  <div style="font-size:30px;font-weight:800;margin-top:2px;">{v}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Charts
    colG1, colG2 = st.columns([0.55, 0.45])

    with colG1:
        st.caption("สัดส่วนแต่ละคลาส (Bar)")
        if df_sum_f["count"].sum() == 0:
            st.info("ยังไม่มีข้อมูลในช่วงที่เลือก")
        else:
            fig_bar = px.bar(
                df_sum_f, x="label", y="count", text="count", height=360,
                color="label",
                color_discrete_map={"pos": "#2bd576", "neu": "#9aa0a6", "neg": "#ff6b6b"},
            )
            fig_bar.update_traces(textposition="outside")
            st.plotly_chart(fig_bar, use_container_width=True)

    with colG2:
        st.caption("สัดส่วนแต่ละคลาส (Pie)")
        if df_sum_f["count"].sum() == 0:
            st.info("ยังไม่มีข้อมูลในช่วงที่เลือก")
        else:
            fig_pie = px.pie(
                df_sum_f, names="label", values="count", height=360,
                color="label",
                color_discrete_map={"pos": "#2bd576", "neu": "#9aa0a6", "neg": "#ff6b6b"},
                hole=0.35,
            )
            fig_pie.update_traces(textposition="inside")
            st.plotly_chart(fig_pie, use_container_width=True)

    st.caption("แนวโน้มรายวัน (Daily Trend)")
    if dfl.empty:
        st.info("ยังไม่มีข้อมูลในช่วงที่เลือก")
    else:
        daily = (
            dfl.assign(date=pd.to_datetime(dfl["timestamp"]).dt.date)
            .groupby(["date", "label"])
            .size()
            .reset_index(name="count")
        )
        fig_line = px.line(
            daily, x="date", y="count", color="label", markers=True, height=380,
            color_discrete_map={"pos": "#2bd576", "neu": "#9aa0a6", "neg": "#ff6b6b"},
        )
        fig_line.update_layout(xaxis_title="date", yaxis_title="count")
        st.plotly_chart(fig_line, use_container_width=True)

    st.caption("ประวัติ (ตามตัวกรอง)")
    st.dataframe(dfl.sort_values("timestamp").reset_index(drop=True), use_container_width=True)

    st.download_button(
        "⬇️ ดาวน์โหลดข้อมูลที่กรอง (CSV)",
        data=dfl.to_csv(index=False, encoding="utf-8-sig"),
        file_name=f"sentiment_logs_{date_from}_{date_to}.csv",
        mime="text/csv",
        use_container_width=True,
    )
    

    st.markdown("</div>", unsafe_allow_html=True)
import re

def _extract_sheet_id(url: str) -> str:
    """
    Extract Google Sheet ID from URL or return raw input if already ID.
    """
    if not url:
        return None
    
    # Regex หาค่า sheet id
    m = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    if m:
        return m.group(1)
    return url.strip()


def page_settings():
    st.header("⚙️ Settings & Export")
    st.write("Google Sheets · ส่งออกข้อมูลไปยังสเปรดชีต")

    # --- ค่าจาก session (จำค่าที่ผู้ใช้เคยกรอก) ---
    s_state = st.session_state
    default_spreadsheet = s_state.get("gsheet_input", "")
    default_ws_logs = s_state.get("ws_logs", "logs")
    default_ws_summary = s_state.get("ws_summary", "summary")
    default_clear = s_state.get("gs_clear_first", True)

    spreadsheet_input = st.text_input(
        "Spreadsheet URL หรือ ID",
        value=default_spreadsheet,
        placeholder="วาง URL ของ Google Sheet หรือพิมพ์เฉพาะ ID ก็ได้",
    )
    ws_logs = st.text_input("ชื่อ Worksheet สำหรับบันทึก Log", value=default_ws_logs)
    ws_summary = st.text_input("ชื่อ Worksheet สำหรับ Summary", value=default_ws_summary)

    col_btn1, col_chk = st.columns([0.7, 0.3])
    with col_chk:
        clear_first = st.checkbox("ล้างชีตก่อนเขียน (แนะนำ)", value=default_clear)

    # เก็บค่ากลับเข้า session
    s_state.gsheet_input = spreadsheet_input
    s_state.ws_logs = ws_logs
    s_state.ws_summary = ws_summary
    s_state.gs_clear_first = clear_first

    # ===== ปุ่มทดสอบการเชื่อมต่อ =====
    if col_btn1.button("🔗 ทดสอบการเชื่อมต่อ", use_container_width=True):
        try:
            sheet_id = _extract_sheet_id(spreadsheet_input)
            test_gsheet_connection(sheet_id, ws_logs)
            st.success("เชื่อมต่อสำเร็จ และเขียนข้อความทดสอบลง A1 แล้ว ✅")
        except Exception as e:
            st.error(f"ทดสอบล้มเหลว: {e}")

    st.markdown("---")

    # ===== ปุ่มส่งออก =====
    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        if st.button("📤 Export Logs", use_container_width=True):
            try:
                df_logs = load_log()  # ใช้ของเดิมในโปรเจกต์คุณ
                if df_logs.empty:
                    st.info("ยังไม่มี Log ให้ส่งออก")
                else:
                    sheet_id = _extract_sheet_id(spreadsheet_input)
                    export_df_to_gsheet(df_logs, sheet_id, ws_logs, clear_first)
                    st.success("ส่งออก Logs สำเร็จ 🚀")
            except Exception as e:
                st.error(f"ส่งออกล้มเหลว: {e}")

    with col_exp2:
        if st.button("📤 Export Summary", use_container_width=True):
            try:
                df_logs = load_log()
                df_sum = make_summary(df_logs)  # ใช้ของเดิมในโปรเจกต์คุณ
                sheet_id = _extract_sheet_id(spreadsheet_input)
                export_df_to_gsheet(df_sum, sheet_id, ws_summary, clear_first)
                st.success("ส่งออก Summary สำเร็จ 🚀")
            except Exception as e:
                st.error(f"ส่งออกล้มเหลว: {e}")
     
def show_user_page():
        st.header("👤 User Profile")
        auth = st.session_state.auth
        st.markdown(f"**ชื่อผู้ใช้:** {auth.get('display_name', auth.get('username'))}")
        st.markdown(f"**บทบาท:** {auth.get('role', 'user')}")
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            del st.session_state.auth
            st.success("ออกจากระบบเรียบร้อย")
            st.rerun()
        st.divider()
        if st.button("🗑️ ลบข้อมูลทั้งหมด", type="primary"):
            st.session_state.clear()
            st.warning("ลบข้อมูลทั้งหมดแล้ว")
            st.rerun()
               





# ============================== LAYOUT & SIDEBAR ==============================
def sidebar():
    with st.sidebar:
        st.header("⚙️ Actions")
        if st.button("ล้างประวัติ (ลบเฉพาะไฟล์ในเครื่อง)", use_container_width=True):
            if LOG_PATH.exists():
                LOG_PATH.unlink()
            st.success("ลบประวัติเรียบร้อย")
            st.rerun()


# ============================== MAIN ==============================
def main():
    # ต้องล็อกอินก่อน
    require_login()
    
    sidebar()
    navbar()
    hero()
    banner() 

    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Analyze", "📊 Summary", "⚙️ Settings", "👤 Profile"])
    with tab1:
        page_analyze()
    with tab2:
        page_summary()
    with tab3:
        page_settings()
    with tab4:
        show_user_page()

if __name__ == "__main__":
    main()
