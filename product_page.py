import streamlit as st

def product_page():
    st.subheader("🥩 Product Management")

    name = st.text_input("Product Name")
    category = st.selectbox("Category", ["Chicken", "Mutton", "Fish"])
    price = st.number_input("Price per Kg", min_value=0)
    available = st.checkbox("Available")

    if st.button("Save Product"):
        st.success(f"{name} saved successfully")

    st.divider()
    st.write("### Existing Products")
    st.table([
        {"Name": "Chicken Curry Cut", "Price": 280, "Available": True},
        {"Name": "Mutton Boneless", "Price": 750, "Available": False},
    ])
