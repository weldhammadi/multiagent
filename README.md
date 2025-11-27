# Multiagent Python Toolkit

A modular framework for generating, testing, and orchestrating Python agents using LLMs (Groq API) and GitHub search. This toolkit enables rapid prototyping of AI-powered tools, code generation, and automation agents.

---

## Table of Contents
- [Overview](#overview)
- [Agents & Modules](#agents--modules)
  - [ToolAgent](#toolagent)
  - [SpeechToTextAgent](#speechtotextagent)
  - [Orchestrator](#orchestrator)
  - [AgentModeles (LLMAgent)](#agentmodeles-llmagent)
  - [AgentTestExecuteur](#agenttestexecuteur)
- [Installation](#installation)
- [Usage Examples](#usage-examples)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)

---

## Overview
This repository provides a set of agents for:
- Generating Python tools and code using LLMs
- Searching for and cloning existing tools from GitHub
- Validating, testing, and assembling agent code
- Supporting speech-to-text, text-to-speech, and other AI tasks

The system is modular: each agent can be used independently or orchestrated together for complex workflows.

---

## Agents & Modules

### 1. ToolAgent (`tool_generator_agent.py`)
**Purpose:**
- Generate new Python tools from user prompts using LLMs
- Search GitHub for existing tools and optionally clone them
- Validate and save generated code, metadata, and config files

**Key Methods:**
- `__init__`: Setup output directory, GitHub, and LLM configs
- `search_repositories`: Search GitHub for repositories by keyword/language
- `clone_repository`: Clone a GitHub repo to a local path
- `call_llm`: Generate tool code/metadata using Groq API
- `save_tool`: Save generated code and metadata to files
- `generate_tool`: Main entry to generate a tool from a prompt
- `run`: Run the agent with a user prompt and context

**Usage Example:**
```python
from tool_generator_agent import ToolAgent
agent = ToolAgent()
result = agent.generate_tool("A tool to summarize CSV files")
print(result['source_code'])
```

---

### 2. SpeechToTextAgent (`speech_to_text_agent.py`)
**Purpose:**
- Convert audio files or bytes to text using Groq's Whisper model

**Key Methods:**
- `transcribe_audio`: Transcribe an audio file to text
- `transcribe_bytes`: Transcribe audio from bytes (for web apps)

**Usage Example:**
```python
from speech_to_text_agent import SpeechToTextAgent
agent = SpeechToTextAgent()
result = agent.transcribe_audio("audio.wav")
print(result['text'])
```

---

### 3. Orchestrator (`orchestrator_agent.py`)
**Purpose:**
- Coordinate ToolAgent and LLMAgent to create full-featured agents from user requests
- Plan, generate, and assemble code for complex agents

**Key Methods:**
- `plan_agent`: Use LLM to break down a user request into tools and LLM functions
- `generate_tools`: Generate code for each tool in the plan
- `generate_llm_functions`: Generate LLM-based functions
- `assemble_final_agent`: Assemble all code into a single agent file
- `run`: Main entry to generate an agent from a user request

**Usage Example:**
```python
from orchestrator_agent import Orchestrator
orchestrator = Orchestrator()
result = orchestrator.run("Create an agent that classifies emails")
print(result['final_path'])
```

---

### 4. AgentModeles (LLMAgent) (`model_generator_agent.py`)
**Purpose:**
- Generate Python functions for LLM, speech-to-text, text-to-speech, image, and video tasks

**Key Methods:**
- `generate_model_function`: Generate a Python function for a given AI task
- `call_llm`: Call the LLM to generate code
- `parse_llm_output`: Parse LLM output into code and metadata

**Usage Example:**
```python
from model_generator_agent import AgentModeles
llm_agent = AgentModeles()
result = llm_agent.generate_model_function(
    description="Summarize a text",
    inputs={"text": "str"},
    outputs={"summary": "str"},
    model_type="llm"
)
print(result['source_code'])
```

---

### 5. AgentTestExecuteur (`execute_test_agent.py`)
**Purpose:**
- Test Python code for syntax and runtime errors
- Install missing imports and report errors in JSON

**Key Methods:**
- `tester_code`: Test code for syntax and execution errors
- `tester_fichier`: Test a Python file
- `sauvegarder_resultat`: Save test results to JSON

**Usage Example:**
```python
from execute_test_agent import AgentTestExecuteur
agent = AgentTestExecuteur()
result = agent.tester_code("print('Hello')")
print(result)
```

---

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/weldhammadi/multiagent.git
   cd multiagent
   ```
2. Install dependencies:
   ```sh
   pip install -r hamza/requirements.txt
   ```
3. Set up your `.env` file with your Groq API key and (optionally) GitHub token:
   ```env
   GROQ_API_KEY=your_groq_api_key
   GITHUB_TOKEN=your_github_token
   ```

---

## Usage Examples
- See the `if __name__ == "__main__"` blocks in each agent file for runnable examples.
- Use the Orchestrator for end-to-end agent generation from a single prompt.

---

## Environment Variables
- `GROQ_API_KEY`: Required for all LLM and AI tasks
- `GITHUB_TOKEN`: Optional, for authenticated GitHub API access

---

## Contributing
Pull requests and issues are welcome! Please document new agents and functions clearly.

---

## License
See `LICENSE` file for details.
