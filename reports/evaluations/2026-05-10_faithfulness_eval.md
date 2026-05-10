# Faithfulness Evaluation Report

Date: 2026-05-10
Project: AIA RAG Case Study Service
Evaluation Type: Faithfulness (LLM-as-Judge)
Version: v1
Supporting CSV: reports/evaluations/2026-05-10_faithfulness_eval.csv

---

## 1. Objective

Evaluate whether the LLM-generated answers are faithful to the retrieved context.

Faithfulness measures the proportion of factual statements in the answer that can be directly supported by the retrieved context. Unfaithful answers contain hallucinations or information not present in the source documents.

PRD Target: Faithfulness ≥ 0.85

---

## 2. Method

### 2.1 LLM-as-Judge

A separate LLM call (qwen-plus, temperature=0) evaluates each answer:

1. The judge breaks the answer into individual factual statements.
2. For each statement, the judge determines if it is supported by the context.
3. A statement is "faithful" if it can be directly inferred from the context.
4. Generic phrases like "based on the policy" are considered faithful as long as the document is referenced.

### 2.2 Scope

- Only answerable (non-refusal) questions are evaluated.
- Safety refusals and out-of-scope refusals are excluded.
- Evaluation dataset: eval/answer_eval_set.jsonl (8 answerable questions)

### 2.3 Scoring

    Faithfulness = faithful_statements / total_statements

A question-level score of ≥ 0.85 is considered "passing".

---

## 3. Results

### 3.1 Summary

| Metric | Value |
|--------|-------|
| Total Answerable Questions | 8 |
| Evaluated Questions | 8 |
| Avg Faithfulness | **100%** |
| Overall Statements | 33 |
| Faithful Statements | 33 |
| Unfaithful Statements | 0 |
| Passing Questions (≥ 0.85) | 8/8 |
| PRD Target | ≥ 85% |
| PRD Status | ✅ PASS |

### 3.2 Per-Question Details

| # | Question | Category | Statements | Faithful | Score |
|---|----------|----------|------------|-----------|-------|
| 1 | What are the audit logging requirements? | compliance | 2 | 2 | 1.0 |
| 2 | How long should audit logs for privileged operations be retained? | compliance | 1 | 1 | 1.0 |
| 3 | API Key 泄露后应该怎么处理？ | security_cn | 8 | 8 | 1.0 |
| 4 | 日志中是否可以记录明文密码和完整 API Key？ | security_cn | 2 | 2 | 1.0 |
| 5 | What endpoints does the AKP Platform provide? | technical_spec | 4 | 4 | 1.0 |
| 6 | What fields are included in the chat log data model? | technical_spec | 10 | 10 | 1.0 |
| 7 | 员工病假需要提供什么材料？ | hr_policy_cn | 1 | 1 | 1.0 |
| 8 | AKP Platform 的核心模块有哪些？ | architecture_cn | 5 | 5 | 1.0 |

---

## 4. Analysis

### 4.1 Why Faithfulness Is High

The system achieves 100% faithfulness due to:

1. **Strict system prompt**: The generator is instructed to answer "strictly based on the provided context" and "do not use external knowledge".
2. **Low temperature**: temperature=0.1 minimizes creative generation.
3. **High-quality retrieval**: Hybrid + rerank retrieval achieves 100% hit rate, ensuring relevant context is always available.
4. **Sufficient context**: top_k=5 provides enough context for comprehensive answers.

### 4.2 Most Complex Answers

The most statement-heavy answers are:

| Question | Statements | Category |
|----------|------------|----------|
| What fields are included in the chat log data model? | 10 | technical_spec |
| API Key 泄露后应该怎么处理？ | 8 | security_cn |
| AKP Platform 的核心模块有哪些？ | 5 | architecture_cn |

Even these complex answers achieved 100% faithfulness, indicating strong context grounding.

---

## 5. Limitations

1. The evaluation set is small (8 answerable questions).
2. The judge LLM may have blind spots for subtle hallucinations.
3. Statement-level granularity may miss structural faithfulness issues.
4. The judge uses the same model family (qwen-plus) as the generator.

---

## 6. Recommendations

1. Expand evaluation set to 30+ questions for higher confidence.
2. Consider using a different model as judge to reduce bias.
3. Add faithfulness evaluation to CI/CD pipeline for regression detection.
4. Monitor faithfulness over time as the knowledge base grows.

---

## 7. Script

Evaluation script:

    scripts/evaluate_faithfulness.py

Usage:

    python scripts/evaluate_faithfulness.py
