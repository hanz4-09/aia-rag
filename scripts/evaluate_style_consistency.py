"""
Style Consistency Evaluation Script (LLM-as-Judge)

Evaluates whether the generated answers maintain consistent style across questions.
Style Consistency covers three dimensions:
1. Language Consistency: Answers match the language of the question (CN→CN, EN→EN)
2. Format Consistency: Answers follow a consistent structure (no random formatting)
3. Tone Professionalism: Answers maintain a professional, concise tone

Each dimension is scored 0-1, and the overall Style Consistency is the average.

PRD Target: Style Consistency >= 0.85
"""

import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.config import load_config
from app.rag.generator import create_generator
from app.rag.pii import redact_pii
from app.rag.retriever_factory import create_retriever
from app.rag.safety import check_safety

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


EVAL_SET_PATH = PROJECT_ROOT / "eval" / "answer_eval_set.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "evaluations"


def load_eval_set(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Answer evaluation set not found: {path}")
    records = []
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def detect_language(text: str) -> str:
    """Detect if text is primarily Chinese or English."""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    total_chars = sum(1 for c in text if c.isalpha())
    if total_chars == 0:
        return "unknown"
    ratio = chinese_chars / total_chars
    return "cn" if ratio > 0.3 else "en"


def evaluate_style_consistency_single(
    question: str,
    answer: str,
    judge_llm: ChatOpenAI,
) -> Dict[str, Any]:
    """
    Use LLM-as-judge to evaluate style consistency.

    Evaluates three dimensions:
    1. Language Consistency: Does the answer language match the question language?
    2. Format Consistency: Is the answer well-structured and consistent?
    3. Tone Professionalism: Is the tone professional and appropriate for an internal KB assistant?
    """
    question_lang = detect_language(question)

    judge_system_prompt = (
        "You are an expert evaluator for RAG (Retrieval-Augmented Generation) systems.\n"
        "Your task is to evaluate the style consistency of a generated answer.\n\n"
        "Evaluate the following three dimensions, each scored from 0 to 1:\n\n"
        "1. language_consistency: Does the answer use the same language as the question?\n"
        "   - 1.0: Perfect language match (Chinese question → Chinese answer, English → English)\n"
        "   - 0.5: Mixed languages but the primary language matches\n"
        "   - 0.0: Wrong language entirely\n\n"
        "2. format_consistency: Is the answer well-structured and appropriate?\n"
        "   - 1.0: Clear structure (bullet points, numbered lists, or well-organized paragraphs)\n"
        "   - 0.5: Somewhat organized but inconsistent formatting\n"
        "   - 0.0: Disorganized, messy, or unreadable formatting\n\n"
        "3. tone_professionalism: Is the tone professional and appropriate for an internal knowledge base?\n"
        "   - 1.0: Professional, concise, objective, grounded in context\n"
        "   - 0.5: Mostly professional but with minor issues (slightly verbose or informal)\n"
        "   - 0.0: Unprofessional, overly casual, emotional, or includes opinions\n\n"
        "Respond ONLY with a JSON object in this exact format:\n"
        '{"language_consistency": 0.0-1.0, "format_consistency": 0.0-1.0, '
        '"tone_professionalism": 0.0-1.0, "overall_score": 0.0-1.0, '
        '"issues": ["issue1", "issue2"]}\n\n'
        "The overall_score should be the average of the three dimensions.\n"
        "The issues array should list any specific problems found (empty if none).\n"
        "Do not include any other text."
    )

    judge_user_prompt = (
        f"Question:\n{question}\n\n"
        f"Answer:\n{answer}\n\n"
        "Evaluate the style consistency of this answer."
    )

    try:
        response = judge_llm.invoke(
            [
                SystemMessage(content=judge_system_prompt),
                HumanMessage(content=judge_user_prompt),
            ]
        )

        response_text = response.content.strip() if response.content else ""

        # Extract JSON
        json_str = response_text
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(json_str)

        lang = result.get("language_consistency", 0)
        fmt = result.get("format_consistency", 0)
        tone = result.get("tone_professionalism", 0)
        overall = result.get("overall_score", (lang + fmt + tone) / 3)
        issues = result.get("issues", [])

        # Recalculate overall to ensure consistency
        overall = round((lang + fmt + tone) / 3, 4)

        return {
            "style_consistency": overall,
            "language_consistency": lang,
            "format_consistency": fmt,
            "tone_professionalism": tone,
            "issues": issues,
            "question_lang": question_lang,
        }

    except Exception as e:
        print(f"  [WARN] Style consistency evaluation failed: {e}")
        return {
            "style_consistency": None,
            "language_consistency": None,
            "format_consistency": None,
            "tone_professionalism": None,
            "issues": [],
            "question_lang": question_lang,
            "error": str(e),
        }


def main():
    config = load_config()
    eval_set = load_eval_set(EVAL_SET_PATH)

    retriever = create_retriever(config)
    generator = create_generator(config)

    llm_config = config["llm"]
    judge_llm = ChatOpenAI(
        model=llm_config.get("model", "qwen-plus"),
        temperature=0.0,
        api_key=llm_config.get("api_key"),
        base_url=llm_config.get("base_url"),
    )

    # Filter to non-refusal questions
    answerable_records = [
        r for r in eval_set if not r.get("expected_refused", False)
    ]

    print(f"Total eval questions: {len(eval_set)}")
    print(f"Answerable questions (for style consistency): {len(answerable_records)}")
    print()

    results = []

    for index, record in enumerate(answerable_records, start=1):
        question = record["question"]
        category = record.get("category", "")
        print(f"[{index}/{len(answerable_records)}] {question}")

        safety_result = check_safety(question)
        if not safety_result["safe"]:
            print(f"  SKIPPED (safety refusal)")
            results.append({
                "question": question,
                "category": category,
                "skipped": True,
                "style_consistency": None,
                "language_consistency": None,
                "format_consistency": None,
                "tone_professionalism": None,
                "issues": "",
                "question_lang": detect_language(question),
            })
            continue

        retrieved_chunks = retriever.retrieve(question)

        generation_result = generator.generate(
            question=question,
            retrieved_chunks=retrieved_chunks,
        )

        answer = redact_pii(generation_result["answer"])

        if generation_result["refused"]:
            print(f"  SKIPPED (refused: {generation_result['refusal_reason']})")
            results.append({
                "question": question,
                "category": category,
                "skipped": True,
                "style_consistency": None,
                "language_consistency": None,
                "format_consistency": None,
                "tone_professionalism": None,
                "issues": "",
                "question_lang": detect_language(question),
            })
            continue

        style = evaluate_style_consistency_single(
            question=question,
            answer=answer,
            judge_llm=judge_llm,
        )

        score = style["style_consistency"]
        lang = style["language_consistency"]
        fmt = style["format_consistency"]
        tone = style["tone_professionalism"]
        issues = style.get("issues", [])

        status = "✅" if score is not None and score >= 0.85 else "❌"
        print(f"  {status} Style: {score} (lang={lang}, fmt={fmt}, tone={tone})")

        if issues:
            for issue in issues[:2]:
                print(f"     - {issue}")

        results.append({
            "question": question,
            "category": category,
            "skipped": False,
            **style,
            "issues": json.dumps(issues, ensure_ascii=False),
        })

    # Summary
    scored = [r for r in results if r.get("style_consistency") is not None]

    if scored:
        avg_style = sum(r["style_consistency"] for r in scored) / len(scored)
        avg_lang = sum(r["language_consistency"] for r in scored) / len(scored)
        avg_fmt = sum(r["format_consistency"] for r in scored) / len(scored)
        avg_tone = sum(r["tone_professionalism"] for r in scored) / len(scored)
        passing = sum(1 for r in scored if r["style_consistency"] >= 0.85)
    else:
        avg_style = avg_lang = avg_fmt = avg_tone = 0
        passing = 0

    summary = {
        "total_answerable": len(answerable_records),
        "total_evaluated": len(scored),
        "avg_style_consistency": round(avg_style, 4),
        "avg_language_consistency": round(avg_lang, 4),
        "avg_format_consistency": round(avg_fmt, 4),
        "avg_tone_professionalism": round(avg_tone, 4),
        "passing_count": passing,
        "passing_rate": round(passing / len(scored), 4) if scored else 0,
        "prd_target": 0.85,
        "prd_pass": avg_style >= 0.85,
    }

    print()
    print("=" * 60)
    print("STYLE CONSISTENCY EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Method:              LLM-as-Judge (3 dimensions)")
    print(f"  Answerable questions: {summary['total_answerable']}")
    print(f"  Evaluated questions:  {summary['total_evaluated']}")
    print(f"  Avg Style Consistency:{summary['avg_style_consistency']}")
    print(f"    - Language:         {summary['avg_language_consistency']}")
    print(f"    - Format:           {summary['avg_format_consistency']}")
    print(f"    - Tone:             {summary['avg_tone_professionalism']}")
    print(f"  Passing (>=0.85):     {summary['passing_count']}/{summary['total_evaluated']}")
    print(f"  PRD Target:           >= {summary['prd_target']}")
    print(f"  PRD Status:           {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)

    # Write CSV
    timestamp = time.strftime("%Y-%m-%d")
    csv_path = OUTPUT_DIR / f"{timestamp}_style_consistency_eval.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type", "question", "category", "skipped", "question_lang",
        "style_consistency", "language_consistency", "format_consistency",
        "tone_professionalism", "issues", "error",
        "total_answerable", "total_evaluated", "avg_style_consistency",
        "avg_language_consistency", "avg_format_consistency",
        "avg_tone_professionalism", "passing_count", "passing_rate",
        "prd_target", "prd_pass",
    ]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        summary_row = {field: "" for field in fieldnames}
        summary_row.update({"row_type": "summary", **summary})
        writer.writerow(summary_row)

        for r in results:
            row = {field: "" for field in fieldnames}
            row["row_type"] = "detail"
            row.update(r)
            writer.writerow(row)

    print(f"\nCSV report: {csv_path}")

    return results, summary


if __name__ == "__main__":
    main()
