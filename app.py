import streamlit as st
import pandas as pd
import subprocess
import json
import os
import sys
import time
import threading
import socket
from io import BytesIO

# --- Page Configuration ---
st.set_page_config(
    page_title="Kathir Memorial - EHR Crawler Panel",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling & Theme (Premium Dark Mode) ---
st.markdown("""
<style>
    /* Global Background and Typography */
    .stApp {
        background-color: #1a1b26;
        color: #c0caf5;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1f2335;
        border-right: 1px solid #414868;
    }
    
    /* Main Dashboard Titles */
    h1, h2, h3 {
        color: #7aa2f7 !important;
        font-weight: 700 !important;
    }
    
    /* Glassmorphic Cards */
    .metric-card {
        background: rgba(36, 40, 60, 0.6);
        border: 1px solid #414868;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(4px);
        margin-bottom: 20px;
    }
    
    .metric-title {
        font-size: 14px;
        color: #9ece6a;
        font-weight: 500;
        margin-bottom: 5px;
    }
    
    .metric-value {
        font-size: 28px;
        color: #7aa2f7;
        font-weight: 700;
    }
    
    /* Styled Buttons */
    div.stButton > button {
        background-color: #7aa2f7;
        color: #1a1b26;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 700;
        font-size: 16px;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 15px rgba(122, 162, 247, 0.4);
    }
    div.stButton > button:hover {
        background-color: #89ddff;
        color: #1a1b26;
        box-shadow: 0 4px 20px rgba(137, 221, 255, 0.6);
        transform: translateY(-2px);
    }
    
    /* Log console styling */
    .log-box {
        background-color: #1a1b26;
        border: 1px solid #414868;
        border-radius: 6px;
        padding: 15px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 12px;
        color: #a9b1d6;
        max-height: 300px;
        overflow-y: scroll;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# --- Background Server Helper ---
def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_mock_portal():
    """Starts the mock patient portal server if not already running."""
    PORT = 8000
    if not is_port_open(PORT):
        # Start uvicorn in a background daemon thread
        def run_uvicorn():
            import uvicorn
            # We run the mock portal app directly
            uvicorn.run("mock_portal:app", host="127.0.0.1", port=PORT, log_level="warning")
            
        thread = threading.Thread(target=run_uvicorn, daemon=True)
        thread.start()
        time.sleep(1.5) # Allow server to bind and boot

# Start background server
start_mock_portal()

# --- App Layout ---
st.title("🏥 Kathir Memorial EHR Crawler Control")
st.write("Secure automated crawler designed to log in and dynamically extract structured datasets from patient records.")

# Sidebar Configuration
st.sidebar.image("https://img.icons8.com/nolan/128/hospital.png", width=80)
st.sidebar.header("Crawler Configuration")
st.sidebar.write("Configure connection details for the target medical archive.")

target_url = st.sidebar.text_input("Login Page URL", value="http://127.0.0.1:8000/login")
username = st.sidebar.text_input("Username", value="admin")
password = st.sidebar.text_input("Password", value="password123", type="password")

st.sidebar.markdown("---")
st.sidebar.header("Parser Settings")
provider = st.sidebar.selectbox(
    "Parser Engine",
    options=["Heuristics", "Ollama", "Gemini", "OpenAI"],
    help="Heuristics runs locally offline. Ollama runs a local LLM. Gemini and OpenAI run cloud models."
)

api_key = ""
model_name = ""
ollama_url = ""

if provider == "Ollama":
    ollama_url = st.sidebar.text_input("Ollama Endpoint", value="http://localhost:11434")
    model_name = st.sidebar.text_input("Ollama Model", value="qwen")
elif provider == "Gemini":
    api_key = st.sidebar.text_input("Gemini API Key", type="password")
    model_name = st.sidebar.text_input("Gemini Model", value="gemini-1.5-flash")
elif provider == "OpenAI":
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    model_name = st.sidebar.text_input("OpenAI Model", value="gpt-4o-mini")

st.sidebar.markdown("---")
st.sidebar.write("### Target Portal Access")
if is_port_open(8000):
    st.sidebar.success("🟢 Local Mock Portal is RUNNING (Port 8000)")
    st.sidebar.write("[Open Mock Portal in New Tab](http://127.0.0.1:8000/login)")
else:
    st.sidebar.error("🔴 Local Mock Portal is OFFLINE")

# Main Page Dashboard Cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">CRAWLER ENGINE</div>
        <div class="metric-value">Scrapy 2.16.0</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">PARSER MODE</div>
        <div class="metric-value">Dynamic Relation</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">OUTPUT FORMATS</div>
        <div class="metric-value">Excel (.xlsx) / CSV</div>
    </div>
    """, unsafe_allow_html=True)

# Scrape Action Trigger
st.subheader("⚡ Execute Patient Record Extraction")
run_button = st.button("🚀 Launch Automated Scraper & Structuring Bot")

output_file = "extracted_patients.json"

if run_button:
    # Cleanup previous run outputs
    if os.path.exists(output_file):
        os.remove(output_file)

    st.info("Initializing Crawler Process...")
    
    # Placeholder for live logs
    log_header = st.write("📝 **Real-time Engine Logs:**")
    log_placeholder = st.empty()
    
    # Run the spider inside a subprocess, catching logs in real-time
    cmd = [
        "python", "-m", "scrapy", "runspider", "spider.py",
        "-a", f"start_url={target_url}",
        "-a", f"username={username}",
        "-a", f"password={password}",
        "-a", f"provider={provider}",
        "-a", f"api_key={api_key}",
        "-a", f"model_name={model_name}",
        "-a", f"ollama_url={ollama_url}",
        "-O", output_file
    ]
    
    log_lines = []
    
    try:
        # Start subprocess
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Stream logs line-by-line
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                log_lines.append(line.strip())
                # Update text area in streamlit with last 10 lines for readability
                log_placeholder.code("\n".join(log_lines[-12:]))
                time.sleep(0.01) # Avoid UI choking
                
        rc = process.poll()
        
        if rc == 0 and os.path.exists(output_file):
            st.success("Crawling completed successfully!")
            
            # Read output JSON
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if data:
                # Convert to DataFrame
                df = pd.DataFrame(data)
                
                # Normalize column orders: Core patient info first, metadata/dynamic fields last
                core_fields = ["Patient Name", "Mobile Number", "Email ID", "Disease", "Hospitalized Duration", "Cure Status", "Medicine", "Previous Record", "Fees"]
                
                # Check for dynamic fields not in core list
                dynamic_fields = [col for col in df.columns if col not in core_fields and col != "Source URL"]
                
                ordered_cols = []
                for fld in core_fields:
                    if fld in df.columns:
                        ordered_cols.append(fld)
                ordered_cols.extend(sorted(dynamic_fields))
                if "Source URL" in df.columns:
                    ordered_cols.append("Source URL")
                    
                df = df[ordered_cols]
                
                # Replace N/A and NaN for cleaner representation
                df.fillna("N/A", inplace=True)
                df.replace("N/A", "N/A", inplace=True)
                
                st.subheader(f"📊 Extracted Patient Records ({len(df)} Profiles)")
                
                # Interactive Table Preview
                st.dataframe(df, use_container_width=True)
                
                # Generate Excel Output using openpyxl in-memory
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Patients Data')
                
                excel_data = excel_buffer.getvalue()
                
                # Download button for Excel
                st.download_button(
                    label="📥 Download Data as Excel (.xlsx)",
                    data=excel_data,
                    file_name="kathir_extracted_patients.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                # Download button for CSV
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Download Data as CSV (.csv)",
                    data=csv_data,
                    file_name="kathir_extracted_patients.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.warning("Crawler executed successfully, but no patient records could be extracted from pages.")
        else:
            st.error(f"Scrapy crawler process exited with error code: {rc}. Please inspect full logs.")
            with st.expander("View Full Execution Log Trace"):
                st.text("\n".join(log_lines))
                
    except Exception as e:
        st.error(f"An error occurred while launching the crawler: {e}")
        
    finally:
        # Cleanup
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except:
                pass
                
# General Instructions Footer
st.markdown("---")
st.markdown("### How it Works")
st.markdown("""
1. **Automated Form Login**: The crawler sends credentials via HTTP POST to the target's `/login` page and retains the authenticated session cookie.
2. **Dynamic Profiling**: It visits the secure patient list and follows profile URLs.
3. **Relation & Attribute Mapping**: The unstructured raw text is run through the parser which matches regex keys, cleans fields, and detects any page-specific dynamic columns (like `Insured under` or `Next review`).
4. **Export Engine**: Discovered columns are dynamically assembled into a tabular grid and packaged for instant download in standard spreadsheet formats.
""")
