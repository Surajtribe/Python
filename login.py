import streamlit as st

def admin_login():
    st.subheader("🔐 Admin Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if email == "admin@desimeat.com" and password == "admin123":
            st.session_state["logged_in"] = True
            st.success("Login successful")
        else:
            st.error("Invalid credentials")
