import streamlit as st
from recipe_app_v4_2 import parse_ingredient, format_amount
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

def clean_ingredient_text(text):
    if not isinstance(text, str):
        return ""
    return (
        text.replace("\r", "\n")        # normalize Windows line breaks
            .replace("\u2028", "\n")   # remove unicode line separators
            .replace("\xa0", " ")      # replace non-breaking spaces
            .replace(",", "\n")        # split comma-separated ingredients into lines
            .strip()
    )

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

    # Replace unicode fractions with numeric equivalents (as decimals)
    for sym, val in unicode_fracs.items():
        text = text.replace(sym, f" {val} ")

    text = text.strip()
    # Collapse multiple spaces
    text = " ".join(text.split())

    # Try mixed number patterns first
    parts = text.split()

    # Case 1: "2 1/2" (whole + normal fraction)
    if len(parts) == 2 and "/" in parts[1]:
        try:
            return float(parts[0]) + float(Fraction(parts[1]))
        except:
            pass

    # Case 2: "2 0.5" (whole + decimal from unicode fraction)
    if len(parts) == 2 and "/" not in parts[1]:
        try:
            return float(parts[0]) + float(parts[1])
        except:
            pass

    # Case 3: simple fraction like "1/2"
    if "/" in text:
        try:
            return float(Fraction(text))
        except:
            return None

    # Case 4: plain decimal or integer ("0.5", "2", "0.3333")
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

def safe_clean(text):
    try:
        return clean_ingredient_text(text)
    except NameError:
        # fallback: minimal cleaning so the page doesn't crash
        if not isinstance(text, str):
            return ""
        return text.replace("\r", "\n").replace(",", "\n").strip()

def compare_recipe_to_pantry(ingredients_text):
    ingredients_text = safe_clean(ingredients_text)
    # rest of function...

def compare_recipe_to_pantry(ingredients_text):
    """Return match stats for a recipe."""
    missing = []
    short = []
    matched = []

    ingredients_text = clean_ingredient_text(ingredients_text)

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