import pandas as pd
from rapidfuzz import fuzz
import streamlit as st

# --- Initialize recipes in session_state ---
if "recipes" not in st.session_state:
    base_df = pd.read_excel(
        r"C:\Users\jcart\OneDrive\Documents\Cooking\Copy of cooking.xlsx",
        sheet_name="Sheet1"
    )
    base_df["Ingredients"] = base_df["Ingredients"].apply(
        lambda x: [i.strip().lower() for i in str(x).split(",")]
    )
    st.session_state.recipes = base_df.copy()

# Always work with the session_state version
recipes = st.session_state.recipes

# --- Manual recipe entry form ---
with st.form("add_recipe"):
    recipe_name = st.text_input("Recipe Name")
    ingredients = st.text_area("Ingredients (comma-separated)")
    submitted = st.form_submit_button("Add Recipe")

if submitted and recipe_name.strip() and ingredients.strip():
    new_recipe = pd.DataFrame([{
        "Recipe Name": recipe_name.strip(),
        "Ingredients": [i.strip().lower() for i in ingredients.split(",")]
    }])
    # Update session state
    st.session_state.recipes = pd.concat([st.session_state.recipes, new_recipe], ignore_index=True)

    # Normalize safeguard
    st.session_state.recipes["Ingredients"] = st.session_state.recipes["Ingredients"].apply(
        lambda x: x if isinstance(x, list) else [i.strip().lower() for i in str(x).split(",")]
    )

    st.success(f"Added recipe: {recipe_name}")

# Use the latest recipes for search
recipes = st.session_state.recipes

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

if st.button("Search"):
    if search_input.strip():
        search_terms = [term.strip() for term in search_input.split(",")]
        matches = search_recipes(search_terms, threshold=threshold, min_percentage=min_percentage)

        if not matches:
            st.warning("No recipes found.")
        else:
            for match in matches:
                st.subheader(f"{match['Recipe']} → {match['Match %']}% overlap")
                st.write(f"Matched {match['Match Count']} terms")
                for ing, score in match["Matched Ingredients"]:
                    st.write(f"- {ing} (similarity score: {score})")
    else:
        st.error("Please enter at least one ingredient.")