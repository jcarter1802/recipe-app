# pages/Use_Up_Ingredients.py
import streamlit as st
import pandas as pd

# Import shared helpers. Ensure these exist in utils.py and are on PYTHONPATH.
# Required helpers: normalized_raw_lines, parse_ingredient, singularize
from utils import normalized_raw_lines, parse_ingredient, singularize

# Ensure session state keys exist
if "recipes" not in st.session_state:
    st.session_state.recipes = pd.DataFrame()

if "pantry" not in st.session_state:
    st.session_state.pantry = {}

st.title("🧾 Use Up Ingredients")

# Helper: canonical pantry key
def pantry_key(item, unit):
    return (singularize(item or ""), unit)

# Compare a single recipe's ingredients to the pantry.
# Accepts ingredients_cell which may be: list[dict], list[str], or str.
# Returns: (missing_list, short_list, matched_count)
def compare_recipe_to_pantry(ingredients_cell):
    missing = []
    short = []
    matched = 0

    # normalized_raw_lines returns list[str] (clean raw lines) or list of dicts if you prefer;
    # we handle both dict and string forms below.
    raw_lines = normalized_raw_lines(ingredients_cell)

    for raw in raw_lines:
        # If the recipe stores structured dicts, normalized_raw_lines may return raw strings.
        # Try to parse; if parse fails, treat as countable item with no quantity.
        try:
            qty, unit, item = parse_ingredient(raw)
        except Exception:
            qty, unit, item = None, None, raw.strip().lower()

        # canonicalize item
        item = singularize(item or "")

        key = pantry_key(item, unit)
        have = st.session_state.pantry.get(key, 0)

        # If no numeric quantity, treat as countable: require at least 1
        if qty is None:
            if have >= 1:
                matched += 1
            else:
                missing.append((item, unit, 1))
        else:
            if have >= qty:
                matched += 1
            else:
                short_amount = max(0, qty - have)
                short.append((item, unit, short_amount))

    return missing, short, matched

# UI: list recipes and show match summary
if st.session_state.recipes is None or st.session_state.recipes.empty:
    st.info("No recipes loaded. Upload recipes on the main page first.")
else:
    df = st.session_state.recipes

    # Show a compact summary table (recipe name and ingredient count)
    try:
        preview = []
        for _, row in df.iterrows():
            name = row.get("Recipe Name", "Unnamed")
            ingredients_cell = row.get("Ingredients", [])
            # Count non-empty parsed lines
            lines = normalized_raw_lines(ingredients_cell)
            preview.append({"Recipe Name": name, "Ingredient Count": len(lines)})
        st.dataframe(pd.DataFrame(preview).head(20))
    except Exception:
        # Fallback: show recipe names only
        st.write("Recipes:")
        for _, r in df.iterrows():
            st.write("-", r.get("Recipe Name", "Unnamed"))

    st.markdown("---")

    # Iterate recipes and show match details
    for idx, row in df.iterrows():
        recipe_name = row.get("Recipe Name", f"Recipe {idx}")
        ingredients_cell = row.get("Ingredients", [])

        missing, short, matched = compare_recipe_to_pantry(ingredients_cell)
        total_ingredients = len(normalized_raw_lines(ingredients_cell))

        # Header with match summary
        pct = (matched / total_ingredients * 100) if total_ingredients else 0
        st.subheader(f"{recipe_name} — {matched}/{total_ingredients} ingredients available ({pct:.0f}%)")

        # Show missing and short lists
        if not missing and not short:
            st.success("You have everything listed (or recipe has no parseable ingredients).")
        else:
            if missing:
                st.warning("Missing items (not in pantry):")
                for item, unit, amt in missing:
                    if unit:
                        st.write(f"- {amt} {unit} {item}")
                    else:
                        st.write(f"- {item} (x{amt})")
            if short:
                st.info("Short on quantity (need more):")
                for item, unit, amt in short:
                    if unit:
                        st.write(f"- {amt} {unit} {item}")
                    else:
                        st.write(f"- {item} (x{amt})")

        # Buttons: add missing to shopping list, or mark as cookable
        col1, col2 = st.columns(2)
        with col1:
            key_add = f"add_shop_{idx}"
            if st.button("Add missing to shopping list", key=key_add):
                # Build structured missing items and append to shopping_list
                if "shopping_list" not in st.session_state:
                    st.session_state.shopping_list = []
                for item, unit, amt in missing + short:
                    # store as simple string or structured dict depending on your app
                    st.session_state.shopping_list.append({
                        "raw": f"{amt} {unit or ''} {item}".strip(),
                        "quantity": amt,
                        "unit": unit,
                        "ingredient": item
                    })
                st.success("Missing items added to shopping list.")
        with col2:
            key_cook = f"cook_recipe_{idx}"
            if st.button("Mark as cookable (deduct pantry)", key=key_cook):
                # Deduct required quantities from pantry where possible
                for raw in normalized_raw_lines(ingredients_cell):
                    try:
                        qty, unit, item = parse_ingredient(raw)
                    except Exception:
                        qty, unit, item = None, None, raw.strip().lower()
                    item = singularize(item or "")
                    k = pantry_key(item, unit)
                    if qty is None:
                        # consume one if available
                        if st.session_state.pantry.get(k, 0) >= 1:
                            st.session_state.pantry[k] = st.session_state.pantry.get(k, 0) - 1
                    else:
                        if k in st.session_state.pantry:
                            st.session_state.pantry[k] = max(0, st.session_state.pantry.get(k, 0) - qty)
                st.success("Pantry updated for this recipe.")

        # Expand to show full ingredient list (cleaned)
      
        if isinstance(ingredients_cell, list):
            for i, el in enumerate(ingredients_cell):
                st.write(f"DEBUG list item {i} repr:", repr(el), "type:", type(el))

        # --- produce a cleaned list for widgets and display (remove empty/None entries) ---
        cleaned_list = normalized_raw_lines(ingredients_cell)
        cleaned_list = [o for o in cleaned_list if isinstance(o, str) and o.strip()]

        # fallback so widgets never receive an empty string
        if not cleaned_list:
            cleaned_list = []
        with st.expander("Show ingredients"):
            cleaned_list = normalized_raw_lines(ingredients_cell)
            if not cleaned_list:
                st.write("No ingredients listed for this recipe.")
            else:
                for ing in cleaned_list:
                    st.write(f"- {ing}")

        st.markdown("---")