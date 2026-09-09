/**
 * NutriAI — Client-Side Script
 * Handles:
 *  - BMI calculator (instant, no API call)
 *  - Form validation (required fields, numeric ranges)
 *  - Loading overlay during form submission
 *  - Option-card keyboard accessibility
 */

/* =====================================================================
   BMI CALCULATOR
   ===================================================================== */

(function initBmiCalculator() {
  const heightInput  = document.getElementById("bmi-height");
  const weightInput  = document.getElementById("bmi-weight");
  const calcBtn      = document.getElementById("calc-bmi-btn");
  const resultDiv    = document.getElementById("bmi-result");

  if (!calcBtn) return; // Not on a page with the calculator

  function computeBmi() {
    const heightCm = parseFloat(heightInput.value);
    const weightKg = parseFloat(weightInput.value);

    clearBmiError();

    if (!heightCm || !weightKg) {
      showBmiError("Please enter both height and weight.");
      return;
    }
    if (heightCm < 50 || heightCm > 300) {
      showBmiError("Please enter a height between 50 and 300 cm.");
      return;
    }
    if (weightKg < 10 || weightKg > 500) {
      showBmiError("Please enter a weight between 10 and 500 kg.");
      return;
    }

    const heightM = heightCm / 100;
    const bmi     = weightKg / (heightM * heightM);
    const bmiRound = Math.round(bmi * 10) / 10;

    const { category, cssClass } = getBmiCategory(bmiRound);

    resultDiv.className = "bmi-result " + cssClass;
    resultDiv.innerHTML = `
      <div class="bmi-value">${bmiRound}</div>
      <div class="bmi-category">${category}</div>
      <div class="bmi-note">
        BMI is a general screening measure and is <strong>not a medical diagnosis</strong>.
        It does not account for muscle mass, bone density, age, or sex differences.
        Always consult a healthcare professional for a full health assessment.
      </div>
    `;
    resultDiv.classList.remove("hidden");
  }

  function getBmiCategory(bmi) {
    if (bmi < 18.5) return { category: "Underweight",   cssClass: "bmi-underweight" };
    if (bmi < 25.0) return { category: "Normal range",  cssClass: "bmi-normal" };
    if (bmi < 30.0) return { category: "Overweight",    cssClass: "bmi-overweight" };
    return             { category: "Obesity",           cssClass: "bmi-obesity" };
  }

  function showBmiError(msg) {
    resultDiv.className = "bmi-result";
    resultDiv.innerHTML = `<div class="bmi-note" style="color:var(--color-red)">${msg}</div>`;
    resultDiv.classList.remove("hidden");
  }

  function clearBmiError() {
    resultDiv.classList.add("hidden");
    resultDiv.innerHTML = "";
  }

  calcBtn.addEventListener("click", computeBmi);

  // Allow Enter key in height/weight fields to trigger calculation
  [heightInput, weightInput].forEach(function(el) {
    el.addEventListener("keydown", function(e) {
      if (e.key === "Enter") { e.preventDefault(); computeBmi(); }
    });
  });
})();


/* =====================================================================
   FORM VALIDATION
   ===================================================================== */

(function initFormValidation() {
  const form      = document.getElementById("nutrition-form");
  const submitBtn = document.getElementById("submit-btn");
  const overlay   = document.getElementById("loading-overlay");

  if (!form) return;

  // ── Validation rules ──
  const rules = [
    {
      id: "name",
      errorId: "name-error",
      validate: function(v) {
        if (!v.trim()) return "Name is required.";
        if (v.trim().length < 2) return "Name must be at least 2 characters.";
        return null;
      }
    },
    {
      id: "age",
      errorId: "age-error",
      validate: function(v) {
        if (!v.trim()) return "Age is required.";
        const n = Number(v);
        if (!Number.isInteger(n) || n < 1 || n > 120) return "Age must be a whole number between 1 and 120.";
        return null;
      }
    },
    {
      id: "gender",
      errorId: "gender-error",
      validate: function(v) {
        if (!v) return "Please select a gender.";
        return null;
      }
    },
    {
      id: "height",
      errorId: "height-error",
      validate: function(v) {
        if (!v.trim()) return "Height is required.";
        const n = parseFloat(v);
        if (isNaN(n) || n < 50 || n > 300) return "Height must be between 50 and 300 cm.";
        return null;
      }
    },
    {
      id: "weight",
      errorId: "weight-error",
      validate: function(v) {
        if (!v.trim()) return "Weight is required.";
        const n = parseFloat(v);
        if (isNaN(n) || n < 10 || n > 500) return "Weight must be between 10 and 500 kg.";
        return null;
      }
    }
  ];

  // Radio group validations (not tied to a single input id)
  const radioRules = [
    { name: "activity_level", errorId: "activity_level-error", label: "Activity level" },
    { name: "fitness_goal",   errorId: "fitness_goal-error",   label: "Fitness goal" },
    { name: "food_preference",errorId: "food_preference-error",label: "Food preference" }
  ];

  // ── Helper: set/clear error ──
  function setError(errorId, msg) {
    const el = document.getElementById(errorId);
    if (!el) return;
    el.textContent = msg || "";
  }

  function markField(id, hasError) {
    const el = document.getElementById(id);
    if (!el) return;
    if (hasError) {
      el.classList.add("invalid");
      el.setAttribute("aria-invalid", "true");
    } else {
      el.classList.remove("invalid");
      el.removeAttribute("aria-invalid");
    }
  }

  function getRadioValue(name) {
    const checked = form.querySelector(`input[name="${name}"]:checked`);
    return checked ? checked.value : "";
  }

  // ── Validate all fields, return true if form is valid ──
  function validateAll() {
    let valid = true;

    // Text/number inputs
    rules.forEach(function(rule) {
      const el  = document.getElementById(rule.id);
      const val = el ? el.value : "";
      const err = rule.validate(val);
      setError(rule.errorId, err || "");
      markField(rule.id, !!err);
      if (err) valid = false;
    });

    // Radio groups
    radioRules.forEach(function(rule) {
      const val = getRadioValue(rule.name);
      if (!val) {
        setError(rule.errorId, `Please select your ${rule.label.toLowerCase()}.`);
        valid = false;
      } else {
        setError(rule.errorId, "");
      }
    });

    return valid;
  }

  // ── Live validation on blur ──
  rules.forEach(function(rule) {
    const el = document.getElementById(rule.id);
    if (!el) return;
    el.addEventListener("blur", function() {
      const err = rule.validate(el.value);
      setError(rule.errorId, err || "");
      markField(rule.id, !!err);
    });
    el.addEventListener("input", function() {
      // Clear error on input so the user isn't pestered mid-typing
      if (el.classList.contains("invalid")) {
        const err = rule.validate(el.value);
        if (!err) {
          setError(rule.errorId, "");
          markField(rule.id, false);
        }
      }
    });
  });

  // ── Form submit ──
  form.addEventListener("submit", function(e) {
    e.preventDefault();

    const valid = validateAll();
    if (!valid) {
      // Scroll to first error
      const firstError = form.querySelector(".error-msg:not(:empty)");
      if (firstError) {
        const parent = firstError.closest(".card") || firstError;
        parent.scrollIntoView({ behavior: "smooth", block: "start" });
      }
      return;
    }

    // Disable button + show overlay
    submitBtn.disabled = true;
    submitBtn.setAttribute("aria-disabled", "true");
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin" aria-hidden="true"></i> Generating…';

    if (overlay) overlay.classList.remove("hidden");

    // Native submit (lets Flask handle the POST)
    form.submit();
  });
})();


/* =====================================================================
   OPTION CARD KEYBOARD ACCESSIBILITY
   Allow Space/Enter to select an option-card radio via keyboard
   ===================================================================== */

(function initOptionCardKeyboard() {
  document.querySelectorAll(".option-card").forEach(function(card) {
    card.addEventListener("keydown", function(e) {
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        const radio = card.querySelector('input[type="radio"]');
        if (radio) { radio.checked = true; radio.dispatchEvent(new Event("change")); }
      }
    });
    // Make the label keyboard-focusable if it contains a radio
    const radio = card.querySelector('input[type="radio"]');
    if (radio) {
      // The hidden radio itself receives focus; reflect it on the outer card
      radio.addEventListener("focus", function() {
        card.querySelector(".option-content").style.outline = "2px solid var(--color-accent)";
        card.querySelector(".option-content").style.outlineOffset = "2px";
      });
      radio.addEventListener("blur", function() {
        card.querySelector(".option-content").style.outline = "";
        card.querySelector(".option-content").style.outlineOffset = "";
      });
    }
  });
})();


/* =====================================================================
   AUTO-SYNC BMI FIELDS  from the main form height/weight inputs
   ===================================================================== */

(function syncBmiFromForm() {
  const formHeight = document.getElementById("height");
  const formWeight = document.getElementById("weight");
  const bmiHeight  = document.getElementById("bmi-height");
  const bmiWeight  = document.getElementById("bmi-weight");

  if (!formHeight || !bmiHeight) return;

  function sync() {
    if (formHeight.value) bmiHeight.value = formHeight.value;
    if (formWeight.value) bmiWeight.value = formWeight.value;
  }

  formHeight.addEventListener("change", sync);
  formWeight.addEventListener("change", sync);
})();
