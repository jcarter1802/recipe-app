import pandas as pd
from rapidfuzz import fuzz
import streamlit as st
import re
from fractions import Fraction

# ✅ Ensure recipes DataFrame exists
if "recipes" not in st.session_state:
    st.session_state.recipes = pd.DataFrame(
        columns=["Recipe Name", "Ingredients", "Instructions"]
    )

# ✅ Ensure shopping list exists
if "shopping_list" not in st.session_state:
    st.session_state.shopping_list = []

UNIT_MAP = {
    "g": ("g", 1), "gram": ("g", 1), "grams": ("g", 1),
    "kg": ("g", 1000), "kilogram": ("g", 1000), "kilograms": ("g", 1000),

    "ml": ("ml", 1), "millilitre": ("ml", 1), "milliliter": ("ml", 1),
    "l": ("ml", 1000), "litre": ("ml", 1000), "liter": ("ml", 1000),

    "tbsp": ("tbsp", 1), "tablespoon": ("tbsp", 1), "tablespoons": ("tbsp", 1),
    "tsp": ("tsp", 1), "teaspoon": ("tsp", 1), "teaspoons": ("tsp", 1),
    "cup": ("cup", 1), "cups": ("cup", 1)
}

from fractions import Fraction
import re

def fraction_to_float(text):
    # Clean weird spaces
    text = (
        text.replace("\u00A0", " ")
            .replace("\u2009", " ")
            .replace("\u202F", " ")
            .replace("\u200A", " ")
            .replace("\u200B", "")
            .replace("\uFEFF", "")
    )

    unicode_fracs = {
        "¼": 1/4, "½": 1/2, "¾": 3/4,
        "⅐": 1/7, "⅑": 1/9, "⅒": 1/10,
        "⅓": 1/3, "⅔": 2/3,
        "⅕": 1/5, "⅖": 2/5, "⅗": 3/5, "⅘": 4/5,
        "⅙": 1/6, "⅚": 5/6,
        "⅛": 1/8, "⅜": 3/8, "⅝": 5/8, "⅞": 7/8,
    }

    # Replace unicode fractions with numeric equivalents
    for sym, val in unicode_fracs.items():
        text = text.replace(sym, f" {val} ")

    text = text.strip()

    # Mixed number: "2 1/2"
    if " " in text and "/" in text:
        whole, frac = text.split(" ", 1)
        try:
            return float(whole) + float(Fraction(frac))
        except:
            return None

    # Simple fraction: "1/2"
    if "/" in text:
        try:
            return float(Fraction(text))
        except:
            return None

    # Decimal or whole number
    try:
        return float(text)
    except:
        return None

def singularize(item):
    item = item.strip().lower()

    irregular = {
        "tomatoes": "tomato", "potatoes": "potato",
        "leaves": "leaf", "knives": "knife",
        "loaves": "loaf", "berries": "berry",
        "cloves": "clove",
    }

    if item in irregular:
        return irregular[item]

    if item.endswith("ies"):
        return item[:-3] + "y"

    if item.endswith("es") and not item.endswith(("ches", "shes", "xes", "sses")):
        return item[:-2]

    if item.endswith("s"):
        return item[:-1]

    return item

def parse_ingredient(ingredient):
    ingredient = ingredient.strip().lower()

    # Normalise all weird spaces
    ingredient = (
        ingredient.replace("\u00A0", " ")
                  .replace("\u2009", " ")
                  .replace("\u202F", " ")
                  .replace("\u200A", " ")
                  .replace("\u200B", "")
                  .replace("\uFEFF", "")
    )

    # ✅ Extract ANY valid amount format
    amount_match = re.match(
        r"^("
        r"\d+\s+[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]"   # mixed unicode fraction: "2 ½", "1 ⅓"
        r"|\d+[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]"       # attached unicode fraction: "2½", "1⅓"
        r"|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]"          # unicode fraction alone: "½"
        r"|\d+\s+\d+/\d+"                    # mixed normal fraction: "2 1/2"
        r"|\d+/\d+"                          # normal fraction: "1/2"
        r"|\d+\.\d+"                         # decimal: "1.5"
        r"|\d+"                              # whole number: "2"
        r")",
        ingredient
    )

    if not amount_match:
        return None, None, singularize(ingredient)

    amount_text = amount_match.group(0)
    rest = ingredient[len(amount_text):].strip()

    # ✅ Extract unit
    unit_match = re.match(r"^([a-zA-Z]+)", rest)
    if not unit_match:
        return None, None, singularize(rest)

    unit = unit_match.group(1).lower()
    item = rest[len(unit):].strip()

    # ✅ Convert amount
    amount = fraction_to_float(amount_text)
    if amount is None:
        return None, None, singularize(item)

    # ✅ Normalise unit
    if unit in UNIT_MAP:
        norm_unit, multiplier = UNIT_MAP[unit]
        return amount * multiplier, norm_unit, singularize(item)

    return amount, unit, singularize(item)

def combine_ingredients(ingredients):
    combined = {}

    for ing in ingredients:
        amount, unit, item = parse_ingredient(ing)
        key = (item, unit)

        if key not in combined:
            combined[key] = 0

        if amount is not None:
            combined[key] += amount
        else:
            combined[key] += 1

    return combined

def format_amount(amount, unit):
    if unit == "g" and amount >= 1000:
        return f"{amount/1000:.1f}kg"
    if unit == "ml" and amount >= 1000:
        return f"{amount/1000:.1f}l"
    return f"{amount}{unit}" if unit else str(amount)

# --- Manual recipe entry form ---
with st.form("add_recipe"):
    recipe_name = st.text_input("Recipe Name")
    ingredients = st.text_area("Ingredients (comma-separated)")
    servings = st.number_input("Number of servings", min_value=1, step=1)
    submitted = st.form_submit_button("Add Recipe")

if submitted and recipe_name.strip() and ingredients.strip():
    new_recipe = pd.DataFrame([{
        "Recipe Name": recipe_name.strip(),
        "Ingredients": [i.strip().lower() for i in ingredients.split(",")],
        "Servings": servings
    }])
    st.session_state.recipes = pd.concat([st.session_state.recipes, new_recipe], ignore_index=True)

    # Normalize safeguard
    st.session_state.recipes["Ingredients"] = st.session_state.recipes["Ingredients"].apply(
        lambda x: x if isinstance(x, list) else [i.strip().lower() for i in str(x).split(",")]
    )

    st.success(f"Added recipe: {recipe_name} ({servings} servings)")

# --- Search function ---
def search_recipes(recipes, search_terms, threshold=0.5, min_percentage=0):
    search_ingredients = [s.strip().lower() for s in search_terms]
    results = []

    for _, row in recipes.iterrows():
        recipe_name = row["Recipe Name"]
        recipe_ingredients = row["Ingredients"]

        overlap = []
        for s in search_ingredients:
            for r in recipe_ingredients:
                score = fuzz.partial_ratio(s, r)
                if score >= threshold:
                    overlap.append((r, score))
                    break

        match_fraction = len(overlap) / len(search_ingredients) if search_ingredients else 0

        if match_fraction >= min_percentage:
            results.append({
                "Recipe": recipe_name,
                "Matched Ingredients": overlap,
                "Match Count": len(overlap),
                "Match %": round(match_fraction * 100, 1)
            })

    results = sorted(results, key=lambda x: x["Match Count"], reverse=True)
    return results

# --- UI ---
st.title("📖 Recipe Finder")
search_input = st.text_input("Enter ingredients (comma separated):")
threshold = st.slider("Threshold (strictness)", 50, 100, 85)
min_percentage = st.slider("Minimum overlap (% of search terms)", 0, 100, 50) / 100.0

# --- Step 1: Search trigger ---
if st.button("Search"):
    if search_input.strip():
        search_terms = [term.strip() for term in search_input.split(",")]
        st.session_state.matches = search_recipes(
            st.session_state.recipes,
            search_terms,
            threshold=threshold,
            min_percentage=min_percentage
        )
    else:
        st.error("Please enter at least one ingredient.")  # ✅ only shows if Search clicked with empty field

# --- Step 2: Results display ---
if "matches" in st.session_state and st.session_state.matches:
    for match in st.session_state.matches:
        recipe_row = st.session_state.recipes[
            st.session_state.recipes["Recipe Name"] == match["Recipe"]
            ].iloc[0]
        servings = recipe_row.get("Servings", "N/A")

        st.subheader(f"{match['Recipe']} → {match['Match %']}% overlap")
        st.write(f"Servings: {servings}")
        st.write(f"Matched {match['Match Count']} terms")

        for ing, score in match["Matched Ingredients"]:
            st.write(f"- {ing} (similarity score: {score})")

        # ✅ Add to shopping list button
        if st.button(f"Add {match['Recipe']} to shopping list", key=f"add_{match['Recipe']}"):
            st.session_state.shopping_list.extend(recipe_row["Ingredients"])
            st.success(f"Added all ingredients from {match['Recipe']} to shopping list!")

        with st.expander("Show all ingredients"):
            for ing in recipe_row["Ingredients"]:
                st.write(f"- {ing}")

st.write("DEBUG PARSE RESULTS:")
for ing in st.session_state.shopping_list:
    amount, unit, item = parse_ingredient(ing)
    st.write(f"'{ing}' → amount={amount}, unit='{unit}', item='{item}'")

# --- Shopping list display ---
st.header("🛒 Shopping List")

# Clear/reset button
if st.button("Clear shopping list"):
    st.session_state.shopping_list = []
    st.success("Shopping list cleared!")

if st.session_state.shopping_list:
    combined = combine_ingredients(st.session_state.shopping_list)

    for (item, unit), amount in combined.items():
        if unit:
            formatted = format_amount(amount, unit)
            st.write(f"- {formatted} {item}")
        else:
            st.write(f"- {item} (x{amount})")
else:
    st.write("Your shopping list is empty.")