### 📚  Requirements & Dependencies

* #### Python


### 📥 Installation Guide & USage : 

#### ⚡ Quick Install:


1. Clone the repository:
```bash
git clone <your-repo-url>
cd cybercrime_rag
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```env
GOOGLE_API_KEY=your_actual_google_api_key_here
GEMINI_MODEL=gemini-2.5-flash
CHUNK_SIZE=250
OVERLAP_SIZE=40
```

4. Run the app:
```bash
streamlit run app.py
```

## Deployment

### Streamlit Cloud
1. Push to GitHub
2. Connect to Streamlit Cloud
3. Add secrets in Streamlit dashboard:
   - `GOOGLE_API_KEY = your_key_here`


### 🍃 Usage :


1. Upload your legal documents (PDF/MD)
2. Wait for processing
3. Ask questions about cybercrime laws
4. Get comprehensive legal recommendations
