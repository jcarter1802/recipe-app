import streamlit as st
import pandas as pd

from utils import (
    parse_ingredient,
    singularize,
    normalized_raw_lines,
)

# -----------------------------
# Unified pantry key system
# -----------------------------
def pantry_key(item, unit):
    item = singularize(item.strip().lower()) if item else ""
    unit = unit.strip().lower() if unit else None
    return (item, unit)

def get_pantry_amount(item, unit):
    key = pantry_key(item, unit)
    return float(st.session_state.pantry.get(key, 0))

# -----------------------------
# Compare recipe to pantry
# -----------------------------
def compare_recipe_to_pantry(ingredients_cell):
    missing = []
    short = []
    matched = 0

    raw_lines = normalized_raw_lines(ingredients_cell)

    for raw in raw_lines:
        try:
            qty, unit, item = parse_ingredient(raw)
        except Exception:
            qty, unit, item = None, None, raw.strip().lower()

        item = singularize(item or "")
        have = get_pantry_amount(item, unit)

        # Countable items (no numeric qty)
        if qty is None:
            if have >= 1:
                matched += 1
            else:
                missing.append((item, unit, 1))
            continue

        # Numeric items
        if have >= qty:
            matched += 1
        else:
            short.append((item, unit, qty - have))

    return missing, short, matched

# -----------------------------
# Page start
# -----------------------------
st.title("🧾 Use Up Ingredients")

if "recipes" not in st.session_state or st.session_state.recipes.empty:
    st.info("No recipes loaded. Upload recipes on the main page first.")
    st.stop()

if "pantry" not in st.session_state:
    st.session_state.pantry = {}

df = st.session_state.recipes

# -----------------------------
# Pantry debug preview
# -----------------------------
st.write("### Pantry (Unified Key View)")
if st.session_state.pantry:
    preview = [{"item": k[0], "unit": k[1], "qty": v} for k, v in st.session_state.pantry.items()]
    st.dataframe(pd.DataFrame(preview))
else:
    st.write("Pantry is EMPTY")

st.markdown("---")

# -----------------------------
# Recipe loop
# -----------------------------
for idx, row in df.iterrows():
    recipe_name = row.get("Recipe Name", f"Recipe {idx}")
    ingredients_cell = row.get("Ingredients", [])

    missing, short, matched = compare_recipe_to_pantry(ingredients_cell)
    total = len(normalized_raw_lines(ingredients_cell))
    pct = (matched / total * 100) if total else 0

    st.subheader(f"{recipe_name} — {matched}/{total} ingredients available ({pct:.0f}%)")

    # Missing + short display
    if not missing and not short:
        st.success("You have everything for this recipe.")
    else:
        if missing:
            st.warning("Missing items:")
            for item, unit, amt in missing:
                st.write(f"- {amt} {unit or ''} {item}".strip())

        if short:
            st.info("Short on quantity:")
            for item, unit, amt in short:
                st.write(f"- Need {amt} more {unit or ''} {item}".strip())

    # Buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Add missing to shopping list", key=f"shop_{idx}"):
            if "shopping_list" not in st.session_state:
                st.session_state.shopping_list = []

            for item, unit, amt in missing + short:
                st.session_state.shopping_list.append({
                    "raw": f"{amt} {unit or ''} {item}".strip(),
                    "quantity": amt,
                    "unit": unit,
                    "ingredient": item
                })
            st.success("Added to shopping list.")

    with col2:
        if st.button("Cook this recipe (deduct pantry)", key=f"cook_{idx}"):
            for raw in normalized_raw_lines(ingredients_cell):
                try:
                    qty, unit, item = parse_ingredient(raw)
                except Exception:
                    qty, unit, item = None, None, raw.strip().lower()

                item = singularize(item or "")
                key = pantry_key(item, unit)

                if qty is None:
                    if st.session_state.pantry.get(key, 0) >= 1:
                        st.session_state.pantry[key] -= 1
                else:
                    if key in st.session_state.pantry:
                        st.session_state.pantry[key] = max(
                            0, st.session_state.pantry[key] - qty
                        )

            st.success("Pantry updated.")

    # Ingredient list
    with st.expander("Show ingredients"):
        cleaned_list = normalized_raw_lines(ingredients_cell)
        if not cleaned_list:
            st.write("No ingredients found.")
        else:
            for ing in cleaned_list:
                st.write(f"- {ing}")

    st.markdown("---")
