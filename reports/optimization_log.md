# Optimization Log

Project: AIA RAG Case Study Service  
Purpose: Track all major optimization work across Phase 2 and Phase 3.

---

## Optimization 001: Hybrid Retrieval

Date: 2026-05-08  
Phase: Phase 2  
Area: Retrieval Quality  
Status: Completed

### Issue / Motivation

Vector-only retrieval had insufficient recall for the internal knowledge base.

### Evidence

Retrieval evaluation showed:

- vector hit_rate = 0.7857
- vector top1_accuracy = 0.5714
- vector MRR = 0.6452

### Change

Added hybrid retrieval combining vector search and BM25 keyword search.

### Validation Result

Hybrid retrieval improved:

- hit_rate: 0.7857 -> 1.0000
- top1_accuracy: 0.5714 -> 0.6429
- MRR: 0.6452 -> 0.8214

### Related Files

- app/rag/keyword_retriever.py
- app/rag/hybrid_retriever.py
- app/rag/retriever_factory.py
- scripts/evaluate_retrieval.py

### Related Reports

- reports/evaluations/2026-05-08_retrieval_vector_vs_hybrid.md
- reports/evaluations/2026-05-08_retrieval_vector_vs_hybrid_mrr.md
- reports/diagnosis/2026-05-08_retrieval_issue_diagnosis.md

---

## Optimization 002: Score-based Reranker

Date: 2026-05-08  
Phase: Phase 2  
Area: Retrieval Ranking  
Status: Completed

### Issue / Motivation

Hybrid retrieval improved recall, but ranking quality was still limited.

### Evidence

Hybrid retrieval result:

- hit_rate = 1.0000
- top1_accuracy = 0.6429
- MRR = 0.8214

### Change

Added configurable score-based reranker.

### Validation Result

Hybrid + rerank improved:

- top1_accuracy: 0.6429 -> 0.7857
- MRR: 0.8214 -> 0.8929
- hit_rate remained 1.0000

### Related Files

- app/rag/reranker.py
- app/rag/hybrid_retriever.py
- configs/app.yaml
- scripts/evaluate_retrieval.py

### Related Reports

- reports/evaluations/2026-05-08_retrieval_three_modes.md
- reports/diagnosis/2026-05-08_retrieval_issue_diagnosis.md

---

## Optimization 003: Safety False Positive Reduction

Date: 2026-05-08  
Phase: Phase 2  
Area: Safety / Refusal Appropriateness  
Status: Completed

### Issue / Motivation

The normal security policy question below was incorrectly refused:

    API Key 泄露后应该怎么处理？

### Evidence

Before the fix:

- refused = true
- refusal_reason = SAFETY_RULE_TRIGGERED
- retrieved_chunk_ids = []
- cache_hit = false

### Change

Changed safety logic from broad keyword blocking to intent-based pattern matching.

### Validation Result

After the fix:

- the question passed safety check
- normal RAG flow executed
- repeated request could hit cache

### Related Files

- app/rag/safety.py

### Related Reports

- reports/diagnosis/2026-05-08_safety_false_positive_diagnosis.md

---

## Optimization 004: In-memory Exact-match Cache

Date: 2026-05-08  
Phase: Phase 2  
Area: Cache / Operations  
Status: Completed

### Issue / Motivation

The operations report had cache_hit_rate, but no real cache existed.

### Evidence

Before implementation:

- cache_hit was always false
- cache_hit_rate was always 0.0

### Change

Added in-memory exact-match cache for non-refusal answers.

Cache key includes:

- normalized question
- retrieval mode
- reranker enabled flag
- top_k

### Validation Result

Repeated identical requests produced:

- first request: cache_hit = false
- second request: cache_hit = true

### Related Files

- app/core/cache.py
- app/api/chat.py
- configs/app.yaml
- scripts/generate_report.py

### Related Reports

- reports/phase2_summary.md

---

## Optimization 005: LLM-based Generator Integration

Date: 2026-05-09  
Phase: Phase 3  
Area: Answer Generation  
Status: Completed

### Issue / Motivation

The previous generator was extractive and did not call a real LLM.

### Evidence

Before the change:

- generator_type = extractive
- input_tokens = null
- output_tokens = null
- answer generation was not LLM-based

### Change

Integrated Alibaba Cloud Bailian / qwen-plus through OpenAI-compatible API.

### Validation Result

LLM request logs showed:

- generator_type = llm
- model_name = qwen-plus
- input_tokens recorded
- output_tokens recorded
- total_tokens recorded
- generation_latency_ms recorded

### Related Files

- app/rag/generator.py
- app/api/chat.py
- app/core/config.py
- configs/app.yaml

### Related Reports

- reports/phase2_summary.md
- reports/operations_report.csv

---

## Optimization 006: Operations Report Token and Cost Estimation

Date: 2026-05-09  
Phase: Phase 3  
Area: Operations / Cost  
Status: Completed

### Issue / Motivation

The operations report did not include real token statistics or cost estimation.

### Evidence

Before the change:

- avg_input_tokens = N/A
- avg_output_tokens = N/A
- cost estimation was unavailable

### Change

Enhanced operations report to calculate:

- total_input_tokens
- total_output_tokens
- total_tokens
- avg_input_tokens
- avg_output_tokens
- avg_total_tokens
- reference_cost_per_1000_calls
- estimated_billable_cost_per_1000_calls

### Validation Result

Example result:

- total_input_tokens = 3717
- total_output_tokens = 311
- reference_cost_per_1000_calls = 0.62 USD
- estimated_billable_cost_per_1000_calls = 0.0 under free quota

### Related Files

- scripts/generate_report.py
- configs/app.yaml

### Related Reports

- reports/operations_report.csv

---

## Optimization 007: LLM Insufficient Context Refusal Conversion

Date: 2026-05-09  
Phase: Phase 3  
Area: Answer Compliance / Refusal Appropriateness  
Status: Completed

### Issue / Motivation

For the out-of-scope question:

    How to configure Kubernetes ingress?

The LLM answered that the internal knowledge base did not contain enough information, but the system still returned:

- refused = false
- refusal_reason = null

### Evidence

Answer evaluation before the fix:

- rule_based_pass_rate = 0.9
- expected_refusal_match_rate = 0.9
- refusal_reason_match_rate = 0.9

### Change

Added insufficient-context answer detection in LLMGenerator.

If the LLM indicates insufficient context, the system now returns:

- refused = true
- refusal_reason = NO_RETRIEVED_CONTEXT

### Validation Result

Answer evaluation after the fix:

- rule_based_pass_rate = 1.0
- expected_refusal_match_rate = 1.0
- refusal_reason_match_rate = 1.0

### Related Files

- app/rag/generator.py
- scripts/evaluate_answers.py

### Related Reports

- reports/diagnosis/2026-05-09_llm_insufficient_context_refusal_diagnosis.md
- reports/evaluations/2026-05-09_answer_quality_after_refusal_fix.md

---

## Optimization 008: Refusal Appropriateness Evaluation

Date: 2026-05-09  
Phase: Phase 3  
Area: Evaluation / Refusal Appropriateness  
Status: Completed

### Issue / Motivation

The project needed a dedicated evaluation to verify that the system refuses unsafe and out-of-scope questions while allowing normal policy questions.

### Evidence

Previous issues showed both false positives and false negatives in refusal behavior.

### Change

Added a refusal appropriateness evaluation set and script.

### Validation Result

Refusal evaluation result:

- total_questions = 14
- pass_rate = 1.0
- refusal_decision_match_rate = 1.0
- refusal_reason_match_rate = 1.0
- false_positive_rate = 0.0
- false_negative_rate = 0.0

### Related Files

- eval/refusal_eval_set.jsonl
- scripts/evaluate_refusals.py

### Related Reports

- reports/evaluations/2026-05-09_refusal_appropriateness.md

---

## Optimization 009: Context Assembly Top-3

Date: 2026-05-10  
Phase: Phase 3  
Area: Context Assembly / Token Efficiency  
Status: Completed

### Issue / Motivation

The retriever could find the expected source, but too many weakly relevant chunks were passed to the LLM.

### Evidence

Context precision baseline:

- source_hit_rate = 1.0
- top1_source_accuracy = 0.8
- avg_context_precision_at_k = 0.46
- avg_irrelevant_chunks = 2.7
- avg_total_chunks = 5.0

### Simulation

Top-N simulation showed:

- Top 5: avg_context_precision = 0.46, avg_irrelevant_chunks = 2.7
- Top 3: avg_context_precision = 0.60, avg_irrelevant_chunks = 1.2
- Top 2: avg_context_precision = 0.65, avg_irrelevant_chunks = 0.7

Top 3 was selected as the best tradeoff.

### Change

Added:

    context:
      max_context_chunks: 3

Retriever still returns top 5, but LLM prompt context uses only top 3 chunks.

### Validation Result

After the change:

- context_chunks_used = 3
- answer evaluation pass rate remained 1.0
- avg_total_tokens reduced from about 1392.56 to 926.89
- avg_generation_latency_ms reduced from about 2145.2 to 1725.7

### Related Files

- configs/app.yaml
- app/rag/generator.py
- app/schemas/response.py
- app/api/chat.py
- scripts/evaluate_context_precision.py
- scripts/evaluate_context_assembly_topn.py

### Related Reports

- reports/evaluations/2026-05-09_context_precision_baseline.md
- reports/evaluations/2026-05-09_context_assembly_topn_comparison.md
- reports/diagnosis/2026-05-10_context_assembly_optimization_report.md

---

## Future Optimization Template

Use this template for future entries.

### Optimization XXX: Title

Date: YYYY-MM-DD  
Phase: Phase X  
Area: Area  
Status: Completed / In Progress

#### Issue / Motivation

Describe the issue or reason for optimization.

#### Evidence

List metrics, logs, evaluation results, or examples.

#### Change

Describe what changed.

#### Validation Result

Describe post-change validation metrics.

#### Related Files

List changed files.

#### Related Reports

List related formal reports.

---

## Optimization 010: Faithfulness Rule-based Evaluation Refinement

Date: 2026-05-10  
Phase: Phase 3  
Area: Evaluation / Faithfulness  
Status: Completed

### Issue / Motivation

The initial rule-based faithfulness evaluation produced false failures.

Two cases failed due to evaluation logic rather than actual answer quality:

1. `What endpoints does the AKP Platform provide?`
2. `How to configure Kubernetes ingress?`

### Evidence

The endpoint answer contained `GET \`/health\`` and `POST \`/chat\``, but the rule expected `GET /health` and `POST /chat`, causing strict string matching to fail.

The Kubernetes ingress case was correctly refused with `NO_RETRIEVED_CONTEXT`, but the evaluator still required context claim support.

### Change

Updated the rule-based faithfulness evaluator to:

- normalize Markdown formatting before text matching
- handle expected refusal cases separately
- skip context-claim support requirement for expected refusal cases

### Validation Result

After the refinement:

- faithfulness_pass_rate = 1.0
- answer_not_empty_rate = 1.0
- expected_refusal_match_rate = 1.0
- source_hit_rate = 1.0
- unsupported_claims_clean_rate = 1.0

### Related Files

- scripts/evaluate_faithfulness_rule_based.py

### Related Reports

- reports/evaluations/2026-05-10_faithfulness_baseline.md
- reports/evaluations/2026-05-10_faithfulness_baseline.csv
---

## Optimization 011: Faithfulness Knowledge Gap Enhancement

Date: 2026-05-10  
Phase: Phase 3  
Area: Faithfulness / Knowledge Base Enhancement / Refusal Handling  
Status: Completed

### Issue / Motivation

LLM-as-Judge faithfulness evaluation found local faithfulness gaps even though the overall PRD target was passing.

Two main questions exposed the issue:

1. `系统在什么情况下会返回拒答？`
2. `敏感数据脱敏的格式是什么？`

The model answers were generally reasonable, but some claims were not explicitly supported by the retrieved context.

### Evidence

For the refusal behavior question, the model initially expanded refusal conditions to include related but unsupported mechanisms, such as:

- PII handling
- safety check behavior
- offline evaluation metrics
- LLM provider failure

After adding the refusal behavior document, another issue appeared: the answer explaining `NO_RETRIEVED_CONTEXT` was incorrectly converted into a `NO_RETRIEVED_CONTEXT` refusal by `_is_insufficient_context_answer()`.

For the PII redaction question, the model made unsupported claims about employee IDs, passwords, and other sensitive values because the existing data security policy did not clearly define the current supported placeholder formats.

Before optimization:

- refusal behavior question had low faithfulness or was incorrectly converted to `NO_RETRIEVED_CONTEXT`
- PII redaction format question had faithfulness = 0.75
- LLM-as-Judge evaluation did not fully pass all answerable questions

### Change

Added two new knowledge base documents:

- `data/raw/07_refusal_behavior_spec_cn.txt`
- `data/raw/08_pii_redaction_spec_cn.txt`

`07_refusal_behavior_spec_cn.txt` defines:

- standard refusal fields
- standard refusal scenarios
- `SAFETY_RULE_TRIGGERED`
- `NO_RETRIEVED_CONTEXT`
- `LOW_RETRIEVAL_CONFIDENCE`
- non-refusal cases such as PII redaction, logging, offline evaluation metrics, runtime errors, and LLM provider failures

`08_pii_redaction_spec_cn.txt` aligns the knowledge base with the current implementation in `app/rag/pii.py`.

It defines the currently supported redaction formats:

- Email -> `[EMAIL]`
- Phone number -> `[PHONE]`
- API Key / Secret / Token / Access Token value -> `[REDACTED_SECRET]`
- 15-18 digit ID number -> `[ID_NUMBER]`

It also explicitly states current limitations:

- no `[EMPLOYEE_ID]` placeholder
- not all employee IDs are recognized as a separate type
- not all natural language password descriptions are automatically redacted
- supported secret redaction mainly depends on field names such as `api_key`, `secret`, `token`, and `access_token`

Also refined insufficient-context detection in:

- `app/rag/generator.py`

The detection now avoids converting explanatory answers about refusal behavior into `NO_RETRIEVED_CONTEXT` refusals.

### Validation Result

After re-ingestion and rerunning LLM-as-Judge faithfulness evaluation:

- answerable questions = 28
- evaluated questions = 28
- avg_faithfulness = 1.0
- overall statements = 78
- faithful statements = 78
- passing = 28 / 28
- PRD target = >= 0.85
- PRD status = PASS

The two previously problematic cases were fixed:

- `系统在什么情况下会返回拒答？`: Faithfulness = 1.0
- `敏感数据脱敏的格式是什么？`: Faithfulness = 1.0

### Related Files

- `data/raw/07_refusal_behavior_spec_cn.txt`
- `data/raw/08_pii_redaction_spec_cn.txt`
- `app/rag/generator.py`
- `app/rag/pii.py`
- `scripts/evaluate_faithfulness_llm_judge.py`

### Related Reports

- `reports/evaluations/2026-05-10_faithfulness_eval.csv`
- `reports/diagnosis/2026-05-10_faithfulness_knowledge_gap_optimization_report.md`

### Final Conclusion

The optimization was successful.

The main lesson is that faithfulness gaps should first be solved by improving the internal knowledge base and aligning documentation with actual implementation, rather than applying broad global prompt changes.

