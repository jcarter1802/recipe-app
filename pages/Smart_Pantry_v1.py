import streamlit as st
from recipe_app_v4 import parse_ingredient, format_amount  # make sure this filename matches

st.title("🏡 Smart Pantry")

# ✅ Ensure pantry exists in session_state
if "pantry" not in st.session_state:
    st.session_state.pantry = {}

# ✅ Add to pantry form
with st.form("add_to_pantry"):
    pantry_input = st.text_input("Add ingredient to pantry (e.g., '1 ½ cup sugar')")
    submitted_pantry = st.form_submit_button("Add to Pantry")

if submitted_pantry and pantry_input.strip():
    amount, unit, item = parse_ingredient(pantry_input)

    if amount is None:
        st.error("Could not understand that ingredient.")
    else:
        key = (item, unit)
        st.session_state.pantry[key] = st.session_state.pantry.get(key, 0) + amount
        st.success(f"Added {pantry_input} to pantry!")

# ✅ Display pantry contents
st.subheader("Your Pantry")

if st.session_state.pantry:
    for (item, unit), amount in st.session_state.pantry.items():
        if unit:
            st.write(f"- {format_amount(amount, unit)} {item}")
        else:
            st.write(f"- {item} (x{amount})")
else:
    st.write("Your pantry is empty.")