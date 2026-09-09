"""
Nutrition Agent Service
Handles all interactions with the Groq API to generate personalised nutrition plans.
"""

import os
import json
import re
import logging
from groq import Groq, APIConnectionError, APIStatusError, RateLimitError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Groq client – initialised lazily so import-time errors are surfaced clearly
# ---------------------------------------------------------------------------

def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Please add it to your .env file."
        )
    return Groq(api_key=api_key)


GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ---------------------------------------------------------------------------
# BMI helper
# ---------------------------------------------------------------------------

def calculate_bmi(height_cm: float, weight_kg: float) -> dict:
    """Return BMI value, category, and an age-appropriate note."""
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 1)
    return {"bmi": bmi, "category": _bmi_category(bmi)}


def _bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25.0:
        return "Normal range"
    elif bmi < 30.0:
        return "Overweight"
    else:
        return "Obesity"


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are NutriAI, a knowledgeable and empathetic nutrition education assistant.
Your role is to provide general nutrition guidance and education — you are NOT a doctor, dietitian,
or medical professional. Always remind users to consult a qualified healthcare provider for personal
medical advice, diagnosis, or treatment.

Guidelines you MUST follow:
1. Base every recommendation strictly on the user-supplied information.
2. Never invent medical conditions, diagnose, or prescribe medication.
3. Clearly state that calorie and macro estimates are approximate general ranges.
4. Provide practical, realistic, affordable food suggestions.
5. Include Indian food options where culturally appropriate (dal, sabzi, roti, rice, etc.).
6. Fully respect the stated food preference (Vegetarian / Vegan / Eggetarian / Non-Vegetarian).
7. Never suggest foods the user is allergic to or has marked as disliked.
8. Avoid extreme calorie restriction, crash diets, or eating-disorder-promoting language.
9. Never recommend prescription medications, illegal substances, or unsafe supplements.
10. If the user mentions a medical condition, medication, or clinical concern, strongly recommend
    consulting a qualified healthcare professional instead of attempting to address it yourself.
11. Keep language simple, encouraging, and non-judgmental.
12. For budget-conscious users, prioritise low-cost whole foods.

Output format:
Return ONLY a valid JSON object — no markdown fences, no extra commentary outside the JSON.
Use exactly this structure:

{
  "summary": "2-3 sentence personalised overview",
  "calorie_guidance": "Daily calorie range estimate with explanation",
  "macros": {
    "protein": "grams/day range and example sources",
    "carbs": "grams/day range and example sources",
    "fats": "grams/day range and example sources"
  },
  "meal_plan": [
    {"meal": "Breakfast", "foods": ["item1", "item2"]},
    {"meal": "Mid-Morning Snack", "foods": ["item1"]},
    {"meal": "Lunch", "foods": ["item1", "item2"]},
    {"meal": "Evening Snack", "foods": ["item1"]},
    {"meal": "Dinner", "foods": ["item1", "item2"]}
  ],
  "seven_day_plan": [
    {
      "day": "Day 1",
      "breakfast": "description",
      "lunch": "description",
      "snack": "description",
      "dinner": "description"
    }
  ],
  "hydration": "Hydration guidance string",
  "foods_to_prioritize": ["food1", "food2"],
  "foods_to_limit": ["food1", "food2"],
  "tips": ["tip1", "tip2", "tip3"],
  "disclaimer": "Important disclaimer reminding the user this is general education, not medical advice"
}

The seven_day_plan array must contain exactly 7 objects (Day 1 through Day 7).
"""

# ---------------------------------------------------------------------------
# User prompt builder
# ---------------------------------------------------------------------------

def _build_user_prompt(data: dict) -> str:
    lines = [
        "Please generate a personalised nutrition plan for the following individual:",
        "",
        f"Name: {data.get('name', 'User')}",
        f"Age: {data.get('age')} years",
        f"Gender: {data.get('gender')}",
        f"Height: {data.get('height')} cm",
        f"Weight: {data.get('weight')} kg",
        f"BMI: {data.get('bmi')} ({data.get('bmi_category')})",
        f"Activity Level: {data.get('activity_level')}",
        f"Fitness Goal: {data.get('fitness_goal')}",
        f"Food Preference: {data.get('food_preference')}",
    ]

    optional_fields = [
        ("allergies", "Allergies / Intolerances"),
        ("disliked_foods", "Foods to Avoid"),
        ("meals_per_day", "Meals per Day"),
        ("cuisine_preference", "Cuisine Preference"),
        ("budget_preference", "Budget Preference"),
        ("additional_notes", "Additional Notes"),
    ]
    for key, label in optional_fields:
        value = data.get(key, "").strip() if data.get(key) else ""
        if value:
            lines.append(f"{label}: {value}")

    lines += [
        "",
        "Important reminders:",
        "- Respect the stated food preference strictly.",
        "- Do NOT include any foods the user is allergic to.",
        "- Do NOT include disliked foods.",
        "- Provide a 7-day example meal plan.",
        "- Return valid JSON only.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Response parser with graceful fallback
# ---------------------------------------------------------------------------

def _parse_response(raw: str) -> dict:
    """Try to extract a JSON object from the model's response."""
    # Strip markdown fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

    # Attempt direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find the outermost { ... } block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: wrap raw text so the UI can still render something
    logger.warning("Could not parse JSON from model response; using fallback.")
    return {
        "summary": raw[:500] if len(raw) > 500 else raw,
        "calorie_guidance": "Please see the summary above.",
        "macros": {"protein": "N/A", "carbs": "N/A", "fats": "N/A"},
        "meal_plan": [],
        "seven_day_plan": [],
        "hydration": "Aim for 8–10 glasses of water per day.",
        "foods_to_prioritize": [],
        "foods_to_limit": [],
        "tips": ["Please consult a registered dietitian for personalised guidance."],
        "disclaimer": (
            "This information is for general education only and is not a substitute "
            "for professional medical or dietary advice."
        ),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_nutrition_plan(user_data: dict) -> dict:
    """
    Send user data to Groq and return a parsed nutrition plan dict.
    Raises NutritionAgentError on failure.
    """
    client = _get_client()
    user_prompt = _build_user_prompt(user_data)

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            max_tokens=4096,
            timeout=60,
        )
    except RateLimitError:
        raise NutritionAgentError(
            "The AI service is currently busy. Please wait a moment and try again."
        )
    except APIConnectionError:
        raise NutritionAgentError(
            "Could not connect to the AI service. Please check your internet connection."
        )
    except APIStatusError as exc:
        logger.error("Groq API error %s: %s", exc.status_code, exc.message)
        raise NutritionAgentError(
            "The AI service returned an error. Please try again in a moment."
        )

    raw_content = response.choices[0].message.content
    return _parse_response(raw_content)


class NutritionAgentError(Exception):
    """Raised when the nutrition agent cannot produce a valid plan."""
