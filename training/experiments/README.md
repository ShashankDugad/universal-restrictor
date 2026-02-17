# Experiment Tracking - Universal Restrictor

## Experiment Log

| ID | Date | Model | Dataset | BLOCK Recall | BLOCK Precision | Notes |
|----|------|-------|---------|--------------|-----------------|-------|
| 001 | 2025-02-16 | MuRIL-base | v1 (curated) | - | - | Baseline |

---

## Experiment Template

Copy this for each experiment:

```markdown
## Experiment XXX: [Title]

**Date:** YYYY-MM-DD  
**Status:** Planning | Running | Complete | Failed

### Hypothesis
What are you testing?

### Configuration

| Parameter | Value |
|-----------|-------|
| Base Model | google/muril-base-cased |
| Dataset Version | v1 |
| Train Samples | 12,000 |
| Val Samples | 1,500 |
| Test Samples | 1,500 |
| Epochs | 4 |
| Batch Size | 16 |
| Learning Rate | 2e-5 |
| Class Weights | {ALLOW: 1.0, WARN: 1.5, BLOCK: 2.0} |
| Threshold | 0.5 |

### Results

| Metric | Stage 1 (Decision) | Stage 2 (Category) |
|--------|-------------------|-------------------|
| Accuracy | - | - |
| BLOCK Recall | - | - |
| BLOCK Precision | - | - |
| F1 (weighted) | - | - |

### Confusion Matrix (Stage 1)
```
              Predicted
              ALLOW  WARN  BLOCK
Actual ALLOW   [  ]  [  ]  [  ]
       WARN    [  ]  [  ]  [  ]
       BLOCK   [  ]  [  ]  [  ]
```

### Per-Language Results

| Language | Samples | BLOCK Recall | BLOCK Precision |
|----------|---------|--------------|-----------------|
| English | - | - | - |
| Hindi | - | - | - |
| Hinglish | - | - | - |

### Training Curves
[Link to W&B / TensorBoard]

### Analysis
What worked? What didn't? Why?

### Next Steps
What to try next based on results?
```

---

## Current Experiments

### Experiment 001: Baseline MuRIL

**Date:** 2025-02-16  
**Status:** Planning

#### Hypothesis
Establish baseline performance with clean gold-set data before scaling up.

#### Configuration

| Parameter | Value |
|-----------|-------|
| Base Model | google/muril-base-cased |
| Dataset Version | v1 (gold set only) |
| Train Samples | 400 |
| Val Samples | 50 |
| Test Samples | 50 |
| Epochs | 5 |
| Batch Size | 8 |
| Learning Rate | 2e-5 |
| Class Weights | {ALLOW: 1.0, WARN: 1.5, BLOCK: 2.0} |

#### Expected Outcome
- BLOCK Recall > 90% on small clean data
- Validates annotation quality before scaling

---

## Ablation Studies Planned

| ID | Variable | Options to Test |
|----|----------|-----------------|
| A1 | Base Model | MuRIL vs XLM-R vs mBERT |
| A2 | Class Weights | 1.5x vs 2.0x vs 2.5x for BLOCK |
| A3 | Threshold | 0.3 vs 0.4 vs 0.5 |
| A4 | Architecture | 2-stage vs 3-class single |
| A5 | Data Mix | 50/30/20 vs 60/20/20 (EN/Hinglish/Hindi) |

---

## Metrics Tracking

### Primary Metrics (Optimize For)
1. **BLOCK Recall** - Must catch toxic content
2. **BLOCK Precision** - Minimize false positives

### Secondary Metrics (Monitor)
1. WARN Recall/Precision
2. Per-language performance
3. Per-category F1
4. Inference latency

### Evaluation Protocol
1. Train on train.jsonl
2. Tune threshold on val.jsonl
3. Final evaluation on test.jsonl (never tune on this)
4. Report all metrics with confidence intervals

---

## Tools

### Weights & Biases Setup
```python
import wandb

wandb.init(
    project="universal-restrictor",
    config={
        "model": "muril-base-cased",
        "dataset_version": "v1",
        "epochs": 4,
        # ... all hyperparameters
    }
)

# Log metrics
wandb.log({
    "train_loss": loss,
    "val_recall": recall,
    "val_precision": precision,
})
```

### TensorBoard Alternative
```python
from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter('runs/exp_001')
writer.add_scalar('Loss/train', loss, epoch)
writer.add_scalar('Recall/val', recall, epoch)
```

---

## Artifact Management

### Model Checkpoints
```
training/
├── checkpoints/
│   ├── exp_001/
│   │   ├── epoch_1/
│   │   ├── epoch_2/
│   │   └── best/
│   └── exp_002/
```

### Evaluation Results
```
training/
├── results/
│   ├── exp_001_results.json
│   ├── exp_001_confusion_matrix.png
│   └── exp_001_per_language.csv
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-02-16 | Initial setup |
