"""
HealthCare — Personal Nutrition & Health Agent
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

from services.nutrition_agent import (  # noqa: E402
    generate_nutrition_plan,
    calculate_bmi,
    NutritionAgentError,
)

# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = [
    "name", "age", "gender", "height", "weight",
    "activity_level", "fitness_goal", "food_preference"
]

ACTIVITY_LEVELS = [
    "Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"
]
FITNESS_GOALS = [
    "Weight Loss", "Weight Maintenance", "Muscle Gain", "General Healthy Eating"
]
FOOD_PREFERENCES = ["Vegetarian", "Non-Vegetarian", "Vegan", "Eggetarian"]
GENDERS = ["Male", "Female", "Non-binary", "Prefer not to say"]

HEALTH_CONDITIONS = [
    "None", "Diabetes (Type 1)", "Diabetes (Type 2)", "Hypertension",
    "High Cholesterol", "PCOS/PCOD", "Thyroid disorder", "Heart disease",
    "Kidney disease", "Liver disease", "Anaemia", "Other"
]


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

    errors = validate_profile(form)
    if errors:
        return render_template(
            "error.html",
            title="Invalid Input",
            message="Please correct the following errors and try again.",
            errors=errors,
        ), 400

    age    = int(form["age"])
    height = float(form["height"])
    weight = float(form["weight"])

    bmi_data       = calculate_bmi(height, weight)
    bmi_for_minors = age < 18

    # ── Health check assessment ──
    health_condition = form.get("health_condition", "None").strip()
    symptoms_raw     = form.get("symptoms", "").strip()
    symptoms_list    = [s.strip() for s in symptoms_raw.split(",") if s.strip()] if symptoms_raw else []
    health_risk      = _assess_health_risk(health_condition, symptoms_list, bmi_data)

    user_data = {
        "name":              form["name"].strip(),
        "age":               age,
        "gender":            form["gender"],
        "height":            height,
        "weight":            weight,
        "bmi":               bmi_data["bmi"] if not bmi_for_minors else "N/A (under 18)",
        "bmi_category":      bmi_data["category"] if not bmi_for_minors else "See note below",
        "activity_level":    form["activity_level"],
        "fitness_goal":      form["fitness_goal"],
        "food_preference":   form["food_preference"],
        "health_condition":  health_condition,
        "symptoms":          ", ".join(symptoms_list),
        "allergies":         form.get("allergies", ""),
        "disliked_foods":    form.get("disliked_foods", ""),
        "meals_per_day":     form.get("meals_per_day", ""),
        "cuisine_preference":form.get("cuisine_preference", ""),
        "budget_preference": form.get("budget_preference", ""),
        "additional_notes":  form.get("additional_notes", ""),
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
        health_risk=health_risk,
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
    return jsonify({"status": "ok", "service": "HealthCare"})


# ---------------------------------------------------------------------------
# Health risk assessment helper
# ---------------------------------------------------------------------------

def _assess_health_risk(condition: str, symptoms: list, bmi_data: dict) -> dict:
    """
    Simple rule-based health risk assessment.
    Returns a dict with risk_level, flags, and a recommendation string.
    This is for informational display only — not a medical diagnosis.
    """
    flags        = []
    risk_level   = "Low"
    see_doctor   = False

    HIGH_RISK_CONDITIONS = {
        "Diabetes (Type 1)", "Diabetes (Type 2)", "Heart disease",
        "Kidney disease", "Liver disease"
    }
    MEDIUM_RISK_CONDITIONS = {
        "Hypertension", "High Cholesterol", "PCOS/PCOD",
        "Thyroid disorder", "Anaemia"
    }

    if condition in HIGH_RISK_CONDITIONS:
        risk_level = "High"
        see_doctor = True
        flags.append(f"Known condition: {condition} — requires professional dietary supervision.")

    elif condition in MEDIUM_RISK_CONDITIONS:
        risk_level = "Medium"
        see_doctor = True
        flags.append(f"Known condition: {condition} — a registered dietitian can provide tailored guidance.")

    # BMI flags
    bmi_val = bmi_data.get("bmi", 0)
    cat     = bmi_data.get("category", "")
    if cat == "Obesity":
        risk_level = max(risk_level, "Medium", key=lambda x: ["Low","Medium","High"].index(x))
        flags.append("BMI indicates obesity — consider consulting a healthcare professional.")
    elif cat == "Underweight":
        flags.append("BMI indicates underweight — ensure adequate calorie and nutrient intake.")

    # Symptom flags
    RED_FLAG_SYMPTOMS = {
        "chest pain", "chest tightness", "shortness of breath",
        "severe headache", "fainting", "numbness", "vision loss",
        "blood in urine", "blood in stool", "sudden weight loss"
    }
    for symptom in symptoms:
        if symptom.lower() in RED_FLAG_SYMPTOMS:
            risk_level = "High"
            see_doctor = True
            flags.append(f"Symptom '{symptom}' may require urgent medical attention.")

    recommendation = (
        "Please consult a qualified doctor or registered dietitian before making dietary changes."
        if see_doctor else
        "No immediate medical concerns detected based on your input. "
        "Always consult a professional for personalised health advice."
    )

    return {
        "risk_level":    risk_level,
        "flags":         flags,
        "see_doctor":    see_doctor,
        "recommendation": recommendation,
    }


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
