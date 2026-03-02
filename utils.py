# utils.py
import re
from fractions import Fraction

# Canonical unit map: maps common unit tokens to (canonical_unit, multiplier_to_base)
UNIT_MAP = {
    "g": ("g", 1), "gram": ("g", 1), "grams": ("g", 1),
    "kg": ("g", 1000), "kilogram": ("g", 1000), "kilograms": ("g", 1000),

    "ml": ("ml", 1), "milliliter": ("ml", 1), "millilitre": ("ml", 1),
    "l": ("ml", 1000), "liter": ("ml", 1000), "litre": ("ml", 1000),

    "tbsp": ("tbsp", 1), "tablespoon": ("tbsp", 1), "tablespoons": ("tbsp", 1),
    "tsp": ("tsp", 1), "teaspoon": ("tsp", 1), "teaspoons": ("tsp", 1),
    "cup": ("cup", 1), "cups": ("cup", 1),
}

# --- Cleaning and splitting raw ingredient text ---
def clean_ingredient_text(text):
    """Normalize raw cell text and return a newline-joined string with no empty lines."""
    if not isinstance(text, str):
        return ""
    s = (
        text.replace("\r", "\n")
            .replace("\u2028", "\n")
            .replace("\xa0", " ")
            .replace("\u200B", "")
            .strip()
    )
    # Replace commas with newlines, split, strip and drop empties
    lines = [line.strip() for line in s.replace(",", "\n").split("\n")]
    return "\n".join([line for line in lines if line])

# --- Normalize a single ingredient line for consistent matching/display ---
def normalize_ingredient_line(line):
    if not isinstance(line, str):
        return ""
    s = line.lower().strip()

    # Replace common unicode fractions with ascii fraction text
    unicode_map = {
        "½": "1/2", "⅓": "1/3", "⅔": "2/3", "¼": "1/4", "¾": "3/4", "⅛": "1/8"
    }
    for uni, ascii_val in unicode_map.items():
        s = s.replace(uni, ascii_val)

    # Normalize unit abbreviations using word boundaries
    abbrev_map = {
        r"\btsp\b": "teaspoon",
        r"\btsps\b": "teaspoon",
        r"\btbsp\b": "tablespoon",
        r"\btbs\b": "tablespoon",
        r"\btbl\b": "tablespoon",
        r"\bg\b": "gram",
        r"\bkg\b": "kilogram",
        r"\bml\b": "milliliter",
        r"\bl\b": "liter",
        r"\bcups\b": "cup",
    }
    for pat, repl in abbrev_map.items():
        s = re.sub(pat, repl, s)

    # Simple plural -> singular conversions for common words
    plural_map = {
        "eggs": "egg", "bananas": "banana", "tomatoes": "tomato",
        "potatoes": "potato", "berries": "berry", "cloves": "clove"
    }
    for p, singular in plural_map.items():
        if s.endswith(p):
            s = s[: -len(p)] + singular

    # Remove trailing punctuation
    s = s.rstrip(",. ")
    return s

# --- Robust fraction and number parser ---
def fraction_to_float(text):
    """Parse mixed numbers, unicode fractions, simple fractions and decimals to float or None."""
    if not isinstance(text, str):
        return None

    t = (
        text.replace("\u00A0", " ")
            .replace("\u2009", " ")
            .replace("\u202F", " ")
            .replace("\u200A", " ")
            .replace("\u200B", "")
            .replace("\uFEFF", "")
            .strip()
    )

    unicode_fracs = {
        "¼": 1/4, "½": 1/2, "¾": 3/4,
        "⅐": 1/7, "⅑": 1/9, "⅒": 1/10,
        "⅓": 1/3, "⅔": 2/3,
        "⅕": 1/5, "⅖": 2/5, "⅗": 3/5, "⅘": 4/5,
        "⅙": 1/6, "⅚": 5/6,
        "⅛": 1/8, "⅜": 3/8, "⅝": 5/8, "⅞": 7/8,
    }
    for sym, val in unicode_fracs.items():
        t = t.replace(sym, f" {val} ")

    t = " ".join(t.split())
    parts = t.split()

    # Mixed number like "2 1/2"
    if len(parts) == 2 and "/" in parts[1]:
        try:
            return float(parts[0]) + float(Fraction(parts[1]))
        except Exception:
            pass

    # Mixed with decimal "2 0.5"
    if len(parts) == 2 and "/" not in parts[1]:
        try:
            return float(parts[0]) + float(parts[1])
        except Exception:
            pass

    # Simple fraction "1/2"
    if "/" in t:
        try:
            return float(Fraction(t))
        except Exception:
            return None

    # Plain number
    try:
        return float(t)
    except Exception:
        return None

# --- Basic singularization for ingredient names ---
def singularize(item):
    if not isinstance(item, str):
        return ""
    s = item.strip().lower()
    irregular = {
        "tomatoes": "tomato", "potatoes": "potato",
        "leaves": "leaf", "knives": "knife",
        "loaves": "loaf", "berries": "berry", "cloves": "clove",
    }
    if s in irregular:
        return irregular[s]
    if s.endswith("ies"):
        return s[:-3] + "y"
    if s.endswith("es") and not s.endswith(("ches", "shes", "xes", "sses")):
        return s[:-2]
    if s.endswith("s"):
        return s[:-1]
    return s

# --- Parse a single ingredient line into (quantity_in_base, canonical_unit, ingredient_name) ---
def parse_ingredient(ingredient):
    """
    Returns (quantity, unit, ingredient_name).
    quantity is numeric (converted by UNIT_MAP multiplier) or None.
    unit is the canonical unit string from UNIT_MAP or the raw unit token if unknown.
    ingredient_name is singularized lower-case string.
    """
    if not isinstance(ingredient, str):
        return None, None, None

    s = ingredient.strip().lower()
    s = (
        s.replace("\u00A0", " ")
         .replace("\u2009", " ")
         .replace("\u202F", " ")
         .replace("\u200A", " ")
         .replace("\u200B", "")
         .replace("\uFEFF", "")
    )

    # Extract leading amount (permissive)
    amount_match = re.match(r"^([0-9\s\/\.\-½¼¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]+)", s)
    if not amount_match:
        # No numeric amount at start -> treat whole string as ingredient name
        return None, None, singularize(s)

    amount_text = amount_match.group(1).strip()
    rest = s[len(amount_text):].strip()

    # Extract unit token (first alphabetic token in rest)
    unit_match = re.match(r"^([a-zA-Z]+)", rest)
    if unit_match:
        unit_raw = unit_match.group(1).lower()
        item = rest[len(unit_raw):].strip()
    else:
        unit_raw = None
        item = rest

    amount = fraction_to_float(amount_text)
    if amount is None:
        return None, None, singularize(item or rest)

    # Normalize unit via UNIT_MAP
    norm_unit = None
    multiplier = 1
    if unit_raw:
        if unit_raw in UNIT_MAP:
            norm_unit, multiplier = UNIT_MAP[unit_raw]
        else:
            u = unit_raw.rstrip("s")
            if u in UNIT_MAP:
                norm_unit, multiplier = UNIT_MAP[u]
            else:
                # fallback: keep raw token as unit
                norm_unit = unit_raw

    qty_in_base = amount * multiplier if norm_unit and multiplier else amount
    return qty_in_base, norm_unit, singularize(item or "")

# --- Helper to produce a clean list of raw strings for display on pages ---
def normalized_raw_lines(ingredients_cell):
    """
    Accepts: list[str], list[dict], or str.
    Returns: list[str] of non-empty raw lines suitable for display.
    """
    if isinstance(ingredients_cell, list):
        out = []
        for it in ingredients_cell:
            if isinstance(it, dict):
                raw = it.get("raw", "")
            else:
                raw = str(it)
            if raw and raw.strip():
                out.append(raw.strip())
        return out
    return [line for line in clean_ingredient_text(str(ingredients_cell)).split("\n") if line.strip()]