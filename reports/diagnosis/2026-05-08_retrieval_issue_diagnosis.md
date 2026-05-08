# Issue Diagnosis Report: Retrieval Quality Improvements

Date: 2026-05-08  
Project: AIA RAG Case Study Service  
Report Type: Issue Diagnosis  
Related Evaluation Report: `reports/evaluations/2026-05-08_retrieval_three_modes.md`  
Supporting CSV: `reports/evaluations/2026-05-08_retrieval_three_modes.csv`

---

## 1. Purpose

This report documents two retrieval quality issues identified during the second-stage RAG evaluation.

The goal is to show a reproducible diagnosis process:

1. Identify an issue from quantitative metrics.
2. Explain the likely root cause.
3. Apply a targeted fix.
4. Verify the improvement using before/after evaluation results.

The two diagnosed issues are:

1. Vector-only retrieval recall was insufficient.
2. Hybrid retrieval ranking quality was still limited.

---

## 2. Evaluation Context

The retrieval evaluation compared three configurations:

1. `vector`
2. `hybrid`
3. `hybrid_rerank`

Evaluation dataset:

```text
eval/retrieval_eval_set.jsonl
```

Evaluation output:

```text
reports/evaluations/2026-05-08_retrieval_three_modes.csv
```

Metrics used:

- Hit Rate
- Top-1 Accuracy
- MRR
- Average retrieval latency

---

## 3. Summary of Evaluation Results

| Retrieval Mode | Hit Rate | Top-1 Accuracy | MRR | Avg Latency |
|---|---:|---:|---:|---:|
| Vector-only | 0.7857 | 0.5714 | 0.6452 | 41.71 ms |
| Hybrid | 1.0000 | 0.6429 | 0.8214 | 10.79 ms |
| Hybrid + Rerank | 1.0000 | 0.7857 | 0.8929 | 9.21 ms |

---

# Issue 1: Vector-only Retrieval Recall Was Insufficient

## 4.1 Symptom

The vector-only retriever did not always retrieve the expected source document in the top-k results.

Observed metric:

```text
vector hit_rate = 0.7857
```

This means that about 21.43% of the evaluation questions did not include the expected source document in the top-k retrieval results.

Examples from the evaluation details:

```text
Question:
What should employees do after a suspected compliance incident?

Expected source:
03_compliance_guide_en.txt

Vector-only result:
expected source not found in top-k
```

```text
Question:
What fields are included in the chat log data model?

Expected source:
05_akp_technical_specification_en.txt

Vector-only result:
expected source not found in top-k
```

```text
Question:
未来系统如何支持 cache？

Expected source:
06_akp_architecture_document_cn.txt

Vector-only result:
expected source not found in top-k
```

---

## 4.2 Evidence

Vector-only summary result:

```text
hit_rate = 0.7857
top1_accuracy = 0.5714
MRR = 0.6452
```

These values show that vector-only retrieval worked as a baseline but did not provide enough recall for the internal knowledge base.

---

## 4.3 Likely Root Cause

The internal knowledge base contains:

- Bilingual Chinese and English content
- Technical terms
- Policy-specific terms
- System names
- API paths
- Logging field names
- Security-related keywords

Vector-only retrieval relies on semantic similarity. It may miss documents when the query contains exact keywords or domain-specific terms that are better handled by keyword matching.

For example:

```text
request_id
cache
audit logging
API Key
/chat
/health
```

These terms are often better handled by keyword retrieval.

---

## 4.4 Fix

Added hybrid retrieval.

Hybrid retrieval combines:

```text
vector search + BM25 keyword search
```

Implementation:

```text
app/rag/keyword_retriever.py
app/rag/hybrid_retriever.py
app/rag/retriever_factory.py
```

Configuration:

```yaml
retrieval:
  mode: hybrid
  vector_weight: 0.6
  keyword_weight: 0.4
```

---

## 4.5 Post-fix Result

After introducing hybrid retrieval:

```text
hit_rate: 0.7857 -> 1.0000
```

Relative improvement:

```text
(1.0000 - 0.7857) / 0.7857 = 27.28%
```

Top-1 Accuracy also improved:

```text
0.5714 -> 0.6429
```

MRR also improved:

```text
0.6452 -> 0.8214
```

---

## 4.6 Conclusion for Issue 1

The issue was successfully mitigated.

Hybrid retrieval improved recall and ensured that the expected source document appeared in the top-k results for all evaluation questions.

This improvement is greater than 10%, satisfying the diagnosis improvement target.

---

# Issue 2: Hybrid Retrieval Ranking Quality Was Limited

## 5.1 Symptom

After hybrid retrieval was introduced, recall became strong:

```text
hybrid hit_rate = 1.0000
```

However, ranking quality was still limited:

```text
hybrid top1_accuracy = 0.6429
hybrid MRR = 0.8214
```

This means the correct source document was usually retrieved, but not always ranked first.

Examples:

```text
Question:
员工病假需要提供什么材料？

Expected source:
02_employee_handbook_cn.txt

Observed issue:
Expected source was retrieved but not ranked first.
```

```text
Question:
What endpoints does the AKP Platform provide?

Expected source:
05_akp_technical_specification_en.txt

Observed issue:
Expected source was retrieved but not ranked first.
```

---

## 5.2 Evidence

Hybrid retrieval summary result:

```text
hit_rate = 1.0000
top1_accuracy = 0.6429
MRR = 0.8214
```

The perfect hit rate shows the expected document was present in the candidate set.

The lower top-1 accuracy shows the ranking order still needed improvement.

---

## 5.3 Likely Root Cause

Hybrid retrieval improved recall by merging vector and keyword results, but the initial rank fusion strategy was still relatively simple.

Potential causes:

1. Similar documents shared overlapping terms.
2. English and Chinese handbooks contained parallel policy content.
3. Technical specification and architecture documents both discussed AKP Platform.
4. The fusion score did not fully optimize top-1 ranking.
5. No second-stage reranking was applied.

---

## 5.4 Fix

Added a configurable score-based reranker.

Implementation:

```text
app/rag/reranker.py
```

The reranker uses available retrieval signals:

```text
hybrid_score
keyword_score
vector_rank
```

Configuration:

```yaml
retrieval:
  enable_reranker: true
  rerank_hybrid_score_weight: 0.7
  rerank_keyword_score_weight: 0.2
  rerank_vector_rank_weight: 0.1
```

The reranker can be turned on or off without code changes.

---

## 5.5 Post-fix Result

After enabling the reranker:

```text
top1_accuracy: 0.6429 -> 0.7857
```

Relative improvement:

```text
(0.7857 - 0.6429) / 0.6429 = 22.21%
```

MRR improved:

```text
0.8214 -> 0.8929
```

Relative MRR improvement:

```text
(0.8929 - 0.8214) / 0.8214 = 8.70%
```

Hit Rate remained stable:

```text
1.0000 -> 1.0000
```

This is expected because reranking changes ordering, not recall.

---

## 5.6 Conclusion for Issue 2

The issue was partially mitigated.

The score-based reranker improved top-1 ranking quality by more than 10%, satisfying the improvement target for ranking quality.

MRR also improved, although the relative improvement was below 10%.

This result supports the conclusion that reranking is useful after hybrid retrieval.

---

## 6. Overall Diagnosis Summary

| Issue | Before | Fix | After | Improvement |
|---|---:|---|---:|---:|
| Vector recall insufficient | hit_rate = 0.7857 | Add hybrid retrieval | hit_rate = 1.0000 | +27.28% |
| Hybrid top-1 ranking limited | top1_accuracy = 0.6429 | Add score-based reranker | top1_accuracy = 0.7857 | +22.21% |

---

## 7. Lessons Learned

### 7.1 Hybrid retrieval improves recall

Vector-only retrieval is a useful semantic baseline, but it is not sufficient for this internal knowledge base.

Hybrid retrieval improves recall by combining semantic search with keyword matching.

### 7.2 Reranking improves ordering

Hybrid retrieval can find the correct source, but the correct source may not always be ranked first.

Reranking improves the ordering of candidate chunks and is useful as a second-stage retrieval step.

### 7.3 Metrics should be interpreted together

Hit Rate, Top-1 Accuracy, and MRR measure different aspects:

```text
Hit Rate: Did we find the expected source?
Top-1 Accuracy: Did we rank it first?
MRR: How close to the top was it?
```

Using all three gives a more complete view of retrieval quality.

---

## 8. Remaining Risks

1. The reranker is currently score-based, not model-based.
2. The evaluation set is small.
3. The current evaluation is source-level, not chunk-level.
4. The system does not yet evaluate answer faithfulness.
5. The system does not yet measure context precision.
6. The current generator is extractive and does not call a real LLM.

---

## 9. Next Actions

Recommended next actions:

1. Add a larger retrieval evaluation set.
2. Add context precision evaluation.
3. Replace score-based reranker with a real cross-encoder reranker.
4. Add answer-level evaluation after LLM generator is available.
5. Add cache and measure cache hit rate.
6. Add end-to-end latency evaluation with concurrent requests.