# 读取 configs/app.yaml
# 读取 .env 里的 OPENAI_API_KEY
# 合并成一个 config 对象
import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config(config_path: str = "configs/app.yaml") -> Dict[str, Any]:
    """
    Load application config from YAML and environment variables.
    """
    load_dotenv(PROJECT_ROOT / ".env")

    full_path = PROJECT_ROOT / config_path

    if not full_path.exists():
        raise FileNotFoundError(f"Config file not found: {full_path}")

    with open(full_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set. Please add it to your .env file.")

    config["openai_api_key"] = openai_api_key

    return config