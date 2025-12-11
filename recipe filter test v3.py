import pandas as pd
from rapidfuzz import fuzz
import streamlit as st

# --- Initialize recipes in session_state ---
if "recipes" not in st.session_state:
    base_df = pd.read_excel(
        "Copy of cooking.xlsx",sheet_name="Sheet1")
    base_df["Ingredients"] = base_df["Ingredients"].apply(
        lambda x: [i.strip().lower() for i in str(x).split(",")]
    )
    if "Servings" not in base_df.columns:
        base_df["Servings"] = None
    st.session_state.recipes = base_df.copy()

    if "shopping_list" not in st.session_state:
        st.session_state.shopping_list = []

# Always work with the session_state version
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
    st.success(f"Added recipe: {recipe_name} ({servings} servings)")
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
                recipe_row = recipes[recipes["Recipe Name"] == match["Recipe"]].iloc[0]
                servings = recipe_row.get("Servings", "N/A")

                st.subheader(f"{match['Recipe']} → {match['Match %']}% overlap")
                st.write(f"Servings: {servings}")
                st.write(f"Matched {match['Match Count']} terms")

                for ing, score in match["Matched Ingredients"]:
                    st.write(f"- {ing} (similarity score: {score})")

                # 🔑 Single button with unique key
                if st.button(f"Add {match['Recipe']} to shopping list", key=f"add_{match['Recipe']}"):
                    st.session_state.shopping_list.extend(recipe_row["Ingredients"])
                    st.success(f"Added all ingredients from {match['Recipe']} to shopping list!")

                with st.expander("Show all ingredients"):
                    st.write("All ingredients:")
                    for ing in recipe_row["Ingredients"]:
                        st.write(f"- {ing}")

                # Optional: expander to show all ingredients
                with st.expander("Show all ingredients"):
                    st.write("All ingredients:")
                    for ing in recipe_row["Ingredients"]:
                        st.write(f"- {ing}")
    else:
        st.error("Please enter at least one ingredient.")

# --- Shopping list display ---
st.header("🛒 Shopping List")
if "shopping_list" not in st.session_state:
    st.session_state.shopping_list = []  # initialize if missing

if st.session_state.shopping_list:
    for item in st.session_state.shopping_list:
        st.write(f"- {item}")
else:
    st.write("Your shopping list is empty.")