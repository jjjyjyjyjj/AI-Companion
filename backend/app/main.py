import os
import asyncio
from typing import AsyncGenerator, Optional
from datetime import datetime, time as dt_time

from app.config import Settings
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Gemini
from google import genai
from google.genai import types

# Database
from app.db.conn import db_session
from app.db.repository import SessionRepository, PlanRepository
from app.models import SessionStatus

# Services
from app.services.music import music_service
from app.services.attention_detector_service import attention_detector_service

# Gemini client (optional - only initialize if API key is available)
try:
    client = genai.Client(api_key=Settings.GEMINI_API_KEY) if Settings.GEMINI_API_KEY else None
except Exception as e:
    print(f"Warning: Could not initialize Gemini client: {e}")
    client = None

app = FastAPI(title="AI Companion API")
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# request models
class ChatRequest(BaseModel):
    session_id: str
    message: str
    system_prompt: str | None = None
    model: str = "gemini-2.5-flash"

class SessionStartRequest(BaseModel):
    subject: str
    duration: int
    audio_type: str
    study_guide: Optional[dict] = None
    pomodoro_sessions: Optional[list] = None
    playlist_provider: Optional[str] = None

class MusicStartRequest(BaseModel):
    audio_type: str
    session_id: Optional[str] = None
    duration_minutes: Optional[int] = None

def sse(data: str) -> str:
    return f"data: {data}\n\n"

# gemini response
async def gemini_stream_text(
    model: str,
    contents: list[str],
    system_prompt: str | None = None, 
    ) -> AsyncGenerator[str, None]:
    """
    Streams partial text using google-genai SDK.
    Docs: client.models.generate_content_stream(...)
    """
    gen_cfg = None
    if system_prompt:
        gen_cfg = types.GenerateContentConfig(system_instruction=system_prompt) if system_prompt else None

    stream = client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=gen_cfg,
    )
    
    # Iterate SDK stream and yield text fragments
    for chunk in stream:
        if getattr(chunk, "text", None):
            yield chunk.text

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/echo")
def echo(data: dict):
    return {"received": data}

#client

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, authorization: str | None = Header(default=None)):
    # TODO: replace with JWT verification
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    async def event_generator():
        contents = [req.message]   # add conversation history or RAG later
        async for frag in gemini_stream_text(req.model, contents, req.system_prompt):
            yield sse(frag)
            await asyncio.sleep(0)  # cooperative yield
        yield sse("[DONE]")
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/session/start")
async def start_session(req: SessionStartRequest, db = Depends(db_session)):
    """Start a new study session and store session data"""
    try:
        # Create session in database
        session = SessionRepository.create(
            db=db,
            session_topic=req.subject,
            status=SessionStatus.ACTIVE
        )
        
        # Create plan if study guide is provided
        if req.study_guide:
            plan_text = f"Study plan for {req.subject}: {req.duration} minutes"
            if req.pomodoro_sessions:
                pomodoro_pattern = ", ".join([f"Session {s.get('id', i+1)}: {s.get('task', '')}" 
                                             for i, s in enumerate(req.pomodoro_sessions)])
            else:
                pomodoro_pattern = f"{req.duration} minute session"
            
            PlanRepository.create(
                db=db,
                session_id=session.session_id,
                pomodoro_pattern=pomodoro_pattern,
                qualitative_guide=str(req.study_guide)
            )
        
        db.commit()
        
        return {
            "session_id": str(session.session_id),
            "status": "active",
            "subject": req.subject,
            "duration": req.duration,
            "audio_type": req.audio_type
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")

@app.post("/api/music/start")
async def start_music(req: MusicStartRequest):
    """Start playing music based on audio type"""
    try:
        result = music_service.start_music(
            audio_type=req.audio_type,
            duration_minutes=req.duration_minutes
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start music: {str(e)}")

@app.post("/api/music/pause")
async def pause_music():
    """Pause currently playing music"""
    try:
        result = music_service.pause_music()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause music: {str(e)}")

@app.post("/api/music/resume")
async def resume_music():
    """Resume paused music"""
    try:
        result = music_service.resume_music()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume music: {str(e)}")

@app.post("/api/music/stop")
async def stop_music():
    """Stop currently playing music"""
    try:
        result = music_service.stop_music()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop music: {str(e)}")

@app.get("/api/music/status")
async def get_music_status():
    """Get current music playback status"""
    return music_service.get_status()

@app.post("/api/attention/start")
async def start_attention_detection():
    """Start attention detection"""
    try:
        success = attention_detector_service.start_detection()
        if success:
            return {"status": "success", "message": "Attention detection started"}
        else:
            raise HTTPException(status_code=500, detail="Failed to start attention detection")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start attention detection: {str(e)}")

@app.post("/api/attention/stop")
async def stop_attention_detection():
    """Stop attention detection"""
    try:
        attention_detector_service.stop_detection()
        return {"status": "success", "message": "Attention detection stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop attention detection: {str(e)}")

@app.get("/api/attention/status")
async def get_attention_status():
    """Get current attention detection status"""
    try:
        status = attention_detector_service.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get attention status: {str(e)}")
