Step 1: Download the Qwen Model via Ollama
Open your Command Prompt (cmd) or PowerShell.
Run this command to download and start the model:
bash


ollama run qwen2.5:1.5b
Wait for the download progress to reach 100%. Once downloaded, it will start a command-line chat session with the model. You can type /exit and press Enter to close the chat. The Ollama service will remain running in the background.
Step 2: Start the Web Scraper Application
Open a new Command Prompt or PowerShell window.
Navigate to your project directory (if you aren't already there):
powershell


cd c:\Users\MONISH\Proj\kathirs_llm
Launch the Streamlit dashboard by running:
powershell


python -m streamlit run app.py
Streamlit will output: Local URL: http://localhost:8501 and it should automatically open a new tab in your web browser. If it doesn't, copy and paste http://localhost:8501 into your browser.
(Note: The FastAPI mock website containing the 9 patient files will automatically start up in the background on port 8000 as soon as you open the Streamlit dashboard).

Step 3: Configure the Control Panel
In the sidebar on the left side of the screen, adjust the following settings:

Crawler Configuration: Keep defaults (Login URL: http://127.0.0.1:8000/login, Username: admin, Password: password123).
Parser Settings:
Change Parser Engine from Heuristics to Ollama.
Set Ollama Endpoint to: http://localhost:11434 (default).
Set Ollama Model to: qwen2.5:1.5b (which matches the model you pulled in Step 1).
Step 4: Execute the Crawler & Download the Excel File
Click the big blue 🚀 Launch Automated Scraper & Structuring Bot button.
Under Real-time Engine Logs, you will see the logs streaming:
The crawler will navigate to /login, submit the credentials, and store the authentication cookies.
It will find the 9 patient records and visit their profiles.
It will feed each profile's unstructured text to your local Qwen model.
The Qwen model will perform Named Entity Recognition (NER), build the relationships, and return structured JSON.
Once completed, a spreadsheet table preview will appear on the dashboard displaying the extracted fields, including dynamically discovered columns like Blood group, Diet plan, and Allergy warning.
Click 📥 Download Data as Excel (.xlsx) or 📄 Download Data as CSV (.csv) to download the structured database file!
