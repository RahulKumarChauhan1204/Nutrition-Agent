"""
NutriAI — Personal Nutrition Agent
Main Flask application entry point.
"""

import os
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB request limit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import after load_dotenv so GROQ_MODEL env var is available
from services.nutrition_agent import (  # noqa: E402
    generate_nutrition_plan,
    calculate_bmi,
    NutritionAgentError,
)

# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = ["name", "age", "gender", "height", "weight", "activity_level",
                   "fitness_goal", "food_preference"]

ACTIVITY_LEVELS = [
    "Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"
]
FITNESS_GOALS = [
    "Weight Loss", "Weight Maintenance", "Muscle Gain", "General Healthy Eating"
]
FOOD_PREFERENCES = ["Vegetarian", "Non-Vegetarian", "Vegan", "Eggetarian"]
GENDERS = ["Male", "Female", "Non-binary", "Prefer not to say"]


def validate_profile(form: dict) -> list[str]:
    """Return a list of human-readable validation errors, empty if valid."""
    errors = []

    for field in REQUIRED_FIELDS:
        if not form.get(field, "").strip():
            errors.append(f"'{field.replace('_', ' ').title()}' is required.")

    try:
        age = int(form.get("age", 0))
        if not (1 <= age <= 120):
            errors.append("Age must be between 1 and 120.")
    except (ValueError, TypeError):
        errors.append("Age must be a valid whole number.")

    try:
        height = float(form.get("height", 0))
        if not (50 <= height <= 300):
            errors.append("Height must be between 50 and 300 cm.")
    except (ValueError, TypeError):
        errors.append("Height must be a valid number.")

    try:
        weight = float(form.get("weight", 0))
        if not (10 <= weight <= 500):
            errors.append("Weight must be between 10 and 500 kg.")
    except (ValueError, TypeError):
        errors.append("Weight must be a valid number.")

    if form.get("activity_level") not in ACTIVITY_LEVELS:
        errors.append("Please select a valid activity level.")

    if form.get("fitness_goal") not in FITNESS_GOALS:
        errors.append("Please select a valid fitness goal.")

    if form.get("food_preference") not in FOOD_PREFERENCES:
        errors.append("Please select a valid food preference.")

    return errors


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate-plan", methods=["POST"])
def generate_plan():
    form = request.form.to_dict()

    # Server-side validation
    errors = validate_profile(form)
    if errors:
        return render_template(
            "error.html",
            title="Invalid Input",
            message="Please correct the following errors and try again.",
            errors=errors,
        ), 400

    age = int(form["age"])
    height = float(form["height"])
    weight = float(form["weight"])

    # BMI calculation
    bmi_data = calculate_bmi(height, weight)
    bmi_for_minors = age < 18

    user_data = {
        "name": form["name"].strip(),
        "age": age,
        "gender": form["gender"],
        "height": height,
        "weight": weight,
        "bmi": bmi_data["bmi"] if not bmi_for_minors else "N/A (under 18)",
        "bmi_category": bmi_data["category"] if not bmi_for_minors else "See note below",
        "activity_level": form["activity_level"],
        "fitness_goal": form["fitness_goal"],
        "food_preference": form["food_preference"],
        "allergies": form.get("allergies", ""),
        "disliked_foods": form.get("disliked_foods", ""),
        "meals_per_day": form.get("meals_per_day", ""),
        "cuisine_preference": form.get("cuisine_preference", ""),
        "budget_preference": form.get("budget_preference", ""),
        "additional_notes": form.get("additional_notes", ""),
    }

    try:
        plan = generate_nutrition_plan(user_data)
    except EnvironmentError as exc:
        logger.error("Configuration error: %s", exc)
        return render_template(
            "error.html",
            title="Configuration Error",
            message=str(exc),
            errors=[],
        ), 500
    except NutritionAgentError as exc:
        logger.warning("NutritionAgentError: %s", exc)
        return render_template(
            "error.html",
            title="AI Service Error",
            message=str(exc),
            errors=[],
        ), 503
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Unexpected error generating plan: %s", exc)
        return render_template(
            "error.html",
            title="Unexpected Error",
            message="Sorry, something went wrong. Please try again in a moment.",
            errors=[],
        ), 500

    return render_template(
        "result.html",
        plan=plan,
        user=user_data,
        bmi=bmi_data,
        bmi_for_minors=bmi_for_minors,
    )


@app.route("/calculate-bmi", methods=["POST"])
def api_calculate_bmi():
    data = request.get_json(silent=True) or {}
    try:
        height = float(data.get("height", 0))
        weight = float(data.get("weight", 0))
        if not (50 <= height <= 300) or not (10 <= weight <= 500):
            return jsonify({"error": "Height or weight out of valid range."}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Height and weight must be valid numbers."}), 400

    result = calculate_bmi(height, weight)
    return jsonify(result)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "NutriAI"})


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_):
    return render_template(
        "error.html",
        title="Page Not Found",
        message="The page you are looking for does not exist.",
        errors=[],
    ), 404


@app.errorhandler(413)
def request_too_large(_):
    return render_template(
        "error.html",
        title="Request Too Large",
        message="Your submission was too large. Please reduce the length of your inputs.",
        errors=[],
    ), 413


@app.errorhandler(500)
def internal_error(_):
    return render_template(
        "error.html",
        title="Server Error",
        message="An unexpected server error occurred. Please try again.",
        errors=[],
    ), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=5000)
