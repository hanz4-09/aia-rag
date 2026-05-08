# Retrieval Evaluation Report v3: Vector-only vs Hybrid vs Hybrid + Rerank

Date: 2026-05-08  
Project: AIA RAG Case Study Service  
Evaluation Type: Retrieval Quality Evaluation  
Version: v3  
Compared Configurations: Vector-only retrieval vs Hybrid retrieval vs Hybrid + Rerank  
Supporting CSV: `reports/evaluations/2026-05-08_retrieval_three_modes.csv`

---

## 1. Evaluation Objective

The objective of this evaluation is to compare three retrieval configurations:

1. Vector-only retrieval
2. Hybrid retrieval
3. Hybrid retrieval with reranking

This evaluation directly supports the case study requirement to compare multiple retrieval configurations quantitatively.

The main goal is to understand:

- Whether hybrid retrieval improves recall compared with vector-only retrieval
- Whether reranking improves ranking quality after hybrid retrieval
- Whether the additional retrieval logic introduces unacceptable latency overhead

---

## 2. Evaluation Dataset

The evaluation dataset contains 14 test questions covering the current mock internal knowledge base.

The dataset covers the following categories:

- HR policy
- Chinese HR policy
- Compliance
- Chinese data security policy
- Technical specification
- Chinese architecture document

Each evaluation record contains:

```json
{
  "question": "User question",
  "expected_source": "Expected source document",
  "category": "Question category"
}
```

The evaluation set is stored at:

```text
eval/retrieval_eval_set.jsonl
```

The detailed result CSV is stored at:

```text
reports/evaluations/2026-05-08_retrieval_three_modes.csv
```

---

## 3. Compared Configurations

### 3.1 Vector-only Retrieval

Vector-only retrieval uses embedding similarity search over the Chroma vector store.

Pipeline:

```text
question
  -> query embedding
  -> Chroma vector search
  -> top-k chunks
```

This is the MVP baseline retrieval mode.

---

### 3.2 Hybrid Retrieval

Hybrid retrieval combines vector search and BM25 keyword search.

Pipeline:

```text
question
  -> vector retriever
  -> keyword retriever
  -> merge by chunk_id
  -> hybrid score ranking
  -> top-k chunks
```

Current fusion strategy:

```text
hybrid_score = vector_weight * vector_rank_score + keyword_weight * keyword_rank_score
```

Current weights:

```yaml
vector_weight: 0.6
keyword_weight: 0.4
```

Hybrid retrieval is designed to improve recall, especially for questions containing technical keywords, system names, policy names, API paths, or domain-specific terms.

---

### 3.3 Hybrid Retrieval + Rerank

Hybrid + Rerank first retrieves candidates using the hybrid retriever, then applies a lightweight score-based reranker.

Pipeline:

```text
question
  -> hybrid retriever
  -> candidate chunks
  -> score-based reranker
  -> reranked top-k chunks
```

Current reranker strategy:

```text
reranker_score =
  rerank_hybrid_score_weight * hybrid_score
  + rerank_keyword_score_weight * keyword_score
  + rerank_vector_rank_weight * vector_rank_score
```

Current reranker weights:

```yaml
rerank_hybrid_score_weight: 0.7
rerank_keyword_score_weight: 0.2
rerank_vector_rank_weight: 0.1
```

This is a lightweight MVP reranker. It does not use a cross-encoder model yet. The purpose of this implementation is to establish the configurable reranker workflow and make reranking measurable in the evaluation pipeline.

---

## 4. Metrics

### 4.1 Hit Rate

Hit Rate measures whether the expected source document appears anywhere in the top-k retrieved results.

```text
hit_rate = number_of_questions_with_expected_source_in_top_k / total_questions
```

This metric mainly reflects recall.

---

### 4.2 Top-1 Accuracy

Top-1 Accuracy measures whether the first retrieved result comes from the expected source document.

```text
top1_accuracy = number_of_questions_with_expected_source_at_rank_1 / total_questions
```

This metric reflects strict ranking quality.

---

### 4.3 Expected Rank

Expected Rank records the position of the expected source document in the retrieved result list.

Examples:

```text
expected source at rank 1 -> expected_rank = 1
expected source at rank 2 -> expected_rank = 2
expected source not retrieved -> expected_rank = empty
```

---

### 4.4 Reciprocal Rank

Reciprocal Rank gives a per-question ranking score.

```text
reciprocal_rank = 1 / expected_rank
```

Examples:

```text
rank 1 -> 1.0
rank 2 -> 0.5
rank 3 -> 0.3333
not retrieved -> 0.0
```

---

### 4.5 MRR

MRR, or Mean Reciprocal Rank, is the average reciprocal rank across all evaluation questions.

```text
MRR = average(reciprocal_rank)
```

MRR is useful because it rewards retrieval systems that rank the correct source closer to the top, even when the correct source is not ranked first.

---

### 4.6 Average Latency

Average latency measures the average retrieval time per question.

```text
avg_latency_ms = average retrieval latency in milliseconds
```

This metric only measures retrieval latency in the local MVP environment. It does not include end-to-end answer generation latency.

---

## 5. Quantitative Results

| Retrieval Mode | Total Questions | Hit Rate | Top-1 Accuracy | MRR | Avg Latency |
|---|---:|---:|---:|---:|---:|
| Vector-only | 14 | 0.7857 | 0.5714 | 0.6452 | 41.71 ms |
| Hybrid | 14 | 1.0000 | 0.6429 | 0.8214 | 10.79 ms |
| Hybrid + Rerank | 14 | 1.0000 | 0.7857 | 0.8929 | 9.21 ms |

---

## 6. Key Findings

### 6.1 Hybrid retrieval significantly improved recall

Hybrid retrieval improved Hit Rate from:

```text
0.7857 -> 1.0000
```

This means hybrid retrieval retrieved the expected source document in the top-k results for all 14 evaluation questions.

The result shows that keyword retrieval complements vector retrieval well, especially for technical terms, policy names, system names, API-related terms, and bilingual document content.

---

### 6.2 Reranking significantly improved top-1 accuracy

Top-1 Accuracy changed as follows:

```text
vector-only:       0.5714
hybrid:            0.6429
hybrid + rerank:   0.7857
```

Hybrid retrieval improved top-1 accuracy slightly compared with vector-only retrieval.

After enabling reranking, top-1 accuracy improved more significantly from 0.6429 to 0.7857.

This shows that the reranker is mainly improving ranking quality, not recall.

---

### 6.3 MRR confirms better overall ranking quality

MRR changed as follows:

```text
vector-only:       0.6452
hybrid:            0.8214
hybrid + rerank:   0.8929
```

MRR provides stronger evidence than Top-1 Accuracy alone.

The improvement from hybrid to hybrid + rerank means that the expected source document is generally ranked closer to the top after reranking.

This confirms the expected behavior:

```text
Hybrid retrieval improves recall.
Reranking improves ordering.
```

---

### 6.4 Latency remained acceptable in local evaluation

Average retrieval latency was:

```text
vector-only:       41.71 ms
hybrid:            10.79 ms
hybrid + rerank:   9.21 ms
```

All three modes are well below the project-level end-to-end requirement of 10 seconds.

However, these numbers should not be over-interpreted because:

- The corpus is small.
- The reranker is currently score-based, not model-based.
- The numbers only measure retrieval latency.
- The current generator is extractive and does not call an LLM.

Future evaluations should measure end-to-end latency with a real LLM generator and a larger corpus.

---

## 7. Interpretation

The three retrieval modes show different strengths:

### Vector-only retrieval

Vector-only retrieval works as a simple semantic baseline.

However, it missed some expected source documents in the top-k results and had the lowest hit rate, top-1 accuracy, and MRR.

This suggests that vector-only retrieval is not sufficient as the default retrieval strategy for this internal knowledge base.

---

### Hybrid retrieval

Hybrid retrieval improved recall significantly.

It successfully included the expected source document in the top-k results for every evaluation question.

This makes hybrid retrieval a better default retrieval mode than vector-only retrieval for the current corpus.

---

### Hybrid + Rerank

Hybrid + Rerank achieved the best ranking quality.

It kept the same perfect hit rate as hybrid retrieval while improving top-1 accuracy and MRR.

This shows that reranking is useful after hybrid retrieval because the correct source is often already present in the candidate set, but not always ranked first.

---

## 8. Known Limitations

### 8.1 Current reranker is score-based, not model-based

The current reranker uses available retrieval signals such as:

- hybrid_score
- keyword_score
- vector_rank

It does not use a cross-encoder model yet.

Therefore, it is better described as a lightweight MVP reranker rather than a semantic reranker.

Future work should replace or extend it with a real cross-encoder reranker.

---

### 8.2 Current evaluation dataset is small

The evaluation set contains 14 questions.

This is enough for MVP-level comparison but not enough for production-level confidence.

Future evaluations should include more questions across:

- HR policy
- Compliance
- Security
- Technical API questions
- Architecture questions
- Bilingual CN/EN questions
- Out-of-scope questions

---

### 8.3 Metrics focus on source-level correctness

The current evaluation checks whether the expected source document is retrieved.

It does not yet evaluate:

- Chunk-level precision
- Context precision
- Answer faithfulness
- Answer compliance
- Refusal appropriateness
- Style consistency

These should be added in future evaluation phases.

---

### 8.4 Latency result is not representative of production

The current latency numbers are collected on a small local corpus.

They do not include:

- LLM generation latency
- Cross-encoder reranking latency
- Larger corpus retrieval latency
- Concurrent request load

Future performance evaluations should include p50 and p95 end-to-end latency under concurrent requests.

---

## 9. Conclusion

This evaluation validates the value of both hybrid retrieval and reranking.

Compared with vector-only retrieval:

```text
hit_rate:       0.7857 -> 1.0000
top1_accuracy:  0.5714 -> 0.7857
MRR:            0.6452 -> 0.8929
```

The result supports the following conclusion:

```text
Hybrid retrieval should be used to improve recall.
Reranking should be used to improve ranking quality.
```

Based on this evaluation, the recommended retrieval configuration for the current project is:

```yaml
retrieval:
  mode: hybrid
  enable_reranker: true
```

However, the current reranker is still a lightweight score-based reranker. A real cross-encoder reranker should be evaluated in a future iteration.

---

## 10. Second-Stage Progress Check

This evaluation completes a key part of the second-stage goal: retrieval control and retrieval evaluation hardening.

Completed in this stage:

- Vector-only retrieval
- Hybrid retrieval
- Config-based retrieval mode switching
- Reranker configuration switch
- Hybrid + rerank retrieval path
- Retrieval evaluation set
- Hit Rate, Top-1 Accuracy, MRR, and latency metrics
- Formal versioned evaluation report

Remaining second-stage items:

- Log field dictionary
- More complete operations report
- Issue diagnosis with before/after evidence
- Optional cache implementation
- Future model-based reranker evaluation

---

## 11. Next Steps

Recommended next steps:

1. Add a log field dictionary for structured logging.
2. Add a formal issue diagnosis report based on retrieval improvements.
3. Consider adding a real cross-encoder reranker.
4. Expand the evaluation dataset.
5. Add context precision evaluation.
6. Add answer-level evaluation after the LLM generator is implemented.