/**
 * HealthCare — Client-Side Script
 * Handles:
 *  - Health Check section: live risk preview + hidden-field sync
 *  - BMI calculator (instant, browser-only)
 *  - Form validation (required fields, numeric ranges)
 *  - Loading overlay during form submission
 *  - Option-card keyboard accessibility
 *  - Auto-sync BMI fields from the main form inputs
 */

/* =====================================================================
   HEALTH CHECK — live risk preview & sync to hidden form fields
   ===================================================================== */

(function initHealthCheck() {
  var condSelect   = document.getElementById("health-condition-display");
  var symptomsInput = document.getElementById("symptoms-display");
  var previewDiv   = document.getElementById("health-check-preview");
  var hiddenCond   = document.getElementById("health_condition");
  var hiddenSymp   = document.getElementById("symptoms");

  if (!condSelect) return;

  var HIGH_RISK   = ["Diabetes (Type 1)", "Diabetes (Type 2)", "Heart disease",
                     "Kidney disease", "Liver disease"];
  var MEDIUM_RISK = ["Hypertension", "High Cholesterol", "PCOS/PCOD",
                     "Thyroid disorder", "Anaemia"];
  var RED_FLAG_SYMPTOMS = [
    "chest pain", "chest tightness", "shortness of breath", "severe headache",
    "fainting", "numbness", "vision loss", "blood in urine",
    "blood in stool", "sudden weight loss"
  ];

  function getRisk() {
    var cond     = condSelect.value;
    var symptoms = symptomsInput.value.split(",").map(function(s) { return s.trim().toLowerCase(); });
    var level    = "Low";
    var msg      = "";
    var seeDoc   = false;

    if (HIGH_RISK.indexOf(cond) !== -1) {
      level  = "High";
      seeDoc = true;
      msg    = "<strong>" + cond + "</strong> requires professional dietary supervision. ";
    } else if (MEDIUM_RISK.indexOf(cond) !== -1) {
      level  = "Medium";
      seeDoc = true;
      msg    = "<strong>" + cond + "</strong> — a registered dietitian can provide tailored guidance. ";
    }

    symptoms.forEach(function(s) {
      if (s && RED_FLAG_SYMPTOMS.indexOf(s) !== -1) {
        level  = "High";
        seeDoc = true;
        msg   += "Symptom <em>'" + escapeHtml(s) + "'</em> may need urgent medical attention. ";
      }
    });

    return { level: level, msg: msg, seeDoc: seeDoc };
  }

  function escapeHtml(str) {
    return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }

  function updatePreview() {
    var cond = condSelect.value;
    var symp = symptomsInput.value.trim();

    // Sync hidden fields
    if (hiddenCond) hiddenCond.value = cond;
    if (hiddenSymp) hiddenSymp.value = symp;

    // Show preview only if something is entered
    if (cond === "None" && !symp) {
      previewDiv.classList.add("hidden");
      previewDiv.className = "health-check-preview hidden";
      return;
    }

    var risk = getRisk();
    var icon = risk.level === "High"
      ? '<i class="fa-solid fa-circle-exclamation" aria-hidden="true"></i>'
      : risk.level === "Medium"
      ? '<i class="fa-solid fa-triangle-exclamation" aria-hidden="true"></i>'
      : '<i class="fa-solid fa-circle-check" aria-hidden="true"></i>';

    var notice = risk.seeDoc
      ? " <strong>Please consult a healthcare professional before making dietary changes.</strong>"
      : " Your entries look routine — still consult a professional for personalised advice.";

    previewDiv.className = "health-check-preview risk-" + risk.level.toLowerCase();
    previewDiv.innerHTML = icon + " <strong>Estimated Risk Level: " + risk.level + ".</strong> "
      + (risk.msg || "") + notice;
    previewDiv.classList.remove("hidden");
  }

  condSelect.addEventListener("change", updatePreview);
  symptomsInput.addEventListener("input", updatePreview);

  // Initialise on load
  updatePreview();
})();


/* =====================================================================
   BMI CALCULATOR
   ===================================================================== */

(function initBmiCalculator() {
  var heightInput = document.getElementById("bmi-height");
  var weightInput = document.getElementById("bmi-weight");
  var calcBtn     = document.getElementById("calc-bmi-btn");
  var resultDiv   = document.getElementById("bmi-result");

  if (!calcBtn) return;

  function computeBmi() {
    clearBmiError();

    var heightCm = parseFloat(heightInput.value);
    var weightKg = parseFloat(weightInput.value);

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

    var heightM  = heightCm / 100;
    var bmi      = weightKg / (heightM * heightM);
    var bmiRound = Math.round(bmi * 10) / 10;
    var cat      = getBmiCategory(bmiRound);

    resultDiv.className = "bmi-result " + cat.cssClass;
    resultDiv.innerHTML =
      '<div class="bmi-value">' + bmiRound + '</div>' +
      '<div class="bmi-category">' + cat.label + '</div>' +
      '<div class="bmi-note">' +
      'BMI is a general screening measure and is <strong>not a medical diagnosis</strong>. ' +
      'It does not account for muscle mass, bone density, age, or sex. ' +
      'Always consult a healthcare professional for a full health assessment.' +
      '</div>';
    resultDiv.classList.remove("hidden");
  }

  function getBmiCategory(bmi) {
    if (bmi < 18.5) return { label: "Underweight",  cssClass: "bmi-underweight" };
    if (bmi < 25.0) return { label: "Normal range", cssClass: "bmi-normal" };
    if (bmi < 30.0) return { label: "Overweight",   cssClass: "bmi-overweight" };
    return               { label: "Obesity",        cssClass: "bmi-obesity" };
  }

  function showBmiError(msg) {
    resultDiv.className = "bmi-result";
    resultDiv.innerHTML = '<div class="bmi-note" style="color:var(--color-red)">' + msg + '</div>';
    resultDiv.classList.remove("hidden");
  }

  function clearBmiError() {
    resultDiv.classList.add("hidden");
    resultDiv.innerHTML = "";
  }

  calcBtn.addEventListener("click", computeBmi);
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
  var form      = document.getElementById("nutrition-form");
  var submitBtn = document.getElementById("submit-btn");
  var overlay   = document.getElementById("loading-overlay");

  if (!form) return;

  // ── Field rules ──
  var rules = [
    {
      id: "name", errorId: "name-error",
      validate: function(v) {
        if (!v.trim()) return "Name is required.";
        if (v.trim().length < 2) return "Name must be at least 2 characters.";
        return null;
      }
    },
    {
      id: "age", errorId: "age-error",
      validate: function(v) {
        if (!v.trim()) return "Age is required.";
        var n = Number(v);
        if (!Number.isInteger(n) || n < 1 || n > 120) return "Age must be a whole number between 1 and 120.";
        return null;
      }
    },
    {
      id: "gender", errorId: "gender-error",
      validate: function(v) { return v ? null : "Please select a gender."; }
    },
    {
      id: "height", errorId: "height-error",
      validate: function(v) {
        if (!v.trim()) return "Height is required.";
        var n = parseFloat(v);
        if (isNaN(n) || n < 50 || n > 300) return "Height must be between 50 and 300 cm.";
        return null;
      }
    },
    {
      id: "weight", errorId: "weight-error",
      validate: function(v) {
        if (!v.trim()) return "Weight is required.";
        var n = parseFloat(v);
        if (isNaN(n) || n < 10 || n > 500) return "Weight must be between 10 and 500 kg.";
        return null;
      }
    }
  ];

  // ── Radio group rules ──
  var radioRules = [
    { name: "activity_level",  errorId: "activity_level-error",  label: "activity level" },
    { name: "fitness_goal",    errorId: "fitness_goal-error",    label: "fitness goal" },
    { name: "food_preference", errorId: "food_preference-error", label: "food preference" }
  ];

  function setError(errorId, msg) {
    var el = document.getElementById(errorId);
    if (el) el.textContent = msg || "";
  }

  function markField(id, hasError) {
    var el = document.getElementById(id);
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
    var checked = form.querySelector('input[name="' + name + '"]:checked');
    return checked ? checked.value : "";
  }

  function validateAll() {
    var valid = true;

    rules.forEach(function(rule) {
      var el  = document.getElementById(rule.id);
      var val = el ? el.value : "";
      var err = rule.validate(val);
      setError(rule.errorId, err || "");
      markField(rule.id, !!err);
      if (err) valid = false;
    });

    radioRules.forEach(function(rule) {
      if (!getRadioValue(rule.name)) {
        setError(rule.errorId, "Please select your " + rule.label + ".");
        valid = false;
      } else {
        setError(rule.errorId, "");
      }
    });

    return valid;
  }

  // ── Live blur validation ──
  rules.forEach(function(rule) {
    var el = document.getElementById(rule.id);
    if (!el) return;
    el.addEventListener("blur", function() {
      var err = rule.validate(el.value);
      setError(rule.errorId, err || "");
      markField(rule.id, !!err);
    });
    el.addEventListener("input", function() {
      if (el.classList.contains("invalid")) {
        var err = rule.validate(el.value);
        if (!err) { setError(rule.errorId, ""); markField(rule.id, false); }
      }
    });
  });

  // ── Submit ──
  form.addEventListener("submit", function(e) {
    e.preventDefault();
    if (!validateAll()) {
      var firstError = form.querySelector(".error-msg:not(:empty)");
      if (firstError) {
        var parent = firstError.closest(".card") || firstError;
        parent.scrollIntoView({ behavior: "smooth", block: "start" });
      }
      return;
    }

    submitBtn.disabled = true;
    submitBtn.setAttribute("aria-disabled", "true");
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin" aria-hidden="true"></i> Analysing your profile…';

    if (overlay) overlay.classList.remove("hidden");
    form.submit();
  });
})();


/* =====================================================================
   OPTION CARD KEYBOARD ACCESSIBILITY
   ===================================================================== */

(function initOptionCardKeyboard() {
  document.querySelectorAll(".option-card").forEach(function(card) {
    card.addEventListener("keydown", function(e) {
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        var radio = card.querySelector('input[type="radio"]');
        if (radio) { radio.checked = true; radio.dispatchEvent(new Event("change")); }
      }
    });

    var radio   = card.querySelector('input[type="radio"]');
    var content = card.querySelector(".option-content");
    if (radio && content) {
      radio.addEventListener("focus", function() {
        content.style.outline = "2px solid var(--color-teal)";
        content.style.outlineOffset = "2px";
      });
      radio.addEventListener("blur", function() {
        content.style.outline = "";
        content.style.outlineOffset = "";
      });
    }
  });
})();


/* =====================================================================
   AUTO-SYNC BMI FIELDS from main form height/weight
   ===================================================================== */

(function syncBmiFromForm() {
  var formHeight = document.getElementById("height");
  var formWeight = document.getElementById("weight");
  var bmiHeight  = document.getElementById("bmi-height");
  var bmiWeight  = document.getElementById("bmi-weight");

  if (!formHeight || !bmiHeight) return;

  function sync() {
    if (formHeight.value) bmiHeight.value = formHeight.value;
    if (formWeight.value) bmiWeight.value = formWeight.value;
  }

  formHeight.addEventListener("change", sync);
  formWeight.addEventListener("change", sync);
})();
