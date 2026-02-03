import streamlit as st

st.set_page_config(page_title="Login", layout="wide")

# ===== STYLE =====
st.markdown("""
<style>
body {
    background-color: #f5f7fb;
}
.login-box {
    background: white;
    padding: 40px;
    border-radius: 12px;
    width: 400px;
    margin: auto;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}
.title {
    text-align: center;
    font-size: 32px;
    font-weight: bold;
    color: #0d6efd;
}
</style>
""", unsafe_allow_html=True)

# ===== SESSION =====
if "login" not in st.session_state:
    st.session_state.login = False

# ===== UI =====
st.markdown("<div class='login-box'>", unsafe_allow_html=True)
st.markdown("<div class='title'>Welcome</div>", unsafe_allow_html=True)

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("LOGIN"):
    if email == "admin@gmail.com" and password == "1234":
        st.session_state.login = True
        st.switch_page("app.py")
    else:
        st.error("Email หรือ Password ไม่ถูกต้อง")

st.markdown("</div>", unsafe_allow_html=True)
