import yaml
import base64
import streamlit as st
from yaml import SafeLoader
import streamlit_authenticator as stauth

from pages.helper import db_queries


st.set_page_config(page_title="Reunite AI – Admin", layout="wide")


def add_bg_from_local(image_file: str):
    """Set a background image from local file."""
    try:
        with open(image_file, "rb") as image_file_obj:
            encoded_string = base64.b64encode(image_file_obj.read())
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url(data:image/{"png"};base64,{encoded_string.decode()});
                background-size: cover;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        
        pass


if "login_status" not in st.session_state:
    st.session_state["login_status"] = False

try:
    with open("login_config.yml") as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error("Configuration file 'login_config.yml' not found")
    st.stop()

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

# Admin login
st.title("Reunite AI – Admin Console")
authenticator.login(location="main")

if st.session_state.get("authentication_status"):
    authenticator.logout("Logout", "sidebar")

    st.session_state["login_status"] = True
    user_info = config["credentials"]["usernames"][st.session_state["username"]]
    st.session_state["user"] = user_info["name"]

    st.subheader(f"Welcome, {user_info['name']}")
    st.write(f"{user_info['area']}, {user_info['city']}")
    st.caption(f"Role: {user_info['role']}")

    st.write("---")

    found_cases = db_queries.get_registered_cases_count(user_info["name"], "F")
    non_found_cases = db_queries.get_registered_cases_count(user_info["name"], "NF")

    found_col, not_found_col = st.columns(2)
    found_col.metric("Cases marked as found", value=len(found_cases))
    not_found_col.metric("Open (not found) cases", value=len(non_found_cases))

    st.info(
        "Use the navigation menu (left sidebar) to register new cases, review existing "
        "records, and run face matching."
    )

elif st.session_state.get("authentication_status") is False:
    st.error("Incorrect username or password.")
elif st.session_state.get("authentication_status") is None:
    st.warning("Please sign in with your admin credentials.")
    st.session_state["login_status"] = False
