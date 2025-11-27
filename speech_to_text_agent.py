"""
Speech-to-Text Agent using Groq Whisper API.

This module provides speech-to-text capabilities for the Streamlit interface.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


class SpeechToTextAgent:
    """
    Agent for converting speech audio to text using Groq's Whisper model.
    
    Supports various audio formats: mp3, mp4, mpeg, mpga, m4a, wav, webm
    """
    
    SUPPORTED_FORMATS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm", ".ogg"}
    MODEL = "whisper-large-v3"
    
    def __init__(self):
        """Initialize the Speech-to-Text agent with Groq client."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        self.client = Groq(api_key=api_key)
    
    def transcribe_audio(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file_path: Path to the audio file
            language: Optional language code (e.g., 'en', 'fr')
            prompt: Optional prompt to guide transcription
            
        Returns:
            Dict with 'text' (transcription) and 'metadata'
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If audio format is not supported
            RuntimeError: If transcription fails
        """
        audio_path = Path(audio_file_path)
        
        # Validate file exists
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        # Validate format
        if audio_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported audio format: {audio_path.suffix}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        try:
            with open(audio_path, "rb") as audio_file:
                # Build transcription parameters
                params = {
                    "file": (audio_path.name, audio_file),
                    "model": self.MODEL,
                    "response_format": "verbose_json"
                }
                
                if language:
                    params["language"] = language
                if prompt:
                    params["prompt"] = prompt
                
                # Call Groq Whisper API
                transcription = self.client.audio.transcriptions.create(**params)
                
                return {
                    "text": transcription.text,
                    "metadata": {
                        "model": self.MODEL,
                        "language": getattr(transcription, "language", language),
                        "duration": getattr(transcription, "duration", None),
                        "file": audio_path.name
                    }
                }
                
        except Exception as exc:
            raise RuntimeError(f"Transcription failed: {exc}") from exc
    
    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio from bytes (useful for Streamlit audio recorder).
        
        Args:
            audio_bytes: Raw audio bytes
            filename: Filename with extension to determine format
            language: Optional language code
            prompt: Optional prompt to guide transcription
            
        Returns:
            Dict with 'text' and 'metadata'
        """
        # Get file extension
        suffix = Path(filename).suffix.lower()
        if not suffix:
            suffix = ".wav"  # Default to wav
        
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported audio format: {suffix}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        try:
            result = self.transcribe_audio(tmp_path, language, prompt)
            return result
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    agent = SpeechToTextAgent()
    print("✅ SpeechToTextAgent initialized successfully")
    print(f"   Model: {agent.MODEL}")
    print(f"   Supported formats: {', '.join(agent.SUPPORTED_FORMATS)}")
