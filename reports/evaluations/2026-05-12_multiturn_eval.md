# Multi-turn Evaluation Report

Date: 2026-05-12
Project: AIA RAG Case Study Service
Evaluation Type: Multi-turn QA Evaluation

## Summary

- Total cases: 6
- Passing cases: 6
- Pass rate: 1.0
- History used rate: 1.0
- Source hit rate: 1.0
- Avg keyword hit rate: 1.0
- PRD pass: True

## Method

Each case contains two turns with the same session_id.
The second turn is a follow-up question.
The evaluator checks whether conversation history was used,
whether the answer was not refused, whether expected source was hit,
and whether expected keywords appeared in the second-turn answer.

## Case Results

### mt_audit_log_retention

- Category: compliance
- Turn 1: What are the audit logging requirements?
- Turn 2: How long should they be retained?
- History turns used: 1
- Source hit: True
- Keyword hit rate: 1.0
- Pass: True
- Answer preview: Audit logs for privileged operations should be retained for at least one year. Operational logs should be retained for at least 90 days, unless a longer retention period is required by legal, security, or business requirements.

### mt_api_key_incident_report

- Category: security_cn
- Turn 1: API Key 泄露后应该怎么处理？
- Turn 2: 多久内要报告？
- History turns used: 1
- Source hit: True
- Keyword hit rate: 1.0
- Pass: True
- Answer preview: 如果员工怀疑 API Key 泄露，必须在 24 小时内向 Security Operations 团队报告。

### mt_annual_leave_approval

- Category: hr_policy
- Turn 1: What is the annual leave policy?
- Turn 2: How long does the manager have to review it?
- History turns used: 1
- Source hit: True
- Keyword hit rate: 1.0
- Pass: True
- Answer preview: Managers should review leave requests within three working days.

### mt_audit_log_required_fields

- Category: compliance_en
- Turn 1: What are the audit logging requirements?
- Turn 2: What fields must be included in those logs?
- History turns used: 1
- Source hit: True
- Keyword hit rate: 1.0
- Pass: True
- Answer preview: Audit logs must include the following fields: timestamp, user identity, action type, target resource, request ID, and result status.

### mt_api_key_report_recipient_cn

- Category: security_cn
- Turn 1: API Key 泄露后应该怎么处理？
- Turn 2: 应该通知谁？
- History turns used: 1
- Source hit: True
- Keyword hit rate: 1.0
- Pass: True
- Answer preview: 如果发现 API Key 泄露，应在 24 小时内通知 Security Operations 团队。

### mt_ocr_api_key_report_window

- Category: ocr_en
- Turn 1: What does the scanned OCR test document say about API Key incidents?
- Turn 2: Within how many hours should they be reported?
- History turns used: 1
- Source hit: True
- Keyword hit rate: 1.0
- Pass: True
- Answer preview: API Key incidents should be reported within 24 hours.
