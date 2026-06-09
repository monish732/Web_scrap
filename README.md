# 🏥 Kathir Memorial - EHR Crawler & Relation Structuring System

An automated web crawler that logs into a secure clinical portal, crawls unstructured patient narrative files, utilizes local or cloud Large Language Models (LLMs) to perform relation extraction, and generates downloadable Excel and CSV spreadsheets.

---

## 🚀 Step-by-Step Running Instructions

### 1. Download & Launch the LLM via Ollama
Before running the scraper, you must download the local model to handle the relation extraction:
1. Open your terminal (Command Prompt or PowerShell).
2. Download and run the **Qwen 2.5 (1.5B)** model by running:
   ```bash
   ollama run qwen2.5:1.5b
   ```
3. Once the download reaches 100%, a command line chat will open. You can type `/exit` and press Enter to exit. The service will continue running in the background.

---

### 2. Run the Streamlit Scraper Dashboard
1. Open a new terminal window.
2. Navigate to this project directory:
   ```powershell
   cd c:\Users\MONISH\Proj\kathirs_llm
   ```
3. Start the dashboard server:
   ```powershell
   python -m streamlit run app.py
   ```
4. Open your browser and go to: **[http://localhost:8501](http://localhost:8501)**.
*(Note: A background FastAPI process simulating the target medical portal automatically boots on port `8000` when the dashboard is loaded).*

---

### 3. Configure Sidebar Settings
In the Streamlit left sidebar, adjust the following parameters:
1. **Target Portal Login**: Keep defaults (Login URL: `http://127.0.0.1:8000/login`, User: `admin`, Pass: `password123`).
2. **Parser Engine**: Change from `Heuristics` to **`Ollama`**.
3. **Ollama Endpoint**: `http://localhost:11434` (default).
4. **Ollama Model**: `qwen2.5:1.5b` (matching the model pulled in Step 1).

---

### 4. Scrape & Download structured Excel
1. Click the **`Launch Automated Scraper & Structuring Bot`** button.
2. Watch the Scrapy spider log in, crawl the **9 patient records**, and pass them to Qwen in real-time.
3. Review the extracted spreadsheet table on the web page. The model automatically extracts the core columns along with dynamically discovered relation columns (e.g. `Blood group`, `Diet plan`, `Allergy warning`).
4. Click **`Download Data as Excel (.xlsx)`** or **`Download Data as CSV`** to save your structured file.

---

## 🛠️ Project Structure
* **`app.py`**: Streamlit control panel, background server starter, and spreadsheet generator.
* **`mock_portal.py`**: FastAPI server hosting the login portal and unstructured patient files.
* **`spider.py`**: Scrapy spider executing authenticated form submission and crawling.
* **`dynamic_parser.py`**: Extraction module routing texts to local Ollama, Gemini API, OpenAI API, or the offline regular-expression parser.
