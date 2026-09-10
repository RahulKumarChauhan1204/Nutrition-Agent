# HealthCare — Personal Nutrition Agent

> **Disclaimer:** HealthCare provides general nutrition education only. It is **not a substitute** for professional medical or dietary advice, diagnosis, or treatment. Always consult a qualified healthcare professional before making significant dietary changes.

---

## Overview

HealthCare is a full-stack web application that uses the **Groq AI API** to generate personalised nutrition plans based on a user's profile, fitness goals, food preferences, and lifestyle. The application calculates BMI, estimates daily calorie and macronutrient needs, and produces a 7-day sample meal plan — all rendered in a clean, responsive dashboard.

---

## Features

- **User profile form** — collects age, gender, height, weight, activity level, fitness goal, food preference, allergies, disliked foods, cuisine preferences, and more
- **Instant BMI calculator** — runs entirely in the browser; shows value, category, and a clear note that BMI is a screening tool, not a diagnosis
- **AI nutrition plan** — powered by the Groq API (LLaMA 3.3 70B by default); returns a structured JSON plan
- **7-day meal plan** — displayed in a responsive table
- **Macronutrient breakdown** — Protein, Carbohydrates, Fats
- **Foods to prioritise / limit**
- **Hydration guidance**
- **Practical nutrition tips**
- **Print-friendly layout** — one click to print or save as PDF
- **Mobile-responsive** design
- **Accessible** — semantic HTML, ARIA labels, keyboard navigation

---

## Technologies Used

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Python 3, Flask, python-dotenv      |
| AI         | Groq API (official Python SDK)      |
| Templates  | Jinja2                              |
| Frontend   | HTML5, CSS3, Vanilla JavaScript     |
| Icons      | Font Awesome 6 (CDN)                |

---

## Project Structure

```
nutrition-agent/
│
├── app.py                  # Flask application & routes
├── requirements.txt        # Python dependencies
├── .env                    # Your local environment variables (not committed)
├── .env.example            # Template for environment variables
├── README.md
│
├── services/
│   └── nutrition_agent.py  # Groq API integration, prompt design, response parsing
│
├── templates/
│   ├── index.html          # Main form page
│   ├── result.html         # Nutrition plan results dashboard
│   └── error.html          # User-friendly error page
│
└── static/
    ├── css/
    │   └── style.css       # All application styles
    └── js/
        └── script.js       # BMI calculator, form validation, loading state
```

---

## Installation & Setup

### Prerequisites

- Python 3.9 or later
- A [Groq API key](https://console.groq.com) (free tier available)
- Internet connection (for the Groq API and Font Awesome CDN)

---

### Step 1 — Clone or download the project

```bash
# If you have git:
git clone <your-repo-url>
cd nutrition-agent

# Or simply download the ZIP and extract it, then open a terminal in the folder.
```

---

### Step 2 — Create a virtual environment

**Windows (PowerShell / Command Prompt):**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

---

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4 — Create your `.env` file

Copy the example file:

**Windows:**
```powershell
copy .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

Open `.env` in any text editor and replace the placeholder with your real Groq API key:

```
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=llama-3.3-70b-versatile
FLASK_DEBUG=false
```

> **Important:** Never commit your `.env` file to version control. Add `.env` to your `.gitignore`.

---

### Step 5 — Run the application

**Windows:**
```powershell
python app.py
```

**macOS / Linux:**
```bash
python app.py
```

You should see output similar to:
```
 * Running on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
```

---

### Step 6 — Open in your browser

Navigate to: **http://localhost:5000**

---

## Configuration Options

All configuration is done through the `.env` file:

| Variable        | Required | Default                    | Description                             |
|-----------------|----------|----------------------------|-----------------------------------------|
| `GROQ_API_KEY`  | Yes      | —                          | Your Groq API key                       |
| `GROQ_MODEL`    | No       | `llama-3.3-70b-versatile`  | Groq model to use                       |
| `FLASK_DEBUG`   | No       | `false`                    | Set to `true` for development auto-reload |

---

## How to Use

1. Open the app at `http://localhost:5000`
2. (Optional) Use the **Quick BMI Calculator** at the top of the page
3. Fill in your **Personal Information** (name, age, gender)
4. Enter your **Body Metrics** (height, weight)
5. Select your **Activity Level** and **Fitness Goal**
6. Choose your **Food Preference**
7. Optionally fill in allergies, disliked foods, cuisine preference, etc.
8. Click **Generate My Nutrition Plan**
9. Wait 10–20 seconds while the AI generates your plan
10. Review your personalised plan, then **Print** or **Create a New Plan**

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `EnvironmentError: GROQ_API_KEY is not set` | Make sure your `.env` file exists and contains a valid `GROQ_API_KEY`. Ensure `venv` is activated when you run `python app.py`. |
| `ModuleNotFoundError: No module named 'groq'` | Run `pip install -r requirements.txt` with your virtual environment activated. |
| `Port 5000 already in use` | Change the port: edit the last line of `app.py` to `app.run(port=5001)` and visit `http://localhost:5001`. |
| `AI service is currently busy` | Groq rate limit hit. Wait a few seconds and try again. |
| `Could not connect to the AI service` | Check your internet connection and Groq API status at https://status.groq.com. |
| Plan generates but looks like plain text | The AI occasionally returns text instead of JSON. The app has a fallback parser — you will still see the output in the summary field. |
| Font Awesome icons not loading | The icons require an internet connection (loaded from a CDN). They will not appear offline. |

---

## Security Notes

- The `GROQ_API_KEY` is loaded server-side only and is **never** sent to the browser.
- All user inputs are validated on both the client (JavaScript) and the server (Python).
- Request size is limited to 1 MB to prevent abuse.
- Exception details are logged server-side but are **not** shown to the user.
- For production deployment, set `FLASK_DEBUG=false` and consider running behind a reverse proxy (e.g., Nginx) with HTTPS.

---

## Nutrition Disclaimer

The nutrition information, calorie estimates, macronutrient guidance, and meal plans generated by HealthCare are for **general educational purposes only**.

- They are **not** medical advice.
- They are **not** a substitute for consultation with a registered dietitian or qualified healthcare professional.
- Calorie and macronutrient figures are **estimates** based on general population data and may not be accurate for your individual circumstances.
- BMI is a **screening tool only** and does not diagnose health conditions.
- For users under 18, adult BMI categories do **not** apply.
- If you have a medical condition, food allergy, eating disorder history, or take medication, please consult a healthcare professional before changing your diet.

---

## License

This project is provided for educational purposes. Feel free to modify and extend it.
