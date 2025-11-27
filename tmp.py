import os
import json
import requests
import logging
import sys
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import pandas as pd
from groq import Groq

# Ensure stdout can handle UTF-8 (useful on Windows)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load environment variables
load_dotenv()

# --------------------------------------------------------------------------- #
# Configuration constants
# --------------------------------------------------------------------------- #
MODEL_NAME: str = "openai/gpt-oss-120b"
TEMPERATURE: float = 0.4
MAX_TOKENS: int = 1024

# Configure a module‑level logger (no secret data is logged)
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def read_csv(file_path: str) -> pd.DataFrame:
    """Loads a CSV file from the given file path and returns its contents as a DataFrame.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        pandas.DataFrame: DataFrame containing the CSV data.

    Raises:
        RuntimeError: If the file does not exist or cannot be read as CSV.
    """
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        raise RuntimeError(
            f"Le fichier CSV spécifié est introuvable: {file_path}"
        )
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la lecture du fichier CSV: {e}")
    return df


def analyze_tabular_data(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyse the provided tabular data and produce a concise textual summary of
    key insights, trends, and observations using the Groq LLM endpoint.

    The function validates the input, serialises the DataFrame to CSV (without
    the index), sends it to the ``openai/gpt-oss-120b`` model and returns the
    model's textual summary.

    Args:
        data (pd.DataFrame): A non‑empty pandas DataFrame containing the data
            to be analysed.

    Returns:
        Dict[str, Any]: A dictionary with a single key ``insights`` whose value
        is the generated summary string.

    Raises:
        ValueError: If ``data`` is not a pandas DataFrame or is empty.
        RuntimeError: If the GROQ_API_KEY is missing or the API request fails.
    """
    # ------------------------------------------------------------------- #
    # Step 1 – Input validation
    # ------------------------------------------------------------------- #
    if not isinstance(data, pd.DataFrame):
        raise ValueError("`data` must be a pandas DataFrame.")
    if data.empty:
        raise ValueError("`data` DataFrame must contain at least one row.")

    # ------------------------------------------------------------------- #
    # Step 2 – Retrieve API key from environment
    # ------------------------------------------------------------------- #
    api_key: Optional[str] = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Environment variable GROQ_API_KEY is not set. "
            "Please configure it before calling this function."
        )

    # ------------------------------------------------------------------- #
    # Step 3 – Initialise Groq client
    # ------------------------------------------------------------------- #
    try:
        groq_client = Groq(api_key=api_key)
    except Exception as exc:
        logger.exception("Failed to initialise Groq client.")
        raise RuntimeError("Could not create Groq client.") from exc

    # ------------------------------------------------------------------- #
    # Step 4 – Build prompt (with data truncation to avoid token limits)
    # ------------------------------------------------------------------- #
    system_message = (
        "You are an expert data analyst. Summarise the key insights, trends, "
        "and observations from the tabular data provided by the user. "
        "Focus on notable patterns, outliers, and any actionable information."
    )
    
    # Build a compact representation to avoid exceeding token limits
    MAX_SAMPLE_ROWS = 50  # Limit sample rows sent to the API
    MAX_CHARS = 8000      # Max characters for the data payload
    
    try:
        # Include basic info about the dataset
        data_info = []
        data_info.append(f"Dataset shape: {data.shape[0]} rows x {data.shape[1]} columns")
        data_info.append(f"Columns: {', '.join(data.columns.tolist())}")
        
        # Add summary statistics for numeric columns
        numeric_cols = data.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            stats_df = data[numeric_cols].describe()
            data_info.append(f"\nNumeric columns statistics:\n{stats_df.to_string()}")
        
        # Add value counts for categorical columns (limited)
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols[:5]:  # Limit to first 5 categorical columns
            value_counts = data[col].value_counts().head(5)
            data_info.append(f"\nTop values for '{col}':\n{value_counts.to_string()}")
        
        # Add a sample of the data
        sample_df = data.head(MAX_SAMPLE_ROWS)
        csv_sample: str = sample_df.to_csv(index=False)
        
        # Combine all info
        data_summary = "\n".join(data_info)
        csv_payload = f"{data_summary}\n\nSample data (first {len(sample_df)} rows):\n{csv_sample}"
        
        # Truncate if still too long
        if len(csv_payload) > MAX_CHARS:
            csv_payload = csv_payload[:MAX_CHARS] + "\n... [truncated due to size]"
            
    except Exception as exc:
        logger.exception("Failed to serialise DataFrame to CSV.")
        raise RuntimeError("Could not convert DataFrame to CSV.") from exc

    user_message = f"Tabular data analysis:\n{csv_payload}"

    # ------------------------------------------------------------------- #
    # Step 5 – Call Groq API
    # ------------------------------------------------------------------- #
    try:
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        summary = response.choices[0].message.content.strip()
    except Exception as exc:
        logger.exception("Groq API request failed.")
        raise RuntimeError("Failed to obtain insights from Groq API.") from exc

    return {"insights": summary}


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("Running my_agent...")
    # Example usage (uncomment and adapt the path as needed):
    df = read_csv("D:\\school\\HETIC\\PYTHON\\github_multiagent\\testdata.csv")
    result = analyze_tabular_data(df)
    print(result["insights"])
    pass