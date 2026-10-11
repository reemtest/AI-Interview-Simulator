"""Local client: same function names as the old lab.py, but each call goes to the Kaggle API."""
from types import SimpleNamespace

import requests

_BASE_URL = ""
_PASSWORD = ""
TIMEOUT = 180  # seconds; the model can be slow


def set_base_url(url: str):
    global _BASE_URL
    _BASE_URL = (url or "").strip().rstrip("/")


def set_password(pw: str):
    global _PASSWORD
    _PASSWORD = (pw or "").strip()


def _post(path: str, payload: dict) -> dict:
    if not _BASE_URL:
        raise RuntimeError("Enter the Kaggle API URL in the sidebar first.")
    headers = {
        "Authorization": f"Bearer {_PASSWORD}",
        "ngrok-skip-browser-warning": "true",   # avoids ngrok's interstitial page
    }
    try:
        r = requests.post(_BASE_URL + path, json=payload, headers=headers, timeout=TIMEOUT)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Cannot reach the server (is the Kaggle notebook running?): {e}")
    if r.status_code == 401:
        raise RuntimeError("Wrong or missing API password.")
    if not r.ok:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise RuntimeError(f"Server error {r.status_code}: {detail}")
    return r.json()


# ---- same names app.py already uses ----
def build_retriever(job_description: str):
    # The server builds and caches the retriever itself, keyed by the job description,
    # so locally we just keep the job description as the "retriever" token.
    return job_description


def generate_questions(cv: str, jd: str, retriever, n: int = 3):
    return _post("/questions", {"cv": cv, "job_description": jd, "n": n})["questions"]


def evaluate_answer(question: str, answer: str, retriever):
    data = _post("/evaluate", {"question": question, "answer": answer,
                               "job_description": retriever})
    return SimpleNamespace(**data)   # gives .score, .feedback, .missing_points, .suggestions


def generate_job_description(role: str) -> str:
    return _post("/job-description", {"role": role})["job_description"]


def suggest_role_and_jd(cv: str):
    d = _post("/suggest-role", {"cv": cv})
    return d["role"], d["reason"], d["job_description"]


def final_report(results: list) -> dict:
    scores = [r["evaluation"].score for r in results]
    avg = sum(scores) / len(scores) if scores else 0
    strengths = [r["question"] for r in results if r["evaluation"].score >= 7]
    weaknesses = [r["question"] for r in results if r["evaluation"].score <= 4]
    return {"average": round(avg, 1), "strengths": strengths, "weaknesses": weaknesses}