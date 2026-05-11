# Model Selection Rationale

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Report Type: Model Selection / Cost-Latency-Quality Trade-off  
Related Components: `configs/app.yaml`, `scripts/evaluate_latency.py`, `scripts/evaluate_faithfulness_llm_judge.py`, `scripts/evaluate_answers.py`, `reports/operations_report.csv`

---

## 1. Purpose

This document explains the model selection rationale for the AIA RAG Case Study Service.

The PRD requires token cost estimates per 1,000 calls and an explicit model-version selection rationale covering quality, cost, and latency trade-offs.

---

## 2. Final Validation Model

The final Phase 3 validation model is:

    qwen-max

The model was selected for final validation because it provides stronger answer quality and more stable reasoning behavior for RAG-style grounded generation.

It was used for final PRD metric validation, including:

- Answer Compliance
- Refusal Appropriateness
- Context Precision
- Faithfulness
- Style Consistency
- Latency
- Concurrency

---

## 3. Final Validation Results

Final validated quality and performance metrics:

    Answer Compliance Rate = 1.0
    Refusal Appropriateness Pass Rate = 1.0
    Avg Context Precision = 0.9807
    Avg Faithfulness = 1.0
    Avg Style Consistency = 0.994
    Latency Within 10s Rate = 0.9667
    Concurrency Success Rate = 1.0
    Concurrency Within 10s Rate = 1.0

These results show that qwen-max satisfies all current PRD quality and performance targets.

---

## 4. Cost Estimate

The operations report provides reference cost estimates based on token usage and configured pricing.

Current operations report includes:

    reference_cost_per_1000_calls = 0.5188
    estimated_billable_cost_per_1000_calls = 0.0

The reference cost is calculated from token counts and configured model pricing.

The estimated billable cost may be zero when free quota is enabled or when the current environment uses non-billable quota.

---

## 5. Quality / Cost / Latency Trade-off

### 5.1 qwen-max

Advantages:

- strongest quality among the tested/available Qwen model options
- better suited for final validation and demo
- more reliable for grounded answer generation
- better style consistency and answer completeness

Trade-offs:

- higher latency than smaller models
- higher token cost
- occasional provider-side generation latency outliers

Observed latency caveat:

    max_latency_ms = 10591
    within_10s_rate = 0.9667

The latency outlier was diagnosed as qwen-max generation latency fluctuation, not retrieval latency.

### 5.2 qwen-plus

Advantages:

- lower cost than qwen-max
- generally lower latency
- suitable for iterative development and repeated evaluation

Trade-offs:

- may be less stable than qwen-max for final quality validation
- may need more prompt or evaluation-set tuning for edge cases

### 5.3 qwen-turbo / qwen-flash or equivalent lower-tier models

Advantages:

- lower cost
- lower latency
- useful for frequent local debugging and repeated development runs

Trade-offs:

- potentially weaker reasoning quality
- potentially lower faithfulness and compliance stability
- should not be used as the only final validation model unless metrics are rerun and pass

---

## 6. Final Model Selection Decision

The project uses a two-tier model strategy:

### Final validation / demo

Use:

    qwen-max

Reason:

    It provides the strongest quality baseline and passed all PRD metrics in the final full evaluation.

### Iterative development / repeated evaluation

Use:

    qwen-plus, qwen-turbo, qwen-flash, or another lower-cost OpenAI-compatible model

Reason:

    These models are more cost-effective and may have lower latency for repeated experiments.

---

## 7. Configuration Flexibility

The model is configurable through:

    configs/app.yaml

Important fields:

    llm.provider
    llm.model
    llm.base_url
    llm.temperature

The project can switch between compatible model versions without changing business logic, as long as the provider exposes an OpenAI-compatible chat completion API.

---

## 8. Conclusion

qwen-max was selected as the final validation model because it provides the best quality and successfully passed all PRD metrics.

Lower-cost models remain appropriate for iterative development, debugging, and repeated evaluation runs.

Final recommendation:

    qwen-max for final validation and demo
    lower-cost models for repeated development evaluation
