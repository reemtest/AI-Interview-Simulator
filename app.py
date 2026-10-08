"""Streamlit GUI for the AI Interview Simulator (backend runs on Kaggle)."""
import os
from pathlib import Path
import streamlit as st
from api_client import (set_base_url, build_retriever, generate_questions,
                        evaluate_answer, final_report, generate_job_description,
                        suggest_role_and_jd)
from pdf_utils import extract_pdf_text
from api_client import (set_base_url, set_password, build_retriever, generate_questions,
                        evaluate_answer, final_report, generate_job_description,
                        suggest_role_and_jd)

DATA = Path(__file__).parent / "Data"
if not DATA.exists():
    DATA = Path(__file__).parent / "data"

st.set_page_config(page_title="AI Interview Simulator", page_icon="🎤")
st.title("🎤 AI Interview Simulator")

defaults = {"started": False, "questions": [], "idx": 0, "results": [], "retriever": None}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

with st.sidebar:
    st.header("Server")
    api_url = st.text_input("Kaggle API URL (ngrok)",
                            value=os.environ.get("REMOTE_API_URL", ""),
                            placeholder="https://xxxx.ngrok-free.dev")
    set_base_url(api_url)
    api_pw = st.text_input("API password", type="password")
    set_password(api_pw)

    st.header("Setup")
    if st.button("Load demo data"):
        st.session_state["cv"] = (DATA / "sample_cv.txt").read_text(encoding="utf-8")
        st.session_state["jd"] = (DATA / "sample_jd.txt").read_text(encoding="utf-8")

    pdf = st.file_uploader("Upload your CV (PDF)", type=["pdf"])
    if pdf is not None:
        pdf_key = f"{pdf.name}-{pdf.size}"
        if st.session_state.get("pdf_key") != pdf_key:
            st.session_state["pdf_key"] = pdf_key
            try:
                text = extract_pdf_text(pdf)
                if text:
                    st.session_state["cv"] = text
                    st.success("CV loaded from PDF. You can edit it below.")
                else:
                    st.warning("No text found in this PDF (maybe a scanned image). "
                               "Paste your CV text below instead.")
            except Exception as e:
                st.error(f"Could not read the PDF: {e}")

    cv = st.text_area("Your CV (paste text or upload a PDF)", key="cv", height=200)
    if st.button("Auto-fill role and job description from my CV"):
        if not api_url.strip():
            st.warning("Enter the Kaggle API URL first.")
        elif not st.session_state.get("cv", "").strip():
            st.warning("Upload a CV or paste its text first.")
        else:
            try:
                with st.spinner("Reading your CV..."):
                    r, why, jd_text = suggest_role_and_jd(st.session_state["cv"])
                st.session_state["role"] = r
                st.session_state["jd"] = jd_text
                st.session_state["role_reason"] = why
            except Exception as e:
                st.error(f"Could not read the CV: {e}")
    if st.session_state.get("role_reason"):
        st.caption(f"Suggested role: {st.session_state['role_reason']}")

    role = st.text_input("Target role (optional)", key="role",
                         placeholder="e.g. AI/ML Engineer")
    if st.button("Generate job description from role"):
        if not api_url.strip():
            st.warning("Enter the Kaggle API URL first.")
        elif not role.strip():
            st.warning("Type a target role first.")
        else:
            try:
                with st.spinner("Writing the job description..."):
                    st.session_state["jd"] = generate_job_description(role)
            except Exception as e:
                st.error(f"Could not generate the job description: {e}")
    jd = st.text_area("Job description (generated or pasted)", key="jd", height=200)
    n = st.slider("Number of questions", 3, 5, 3)

    if st.button("Start interview", type="primary"):
        if not api_url.strip():
            st.warning("Enter the Kaggle API URL first.")
        elif not cv.strip() or not jd.strip():
            st.warning("Please provide both a CV and a job description.")
        else:
            try:
                with st.spinner("Preparing your interview..."):
                    retriever = build_retriever(jd)
                    questions = generate_questions(cv, jd, retriever, n)
                st.session_state.update(
                    started=True, questions=questions, idx=0, results=[], retriever=retriever
                )
                st.rerun()
            except Exception as e:
                st.error(f"Could not start the interview: {e}")

# ---- Main area ----
s = st.session_state
if not s.started:
    st.info("Paste the Kaggle URL in the sidebar, fill in the setup "
            "(or click **Load demo data**), then press **Start interview**.")

elif s.idx < len(s.questions):
    q = s.questions[s.idx]
    st.progress(s.idx / len(s.questions))
    st.subheader(f"Question {s.idx + 1} of {len(s.questions)}")
    st.write(q)
    answer = st.text_area("Your answer", key=f"ans_{s.idx}", height=150)

    if st.button("Submit answer"):
        if not answer.strip():
            st.warning("Please write an answer first.")
        else:
            try:
                with st.spinner("Evaluating..."):
                    ev = evaluate_answer(q, answer, s.retriever)
                s.results.append({"question": q, "answer": answer, "evaluation": ev})
                s.idx += 1
                st.rerun()
            except Exception as e:
                st.error(f"Evaluation failed, please try again: {e}")

    if s.results:
        last = s.results[-1]["evaluation"]
        with st.expander("Feedback on your previous answer"):
            st.metric("Score", f"{last.score}/10")
            st.write(last.feedback)

else:
    st.success("Interview complete! 🎉")
    report = final_report(s.results)
    st.metric("Overall score", f"{report['average']}/10")
    for r in s.results:
        ev = r["evaluation"]
        with st.expander(f"{r['question']}  —  {ev.score}/10"):
            st.write("**Your answer:**", r["answer"])
            st.write("**Feedback:**", ev.feedback)
            st.write("**Missing points:**")
            for m in ev.missing_points:
                st.write(f"- {m}")
            st.write("**Suggestions:**")
            for t in ev.suggestions:
                st.write(f"- {t}")
    if report["strengths"]:
        st.write("**Strengths:**", "; ".join(report["strengths"]))
    if report["weaknesses"]:
        st.write("**Needs work:**", "; ".join(report["weaknesses"]))
    if st.button("Start over"):
        for k in ["started", "questions", "idx", "results", "retriever"]:
            del st.session_state[k]
        st.rerun()