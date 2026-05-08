# Retrieval Evaluation Report: Vector-only vs Hybrid

Date: 2026-05-08  
Project: AIA RAG Case Study Service  
Evaluation Type: Retrieval Quality Evaluation  
Compared Configurations: Vector-only retrieval vs Hybrid retrieval

---

## 1. Evaluation Objective

The objective of this evaluation is to compare the retrieval quality of two retrieval modes:

1. Vector-only retrieval
2. Hybrid retrieval

The evaluation focuses on whether the retriever can find the expected source document for a given user question.

This evaluation is part of the RAG case study requirement to compare retrieval configurations quantitatively and support technical decisions with evidence.

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

The detailed CSV result is stored at:

```text
reports/evaluations/2026-05-08_retrieval_vector_vs_hybrid.csv
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

---

## 4. Metrics

### 4.1 Hit Rate

Hit Rate measures whether the expected source document appears anywhere in the top-k retrieved results.

```text
hit_rate = number_of_questions_with_expected_source_in_top_k / total_questions
```

This metric reflects recall.

### 4.2 Top-1 Accuracy

Top-1 Accuracy measures whether the first retrieved result comes from the expected source document.

```text
top1_accuracy = number_of_questions_with_expected_source_at_rank_1 / total_questions
```

This metric reflects ranking quality.

### 4.3 Average Latency

Average latency measures the average retrieval time per question.

```text
avg_latency_ms = average retrieval latency in milliseconds
```

---

## 5. Quantitative Results

| Retrieval Mode | Total Questions | Hit Rate | Top-1 Accuracy | Avg Latency |
|---|---:|---:|---:|---:|
| Vector-only | 14 | 0.7857 | 0.5714 | 12.86 ms |
| Hybrid | 14 | 1.0000 | 0.6429 | 9.29 ms |

---

## 6. Key Findings

### 6.1 Hybrid retrieval improved recall

Hybrid retrieval improved hit rate from 0.7857 to 1.0000.

This means that, in this evaluation set, hybrid retrieval was able to include the expected source document in the top-k results for every test question.

The improvement shows that keyword matching helps recover relevant documents that vector-only retrieval may miss, especially when the query contains domain-specific terms, system names, policy names, or technical keywords.

### 6.2 Hybrid retrieval slightly improved top-1 ranking

Top-1 accuracy improved from 0.5714 to 0.6429.

This shows that hybrid retrieval not only improved recall but also slightly improved ranking quality.

However, the top-1 score is still not high enough for a production-grade RAG system. Some relevant documents are retrieved but not ranked first.

### 6.3 Latency remained acceptable

Hybrid retrieval average latency was 9.29 ms in this local MVP evaluation.

This is well below the project-level performance requirement that 90% of QA requests should complete end-to-end within 10 seconds.

However, this latency only measures retrieval time in a small local dataset. Future evaluations should include larger corpora and end-to-end latency including generation.

---

## 7. Known Issues

### 7.1 Bilingual HR ranking issue

For the question:

```text
员工病假需要提供什么材料？
```

The expected source was:

```text
02_employee_handbook_cn.txt
```

However, the top-1 result was:

```text
01_employee_handbook_en.txt
```

The expected Chinese handbook was still retrieved, but it was not ranked first.

Possible reasons:

- The English and Chinese employee handbooks contain semantically similar content.
- The multilingual embedding model may consider both documents highly related.
- The current hybrid score does not explicitly prefer same-language documents.

### 7.2 Remote work question ranking issue

For the question:

```text
远程办公时可以使用个人设备访问公司系统吗？
```

The expected source was:

```text
02_employee_handbook_cn.txt
```

However, the top-1 result was:

```text
05_akp_technical_specification_en.txt
```

Possible reasons:

- The query contains terms related to systems and access.
- The technical specification document also contains system access and authentication-related content.
- The retriever currently does not distinguish HR policy intent from technical system intent.

### 7.3 Technical specification vs architecture overlap

For the question:

```text
What endpoints does the AKP Platform provide?
```

The expected source was:

```text
05_akp_technical_specification_en.txt
```

However, the top-1 result was:

```text
06_akp_architecture_document_cn.txt
```

Possible reasons:

- Both documents mention AKP Platform.
- Architecture content and technical specification content overlap.
- Current hybrid ranking does not yet use reranking or document-type awareness.

---

## 8. Conclusion

Hybrid retrieval provides a clear improvement over vector-only retrieval in this evaluation.

The most important improvement is recall:

```text
hit_rate: 0.7857 -> 1.0000
```

Top-1 accuracy also improved:

```text
top1_accuracy: 0.5714 -> 0.6429
```

Based on these results, hybrid retrieval should be kept as a supported retrieval mode in the project.

However, ranking quality still needs further improvement. The next optimization should focus on improving top-1 accuracy and document ranking quality.

---

## 9. Next Steps

Recommended next steps:

1. Add MRR to the evaluation script to better measure ranking quality.
2. Tune hybrid retrieval weights.
3. Add document-type or language-aware ranking signals.
4. Add configurable reranker.
5. Compare vector-only, hybrid, and hybrid + rerank in the next evaluation.
6. Generate a new formal evaluation report after each evaluation run.