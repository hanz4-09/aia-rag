# Optimization Report: Faithfulness Knowledge Gap Enhancement

Date: 2026-05-10  
Project: AIA RAG Case Study Service  
Report Type: Optimization Summary  
Optimization Area: Faithfulness / Knowledge Base Enhancement / Refusal Handling  
Related Components: `data/raw/`, `app/rag/generator.py`, `scripts/evaluate_faithfulness_llm_judge.py`

---

## 1. Purpose

This report documents the optimization work performed to improve LLM-as-Judge faithfulness results.

The goal was to resolve local faithfulness failures found during Phase 3 evaluation without relying on broad global prompt changes.

---

## 2. Initial Issue

The LLM-as-Judge faithfulness evaluation initially passed the overall PRD target, but several local cases exposed knowledge gaps and false-positive post-processing behavior.

The main problematic cases were:

1. `系统在什么情况下会返回拒答？`
2. `敏感数据脱敏的格式是什么？`

The overall PRD faithfulness target was still met, but these local cases showed that the answer sometimes expanded beyond what the retrieved context explicitly supported.

---

## 3. Issue 1: Refusal Behavior Knowledge Gap

### Problem

For the question:

    系统在什么情况下会返回拒答？

The answer incorrectly expanded refusal conditions to include items such as:

- PII handling
- safety check behavior
- offline evaluation metrics
- LLM provider failure

These were related system mechanisms, but the knowledge base did not clearly define which cases should set:

    refused = true
    refusal_reason = ...

### Evidence

Before optimization, the LLM-as-Judge faithfulness score for this case dropped below the target.

The judge identified unsupported statements around refusal conditions.

### Change

A new knowledge document was added:

    data/raw/07_refusal_behavior_spec_cn.txt

This document explicitly defines:

- standard refusal fields
- standard refusal reasons
- SAFETY_RULE_TRIGGERED
- NO_RETRIEVED_CONTEXT
- LOW_RETRIEVAL_CONFIDENCE
- non-refusal cases
- difference between refusal and runtime errors

### Validation

After ingestion, retrieval for the question:

    系统在什么情况下会返回拒答？

returned `07_refusal_behavior_spec_cn.txt` as the top source.

After fixing the insufficient-context false positive, the LLM-as-Judge faithfulness score improved to:

    1.0

---

## 4. Issue 2: Insufficient Context Detection False Positive

### Problem

After adding the refusal behavior document, the system retrieved the correct context, but the question:

    系统在什么情况下会返回拒答？

was incorrectly converted into:

    refused = true
    refusal_reason = NO_RETRIEVED_CONTEXT

The reason was that `_is_insufficient_context_answer()` matched phrases such as:

    无法从内部知识库中找到足够相关的信息

even when the answer was only explaining the meaning of `NO_RETRIEVED_CONTEXT`.

### Change

The insufficient-context detection logic was made stricter.

The updated logic now:

- only converts short, direct insufficient-context answers into refusals
- avoids converting explanatory answers about refusal behavior
- ignores explanatory markers such as `NO_RETRIEVED_CONTEXT`, `refused=true`, `拒答场景`, and `拒答条件`

### Validation

After the change, the `/chat` API returned:

    refused = false
    refusal_reason = null

for the question:

    系统在什么情况下会返回拒答？

The answer was then evaluated normally by LLM-as-Judge and received:

    Faithfulness = 1.0

---

## 5. Issue 3: PII Redaction Knowledge Gap

### Problem

For the question:

    敏感数据脱敏的格式是什么？

The model answered with partially unsupported claims about redaction formats for employee IDs, passwords, and other sensitive values.

The existing data security policy mentioned redaction, but did not clearly define all supported placeholder formats according to the actual implementation.

### Evidence

Before optimization, LLM-as-Judge reported:

    Faithfulness = 0.75

The unfaithful statement was related to unsupported or overly broad redaction behavior.

### Change

A new knowledge document was added:

    data/raw/08_pii_redaction_spec_cn.txt

This document aligns with the actual implementation in `app/rag/pii.py`.

It defines the currently supported redaction formats:

| Data Type | Redacted Format |
|---|---|
| Email | `[EMAIL]` |
| Phone number | `[PHONE]` |
| API Key / Secret / Token / Access Token value | `[REDACTED_SECRET]` |
| 15-18 digit ID number | `[ID_NUMBER]` |

It also explicitly states current limitations:

- no `[EMPLOYEE_ID]` placeholder
- not all employee IDs are recognized as a separate type
- not all natural language password descriptions are automatically redacted
- supported secret redaction mainly depends on key names such as `api_key`, `secret`, `token`, and `access_token`

### Validation

After ingestion, retrieval for:

    敏感数据脱敏的格式是什么？

returned `08_pii_redaction_spec_cn.txt` as the top source.

The LLM-as-Judge score improved to:

    Faithfulness = 1.0

---

## 6. Final LLM-as-Judge Evaluation Result

After all changes, the LLM-as-Judge faithfulness evaluation result was:

| Metric | Value |
|---|---:|
| Answerable Questions | 28 |
| Evaluated Questions | 28 |
| Avg Faithfulness | 1.0 |
| Overall Statements | 78 |
| Faithful Statements | 78 |
| Passing Count | 28 / 28 |
| PRD Target | >= 0.85 |
| PRD Status | PASS |

This confirms that the Phase 3 faithfulness requirement is satisfied.

---

## 7. Key Lesson

The most effective fix was not broad prompt tuning.

The better approach was:

    identify unsupported answer claims
    clarify the missing knowledge in the internal knowledge base
    re-ingest documents
    rerun faithfulness evaluation

This is more stable and more aligned with RAG best practices.

---

## 8. Conclusion

This optimization successfully resolved the remaining LLM-as-Judge faithfulness gaps.

The system now passes the PRD faithfulness target with:

    Avg Faithfulness = 1.0
    Passing = 28 / 28
    PRD Status = PASS

The added knowledge documents also make the system behavior more explainable and easier to maintain.
