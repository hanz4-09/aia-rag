"""
Faithfulness Evaluation Script (LLM-as-Judge)

Evaluates whether the generated answer is faithful to the retrieved context.
Uses a separate LLM call to judge faithfulness on a per-statement basis.

Faithfulness = (number of faithful statements) / (total statements in answer)

PRD Target: Faithfulness >= 0.85
"""

import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def run_answer_pipeline(
    question: str,
    config: Dict[str, Any],
    retriever,
    generator,
) -> Dict[str, Any]:
    """Run the full RAG pipeline and return answer + context."""
    start_time = time.time()

    safety_result = check_safety(question)
    if not safety_result["safe"]:
        return {
            "answer": safety_result["message"],
            "refused": True,
            "refusal_reason": safety_result["reason"],
            "context_text": "",
            "sources": [],
            "retrieved_chunks": [],
        }

    retrieved_chunks = retriever.retrieve(question)

    generation_result = generator.generate(
        question=question,
        retrieved_chunks=retrieved_chunks,
    )

    answer = redact_pii(generation_result["answer"])

    # Build context text for faithfulness evaluation
    context_parts = []
    for chunk in retrieved_chunks:
        metadata = chunk.get("metadata", {})
        filename = metadata.get("filename", "unknown")
        text = chunk.get("text", "")
        context_parts.append(f"[Source: {filename}]\n{text}")

    context_text = "\n\n---\n\n".join(context_parts)

    return {
        "answer": answer,
        "refused": generation_result["refused"],
        "refusal_reason": generation_result["refusal_reason"],
        "context_text": context_text,
        "sources": generation_result["sources"],
        "retrieved_chunks": retrieved_chunks,
    }

def clean_json_response(response_text: str) -> str:
    """
    Clean common LLM JSON response wrappers such as markdown code fences.
    """
    text = response_text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()

    return text

def extract_json_object(response_text: str) -> str:
    """
    Extract the first complete JSON object from text using balanced braces.

    This is more robust than regex like r'\\{[^}]+\\}', because judge output
    may contain nested JSON objects inside arrays.
    """
    text = clean_json_response(response_text)

    start_index = text.find("{")
    if start_index == -1:
        raise ValueError("No JSON object start found in judge response.")

    brace_count = 0
    in_string = False
    escape = False

    for index in range(start_index, len(text)):
        char = text[index]

        if escape:
            escape = False
            continue

        if char == "\\":
            escape = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1

            if brace_count == 0:
                return text[start_index : index + 1]

    raise ValueError("No complete JSON object found in judge response.")

def evaluate_faithfulness_single(
    question: str,
    answer: str,
    context: str,
    judge_llm: ChatOpenAI,
) -> Dict[str, Any]:
    """
    Use LLM-as-judge to evaluate faithfulness.

    Returns:
        - faithfulness_score: float (0-1)
        - total_statements: int
        - faithful_statements: int
        - unfaithful_statements: list of {statement, reason}
    """
    judge_system_prompt = (
        "You are an expert evaluator for RAG (Retrieval-Augmented Generation) systems.\n"
        "Your task is to evaluate whether a generated answer is faithful to the provided context.\n\n"
        "Instructions:\n"
        "1. Break the answer into individual factual statements/claims.\n"
        "2. For each statement, determine if it is supported by the context.\n"
        "3. A statement is 'faithful' if it can be directly inferred from the context.\n"
        "4. A statement is 'unfaithful' if it contradicts the context or cannot be inferred from it.\n"
        "5. Generic phrases like 'based on the policy' or 'according to the document' are faithful "
        "as long as the document is referenced in the context.\n"
        "6. If the answer says it cannot find information (refusal), rate it as fully faithful (score=1.0).\n\n"
        "Respond ONLY with a valid JSON object in this exact format:\n"
        '{"total_statements": N, "faithful_statements": N, '
        '"unfaithful_details": [{"statement": "...", "reason": "..."}]}\n\n'
        "Do not include markdown code fences. Do not include any text outside the JSON object."
    )

    judge_user_prompt = (
        f"Context:\n{context}\n\n"
        f"Question:\n{question}\n\n"
        f"Answer:\n{answer}\n\n"
        "Evaluate the faithfulness of the answer to the context."
    )

    try:
        response = judge_llm.invoke(
            [
                SystemMessage(content=judge_system_prompt),
                HumanMessage(content=judge_user_prompt),
            ]
        )

        response_text = response.content.strip() if response.content else ""

        try:
            result = json.loads(clean_json_response(response_text))
        except json.JSONDecodeError:
            json_text = extract_json_object(response_text)
            result = json.loads(json_text)

        total = result.get("total_statements", 0)
        faithful = result.get("faithful_statements", 0)
        unfaithful_details = result.get("unfaithful_details", [])

        if total == 0:
            return {
                "faithfulness_score": 1.0,
                "total_statements": 0,
                "faithful_statements": 0,
                "unfaithful_details": [],
            }

        score = faithful / total

        return {
            "faithfulness_score": round(score, 4),
            "total_statements": total,
            "faithful_statements": faithful,
            "unfaithful_details": unfaithful_details,
        }

    except Exception as e:
        print(f"  [WARN] Faithfulness evaluation failed: {e}")

        raw_response = ""
        try:
            raw_response = response.content if response and response.content else ""
        except Exception:
            raw_response = ""

        if raw_response:
            print(f"  [WARN] Raw judge response preview: {raw_response[:500]}")

        return {
            "faithfulness_score": None,
            "total_statements": None,
            "faithful_statements": None,
            "unfaithful_details": [],
            "error": str(e),
        }

def main():
    config = load_config()
    eval_set = load_eval_set(EVAL_SET_PATH)

    # Create RAG pipeline components
    retriever = create_retriever(config)
    generator = create_generator(config)

    # Create judge LLM (use same config)
    llm_config = config["llm"]
    judge_llm = ChatOpenAI(
        model=llm_config.get("model", "qwen-plus"),
        temperature=0.0,  # Use 0 for deterministic judging
        api_key=llm_config.get("api_key"),
        base_url=llm_config.get("base_url"),
    )

    # Filter to non-refusal questions only for faithfulness evaluation
    answerable_records = [
        r for r in eval_set if not r.get("expected_refused", False)
    ]

    print(f"Total eval questions: {len(eval_set)}")
    print(f"Answerable questions (for faithfulness): {len(answerable_records)}")
    print()

    results = []

    for index, record in enumerate(answerable_records, start=1):
        question = record["question"]
        category = record.get("category", "")
        print(f"[{index}/{len(answerable_records)}] {question}")

        # Run RAG pipeline
        pipeline_result = run_answer_pipeline(
            question=question,
            config=config,
            retriever=retriever,
            generator=generator,
        )

        answer = pipeline_result["answer"]
        context = pipeline_result["context_text"]
        refused = pipeline_result["refused"]

        # Skip faithfulness evaluation for refused answers
        if refused:
            print(f"  SKIPPED (refused: {pipeline_result['refusal_reason']})")
            results.append({
                "question": question,
                "category": category,
                "refused": True,
                "refusal_reason": pipeline_result["refusal_reason"],
                "faithfulness_score": None,
                "total_statements": None,
                "faithful_statements": None,
                "unfaithful_details": "",
                "answer_preview": answer[:200].replace("\n", " "),
            })
            continue

        # Evaluate faithfulness
        faithfulness = evaluate_faithfulness_single(
            question=question,
            answer=answer,
            context=context,
            judge_llm=judge_llm,
        )

        score = faithfulness["faithfulness_score"]
        total_stmts = faithfulness["total_statements"]
        faithful_stmts = faithfulness["faithful_statements"]
        unfaithful = faithfulness.get("unfaithful_details", [])

        status = "✅" if score is not None and score >= 0.85 else "❌"
        print(f"  {status} Faithfulness: {score} ({faithful_stmts}/{total_stmts} statements)")

        if unfaithful:
            for detail in unfaithful[:2]:  # Show max 2 unfaithful statements
                print(f"     - Unfaithful: {detail.get('statement', '')[:80]}...")
                print(f"       Reason: {detail.get('reason', '')[:80]}")

        results.append({
            "question": question,
            "category": category,
            "refused": False,
            "refusal_reason": "",
            "faithfulness_score": score,
            "total_statements": total_stmts,
            "faithful_statements": faithful_stmts,
            "unfaithful_details": json.dumps(unfaithful, ensure_ascii=False),
            "answer_preview": answer[:200].replace("\n", " "),
        })

    # Calculate summary
    scored_results = [
        r for r in results
        if r["faithfulness_score"] is not None
    ]

    if scored_results:
        avg_faithfulness = sum(r["faithfulness_score"] for r in scored_results) / len(scored_results)
        total_statements = sum(r["total_statements"] or 0 for r in scored_results)
        total_faithful = sum(r["faithful_statements"] or 0 for r in scored_results)
        passing = sum(1 for r in scored_results if r["faithfulness_score"] >= 0.85)
    else:
        avg_faithfulness = 0
        total_statements = 0
        total_faithful = 0
        passing = 0

    summary = {
        "total_answerable": len(answerable_records),
        "total_evaluated": len(scored_results),
        "avg_faithfulness": round(avg_faithfulness, 4),
        "overall_statements": total_statements,
        "overall_faithful": total_faithful,
        "overall_faithfulness_rate": (
            round(total_faithful / total_statements, 4) if total_statements > 0 else 0
        ),
        "passing_count": passing,
        "passing_rate": round(passing / len(scored_results), 4) if scored_results else 0,
        "prd_target": 0.85,
        "prd_pass": avg_faithfulness >= 0.85,
    }

    print()
    print("=" * 60)
    print("FAITHFULNESS EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Answerable questions:  {summary['total_answerable']}")
    print(f"  Evaluated questions:   {summary['total_evaluated']}")
    print(f"  Avg Faithfulness:      {summary['avg_faithfulness']}")
    print(f"  Overall statements:    {summary['overall_statements']}")
    print(f"  Faithful statements:   {summary['overall_faithful']}")
    print(f"  Passing (>=0.85):      {summary['passing_count']}/{summary['total_evaluated']}")
    print(f"  PRD Target:            >= {summary['prd_target']}")
    print(f"  PRD Status:            {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)

    # Write CSV report
    timestamp = time.strftime("%Y-%m-%d")
    csv_path = OUTPUT_DIR / f"{timestamp}_faithfulness_eval.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type", "question", "category", "refused", "refusal_reason",
        "faithfulness_score", "total_statements", "faithful_statements",
        "unfaithful_details", "answer_preview",
        "total_answerable", "total_evaluated", "avg_faithfulness",
        "overall_statements", "overall_faithful", "overall_faithfulness_rate",
        "passing_count", "passing_rate", "prd_target", "prd_pass",
    ]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        summary_row = {field: "" for field in fieldnames}
        summary_row.update({
            "row_type": "summary",
            **summary,
        })
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
