# Feedback Loop Architecture

## Overview

A system that learns from human corrections to improve detection accuracy over time.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FEEDBACK LOOP SYSTEM                               │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌──────────┐     ┌──────────────┐     ┌──────────────┐
     │  User    │────▶│  Restrictor  │────▶│   Decision   │
     │  Input   │     │     API      │     │  ALLOW/BLOCK │
     └──────────┘     └──────────────┘     └──────┬───────┘
                                                   │
                      ┌────────────────────────────┼────────────────────────┐
                      │                            ▼                        │
                      │  ┌─────────────────────────────────────────────┐   │
                      │  │            FEEDBACK COLLECTION               │   │
                      │  │                                              │   │
                      │  │  User Actions:                               │   │
                      │  │  • 👍 Correct detection                      │   │
                      │  │  • 👎 Wrong detection (false positive)       │   │
                      │  │  • 🚨 Missed detection (false negative)      │   │
                      │  │  • ✏️  Category correction                   │   │
                      │  │                                              │   │
                      │  └─────────────────────┬───────────────────────┘   │
                      │                        │                           │
                      │                        ▼                           │
                      │  ┌─────────────────────────────────────────────┐   │
                      │  │           FEEDBACK STORAGE                   │   │
                      │  │                                              │   │
                      │  │  DynamoDB Table: feedback                    │   │
                      │  │  ├── tenant_id (PK)                         │   │
                      │  │  ├── feedback_id (SK)                       │   │
                      │  │  ├── request_id                             │   │
                      │  │  ├── original_input_hash                    │   │
                      │  │  ├── original_decision                      │   │
                      │  │  ├── feedback_type (correct/fp/fn/category) │   │
                      │  │  ├── corrected_category (optional)          │   │
                      │  │  ├── timestamp                              │   │
                      │  │  └── reviewed (bool)                        │   │
                      │  │                                              │   │
                      │  └─────────────────────┬───────────────────────┘   │
                      │                        │                           │
                      └────────────────────────┼───────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OFFLINE TRAINING PIPELINE                            │
│                                                                              │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐            │
│  │   Aggregate    │    │    Quality     │    │   Training     │            │
│  │   Feedback     │───▶│    Filter      │───▶│   Dataset      │            │
│  │   (Weekly)     │    │   (Min 100)    │    │   Generation   │            │
│  └────────────────┘    └────────────────┘    └───────┬────────┘            │
│                                                       │                     │
│                                                       ▼                     │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐            │
│  │   Deploy if    │    │   A/B Test     │    │   Fine-tune    │            │
│  │   Better       │◀───│   Validation   │◀───│   Model        │            │
│  │                │    │                │    │                │            │
│  └────────────────┘    └────────────────┘    └────────────────┘            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Feedback Collection API

New endpoints to add to the API:

```python
# POST /feedback
{
    "request_id": "uuid-from-original-request",
    "feedback_type": "false_positive",  # correct | false_positive | false_negative | category_correction
    "corrected_category": "pii_email",  # optional, for category corrections
    "comment": "This is not PII"        # optional
}

# Response
{
    "feedback_id": "fb_xxx",
    "status": "recorded"
}
```

### 2. Feedback Types

| Type | Meaning | Training Signal |
|------|---------|-----------------|
| `correct` | Detection was accurate | Positive reinforcement |
| `false_positive` | Flagged but shouldn't have been | Remove from positive class |
| `false_negative` | Missed but should have flagged | Add to positive class |
| `category_correction` | Wrong category assigned | Correct label for training |

### 3. Data Storage Schema

```sql
-- DynamoDB: feedback_logs
tenant_id (PK)          -- String: customer identifier
feedback_id (SK)        -- String: unique feedback ID
request_id              -- String: original request reference
input_hash              -- String: SHA256 of input (never store raw input)
original_decision       -- String: ALLOW/BLOCK/REDACT
original_categories     -- List: detected categories
feedback_type           -- String: correct/false_positive/false_negative/category_correction
corrected_category      -- String: (optional) what it should have been
confidence              -- Number: original confidence score
timestamp               -- Number: Unix timestamp
reviewed                -- Boolean: has human reviewed this?
included_in_training    -- Boolean: used in model update?
```

### 4. Training Pipeline Trigger Conditions

DO NOT retrain constantly. Trigger retraining when:

| Condition | Threshold | Rationale |
|-----------|-----------|-----------|
| Feedback volume | ≥500 new samples | Statistical significance |
| Time elapsed | ≥7 days since last train | Prevent staleness |
| False positive rate | >5% of flagged items | Quality degradation |
| False negative reports | >10 per day | Missing threats |
| New category requested | Customer request | Feature expansion |

### 5. Training Data Generation

```python
def generate_training_data(feedback_records):
    """
    Convert feedback into training samples.
    
    CRITICAL: Never include raw user input in training.
    Only use:
    - Public datasets
    - Synthetic data based on patterns
    - Anonymized/generalized examples
    """
    training_samples = []
    
    for record in feedback_records:
        if record.feedback_type == "false_positive":
            # This was flagged but shouldn't have been
            # Pattern: similar structure, but benign
            # DO NOT use actual user text
            training_samples.append({
                "pattern_type": record.original_categories[0],
                "signal": "negative",  # Don't flag this pattern
                "context": record.get("anonymized_context"),
            })
        
        elif record.feedback_type == "false_negative":
            # This should have been flagged
            # Request human review before including
            if record.reviewed:
                training_samples.append({
                    "pattern_type": record.corrected_category,
                    "signal": "positive",  # Do flag this pattern
                    "context": record.get("anonymized_context"),
                })
    
    return training_samples
```

### 6. A/B Testing for Model Updates

```
┌─────────────────────────────────────────────┐
│           A/B TEST ARCHITECTURE             │
│                                             │
│   Incoming Request                          │
│         │                                   │
│         ▼                                   │
│   ┌───────────┐                            │
│   │  Router   │──── 90% ────▶ Model A      │
│   │ (Random)  │               (Current)     │
│   │           │                             │
│   │           │──── 10% ────▶ Model B      │
│   └───────────┘               (Candidate)   │
│                                             │
│   Both results logged, only A returned      │
│   to user until B proves better             │
│                                             │
└─────────────────────────────────────────────┘
```

**Promotion criteria for Model B:**
- False positive rate ≤ Model A
- False negative rate < Model A (improvement)
- Latency within 10% of Model A
- Minimum 1000 shadow requests

### 7. Privacy-Preserving Feedback

**CRITICAL: Never store raw user input**

```python
def store_feedback(request_id, input_text, feedback_type):
    """Store feedback without raw input."""
    
    return {
        "request_id": request_id,
        "input_hash": hashlib.sha256(input_text.encode()).hexdigest(),
        "input_length": len(input_text),
        "input_features": {
            "has_email_pattern": bool(re.search(r'@', input_text)),
            "has_numbers": bool(re.search(r'\d{4,}', input_text)),
            "word_count": len(input_text.split()),
            # Anonymized features only
        },
        "feedback_type": feedback_type,
        "timestamp": time.time(),
    }
```

### 8. Feedback Loop Metrics

Track these to measure loop effectiveness:

| Metric | Formula | Target |
|--------|---------|--------|
| Feedback rate | feedbacks / requests | >0.1% |
| False positive rate | FP feedback / total blocks | <5% |
| False negative rate | FN feedback / total allows | <1% |
| Model improvement | (old_accuracy - new_accuracy) | >0 |
| Time to incorporate | feedback_date → model_deploy | <14 days |

## Implementation Phases

### Phase 1: Feedback Collection (Week 1-2)
- [ ] Add `/feedback` endpoint
- [ ] Create DynamoDB table
- [ ] Add feedback button to any demo UI
- [ ] Store feedback with privacy preservation

### Phase 2: Feedback Dashboard (Week 3-4)
- [ ] Admin view of feedback
- [ ] Manual review queue for false negatives
- [ ] Export for analysis

### Phase 3: Automated Training (Week 5-8)
- [ ] Training data generation script
- [ ] Fine-tuning pipeline (SageMaker or local)
- [ ] A/B testing infrastructure
- [ ] Automated deployment with rollback

### Phase 4: Continuous Improvement (Ongoing)
- [ ] Weekly feedback review
- [ ] Monthly model evaluation
- [ ] Quarterly major updates

## Cost Estimate

| Component | Monthly Cost | Notes |
|-----------|--------------|-------|
| DynamoDB (feedback storage) | $5-20 | Pay per request |
| S3 (training data) | $1-5 | Minimal storage |
| SageMaker training | $50-200 | Only when retraining |
| Lambda (pipeline) | $1-10 | Event-driven |
| **Total** | **$60-240/month** | Scale with usage |

## Security Considerations

1. **Never store raw user input** — only hashes and anonymized features
2. **Feedback requires authentication** — prevent abuse
3. **Rate limit feedback** — max 10 per minute per user
4. **Review before training** — human-in-the-loop for false negatives
5. **Audit trail** — log all model changes
6. **Rollback capability** — instant revert if new model degrades

## Example: Full Feedback Flow

```
1. User sends: "Contact john@acme.com for details"
2. API returns: { action: "redact", categories: ["pii_email"] }
3. User clicks: "👎 Wrong - this is a public business email"
4. System stores:
   {
     request_id: "req_123",
     input_hash: "a1b2c3...",
     feedback_type: "false_positive",
     original_categories: ["pii_email"],
     comment: "public business email"
   }
5. After 500 similar feedbacks about business emails...
6. Training pipeline triggers:
   - Analyzes patterns in false positives
   - Generates rule: "emails with company domains in public context = lower severity"
   - Tests against A/B holdout
   - If better, deploys
7. Future: business emails in public context → ALLOW_WITH_WARNING instead of REDACT
```

## Files to Create

```
restrictor/
├── feedback/
│   ├── __init__.py
│   ├── models.py        # Feedback data models
│   ├── storage.py       # DynamoDB operations
│   └── collector.py     # Feedback collection logic
├── training/
│   ├── __init__.py
│   ├── data_generator.py  # Convert feedback to training data
│   ├── fine_tuner.py      # Model fine-tuning
│   └── ab_tester.py       # A/B testing logic
```

## Next Steps

1. Implement Phase 1 (feedback collection) now
2. Wait for 500+ feedback samples
3. Then implement training pipeline
