import uuid
from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="Mock Patient Portal")

# Simple in-memory session database
SESSIONS = set()

# Mock patient data database
PATIENTS = {
    "1": {
        "title": "Patient File #1084",
        "narrative": "Patient Name: Monish Kumar. He can be contacted at 9876543210. His email is monish.k@hospital.com. The patient was admitted due to Acute Appendicitis and has been hospitalized for 5 days. Treatment cure status is classified as Cured. Billed fees: $1500. Prescribed medicines: Amoxicillin (500mg), Paracetamol (650mg). Previous record: Has history of Mild Asthma in 2024. Next review: in 2 weeks."
    },
    "2": {
        "title": "Medical Case #3092",
        "narrative": "Here is the medical report for patient Alice Smith. Contact phone number: +1-555-0199. Email identifier: alice.smith@mail.com. Billed fees: 450 USD. The patient is suffering from Severe Influenza. Admitted for a duration of 3 days. Cure status: In Recovery. Prescribed medication: Tamiflu (75mg once daily) and Vitamin C supplements. Prior medical logs: None reported. Insured under: HealthFirst."
    },
    "3": {
        "title": "Patient Record #9941",
        "narrative": "Patient Name: Rajesh Patel. Mobile: 9123456789. Mail address: rajesh.patel@clinic.in. Diagnosed with Type 2 Diabetes. Billed fees: 3200 INR. Hospitalised duration: 12 days. Cure status: Controlled. Current medicines: Metformin 1000mg, Glipizide 5mg. Previous medical history: Hypertension diagnosed in 2022, coronary bypass surgery in 2025."
    },
    "4": {
        "title": "Clinical Chart #1222",
        "narrative": "Record of Sarah Connor, reach at 555-987-6543. Email: s.connor@cyber.org. Billed fees: $850. Medical condition: Chronic Migraine. Admitted for 1 day. Status: Under Treatment. Prescription: Sumatriptan 50mg, Ibuprofen. History: Concussion in 2023. Patient notes: Prefers quiet environment."
    },
    "5": {
        "title": "Clinical File #4088",
        "narrative": "Patient file of John Doe. Contact number: 123-456-7890. Email: john.doe@test.com. Admitted due to Pneumonia. Hospitalized for 8 days. Billed fees: $2200. Cure: Fully Recovered. Medicines: Levofloxacin, Albuterol inhaler. Previous record: Seasonal allergies. Blood group: O-positive. Emergency contact: Jane Doe (555-0011)."
    },
    "6": {
        "title": "Patient Record #7719",
        "narrative": "Vikram Singh, male patient. Reachable at 9812345670. Email address: vikram.s@wellness.in. Medical issue: Kidney Stones. Hospitalized for 2 days. Cure status: Cured after lithotripsy. Medicine prescribed: tamsulosin (0.4mg), Ibuprofen 400mg. Previous medical history: Kidney stones in 2023. Billed fees: 45000 INR. Allergy warning: penicillin."
    },
    "7": {
        "title": "Medical Case #2512",
        "narrative": "Clinical summary of Emily Watson. Reach at 555-123-9876. Mail ID: emily.watson@care.org. Billed fees: 1150 USD. Condition: Fracture Left Arm. Hospitalization: 1 day. Status: Under Treatment. Prescription: Codeine, calcium supplements. Prior medical history: Osteopenia diagnosed in 2025. Cast removal date: July 15th."
    },
    "8": {
        "title": "Patient File #8831",
        "narrative": "Patient Name: Aarav Mehta. Phone number: 9876541230. Email ID: aarav.mehta@clinic.com. Diagnosis: Acute Gastritis. Hospitalized duration: 4 days. Cure status: Resolved. Medicines: Pantoprazole 40mg, Antacids. Past records show mild acid reflux. Total fees: $750. Diet plan: Bland diet, no spicy foods."
    },
    "9": {
        "title": "Clinical Chart #6610",
        "narrative": "Medical file of Elena Rostova, contact info: 555-888-9999, email: elena.r@redhealth.ru. Billed fees: 1800 USD. Diagnosis: Acute Bronchitis. Admitted for: 6 days. Cure status: Cured. Medicine: Azithromycin, cough syrup. Prior history: Smoking for 10 years, quit in 2024. Next scan: October 2026."
    }
}

# HTML Template Helper
def render_page(title: str, content: str, logged_in: bool = True) -> str:
    nav = ""
    if logged_in:
        nav = '<a href="/patients" style="color:#a9b1d6;text-decoration:none;margin-right:20px;font-weight:600;">📋 Patient Database</a><a href="/logout" style="color:#f7768e;text-decoration:none;font-weight:600;">🚪 Logout</a>'
    else:
        nav = '<span style="color:#565f89;font-weight:600;">🔒 Secure Access</span>'

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title} - Kathir Memorial Portal</title>
        <meta charset="utf-8">
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Plus Jakarta Sans', sans-serif;
                background-color: #1a1b26;
                color: #c0caf5;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                min-height: 100vh;
            }}
            header {{
                background-color: #1f2335;
                border-bottom: 1px solid #414868;
                padding: 15px 40px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .logo {{
                font-size: 20px;
                font-weight: 700;
                color: #7aa2f7;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .container {{
                flex: 1;
                max-width: 900px;
                margin: 40px auto;
                padding: 0 20px;
                width: 100%;
                box-sizing: border-box;
            }}
            .card {{
                background-color: #24283c;
                border: 1px solid #414868;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            }}
            h1, h2, h3 {{
                color: #7aa2f7;
                margin-top: 0;
            }}
            .input-group {{
                margin-bottom: 20px;
            }}
            label {{
                display: block;
                margin-bottom: 8px;
                color: #9ece6a;
                font-size: 14px;
                font-weight: 500;
            }}
            input[type="text"], input[type="password"] {{
                width: 100%;
                padding: 12px;
                border: 1px solid #414868;
                border-radius: 6px;
                background-color: #1a1b26;
                color: #c0caf5;
                font-size: 16px;
                box-sizing: border-box;
                transition: border-color 0.2s;
            }}
            input[type="text"]:focus, input[type="password"]:focus {{
                border-color: #7aa2f7;
                outline: none;
            }}
            button {{
                background-color: #7aa2f7;
                color: #1a1b26;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: 700;
                cursor: pointer;
                transition: background-color 0.2s, transform 0.1s;
            }}
            button:hover {{
                background-color: #89ddff;
            }}
            button:active {{
                transform: scale(0.98);
            }}
            .patient-link {{
                display: block;
                padding: 15px;
                border: 1px solid #414868;
                border-radius: 8px;
                margin-bottom: 12px;
                color: #c0caf5;
                text-decoration: none;
                background-color: #1f2335;
                transition: transform 0.2s, border-color 0.2s;
            }}
            .patient-link:hover {{
                transform: translateX(5px);
                border-color: #7aa2f7;
                background-color: #24283c;
            }}
            .narrative-box {{
                background-color: #1a1b26;
                border-left: 4px solid #f7768e;
                padding: 20px;
                border-radius: 4px;
                line-height: 1.6;
                font-size: 16px;
                white-space: pre-line;
            }}
            .error {{
                color: #f7768e;
                background-color: rgba(247, 118, 142, 0.1);
                border: 1px solid #f7768e;
                padding: 10px;
                border-radius: 6px;
                margin-bottom: 20px;
                font-size: 14px;
            }}
            footer {{
                text-align: center;
                padding: 20px;
                color: #565f89;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <header>
            <div class="logo">
                <span style="font-size:24px;">🏥</span> Kathir Memorial Hospital
            </div>
            <nav>{nav}</nav>
        </header>
        <div class="container">
            <div class="card">
                {content}
            </div>
        </div>
        <footer>
            &copy; 2026 Kathir Memorial Hospital Medical Records Portal. All rights reserved.
        </footer>
    </body>
    </html>
    """

def check_auth(request: Request) -> bool:
    session_id = request.cookies.get("session_id")
    return session_id in SESSIONS

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    if check_auth(request):
        return RedirectResponse(url="/patients")
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request, error: str = None):
    error_html = f'<div class="error">{error}</div>' if error else ""
    form_content = f"""
    <h2>Portal Security Login</h2>
    <p style="color: #9ece6a; margin-bottom: 25px;">Please log in with your credentials to access the patient database.</p>
    {error_html}
    <form action="/login" method="post">
        <div class="input-group">
            <label for="username">Username</label>
            <input type="text" id="username" name="username" placeholder="e.g. admin" required autocomplete="off">
        </div>
        <div class="input-group">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" placeholder="••••••••" required>
        </div>
        <button type="submit">Verify & Log In</button>
    </form>
    <div style="margin-top: 20px; font-size: 13px; color: #565f89;">
        <strong>Demo Credentials:</strong> admin / password123
    </div>
    """
    return HTMLResponse(content=render_page("Login", form_content, logged_in=False))

@app.post("/login")
def login_post(response: Response, username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "password123":
        session_id = str(uuid.uuid4())
        SESSIONS.add(session_id)
        response = RedirectResponse(url="/patients", status_code=303)
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response
    else:
        return RedirectResponse(url="/login?error=Invalid+username+or+password", status_code=303)

@app.get("/logout")
def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if session_id in SESSIONS:
        SESSIONS.remove(session_id)
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="session_id")
    return response

@app.get("/patients", response_class=HTMLResponse)
def list_patients(request: Request):
    if not check_auth(request):
        return RedirectResponse(url="/login")

    links = ""
    for pid, pdata in PATIENTS.items():
        links += f"""
        <a href="/patient/{pid}" class="patient-link">
            <span style="font-weight:600; color:#bb9af7;">{pdata['title']}</span>
            <div style="font-size:13px; color:#565f89; margin-top:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                {pdata['narrative'][:120]}...
            </div>
        </a>
        """

    content = f"""
    <h2>Electronic Health Records Database</h2>
    <p style="color:#9ece6a; margin-bottom:20px;">Select a clinical file to view complete unstructured patient profiles.</p>
    <div style="margin-top:20px;">
        {links}
    </div>
    """
    return HTMLResponse(content=render_page("Patient Database", content))

@app.get("/patient/{patient_id}", response_class=HTMLResponse)
def get_patient(patient_id: str, request: Request):
    if not check_auth(request):
        return RedirectResponse(url="/login")

    if patient_id not in PATIENTS:
        return RedirectResponse(url="/patients")

    pdata = PATIENTS[patient_id]
    content = f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
        <h2>{pdata['title']}</h2>
        <a href="/patients" style="color:#7aa2f7; text-decoration:none; font-size:14px; font-weight:600;">&larr; Back to Database</a>
    </div>
    <div class="narrative-box">
        {pdata['narrative']}
    </div>
    """
    return HTMLResponse(content=render_page(pdata['title'], content))
