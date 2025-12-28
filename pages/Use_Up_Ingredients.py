import streamlit as st
from recipe_app_v4 import parse_ingredient, format_amount
import pandas as pd

st.title("🍳 Use Up Ingredients")

# Ensure pantry exists
if "pantry" not in st.session_state:
    st.session_state.pantry = {}

# Ensure recipes exist
if "recipes" not in st.session_state or st.session_state.recipes.empty:
    st.warning("No recipes available yet.")
    st.stop()

recipes_df = st.session_state.recipes

def compare_recipe_to_pantry(ingredients_text):
    """Return match stats for a recipe."""
    missing = []
    short = []
    matched = []

    for line in ingredients_text.split("\n"):
        amount, unit, item = parse_ingredient(line)

        if item is None:
            continue

        key = (item, unit)
        pantry_amount = st.session_state.pantry.get(key, 0)

        if pantry_amount == 0:
            missing.append(line)
        elif pantry_amount < amount:
            short.append(f"{line} (short by {format_amount(amount - pantry_amount, unit)})")
        else:
            matched.append(line)

    return missing, short, matched


perfect_matches = []
almost_matches = []
poor_matches = []

for idx, row in recipes_df.iterrows():
    missing, short, matched = compare_recipe_to_pantry(row["Ingredients"])

    score = len(missing) + len(short)

    if score == 0:
        perfect_matches.append((row["Recipe Name"], missing, short, matched))
    elif score <= 2:
        almost_matches.append((row["Recipe Name"], missing, short, matched))
    else:
        poor_matches.append((row["Recipe Name"], missing, short, matched))

st.subheader("✅ Recipes You Can Make Right Now")
if perfect_matches:
    for name, missing, short, matched in perfect_matches:
        st.markdown(f"### {name}")
        st.write("All ingredients available!")
else:
    st.write("No perfect matches yet.")

st.subheader("🟡 Almost There (1–2 missing)")
if almost_matches:
    for name, missing, short, matched in almost_matches:
        st.markdown(f"### {name}")
        if missing:
            st.write("Missing:", missing)
        if short:
            st.write("Short:", short)
else:
    st.write("No almost matches yet.")

st.subheader("🔍 Other Recipes")
for name, missing, short, matched in poor_matches:
    st.markdown(f"### {name}")
    st.write(f"Missing {len(missing)} ingredients")