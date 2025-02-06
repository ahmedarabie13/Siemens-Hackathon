import os
import json
import re
from datetime import datetime
from pathlib import Path

from crewai import Agent, Task, Crew, LLM, Process
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from pydantic import BaseModel, Field

def clean_json_output(raw_output: str) -> str:
    """
    Ensures Mistral's output is a clean, valid JSON string.
    """
    cleaned = raw_output.strip()

    # Remove markdown code blocks if present
    cleaned = re.sub(r"```json|```", "", cleaned, flags=re.MULTILINE).strip()

    # Check if output is valid JSON
    try:
        json.loads(cleaned)  # Validate JSON
        return cleaned
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parsing Error: {e}")
        return '{"error": "Invalid JSON format"}'


def parse_flow_json(raw_result) -> dict:
    """
    Parses Mistral's output into JSON. If invalid, wraps it in a dictionary.
    """
    cleaned = clean_json_output(str(raw_result))
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON", "raw_output": cleaned}