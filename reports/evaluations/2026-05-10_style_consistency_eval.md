# Style Consistency Evaluation Report

Date: 2026-05-10
Project: AIA RAG Case Study Service
Evaluation Type: Style Consistency (LLM-as-Judge)
Version: v1
Supporting CSV: reports/evaluations/2026-05-10_style_consistency_eval.csv

---

## 1. Objective

Evaluate whether the generated answers maintain consistent style across questions.

Style Consistency measures whether the system produces answers that are:
- **Language-consistent**: Matching the question's language (CN→CN, EN→EN)
- **Format-consistent**: Well-structured with uniform formatting
- **Tone-professional**: Professional, concise, and appropriate for an internal KB assistant

PRD Target: Style Consistency >= 0.85

---

## 2. Method

### 2.1 LLM-as-Judge (Three Dimensions)

A separate LLM call (qwen-plus, temperature=0) evaluates each answer on three dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Language Consistency | 1/3 | Does the answer use the same language as the question? |
| Format Consistency | 1/3 | Is the answer well-structured with consistent formatting? |
| Tone Professionalism | 1/3 | Is the tone professional and appropriate? |

### 2.2 Scoring

Each dimension is scored 0.0 to 1.0:

- **1.0**: Perfect (exact language match, clear structure, professional tone)
- **0.5**: Partial (mixed language, somewhat organized, minor tone issues)
- **0.0**: Poor (wrong language, disorganized, unprofessional)

    Style Consistency = (Language + Format + Tone) / 3

### 2.3 Scope

- Evaluation dataset: eval/answer_eval_set.jsonl (28 answerable questions)
- 1 question refused (NO_RETRIEVED_CONTEXT), excluded from scoring
- 27 questions evaluated

---

## 3. Results

### 3.1 Summary

| Metric | Value | PRD Target | Status |
|--------|-------|------------|--------|
| Avg Style Consistency | **98.15%** | >= 85% | ✅ PASS |
| Avg Language Consistency | **100%** | - | - |
| Avg Format Consistency | **96.30%** | - | - |
| Avg Tone Professionalism | **98.15%** | - | - |
| Passing Questions (>= 0.85) | 25/27 | - | - |

### 3.2 Dimension Breakdown

| Dimension | Score | Analysis |
|-----------|-------|----------|
| Language Consistency | 100% | All answers perfectly match question language (CN/EN) |
| Format Consistency | 96.30% | 1 answer had inconsistent formatting (mixed code styles) |
| Tone Professionalism | 98.15% | 1 answer was slightly vague in tone |

### 3.3 Below-Perfect Cases

| Question | Score | Language | Format | Tone | Issue |
|----------|-------|----------|--------|------|-------|
| Chat log data model fields | 83.3% | 1.0 | 0.5 | 1.0 | Mixed inline code backticks with plain text, redundant field listing |
| 员工病假需要提供什么材料？ | 66.7% | 1.0 | 0.5 | 0.5 | Overly brief format, vague tone ("may need", "per local HR rules") |

---

## 4. Analysis

### 4.1 Why Style Consistency Is High

1. **Explicit language instruction**: System prompt includes "If the user asks in Chinese, answer in Chinese. If the user asks in English, answer in English."
2. **Low temperature**: temperature=0.1 ensures consistent, non-creative outputs.
3. **Strict context grounding**: "Answer strictly based on the provided context" limits style variation.
4. **Professional system prompt**: "Keep the answer concise, professional, and grounded."

### 4.2 Improvement Opportunities

The two below-perfect cases reveal:

1. **Format issue**: When listing many fields, the LLM sometimes mixes formatting styles (backticks vs plain text). Could be improved by adding format guidance to the system prompt.

2. **Tone issue**: When the source document itself is vague ("may need", "per local rules"), the LLM faithfully reproduces this vagueness. This is technically correct (faithful) but hurts style consistency.

---

## 5. Limitations

1. LLM-as-judge may have inconsistent standards across evaluations.
2. The judge uses the same model family as the generator.
3. Format consistency is somewhat subjective.
4. Only 27 questions evaluated.

---

## 6. Recommendations

1. Add format guidance to system prompt (e.g., "Use bullet points for lists of 3+ items").
2. Monitor style consistency as the knowledge base grows.
3. Consider using a different model as judge to reduce bias.

---

## 7. Script

    scripts/evaluate_style_consistency.py

Usage:

    python scripts/evaluate_style_consistency.py
