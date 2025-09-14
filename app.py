from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import JSONResponse, StreamingResponse
import tempfile, os, io, shutil
from utils import text_to_speech_google, text_to_speech_clone, pdf_to_text

app = FastAPI(title="Voice API")

# Temporary directories for voices and PDFs
VOICE_TEMP_DIR = tempfile.mkdtemp(prefix="uploaded_voices_")
PDF_TEMP_DIR = tempfile.mkdtemp(prefix="uploaded_pdfs_")

@app.on_event("startup")
async def startup_event():
    os.makedirs(VOICE_TEMP_DIR, exist_ok=True)
    os.makedirs(PDF_TEMP_DIR, exist_ok=True)

@app.on_event("shutdown")
async def shutdown_event():
    # Delete all temporary voices and PDFs on server shutdown
    if os.path.exists(VOICE_TEMP_DIR):
        shutil.rmtree(VOICE_TEMP_DIR)
    if os.path.exists(PDF_TEMP_DIR):
        shutil.rmtree(PDF_TEMP_DIR)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Upload a voice sample temporarily
@app.post("/upload-voice")
async def upload_voice(file: UploadFile):
    try:
        ext = os.path.splitext(file.filename)[1] or ".wav"
        save_path = os.path.join(VOICE_TEMP_DIR, file.filename)
        with open(save_path, "wb") as f:
            f.write(await file.read())
        return {"message": "Voice uploaded successfully", "name": file.filename}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Upload PDF temporarily
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile):
    try:
        save_path = os.path.join(PDF_TEMP_DIR, file.filename)
        with open(save_path, "wb") as f:
            f.write(await file.read())
        return {"message": "PDF uploaded successfully", "name": file.filename}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# List all uploaded voices
@app.get("/voices")
async def list_voices():
    voices = [f for f in os.listdir(VOICE_TEMP_DIR) if os.path.isfile(os.path.join(VOICE_TEMP_DIR, f))]
    return {"voices": voices}

# List all uploaded PDFs
@app.get("/pdfs")
async def list_pdfs():
    pdfs = [f for f in os.listdir(PDF_TEMP_DIR) if os.path.isfile(os.path.join(PDF_TEMP_DIR, f))]
    return {"pdfs": pdfs}

@app.post("/tts")
async def tts_endpoint(text: str = Form(...), lang: str = Form("en"), slow: bool = Form(False)):
    try:
        audio_bytes, fmt = text_to_speech_google(text, lang=lang, slow=slow)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type=f"audio/{fmt}")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/clone-voice")
async def clone_endpoint(
    text: str = Form(...),
    voice_name: str = Form(...),  # Name of previously uploaded voice
    lang: str = Form("en")
):
    try:
        # Construct path to the temporary voice file
        voice_path = os.path.join(VOICE_TEMP_DIR, voice_name)

        # Check if the voice exists
        if not os.path.isfile(voice_path):
            return JSONResponse(
                status_code=400,
                content={"error": f"Voice '{voice_name}' not found."}
            )

        # Generate cloned audio
        audio_bytes, fmt = text_to_speech_clone(text, speaker_wav_path=voice_path, lang=lang)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type=f"audio/{fmt}")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/pdf-tts")
async def pdf_to_tts(
    pdf_name: str = Form(...),  # Name of previously uploaded PDF
    lang: str = Form("en"),
    slow: bool = Form(False),
    start_page: int = Form(1),
    end_page: int = Form(-1)
):
    try:
        pdf_path = os.path.join(PDF_TEMP_DIR, pdf_name)

        # Check if PDF exists
        if not os.path.isfile(pdf_path):
            return JSONResponse(
                status_code=400,
                content={"error": f"PDF '{pdf_name}' not found."}
            )

        # Extract text from PDF
        with open(pdf_path, "rb") as f:
            text, total_pages = pdf_to_text(f, (start_page, end_page) if end_page != -1 else None)

        if not text.strip():
            raise Exception("No text could be extracted from the PDF")

        # Convert text to speech
        audio_bytes, fmt = text_to_speech_google(text, lang=lang, slow=slow)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type=f"audio/{fmt}")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Convert PDF to speech using a cloned voice from uploaded files
@app.post("/pdf-clone-voice")
async def pdf_clone_voice(
    pdf_name: str = Form(...),     # Name of previously uploaded PDF
    voice_name: str = Form(...),   # Name of previously uploaded voice
    lang: str = Form("en"),
    start_page: int = Form(1),
    end_page: int = Form(-1)
):
    try:
        pdf_path = os.path.join(PDF_TEMP_DIR, pdf_name)
        voice_path = os.path.join(VOICE_TEMP_DIR, voice_name)

        if not os.path.isfile(pdf_path):
            return JSONResponse(status_code=400, content={"error": f"PDF '{pdf_name}' not found."})
        if not os.path.isfile(voice_path):
            return JSONResponse(status_code=400, content={"error": f"Voice '{voice_name}' not found."})

        # Extract text from PDF
        with open(pdf_path, "rb") as f:
            text, total_pages = pdf_to_text(f, (start_page, end_page) if end_page != -1 else None)

        if not text.strip():
            raise Exception("No text could be extracted from the PDF")

        # Generate cloned audio
        audio_bytes, fmt = text_to_speech_clone(text, speaker_wav_path=voice_path, lang=lang)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type=f"audio/{fmt}")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Keep other endpoints like /tts, /clone-voice unchanged
