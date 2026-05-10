import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config(config_path: str = "configs/app.yaml") -> Dict[str, Any]:
    """
    Load application config from YAML file and .env file.

    Notes:
    - Phase 1 used OPENAI_API_KEY.
    - Phase 3 supports OpenAI-compatible providers such as Alibaba Cloud Bailian.
    - Use LLM_API_KEY for the LLM generator.
    """
    load_dotenv(PROJECT_ROOT / ".env")

    full_path = PROJECT_ROOT / config_path

    if not full_path.exists():
        raise FileNotFoundError(f"Config file not found: {full_path}")

    with open(full_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    llm_config = config.get("llm", {})
    generator_config = config.get("generator", {})

    llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    llm_base_url = os.getenv("LLM_BASE_URL") or llm_config.get("base_url")

    if "llm" not in config:
        config["llm"] = {}

    config["llm"]["api_key"] = llm_api_key
    config["llm"]["base_url"] = llm_base_url

    if generator_config.get("type") == "llm" and not llm_api_key:
        raise ValueError(
            "LLM_API_KEY is not set. Please add it to your .env file, "
            "or set generator.type to extractive in configs/app.yaml."
        )

    return config