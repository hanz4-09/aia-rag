# Context Precision Evaluation Report: Baseline

Date: 2026-05-09  
Project: AIA RAG Case Study Service  
Evaluation Type: Context Precision Evaluation  
Version: v1  
Supporting CSV: reports/evaluations/2026-05-09_context_precision_baseline.csv

---

## 1. Objective

This evaluation measures whether the retrieved context chunks are relevant enough to be passed into the LLM generator.

The goal is to understand:

- Whether the expected source appears in the retrieved context
- Whether the expected source is ranked first
- How many retrieved chunks are relevant
- How many retrieved chunks are likely irrelevant
- Whether too much noisy context is being sent to the LLM

---

## 2. Evaluation Dataset

Evaluation set:

    eval/context_precision_eval_set.jsonl

Total questions:

    10

Each test case contains:

- question
- expected_source
- category
- relevant_keywords

A chunk is considered relevant when:

    chunk filename == expected_source
    and
    chunk text contains at least one relevant keyword

This is a rule-based approximation of context precision.

---

## 3. Metrics

Metrics:

- source_hit_rate
- top1_source_accuracy
- avg_context_precision_at_k
- avg_relevant_chunks
- avg_irrelevant_chunks
- avg_total_chunks
- avg_retrieval_latency_ms

context_precision_at_k is calculated as:

    relevant_chunks / total_retrieved_chunks

---

## 4. Summary Results

| Metric | Value |
|---|---:|
| Total Questions | 10 |
| Source Hit Rate | 1.0 |
| Top-1 Source Accuracy | 0.8 |
| Avg Context Precision@K | 0.46 |
| Avg Relevant Chunks | 2.3 |
| Avg Irrelevant Chunks | 2.7 |
| Avg Total Chunks | 5.0 |
| Avg Retrieval Latency ms | 12.6 |

---

## 5. Interpretation

This report establishes the first context precision baseline.

If source_hit_rate is high but avg_context_precision_at_k is low, it means the retriever usually finds the expected source but also passes many irrelevant chunks to the LLM.

That can increase:

- input token usage
- generation latency
- model cost
- risk of answer distraction

---

## 6. Limitations

Current limitations:

1. This is rule-based, not semantic.
2. Relevance is judged by expected source and keyword overlap.
3. Some truly relevant chunks may be marked irrelevant if they use different wording.
4. Some keyword-matching chunks may not actually be useful for answering.
5. This evaluation does not yet measure answer faithfulness.

---

## 7. Next Steps

Recommended next steps:

1. Review low context precision cases in the CSV.
2. Consider reducing top_k if too many irrelevant chunks are passed.
3. Improve context assembly.
4. Consider filtering weak keyword-only chunks.
5. Add LLM-as-judge context relevance evaluation in a future version.
