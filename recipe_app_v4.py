import pandas as pd
from rapidfuzz import fuzz
import streamlit as st
import re

# ✅ Unit normalisation map
UNIT_MAP = {
    # weight
    "g": ("g", 1),
    "gram": ("g", 1),
    "grams": ("g", 1),
    "kg": ("g", 1000),
    "kilogram": ("g", 1000),
    "kilograms": ("g", 1000),

    # volume
    "ml": ("ml", 1),
    "millilitre": ("ml", 1),
    "milliliter": ("ml", 1),
    "l": ("ml", 1000),
    "litre": ("ml", 1000),
    "liter": ("ml", 1000),

    # spoons
    "tbsp": ("tbsp", 1),
    "tablespoon": ("tbsp", 1),
    "tablespoons": ("tbsp", 1),

    "tsp": ("tsp", 1),
    "teaspoon": ("tsp", 1),
    "teaspoons": ("tsp", 1),
}

# ✅ Plural → singular conversion
def singularize(item):
    item = item.strip().lower()

    # Irregular plurals
    irregular = {
        "tomatoes": "tomato",
        "potatoes": "potato",
        "leaves": "leaf",
        "knives": "knife",
        "loaves": "loaf",
        "berries": "berry",
        "cloves": "clove",
    }

    if item in irregular:
        return irregular[item]

    # Words ending in "ies" → "y" (berries → berry)
    if item.endswith("ies"):
        return item[:-3] + "y"

    # Words ending in "es" (but not ches/shes/xes/sses)
    if item.endswith("es") and not item.endswith(("ches", "shes", "xes", "sses")):
        return item[:-2]

    # Words ending in "s" → remove s
    if item.endswith("s"):
        return item[:-1]

    return item

import re

# ✅ Unit normalisation map
UNIT_MAP = {
    # weight
    "g": ("g", 1),
    "gram": ("g", 1),
    "grams": ("g", 1),
    "kg": ("g", 1000),
    "kilogram": ("g", 1000),
    "kilograms": ("g", 1000),

    # volume
    "ml": ("ml", 1),
    "millilitre": ("ml", 1),
    "milliliter": ("ml", 1),
    "l": ("ml", 1000),
    "litre": ("ml", 1000),
    "liter": ("ml", 1000),

    # spoons
    "tbsp": ("tbsp", 1),
    "tablespoon": ("tbsp", 1),
    "tablespoons": ("tbsp", 1),

    "tsp": ("tsp", 1),
    "teaspoon": ("tsp", 1),
    "teaspoons": ("tsp", 1),
}

# ✅ Plural → singular conversion
def singularize(item):
    item = item.strip().lower()

    # Irregular plurals
    irregular = {
        "tomatoes": "tomato",
        "potatoes": "potato",
        "leaves": "leaf",
        "knives": "knife",
        "loaves": "loaf",
        "berries": "berry",
        "cloves": "clove",
    }

    if item in irregular:
        return irregular[item]

    # Words ending in "ies" → "y" (berries → berry)
    if item.endswith("ies"):
        return item[:-3] + "y"

    # Words ending in "es" (but not ches/shes/xes/sses)
    if item.endswith("es") and not item.endswith(("ches", "shes", "xes", "sses")):
        return item[:-2]

    # Words ending in "s" → remove s
    if item.endswith("s"):
        return item[:-1]

    return item


# ✅ Ingredient parser (ranges + units + plural handling)
def parse_ingredient(ingredient):
    ingredient = ingredient.strip().lower()

    # ✅ Handle ranges like "1/2-3/4 cup rice" or "½–1 cup rice"
    range_match = re.match(r"^\s*([\d\s\/\.\¼\½\¾\⅐-\⅞]+)\s*[-–]\s*([\d\s\/\.\¼\½\¾\⅐-\⅞]+)\s*([a-zA-Z]+)\s+(.*)$",
                           ingredient)
    if range_match:
        low_text = range_match.group(1).strip()
        high_text = range_match.group(2).strip()
        unit = range_match.group(3).lower()
        item = range_match.group(4).strip().lower()

        # ✅ Convert fractions
        low = fraction_to_float(low_text)
        high = fraction_to_float(high_text)

        # ✅ Use upper value
        amount = high

        # ✅ Normalise unit
        if unit in UNIT_MAP:
            norm_unit, multiplier = UNIT_MAP[unit]
            amount = amount * multiplier
            item = singularize(item)
            return amount, norm_unit, item

        item = singularize(item)
        return amount, unit, item

    # ✅ Handle normal single-value ingredients (including fractions)
    pattern = r"^\s*([\d\s\/\.\¼\½\¾\⅐-\⅞]+)\s*([a-zA-Z]+)\s+(.*)$"
    match = re.match(pattern, ingredient)

    if match:
        amount_text = match.group(1).strip()
        unit = match.group(2).lower()
        item = match.group(3).strip().lower()

        # ✅ Convert fraction → float
        amount = fraction_to_float(amount_text)

        # ✅ Normalise unit
        if unit in UNIT_MAP:
            norm_unit, multiplier = UNIT_MAP[unit]
            amount = amount * multiplier
            item = singularize(item)
            return amount, norm_unit, item

        item = singularize(item)
        return amount, unit, item

    # ✅ Unitless items (e.g., "onions")
    item = singularize(ingredient)
    return None, None, item


# ✅ Combine duplicate ingredients
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
            combined[key] += 1  # count unitless items

    return combined


# ✅ Format amounts nicely (1000g → 1kg, 1500ml → 1.5l)
def format_amount(amount, unit):
    if unit == "g" and amount >= 1000:
        return f"{amount/1000:.1f}kg"
    if unit == "ml" and amount >= 1000:
        return f"{amount/1000:.1f}l"
    return f"{amount}{unit}" if unit else str(amount)

# ✅ Ingredient parser (ranges + units + plural handling)
def parse_ingredient(ingredient):
    ingredient = ingredient.strip().lower()

    # ✅ Handle ranges like "500-600g chicken breast"
    range_match = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*([a-zA-Z]+)\s+(.*)$", ingredient)
    if range_match:
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        unit = range_match.group(3).lower()
        item = range_match.group(4).strip().lower()

        # Normalise unit
        if unit in UNIT_MAP:
            norm_unit, multiplier = UNIT_MAP[unit]
            high = high * multiplier
            item = singularize(item)
            return high, norm_unit, item

        item = singularize(item)
        return high, unit, item

    # ✅ Handle normal single-value ingredients
    pattern = r"^\s*([\d\.]+)\s*([a-zA-Z]+)\s+(.*)$"
    match = re.match(pattern, ingredient)

    if match:
        amount = float(match.group(1))
        unit = match.group(2).lower()
        item = match.group(3).strip().lower()

        # Normalise unit
        if unit in UNIT_MAP:
            norm_unit, multiplier = UNIT_MAP[unit]
            amount = amount * multiplier
            item = singularize(item)
            return amount, norm_unit, item

        item = singularize(item)
        return amount, unit, item

    # ✅ Unitless items (e.g., "onions")
    item = singularize(ingredient)
    return None, None, item


# ✅ Combine duplicate ingredients
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
            combined[key] += 1  # count unitless items

    return combined


# ✅ Format amounts nicely (1000g → 1kg, 1500ml → 1.5l)
def format_amount(amount, unit):
    if unit == "g" and amount >= 1000:
        return f"{amount/1000:.1f}kg"
    if unit == "ml" and amount >= 1000:
        return f"{amount/1000:.1f}l"
    return f"{amount}{unit}" if unit else str(amount)
# --- Initialize recipes and shopping list in session_state ---
if "recipes" not in st.session_state:
    base_df = pd.read_excel("C:\Users\jcart\OneDrive\Desktop\the plan\Copy of cooking.xlsx", sheet_name="Sheet1")
    base_df["Ingredients"] = base_df["Ingredients"].apply(
        lambda x: [i.strip().lower() for i in str(x).split(",")]
    )
    if "Servings" not in base_df.columns:
        base_df["Servings"] = None
    st.session_state.recipes = base_df.copy()

if "shopping_list" not in st.session_state:
    st.session_state.shopping_list = []

recipes = st.session_state.recipes

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
def search_recipes(search_ingredients, threshold=85, min_percentage=0.5):
    search_ingredients = [s.strip().lower() for s in search_ingredients]
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
            search_terms, threshold=threshold, min_percentage=min_percentage
        )
    else:
        st.error("Please enter at least one ingredient.")  # ✅ only shows if Search clicked with empty field

# --- Step 2: Results display ---
if "matches" in st.session_state and st.session_state.matches:
    for match in st.session_state.matches:
        recipe_row = recipes[recipes["Recipe Name"] == match["Recipe"]].iloc[0]
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