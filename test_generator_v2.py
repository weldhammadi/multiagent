from advanced_generator import AgentModeles
import dotenv
# Load environment variables from .env file
dotenv.load_dotenv()
# Initialize agent
agent = AgentModeles()

# Example 1: Generate Speech-to-Text function
result = agent.generate_model_function(
    description="Transcribe French podcast audio to text with timestamps",
    inputs={
        "audio_path": "str (path to audio file)",
        "include_timestamps": "bool"
    },
    outputs={
        "transcription": "str",
        "language": "str",
        "segments": "list[dict]"
    },
    model_type="speech_to_text",
    constraints="Must handle files up to 25MB, support mp3 and wav formats"
)

print(result["context"])  # Long professional context
print(result["source_code"])  # Generated function code
print(result["prompt"])  # Complete prompt used

# Example 2: Generate Text-to-Speech function
result2 = agent.generate_model_function(
    description="Convert marketing copy to natural French speech",
    inputs={
        "text": "str",
        "voice_style": "str (casual/professional)"
    },
    outputs={
        "audio_data": "bytes",
        "duration_seconds": "float"
    },
    model_type="text_to_speech"
)

# See all available models
print(agent.get_available_models())