import os
import requests
from types import SimpleNamespace

BASE_URL = os.environ.get("REMOTE_API_URL", "").rstrip("/")
PASSWORD = os.environ.get("REMOTE_API_PASSWORD", "")


def set_base_url(url: str):
    global BASE_URL
    BASE_URL = (url or "").strip().rstrip("/")


def set_password(pw: str):
    global PASSWORD
    PASSWORD = pw or ""


def _post(path, payload):
    if not BASE_URL:
        raise RuntimeError("API URL is not set.")
    headers = {"ngrok-skip-browser-warning": "1",
               "Authorization": f"Bearer {PASSWORD}"}
    r = requests.post(BASE_URL + path, json=payload, headers=headers, timeout=180)
    if r.status_code == 401:
        raise RuntimeError("Wrong password. Check the password in the sidebar.")
    if not r.ok:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise RuntimeError(f"{r.status_code}: {detail}")
    return r.json()
def build_retriever(jd):
    return jd  # the server builds and caches the retriever itself


def generate_questions(cv, jd, retriever, n=3):
    return _post("/questions", {"cv": cv, "job_description": jd, "n": n})["questions"]


def evaluate_answer(question, answer, retriever):
    d = _post("/evaluate", {"question": question, "answer": answer,
                            "job_description": retriever})
    return SimpleNamespace(**d)


def generate_job_description(role):
    return _post("/job-description", {"role": role})["job_description"]


def suggest_role_and_jd(cv):
    d = _post("/suggest-role", {"cv": cv})
    return d["role"], d["reason"], d["job_description"]


def final_report(results):
    scores = [r["evaluation"].score for r in results]
    avg = sum(scores) / len(scores) if scores else 0
    return {
        "average": round(avg, 1),
        "strengths": [r["question"] for r in results if r["evaluation"].score >= 7],
        "weaknesses": [r["question"] for r in results if r["evaluation"].score <= 4],
    }