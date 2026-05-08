# Retrieval Evaluation Report v2: Vector-only vs Hybrid with MRR

Date: 2026-05-08  
Project: AIA RAG Case Study Service  
Evaluation Type: Retrieval Quality Evaluation  
Version: v2  
Compared Configurations: Vector-only retrieval vs Hybrid retrieval  
Supporting CSV: `reports/evaluations/2026-05-08_retrieval_vector_vs_hybrid_mrr.csv`

---

## 1. Evaluation Objective

The objective of this evaluation is to compare the retrieval quality of two retrieval modes:

1. Vector-only retrieval
2. Hybrid retrieval

This v2 evaluation extends the previous retrieval evaluation by adding two ranking-oriented metrics:

- `expected_rank`
- `MRR`, Mean Reciprocal Rank

The purpose is to better understand not only whether the expected source document appears in the top-k results, but also how highly it is ranked.

---

## 2. What Changed Since v1

The previous evaluation report compared vector-only retrieval and hybrid retrieval using:

- Hit Rate
- Top-1 Accuracy
- Average Retrieval Latency

This v2 evaluation adds:

```text
expected_rank
reciprocal_rank
MRR
```

This change makes the evaluation more informative.

Hit Rate can tell whether the correct source was retrieved at all.  
Top-1 Accuracy can tell whether the correct source was ranked first.  
MRR provides a middle-ground ranking metric by giving partial credit when the correct source appears at rank 2, rank 3, or lower.

---

## 3. Evaluation Dataset

The evaluation dataset contains 14 questions covering the current mock internal knowledge base.

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
reports/evaluations/2026-05-08_retrieval_vector_vs_hybrid_mrr.csv
```

---

## 4. Compared Configurations

### 4.1 Vector-only Retrieval

Vector-only retrieval uses embedding similarity search over the Chroma vector store.

Pipeline:

```text
question
  -> query embedding
  -> Chroma vector search
  -> top-k chunks
```

### 4.2 Hybrid Retrieval

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

---

## 5. Metrics

### 5.1 Hit Rate

Hit Rate measures whether the expected source document appears anywhere in the top-k retrieved results.

```text
hit_rate = number_of_questions_with_expected_source_in_top_k / total_questions
```

This metric mainly reflects recall.

### 5.2 Top-1 Accuracy

Top-1 Accuracy measures whether the first retrieved result comes from the expected source document.

```text
top1_accuracy = number_of_questions_with_expected_source_at_rank_1 / total_questions
```

This metric reflects strict ranking quality.

### 5.3 Expected Rank

Expected Rank records the position of the expected source document in the retrieved result list.

Examples:

```text
expected source at rank 1 -> expected_rank = 1
expected source at rank 2 -> expected_rank = 2
expected source not retrieved -> expected_rank = empty
```

### 5.4 Reciprocal Rank

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

### 5.5 MRR

MRR, or Mean Reciprocal Rank, is the average reciprocal rank across all evaluation questions.

```text
MRR = average(reciprocal_rank)
```

MRR is useful because it rewards retrieval systems that rank the correct source closer to the top, even when the correct source is not ranked first.

### 5.6 Average Latency

Average latency measures the average retrieval time per question.

```text
avg_latency_ms = average retrieval latency in milliseconds
```

---

## 6. Quantitative Results

| Retrieval Mode | Total Questions | Hit Rate | Top-1 Accuracy | MRR | Avg Latency |
|---|---:|---:|---:|---:|---:|
| Vector-only | 14 | 0.7857 | 0.5714 | 0.6452 | 12.07 ms |
| Hybrid | 14 | 1.0000 | 0.6429 | 0.8214 | 8.79 ms |

---

## 7. Key Findings

### 7.1 Hybrid retrieval improved recall

Hybrid retrieval improved Hit Rate from:

```text
0.7857 -> 1.0000
```

This means hybrid retrieval retrieved the expected source document in the top-k results for all 14 evaluation questions.

This is a strong improvement over vector-only retrieval and shows that keyword matching helps recover relevant documents that vector similarity alone may miss.

### 7.2 Hybrid retrieval improved strict top-1 ranking

Top-1 Accuracy improved from:

```text
0.5714 -> 0.6429
```

This means hybrid retrieval ranked the expected source as the first result more often than vector-only retrieval.

However, top-1 accuracy is still not high enough for a production-grade RAG system. Some relevant documents are retrieved but not ranked first.

### 7.3 Hybrid retrieval significantly improved MRR

MRR improved from:

```text
0.6452 -> 0.8214
```

This is the most important new finding in v2.

The improvement means that hybrid retrieval does not only retrieve the correct source more often; it also ranks the correct source closer to the top overall.

Compared with Hit Rate and Top-1 Accuracy, MRR gives a more balanced view of ranking quality.

### 7.4 Latency remained acceptable

The average retrieval latency was:

```text
vector-only: 12.07 ms
hybrid: 8.79 ms
```

In this local MVP dataset, hybrid retrieval did not introduce noticeable latency overhead.

However, this result should not be over-interpreted because the current corpus is small. Future evaluation should include larger corpora and end-to-end latency including generation.

---

## 8. Known Issues

### 8.1 Chinese HR questions are still not always ranked first

For the question:

```text
员工病假需要提供什么材料？
```

The expected source is:

```text
02_employee_handbook_cn.txt
```

However, the top-1 result is still:

```text
01_employee_handbook_en.txt
```

The expected Chinese handbook is retrieved, but not ranked first.

Possible reasons:

- The English and Chinese handbooks contain semantically similar content.
- The multilingual embedding model treats both documents as highly relevant.
- The current hybrid ranking does not explicitly prefer same-language documents.

### 8.2 HR policy intent and technical access intent can overlap

For the question:

```text
远程办公时可以使用个人设备访问公司系统吗？
```

The expected source is:

```text
02_employee_handbook_cn.txt
```

However, the top result can still be a technical specification document.

Possible reasons:

- The query contains terms such as system, device, and access.
- These terms also appear in technical documents.
- The retriever currently does not classify user intent before retrieval.

### 8.3 Technical specification and architecture content overlap

For questions about AKP Platform, technical specification and architecture documents can both appear highly relevant.

For example:

```text
What endpoints does the AKP Platform provide?
```

The expected source is:

```text
05_akp_technical_specification_en.txt
```

But architecture documents may rank higher because they also discuss AKP Platform and system modules.

Possible reasons:

- Technical specification and architecture documents share many domain terms.
- Current hybrid scoring does not consider document type.
- No reranker is used yet.

---

## 9. Interpretation

The v2 evaluation provides stronger evidence than the v1 evaluation.

In v1, Hit Rate showed that hybrid retrieval improved recall, but it was still unclear whether the correct documents were ranked meaningfully better.

In v2, MRR confirms that hybrid retrieval improves ranking quality as well.

The main conclusion is:

```text
Hybrid retrieval improves both recall and overall ranking quality compared with vector-only retrieval.
```

However, top-1 accuracy still needs improvement.

---

## 10. Conclusion

Hybrid retrieval should remain a supported retrieval mode in the project.

Compared with vector-only retrieval, hybrid retrieval achieved:

```text
hit_rate:       0.7857 -> 1.0000
top1_accuracy:  0.5714 -> 0.6429
MRR:            0.6452 -> 0.8214
```

This demonstrates that hybrid retrieval is a better default retrieval strategy for the current internal knowledge base.

The next optimization should focus on improving top-1 ranking quality.

---

## 11. Next Steps

Recommended next steps:

1. Tune hybrid retrieval weights.
2. Add document-type or language-aware ranking signals.
3. Add configurable reranker.
4. Compare vector-only, hybrid, and hybrid + rerank.
5. Add context precision evaluation.
6. Continue generating one new formal Markdown report for every evaluation run.