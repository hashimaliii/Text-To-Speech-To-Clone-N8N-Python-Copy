import os, tempfile, io
from gtts import gTTS
from TTS.api import TTS
from PyPDF2 import PdfReader
from pydub import AudioSegment

def pdf_to_text(pdf_file, page_range=None):
    reader = PdfReader(pdf_file)
    total_pages = len(reader.pages)

    if page_range:
        start, end = page_range
        start = max(1, min(start, total_pages)) - 1
        end = max(start + 1, min(end, total_pages))
        pages = reader.pages[start:end]
    else:
        pages = reader.pages

    text = ""
    for page in pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text, total_pages

def text_to_speech_google(text, lang="en", slow=False):
    tts = gTTS(text=text, lang=lang, slow=slow)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tts.save(tmp.name)
        with open(tmp.name, "rb") as f:
            audio_bytes = f.read()
    return audio_bytes, "mp3"

def text_to_speech_clone(text, speaker_wav_path, lang="en"):
    model = TTS("tts_models/multilingual/multi-dataset/your_tts")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        model.tts_to_file(text=text, speaker_wav=speaker_wav_path, language=lang, file_path=tmp.name)
        with open(tmp.name, "rb") as f:
            audio_bytes = f.read()
    return audio_bytes, "wav"
