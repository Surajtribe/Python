import streamlit as st

def category_page():
    st.subheader("📦 Category Management")

    category = st.text_input("Category Name")

    if st.button("Add Category"):
        st.success(f"Category '{category}' added")

    st.write("### Categories")
    st.write("- Chicken")
    st.write("- Mutton")
    st.write("- Fish")
