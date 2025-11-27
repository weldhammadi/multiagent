"""
🤖 Agent Generator - Streamlit Interface

A beautiful and intuitive interface for generating AI agents using the Orchestrator.
Features:
- Text input or voice input (speech-to-text)
- Real-time status updates during generation
- Code preview with syntax highlighting
- Download generated files
"""

import os
import sys
import io
import zipfile
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import threading
import queue

import streamlit as st
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


from orchestrator_agent import Orchestrator
from speech_to_text_agent import SpeechToTextAgent
from github_push import push_project

# Load environment variables
load_dotenv()

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="🤖 Agent Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding: 1rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    /* Status card styling */
    .status-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
        margin: 0.5rem 0;
    }
    
    .status-card.success {
        border-left-color: #28a745;
        background: #d4edda;
    }
    
    .status-card.error {
        border-left-color: #dc3545;
        background: #f8d7da;
    }
    
    .status-card.warning {
        border-left-color: #ffc107;
        background: #fff3cd;
    }
    
    .status-card.info {
        border-left-color: #17a2b8;
        background: #d1ecf1;
    }
    
    /* Code container */
    .code-container {
        background: #1e1e1e;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Input styling */
    .stTextArea > div > div > textarea {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        transition: border-color 0.3s ease;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        padding: 2rem 1rem;
    }
    
    /* File info cards */
    .file-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Log container */
    .log-container {
        background: #1a1a2e;
        color: #00ff88;
        font-family: 'Courier New', monospace;
        padding: 1rem;
        border-radius: 10px;
        max-height: 400px;
        overflow-y: auto;
        font-size: 0.85rem;
        line-height: 1.6;
    }
    
    /* Voice button */
    .voice-btn {
        background: linear-gradient(135deg, #ff6b6b 0%, #ff8e53 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 50px;
        font-size: 1.1rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Metrics cards */
    .metric-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .metric-label {
        color: #666;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "logs": [],
        "generation_status": "idle",  # idle, running, completed, error
        "generated_result": None,
        "generated_code": None,
        "generated_files": {},
        "transcribed_text": "",
        "input_mode": "text",  # text or voice
        "orchestrator": None,
        "stt_agent": None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def add_log(message: str, level: str = "info"):
    """Add a log message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "progress": "🔄",
        "tool": "🔧",
        "llm": "🤖",
        "plan": "📋",
        "code": "💻",
        "file": "📁"
    }
    icon = icons.get(level, "•")
    st.session_state.logs.append(f"[{timestamp}] {icon} {message}")


def clear_logs():
    """Clear all logs."""
    st.session_state.logs = []


def get_orchestrator() -> Orchestrator:
    """Get or create the Orchestrator instance."""
    if st.session_state.orchestrator is None:
        output_dir = Path(__file__).parent / "output"
        st.session_state.orchestrator = Orchestrator(
            output_dir=str(output_dir),
            enable_github_search=False
        )
    return st.session_state.orchestrator


def get_stt_agent() -> Optional[SpeechToTextAgent]:
    """Get or create the Speech-to-Text agent."""
    if st.session_state.stt_agent is None:
        try:
            st.session_state.stt_agent = SpeechToTextAgent()
        except Exception as e:
            st.error(f"Failed to initialize Speech-to-Text: {e}")
            return None
    return st.session_state.stt_agent


def create_zip_download(files_dict: Dict[str, str]) -> bytes:
    """Create a ZIP file from a dictionary of files."""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in files_dict.items():
            zip_file.writestr(filename, content)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def run_generation_with_callback(user_request: str, agent_name: str, status_container, log_container):
    """
    Run the agent generation process with real-time progress updates.
    
    This function captures all progress messages from the orchestrator and
    displays them in real-time using Streamlit containers.
    """
    try:
        st.session_state.generation_status = "running"
        clear_logs()
        
        # Create progress callback that updates Streamlit in real-time
        def progress_callback(message: str, level: str):
            """Callback to receive progress updates from orchestrator."""
            add_log(message, level)
            # Update the log display in real-time
            with log_container:
                log_text = "<br>".join(st.session_state.logs[-50:])  # Show last 50 logs
                st.markdown(
                    f'<div class="log-container">{log_text}</div>',
                    unsafe_allow_html=True
                )
        
        # Update status
        with status_container:
            st.markdown("### 🟡 Generation in progress...")
            st.progress(0.1, text="Starting...")
        
        add_log(f"🚀 Starting agent generation: {agent_name}", "progress")
        add_log(f"📝 User request: {user_request[:100]}...", "info")
        
        orchestrator = get_orchestrator()
        orchestrator.reset()
        
        # Set the progress callback to capture all messages
        orchestrator.set_progress_callback(progress_callback)
        
        with status_container:
            st.progress(0.2, text="Planning...")
        
        # Run the full orchestrator workflow
        result = orchestrator.run(user_request, agent_name)
        
        with status_container:
            st.progress(0.9, text="Collecting files...")
        
        # Read generated files
        files_dict = {}
        final_path = Path(result["final_path"])
        config_result = result.get("config_files", {})
        
        # Main agent file
        if final_path.exists():
            files_dict[final_path.name] = final_path.read_text(encoding="utf-8")
            st.session_state.generated_code = files_dict[final_path.name]
        
        # Env file
        env_file = config_result.get("env_file")
        if env_file and Path(env_file).exists():
            env_path = Path(env_file)
            files_dict[env_path.name] = env_path.read_text(encoding="utf-8")
        
        # Credentials file
        creds_file = config_result.get("credentials_file")
        if creds_file and Path(creds_file).exists():
            creds_path = Path(creds_file)
            files_dict[creds_path.name] = creds_path.read_text(encoding="utf-8")
        
        # Config files
        for name, path in config_result.get("config_files", {}).items():
            if path and Path(path).exists():
                p = Path(path)
                files_dict[p.name] = p.read_text(encoding="utf-8")
        
        st.session_state.generated_files = files_dict
        st.session_state.generated_result = {
            "plan": result.get("plan", {}),
            "tools": orchestrator.generated_tools,
            "llm_functions": orchestrator.generated_llm_functions,
            "final_path": str(final_path),
            "config_files": config_result
        }

        # Automatically push output folder to GitHub after generation
        add_log("🔄 Pushing output folder to GitHub...", "progress")
        push_success = push_project(f"Auto-push after agent generation: {agent_name}")
        if push_success:
            add_log("✅ Output folder pushed to GitHub.", "success")
        else:
            add_log("❌ Failed to push output folder to GitHub.", "error")

        with status_container:
            st.progress(1.0, text="Complete!")

        add_log("=" * 40, "info")
        add_log("🎉 Agent generation completed successfully!", "success")
        add_log("=" * 40, "info")
        st.session_state.generation_status = "completed"
        
    except Exception as e:
        add_log(f"❌ Error during generation: {str(e)}", "error")
        st.session_state.generation_status = "error"
        with status_container:
            st.error(f"Generation failed: {e}")
        raise e


def run_generation(user_request: str, agent_name: str):
    """Legacy wrapper for backward compatibility."""
    # This is now handled by run_generation_with_callback in the main app
    pass


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Agent Generator</h1>
        <p>Create powerful AI agents with natural language - Type or Speak your ideas</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with settings and info."""
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # Agent name input
        agent_name = st.text_input(
            "Agent Name",
            value="my_agent",
            help="Name for the generated agent files"
        )
        
        st.markdown("---")
        
        # API Key status
        st.markdown("## 🔑 API Status")
        
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            st.success("✅ GROQ_API_KEY configured")
        else:
            st.error("❌ GROQ_API_KEY not set")
            st.info("Add GROQ_API_KEY to your .env file")
        
        st.markdown("---")
        
        # Quick examples
        st.markdown("## 💡 Examples")
        
        examples = [
            ("📧 Email Classifier", "An agent that reads emails and classifies them into categories like work, personal, spam, and important."),
            ("📖 Story Generator", "An agent that creates children's stories and converts them to audio using text-to-speech."),
            ("🌤️ Weather Bot", "An agent that fetches weather data and provides natural language summaries."),
            ("📊 Data Analyzer", "An agent that analyzes CSV files and generates insights using AI."),
        ]
        
        for title, desc in examples:
            if st.button(title, key=f"example_{title}"):
                st.session_state.transcribed_text = desc
                st.rerun()
        
        st.markdown("---")
        
        # Stats
        if st.session_state.generated_result:
            st.markdown("## 📊 Last Generation")
            result = st.session_state.generated_result
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tools", len(result.get("tools", [])))
            with col2:
                st.metric("LLM Functions", len(result.get("llm_functions", [])))
        
        return agent_name


def render_input_section():
    """Render the input section with text and voice options."""
    st.markdown("## 📝 Describe Your Agent")
    
    # Input mode tabs
    tab_text, tab_voice = st.tabs(["⌨️ Type", "🎤 Speak"])
    
    with tab_text:
        user_input = st.text_area(
            "What should your agent do?",
            value=st.session_state.transcribed_text,
            height=150,
            placeholder="Example: I want an agent that reads my emails, classifies them by importance, and sends me a daily summary...",
            key="text_input"
        )
        
        if user_input != st.session_state.transcribed_text:
            st.session_state.transcribed_text = user_input
    
    with tab_voice:
        st.markdown("### 🎤 Voice Input")
        st.info("Upload an audio file or record your voice to describe your agent.")
        
        # Audio file upload
        audio_file = st.file_uploader(
            "Upload audio file",
            type=["wav", "mp3", "m4a", "ogg", "webm"],
            help="Supported formats: WAV, MP3, M4A, OGG, WebM"
        )
        
        if audio_file is not None:
            st.audio(audio_file, format=f"audio/{audio_file.name.split('.')[-1]}")
            
            if st.button("🔊 Transcribe Audio", type="primary"):
                with st.spinner("Transcribing audio..."):
                    try:
                        stt_agent = get_stt_agent()
                        if stt_agent:
                            audio_bytes = audio_file.read()
                            result = stt_agent.transcribe_bytes(
                                audio_bytes,
                                filename=audio_file.name
                            )
                            st.session_state.transcribed_text = result["text"]
                            st.success("✅ Transcription complete!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Transcription failed: {e}")
        
        # Show transcribed text
        if st.session_state.transcribed_text:
            st.markdown("### 📄 Transcribed Text")
            st.text_area(
                "Edit if needed:",
                value=st.session_state.transcribed_text,
                height=100,
                key="transcribed_display"
            )
    
    return st.session_state.transcribed_text


def render_status_panel():
    """Render the real-time status panel with live updates."""
    st.markdown("## 📡 Generation Status")
    
    # Status container for progress bar - will be updated during generation
    status_container = st.empty()
    
    # Render current status
    with status_container.container():
        status = st.session_state.generation_status
        status_displays = {
            "idle": ("⚪", "Ready to generate", None),
            "running": ("🟡", "Generation in progress...", 0.5),
            "completed": ("🟢", "Generation completed!", 1.0),
            "error": ("🔴", "Generation failed", None)
        }
        
        icon, text, progress_val = status_displays.get(status, ("⚪", "Unknown", None))
        st.markdown(f"### {icon} {text}")
        
        if progress_val is not None:
            st.progress(progress_val)
    
    # Log display container
    st.markdown("### 📋 Activity Log")
    log_container = st.empty()
    
    with log_container.container():
        if st.session_state.logs:
            # Format logs with HTML for better display
            log_text = "<br>".join(st.session_state.logs[-50:])  # Show last 50 logs
            st.markdown(
                f'<div class="log-container">{log_text}</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("📝 Logs will appear here during generation...")
    
    return status_container, log_container


def render_code_preview():
    """Render the generated code preview."""
    st.markdown("## 💻 Generated Code")
    
    if st.session_state.generated_code:
        # Code stats
        code = st.session_state.generated_code
        lines = code.count('\n') + 1
        chars = len(code)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Lines of Code", f"{lines:,}")
        with col2:
            st.metric("Characters", f"{chars:,}")
        with col3:
            functions = code.count("def ")
            st.metric("Functions", functions)
        
        # Code display with syntax highlighting
        with st.expander("📄 View Full Code", expanded=True):
            st.code(code, language="python", line_numbers=True)
    else:
        st.info("Generated code will appear here after generation...")


def render_download_section():
    """Render the download section for generated files."""
    st.markdown("## 📥 Download Files")
    
    if st.session_state.generated_files:
        files = st.session_state.generated_files
        
        # Individual file downloads
        st.markdown("### Individual Files")
        
        for filename, content in files.items():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # File icon based on extension
                ext = Path(filename).suffix
                icons = {".py": "🐍", ".env": "🔐", ".json": "📋"}
                icon = icons.get(ext, "📄")
                st.markdown(f"{icon} **{filename}**")
            
            with col2:
                size = len(content)
                if size < 1024:
                    st.caption(f"{size} B")
                else:
                    st.caption(f"{size/1024:.1f} KB")
            
            with col3:
                st.download_button(
                    label="⬇️",
                    data=content,
                    file_name=filename,
                    mime="text/plain",
                    key=f"download_{filename}"
                )
        
        st.markdown("---")
        
        # Download all as ZIP
        st.markdown("### 📦 Download All")
        
        zip_data = create_zip_download(files)
        result = st.session_state.generated_result
        agent_name = Path(result.get("final_path", "agent")).stem if result else "agent"
        
        st.download_button(
            label="📦 Download All Files (ZIP)",
            data=zip_data,
            file_name=f"{agent_name}_files.zip",
            mime="application/zip",
            type="primary"
        )
    else:
        st.info("Generated files will be available for download after generation...")


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    """Main application entry point."""
    render_header()
    
    # Sidebar
    agent_name = render_sidebar()
    
    # Main content
    col_left, col_right = st.columns([1.2, 1])
    
    with col_left:
        # Input section
        user_request = render_input_section()
        
        st.markdown("---")
        
        # Generate button
        col_btn1, col_btn2 = st.columns(2)
        
        generate_clicked = False
        with col_btn1:
            generate_disabled = (
                not user_request or 
                st.session_state.generation_status == "running"
            )
            
            generate_clicked = st.button(
                "🚀 Generate Agent",
                type="primary",
                disabled=generate_disabled,
                use_container_width=True
            )
        
        with col_btn2:
            if st.button(
                "🔄 Reset",
                use_container_width=True
            ):
                st.session_state.generation_status = "idle"
                st.session_state.generated_result = None
                st.session_state.generated_code = None
                st.session_state.generated_files = {}
                st.session_state.transcribed_text = ""
                clear_logs()
                if st.session_state.orchestrator:
                    st.session_state.orchestrator.reset()
                st.rerun()
        
        st.markdown("---")
        
        # Status panel - returns containers for live updates
        status_container, log_container = render_status_panel()
        
        # Run generation if button was clicked
        if generate_clicked:
            run_generation_with_callback(user_request, agent_name, status_container, log_container)
            st.rerun()
    
    with col_right:
        # Code preview
        render_code_preview()
        
        st.markdown("---")
        
        # Download section
        render_download_section()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #666; padding: 1rem;">
            <p>🤖 Agent Generator | Built with Streamlit & Groq API</p>
            <p style="font-size: 0.8rem;">Create powerful AI agents with natural language</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
