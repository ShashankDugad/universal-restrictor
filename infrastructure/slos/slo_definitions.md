# Universal Restrictor - Service Level Objectives (SLOs)

**Version:** 1.0  
**Date:** 2025-02-16  
**Owner:** Shashank Dugad

---

## 1. Overview

This document defines the Service Level Objectives (SLOs) for the Universal Restrictor API. These targets guide operational decisions and incident response.

---

## 2. SLO Definitions

### 2.1 Availability

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Uptime** | 99.9% | Monthly |
| **Allowed Downtime** | 43.2 min/month | Rolling 30 days |

**Definition:** Percentage of successful HTTP responses (non-5xx) from the `/health` endpoint.

```
Availability = (Total Requests - 5xx Errors) / Total Requests × 100
```

### 2.2 Latency

| Percentile | Target | Measurement |
|------------|--------|-------------|
| **p50** | < 100ms | Rolling 1 hour |
| **p95** | < 200ms | Rolling 1 hour |
| **p99** | < 500ms | Rolling 1 hour |

**Definition:** Time from request received to response sent for `/analyze` endpoint.

### 2.3 Error Rate

| Metric | Target | Measurement |
|--------|--------|-------------|
| **5xx Error Rate** | < 0.1% | Rolling 1 hour |
| **4xx Error Rate** | < 5% | Rolling 1 hour |

**Definition:** Percentage of requests returning error status codes.

### 2.4 Model Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| **BLOCK Recall** | ≥ 95% | Weekly evaluation |
| **BLOCK Precision** | ≥ 80% | Weekly evaluation |
| **False Positive Rate** | < 5% | Weekly evaluation |

**Definition:** Evaluated against held-out test set and production samples.

---

## 3. Error Budgets

### 3.1 Calculation

```
Monthly Error Budget = 100% - SLO Target

Availability: 100% - 99.9% = 0.1% (43.2 minutes)
Error Rate:   100% - 99.9% = 0.1% of requests
Latency p99:  100% - 99.5% = 0.5% can exceed 500ms
```

### 3.2 Budget Consumption Thresholds

| Consumption | Status | Action |
|-------------|--------|--------|
| 0-50% | 🟢 Healthy | Normal operations |
| 50-75% | 🟡 Warning | Review recent changes |
| 75-100% | 🟠 Critical | Freeze non-critical deploys |
| >100% | 🔴 Exhausted | Incident, all hands on deck |

### 3.3 Budget Reset

- Error budgets reset on the 1st of each month (00:00 UTC)
- Carryover: Unused budget does NOT carry over

---

## 4. Monitoring & Alerting

### 4.1 Metrics to Track

```yaml
# CloudWatch Metrics
metrics:
  - name: RequestCount
    namespace: UniversalRestrictor
    dimensions: [Endpoint, StatusCode]
    
  - name: Latency
    namespace: UniversalRestrictor
    dimensions: [Endpoint]
    statistics: [p50, p95, p99]
    
  - name: ErrorCount
    namespace: UniversalRestrictor
    dimensions: [Endpoint, ErrorType]
    
  - name: ModelConfidence
    namespace: UniversalRestrictor
    dimensions: [Decision]
    
  - name: ModelLatency
    namespace: UniversalRestrictor
    dimensions: [Stage]
```

### 4.2 Alert Thresholds

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| High Error Rate | 5xx > 1% for 5 min | P1 | Page on-call |
| High Latency | p99 > 1s for 5 min | P2 | Slack alert |
| Low Availability | Uptime < 99% in 1 hr | P1 | Page on-call |
| Budget Warning | > 50% consumed | P3 | Email alert |
| Budget Critical | > 75% consumed | P2 | Slack alert |
| Model Drift | Confidence avg < 0.7 | P3 | Email alert |

### 4.3 Alert Destinations

| Severity | Destination | Response Time |
|----------|-------------|---------------|
| P1 | PagerDuty + Phone | < 15 min |
| P2 | Slack #alerts | < 1 hour |
| P3 | Email | < 24 hours |

---

## 5. Dashboards

### 5.1 Real-Time Dashboard (CloudWatch)

```
┌─────────────────────────────────────────────────────────────┐
│                    UNIVERSAL RESTRICTOR                      │
│                    Real-Time Dashboard                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Availability│  │  Latency    │  │ Error Rate  │        │
│  │   99.95%    │  │  p99: 180ms │  │    0.02%    │        │
│  │   🟢 OK     │  │   🟢 OK     │  │   🟢 OK     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Requests per Second                     │   │
│  │  ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃▄▅▆▇█▇▆▅▄▃▂▁                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Latency Distribution                    │   │
│  │  p50: ███████████░░░░░ 85ms                         │   │
│  │  p95: ████████████████░ 165ms                       │   │
│  │  p99: █████████████████░ 180ms                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Error Budget: ████████████████████░░░░░ 78% remaining     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Weekly Report Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│                    WEEKLY SLO REPORT                         │
│                    Feb 10-16, 2025                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SLO COMPLIANCE                                             │
│  ├── Availability: 99.94% ✅ (target: 99.9%)               │
│  ├── Latency p99:  195ms  ✅ (target: <500ms)              │
│  └── Error Rate:   0.05%  ✅ (target: <0.1%)               │
│                                                             │
│  MODEL PERFORMANCE                                          │
│  ├── BLOCK Recall:    94.2% ⚠️ (target: 95%)               │
│  ├── BLOCK Precision: 81.5% ✅ (target: 80%)               │
│  └── False Positives: 4.2%  ✅ (target: <5%)               │
│                                                             │
│  INCIDENTS                                                  │
│  └── 0 P1, 1 P2 (latency spike on Feb 12, 3 min)          │
│                                                             │
│  ERROR BUDGET                                               │
│  └── 82% remaining (7.8 min consumed of 43.2 min)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Incident Response

### 6.1 Severity Levels

| Level | Definition | Example | Response |
|-------|------------|---------|----------|
| **P1** | Service down or data loss | 5xx > 10%, API unreachable | Immediate, all hands |
| **P2** | Degraded performance | Latency > 2x normal | < 1 hour |
| **P3** | Minor issue | Single endpoint slow | < 24 hours |
| **P4** | Cosmetic/low impact | Dashboard UI bug | Next sprint |

### 6.2 Incident Workflow

```
1. DETECT
   └── Alert fires or user reports

2. TRIAGE (< 5 min)
   ├── Assign severity
   ├── Page on-call if P1/P2
   └── Create incident channel

3. MITIGATE (< 30 min for P1)
   ├── Identify root cause
   ├── Apply fix or rollback
   └── Verify recovery

4. RESOLVE
   ├── Confirm SLOs restored
   ├── Notify stakeholders
   └── Close incident

5. POSTMORTEM (within 48 hrs for P1/P2)
   ├── Timeline
   ├── Root cause
   ├── Action items
   └── Lessons learned
```

### 6.3 Rollback Criteria

Automatic rollback if within 30 min of deploy:
- Error rate > 1%
- Latency p99 > 2x baseline
- Availability < 99%

---

## 7. SLO Review Process

| Frequency | Review | Participants |
|-----------|--------|--------------|
| Daily | Check dashboards | On-call |
| Weekly | SLO compliance report | Team |
| Monthly | Error budget review | Team + stakeholders |
| Quarterly | SLO target review | Leadership |

---

## 8. Appendix: CloudWatch Alarm Definitions

```yaml
# availability_alarm.yaml
AlarmName: UniversalRestrictor-LowAvailability
MetricName: 5XXError
Namespace: AWS/ApiGateway
Statistic: Sum
Period: 300
EvaluationPeriods: 2
Threshold: 10
ComparisonOperator: GreaterThanThreshold
AlarmActions:
  - arn:aws:sns:us-east-1:xxx:pagerduty

# latency_alarm.yaml
AlarmName: UniversalRestrictor-HighLatency
MetricName: Latency
Namespace: AWS/ApiGateway
ExtendedStatistic: p99
Period: 300
EvaluationPeriods: 2
Threshold: 1000
ComparisonOperator: GreaterThanThreshold
AlarmActions:
  - arn:aws:sns:us-east-1:xxx:slack-alerts
```

---

**End of SLO Document**
