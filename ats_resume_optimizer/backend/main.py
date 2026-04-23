import os
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ats_engine import analyze, ATSReport
from optimizer import optimize_resume
from resume_parser import parse_resume

app = FastAPI(title="ATS Resume Optimizer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeResponse(BaseModel):
    keyword_score: float
    semantic_score: float
    overall_score: float
    verdict: str
    matched_keywords: list[str]
    missing_keywords: list[str]
    jd_keyword_count: int
    resume_keyword_count: int
    resume_text: str


class OptimizeResponse(BaseModel):
    optimized_resume: str
    keyword_score: float
    semantic_score: float
    overall_score: float
    verdict: str
    matched_keywords: list[str]
    missing_keywords: list[str]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
):
    try:
        resume_text = await parse_resume(resume)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from resume")
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")

    report: ATSReport = analyze(resume_text, job_description)

    return AnalyzeResponse(
        keyword_score=report.keyword_score,
        semantic_score=report.semantic_score,
        overall_score=report.overall_score,
        verdict=report.verdict,
        matched_keywords=report.matched_keywords,
        missing_keywords=report.missing_keywords,
        jd_keyword_count=report.jd_keyword_count,
        resume_keyword_count=report.resume_keyword_count,
        resume_text=resume_text,
    )


@app.post("/api/optimize", response_model=OptimizeResponse)
async def optimize_endpoint(
    resume: UploadFile = File(None),
    resume_text_input: str = Form(None),
    job_description: str = Form(...),
):
    if resume is not None and resume.filename:
        try:
            resume_text = await parse_resume(resume)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif resume_text_input:
        resume_text = resume_text_input
    else:
        raise HTTPException(status_code=400, detail="Provide resume file or resume_text_input")

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from resume")

    report: ATSReport = analyze(resume_text, job_description)

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY not configured. Set it in backend/.env to enable optimization.",
        )

    try:
        optimized = optimize_resume(resume_text, job_description, report.missing_keywords)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI optimization failed: {str(e)}")

    optimized_report: ATSReport = analyze(optimized, job_description)

    return OptimizeResponse(
        optimized_resume=optimized,
        keyword_score=optimized_report.keyword_score,
        semantic_score=optimized_report.semantic_score,
        overall_score=optimized_report.overall_score,
        verdict=optimized_report.verdict,
        matched_keywords=optimized_report.matched_keywords,
        missing_keywords=optimized_report.missing_keywords,
    )
