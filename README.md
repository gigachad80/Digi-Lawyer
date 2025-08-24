🚀 **Project Name: DigiLawyer**  
===============

![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-purple.svg)  
<a href="https://github.com/gigach/Digi-Lawyer/issues"><img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat"></a>

 **DigiLawyer is RAG-based AI Assistant for Cybercrime Law Guidance and Complaint Filing (Retrieval-Augmented Generation)**

---

## 📋 Table of Contents

- [📌 Overview](#-overview)  
- [🤔 Why This Name?](#-why-this-name)  
- [⌚ Development Time](#-development-time)  
- [🙃 Why I Created This](#why-i-created-this)  
- [📚 Requirements & Dependencies](#-requirements--dependencies)  
- [📥 Installation Guide & Usage](#-installation-guide--usage)  
  - [⚡ Quick Install](#-quick-install)  
- [🍃 Usage](#-usage)  
- [⚙️ Environment Variables](#️-environment-variables)   
- [📝 Roadmap / To-do](#-roadmap--to-do)  
- [💓 Credits](#-credits)  
- [📞 Contact](#-contact)  
- [📄 License](#-license)  

---

### 📌 Overview

**_DigiLawyer_** is a legal assistant that helps users understand and apply Indian cybercrime laws. It uses RAG (Retrieval-Augmented Generation) technology to provide accurate legal recommendations, specific law sections, complaint filing procedures, and penalty information by analyzing uploaded legal documents.

---

### 🤔 Why This Name?

Because it's a digital lawyer specializing in cybercrime laws, helping users navigate legal complexities using AI technology.

---

### ⏱️ Total Time Spent


3 hours, 1 minute, 13 seconds

This includes development, testing, and writing the README.

Spent 44 minutes attempting deployment with Ploomber to avoid authorizing Streamlit with GitHub.

Tried multiple versions since I’m new to Streamlit.

Also created a CLI version of the app as an alternative.

Eventually returned to Streamlit for deployment. 🥲

---

### 🙃 Why I Created This

As a cybersecurity professional who is also learning cybercrime investigation, I often encounter situations where understanding the legal implications of cybercrimes is crucial. Instead of manually searching through numerous legal documents and laws, I decided to create an AI assistant that can instantly provide relevant legal information and recommendations.

---

### 📚 Requirements & Dependencies

- **Python 3.8+**  
- **Streamlit**  
- **Google Gemini API**  
- **LangChain**

---

### 📥 Installation Guide & Usage

#### ⚡ Quick Install

1. Clone this repository:

   ```bash
   git clone https://github.com/gigachad80/Digi-Lawyer
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
---

### 🍃 Usage

3. Import all the credentials in a `.env` file (default: `gemini-2.5-flash`)  
4. Run the application:

   ```bash
   streamlit run app.py
   ```

OR 

5. Directley visit on site : https://cyberlex.streamlit.app and upload documents 
---

### ⚙️ Environment Variables

1. Go to https://aistudio.google.com/
2. Create API key
3. Set model & API key in .env & chunking & overlap size 
4. By default https://cyberlex.streamlit.app uses Gemini-2.5-flash , 250 as chunking size and overlap size as 40

---

### 📝 Roadmap / To-do

- [ ] Integrate more legal sources and datasets  
- [ ] Add a customization section in the README for international countries  
- [ ] Attach a demo GIF or video to the README  

---

### 💓 Credits

- **Karan Sir** — for lectures on Cyber Laws  
- **Kanik Gupta** — for assistance with deploying the app on Streamlit 

---

### 📞 Contact

📧 Email: **pookielinuxuser@tutamail.com**

---

### 📄 License

Licensed under the **RPL 1.5** and a **Custom License**.  
Check here: [`CREDITS.md`](https://github.com/gigachad80/Digi-Lawyer/blob/main/CREDITS.md) (Important)  
Also see: [`LICENSE.md`](https://github.com/gigachad80/Digi-Lawyer/blob/main/LICENCE.md)


---

🕒 **Last Updated:** August 24, 2025




1. Clone the repository:
```bash
git clone https://github.com/gigachad80/Digi-Lawyer
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
