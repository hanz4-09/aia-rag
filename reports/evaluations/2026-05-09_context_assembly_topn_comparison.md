# Context Assembly Top-N Comparison Report

Date: 2026-05-09  
Project: AIA RAG Case Study Service  
Evaluation Type: Context Assembly Simulation  
Version: v1  
Supporting CSV: reports/evaluations/2026-05-09_context_assembly_topn_comparison.csv

---

## 1. Objective

This evaluation simulates different context assembly strategies before changing the production RAG flow.

The current retriever returns top 5 chunks.

This simulation compares what happens if the generator only uses:

- top 5 chunks
- top 3 chunks
- top 2 chunks

The goal is to check whether reducing context chunks can improve context precision without significantly hurting source coverage.

---

## 2. Evaluation Dataset

Evaluation set:

    eval/context_precision_eval_set.jsonl

The dataset includes 10 representative questions across:

- compliance
- data security
- technical specification
- HR policy
- architecture

---

## 3. Method

For each question:

1. Retrieve top 5 chunks using hybrid + rerank.
2. Simulate context assembly with top N chunks.
3. Calculate source hit and context precision for each N.

A chunk is considered relevant when:

    chunk filename == expected_source
    and
    chunk text contains at least one relevant keyword

This is a rule-based approximation.

---

## 4. Summary Results

| Context Strategy | Total Questions | Source Hit Rate | Top-1 Source Accuracy | Avg Context Precision | Avg Relevant Chunks | Avg Irrelevant Chunks | Avg Total Chunks | Avg Retrieval Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Top 5 | 10 | 1.0 | 0.8 | 0.46 | 2.3 | 2.7 | 5.0 | 11.3 ms |
| Top 3 | 10 | 1.0 | 0.8 | 0.6 | 1.8 | 1.2 | 3.0 | 11.3 ms |
| Top 2 | 10 | 1.0 | 0.8 | 0.65 | 1.3 | 0.7 | 2.0 | 11.3 ms |

---

## 5. Interpretation

This report should be used to decide whether the system should reduce the number of chunks passed to the LLM.

A good context assembly strategy should:

- keep source_hit_rate high
- keep top1_source_accuracy high
- improve avg_context_precision
- reduce avg_irrelevant_chunks
- reduce expected input tokens and generation latency

If top 3 maintains source coverage while improving context precision, it is a strong candidate for the next context assembly configuration.

---

## 6. Limitations

Current limitations:

1. This is a simulation, not yet a production behavior change.
2. Relevance is rule-based.
3. Keyword matching may undercount semantic relevance.
4. It does not directly measure final answer faithfulness.
5. Token reduction is inferred, not directly measured here.

---

## 7. Next Steps

Recommended next steps:

1. Review the top-N comparison results.
2. If top 3 gives a good tradeoff, add a configurable context.max_context_chunks setting.
3. Update LLMGenerator to use only selected context chunks.
4. Rerun answer quality and operations reports.
5. Generate a follow-up formal evaluation report after the change.
