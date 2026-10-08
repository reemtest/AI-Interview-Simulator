# 🎤 AI Interview Simulator

Streamlit app that generates interview questions from your CV and a job description, then scores your answers. The AI backend (FastAPI + LangChain + Gemini) runs on a Kaggle notebook and is exposed through ngrok.

## Architecture

- **Kaggle:** FastAPI server, RAG (Chroma), Gemini calls
- **Local:** Streamlit interface, PDF reading, API client

## Run locally

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

Then paste the Kaggle ngrok URL into the sidebar.

## Backend

The Kaggle notebook is in `kaggle/interview_backend.ipynb`.
