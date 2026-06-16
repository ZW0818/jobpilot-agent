from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from schemas.jobpilot_schema import CareerChatRequest, CareerChatResponse, JobPilotResult
from services.career_chat_service import CareerChatService
from services.file_service import extract_text_from_upload
from services.supervisor_service import SupervisorService


router = APIRouter(prefix="/api", tags=["jobpilot"])


@router.post("/analyze", response_model=JobPilotResult)
async def analyze_resume(
    resume_file: UploadFile = File(...),
    jd_text: str = Form(...),
) -> JobPilotResult:
    if not jd_text or not jd_text.strip():
        raise HTTPException(status_code=400, detail="jd_text is required.")

    resume_text = await extract_text_from_upload(resume_file)
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="resume_file did not contain readable text.")

    supervisor = SupervisorService()
    return supervisor.run(resume_text=resume_text, jd_text=jd_text)


@router.post("/chat", response_model=CareerChatResponse)
async def career_chat(payload: CareerChatRequest) -> CareerChatResponse:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question is required.")

    chat_service = CareerChatService()
    return chat_service.answer(question=question, history=payload.history)
