import re
import json
import requests

SYSTEM_PROMPT = """You are an expert medical relation extraction assistant.
Analyze the following unstructured patient narrative text.
Perform Named Entity Recognition (NER) and Relation Extraction to build structured key-value relationships.

Extract and return a valid JSON object.
You MUST output the following standard fields if they are found in the text. Use these exact keys:
- "Patient Name"
- "Mobile Number"
- "Email ID"
- "Disease"
- "Hospitalized Duration"
- "Cure Status"
- "Medicine"
- "Previous Record"
- "Fees"

If any of these standard fields are missing in the text, set their value to "N/A".

In addition, identify any other relationships or attributes of the patient mentioned in the text (e.g. blood group, diet plan, allergy warning, cast removal date, emergency contact, insured status, patient notes, next scan/review, age, gender, etc.). Add these as new keys in the JSON object exactly as you discover them. Do not include empty keys.

Do not output any introductory or explanatory text. Return ONLY the raw JSON object.
"""

def clean_value(val: str) -> str:
    """Helper to clean extra spaces and trailing punctuation from extracted values."""
    if not val:
        return ""
    val = val.strip()
    # Remove trailing periods if they terminate a sentence, but keep it if it's part of an email or decimal
    if val.endswith('.') and not val.endswith('.com') and not re.search(r'\d\.\d$', val):
        val = val[:-1]
    return val.strip()

def clean_json_string(s: str) -> str:
    """Removes markdown backticks and wraps from JSON response strings."""
    s = s.strip()
    if s.startswith("```json"):
        s = s[7:]
    elif s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    return s.strip()

def parse_patient_narrative_heuristics(text: str) -> dict:
    """
    Fallback parser using regular expressions and heuristics to extract patient information.
    """
    data = {}
    
    # --- 1. Basic Text Cleanup ---
    normalized_text = text.replace('\n', ' ').strip()
    
    # --- 2. Extract Standard Entities (Email, Mobile, Fees) via direct Regex ---
    
    # Email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        data["Email ID"] = email_match.group(0)
        
    # Phone/Mobile
    phone_match = re.search(r'(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}|\b\d{10}\b', text)
    if phone_match:
        data["Mobile Number"] = phone_match.group(0)

    # Fees
    fees_match = re.search(r'(?:\$\d+(?:\.\d{2})?|\b\d+\s*(?:USD|INR|fees|billed)\b|\b(?:fees|billed|amount):\s*\$?\d+)', text, re.IGNORECASE)
    if fees_match:
        data["Fees"] = clean_value(fees_match.group(0))
    else:
        fees_fallback = re.search(r'\$\d+|\b\d+\s*(?:USD|INR)\b', text)
        if fees_fallback:
            data["Fees"] = clean_value(fees_fallback.group(0))

    # --- 3. Extract Patient Name ---
    name_patterns = [
        r'Patient Name:\s*([^.\n,]+)',
        r'patient\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'Record of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'report for patient\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
    ]
    for pattern in name_patterns:
        name_match = re.search(pattern, text, re.IGNORECASE)
        if name_match:
            data["Patient Name"] = clean_value(name_match.group(1))
            break

    # --- 4. Sentence-based Semantic Keyword Extraction ---
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        # Disease / Condition
        if any(kw in sentence.lower() for kw in ["diagnosed with", "suffering from", "admitted due to", "medical condition"]):
            disease_match = re.search(r'(?:diagnosed with|suffering from|admitted due to|medical condition:?)\s+([^.\n,]+)', sentence, re.IGNORECASE)
            if disease_match:
                raw_disease = disease_match.group(1)
                clause_split = re.split(r'\s+\b(?:and|but|for)\b\s+(?:has|was|is|been|had|hospitalized|admitted)\b', raw_disease, flags=re.IGNORECASE)
                data["Disease"] = clean_value(clause_split[0])
                
        # Hospitalization Duration
        if any(kw in sentence.lower() for kw in ["hospitalized for", "admitted for", "duration of"]):
            duration_match = re.search(r'(?:hospitalized for|admitted for|duration of|hospitalised duration:?)\s+(\d+\s+\w+)', sentence, re.IGNORECASE)
            if duration_match:
                data["Hospitalized Duration"] = clean_value(duration_match.group(1))
                
        # Cure Status
        if any(kw in sentence.lower() for kw in ["cure status", "cured", "recovery", "status:", "controlled"]):
            status_match = re.search(r'(?:cure status is classified as|status:?|cure status:?)\s*([^.\n,]+)', sentence, re.IGNORECASE)
            if status_match:
                data["Cure Status"] = clean_value(status_match.group(1))
            elif "cured" in sentence.lower():
                data["Cure Status"] = "Cured"
            elif "in recovery" in sentence.lower():
                data["Cure Status"] = "In Recovery"
            elif "controlled" in sentence.lower():
                data["Cure Status"] = "Controlled"

        # Medicines
        if any(kw in sentence.lower() for kw in ["prescribed", "medication", "medicines", "prescription", "current medicines"]):
            med_match = re.search(r'(?:prescribed medicines|prescribed medication|current medicines|prescription|medicines):\s*([^.\n]+)', sentence, re.IGNORECASE)
            if med_match:
                data["Medicine"] = clean_value(med_match.group(1))
            else:
                med_match_alt = re.search(r'(?:prescribed|prescription:?)\s+([^.\n]+)', sentence, re.IGNORECASE)
                if med_match_alt:
                    data["Medicine"] = clean_value(med_match_alt.group(1))

        # Previous record / History
        if any(kw in sentence.lower() for kw in ["history of", "prior medical", "previous medical", "history:", "previous record"]):
            hist_match = re.search(r'(?:history of|prior medical logs|previous medical history|history|previous record):\s*([^.\n]+)', sentence, re.IGNORECASE)
            if hist_match:
                data["Previous Record"] = clean_value(hist_match.group(1))
            else:
                hist_match_alt = re.search(r'(?:history of|history:)\s+([^.\n]+)', sentence, re.IGNORECASE)
                if hist_match_alt:
                    data["Previous Record"] = clean_value(hist_match_alt.group(1))

    # --- 5. Dynamic Key-Value Structure Extraction ---
    kv_matches = re.finditer(r'\b([\w\s]{3,20})\s*:\s*([^.\n]+)', text)
    for m in kv_matches:
        key = m.group(1).strip()
        val = m.group(2).strip()
        
        key_lower = key.lower()
        if "name" in key_lower and "patient" in key_lower:
            if "Patient Name" not in data or data["Patient Name"] in ["", "N/A"]:
                data["Patient Name"] = clean_value(val)
        elif "phone" in key_lower or "mobile" in key_lower or "contact" in key_lower:
            if "Mobile Number" not in data or data["Mobile Number"] in ["", "N/A"]:
                data["Mobile Number"] = clean_value(val)
        elif "email" in key_lower or "mail" in key_lower:
            if "Email ID" not in data or data["Email ID"] in ["", "N/A"]:
                data["Email ID"] = clean_value(val)
        elif "fee" in key_lower or "bill" in key_lower:
            if "Fees" not in data or data["Fees"] in ["", "N/A"]:
                data["Fees"] = clean_value(val)
        elif "medicine" in key_lower or "medication" in key_lower or "prescription" in key_lower:
            if "Medicine" not in data or data["Medicine"] in ["", "N/A"]:
                data["Medicine"] = clean_value(val)
        elif "history" in key_lower or "prior log" in key_lower or "previous record" in key_lower:
            if "Previous Record" not in data or data["Previous Record"] in ["", "N/A"]:
                data["Previous Record"] = clean_value(val)
        elif "duration" in key_lower:
            if "Hospitalized Duration" not in data or data["Hospitalized Duration"] in ["", "N/A"]:
                data["Hospitalized Duration"] = clean_value(val)
        elif "cure" in key_lower or "status" in key_lower:
            if "Cure Status" not in data or data["Cure Status"] in ["", "N/A"]:
                data["Cure Status"] = clean_value(val)
        elif "disease" in key_lower or "condition" in key_lower:
            if "Disease" not in data or data["Disease"] in ["", "N/A"]:
                data["Disease"] = clean_value(val)
        else:
            if not any(stop_word in key_lower for stop_word in ["http", "https", "www", "date", "time"]):
                data[key] = clean_value(val)

    # --- 6. Post-processing Synonyms and Defaults ---
    required_keys = ["Patient Name", "Mobile Number", "Email ID", "Disease", "Hospitalized Duration", "Cure Status", "Medicine", "Previous Record", "Fees"]
    for rk in required_keys:
        if rk not in data:
            data[rk] = "N/A"
            
    return data

def parse_patient_narrative_llm(text: str, provider: str, api_key: str = "", model_name: str = "", ollama_url: str = "") -> dict:
    """
    Sends unstructured patient text to an LLM provider and receives structured extraction results in JSON.
    """
    if provider == "Ollama":
        url = ollama_url or "http://localhost:11434"
        if not url.endswith("/api/generate"):
            url = url.rstrip("/") + "/api/generate"
            
        payload = {
            "model": model_name or "qwen",
            "prompt": f"{SYSTEM_PROMPT}\n\nPatient text:\n{text}",
            "stream": False,
            "format": "json"
        }
        
        response = requests.post(url, json=payload, timeout=20)
        response.raise_for_status()
        res_data = response.json()
        raw_response = res_data.get("response", "")
        return json.loads(clean_json_string(raw_response))
        
    elif provider == "Gemini":
        model = model_name or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": f"{SYSTEM_PROMPT}\n\nPatient text:\n{text}"}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        
        response = requests.post(url, json=payload, timeout=20)
        response.raise_for_status()
        res_data = response.json()
        
        candidates = res_data.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if parts:
                raw_response = parts[0].get("text", "")
                return json.loads(clean_json_string(raw_response))
        raise ValueError("Invalid Gemini response body structure.")
        
    elif provider == "OpenAI":
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name or "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        res_data = response.json()
        
        choices = res_data.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            raw_response = message.get("content", "")
            return json.loads(clean_json_string(raw_response))
        raise ValueError("Invalid OpenAI response body structure.")
        
    else:
        raise ValueError(f"Unknown provider: {provider}")

def parse_patient_narrative(text: str, provider: str = "Heuristics", api_key: str = "", model_name: str = "", ollama_url: str = "") -> dict:
    """
    Main parser coordinating LLM and rule-based heuristic extraction.
    """
    if provider == "Heuristics" or not provider:
        return parse_patient_narrative_heuristics(text)
        
    try:
        return parse_patient_narrative_llm(text, provider, api_key, model_name, ollama_url)
    except Exception as e:
        # Graceful fallback to regex heuristics
        print(f"[Parser WARNING] LLM extraction with {provider} failed: {e}. Falling back to Rule-based Heuristics.")
        return parse_patient_narrative_heuristics(text)

if __name__ == "__main__":
    sample_text = "Patient Name: John Doe. Emergency contact: Jane Doe (555-0011). Diagnosed with acute Pneumonia, hospitalized for 8 days. Fully Recovered. Billed: $2200."
    parsed = parse_patient_narrative(sample_text)
    print("Parsed output (Heuristics):")
    for k, v in parsed.items():
        print(f"  {k}: {v}")
