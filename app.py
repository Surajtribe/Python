import streamlit as st
from login import admin_login
from products import product_page
from categories import category_page

st.set_page_config(page_title="Desi Meat Admin", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    admin_login()
else:
    st.sidebar.title("🛠️ Admin Panel")
    page = st.sidebar.radio("Navigate", ["Products", "Categories", "Logout"])

    if page == "Products":
        product_page()
    elif page == "Categories":
        category_page()
    elif page == "Logout":
        st.session_state["logged_in"] = False
        st.experimental_rerun()
