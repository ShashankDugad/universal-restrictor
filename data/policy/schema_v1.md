# Universal Restrictor - Data Schema v1.0

## JSONL Format

Each line in the dataset is a JSON object with this structure:

```json
{
  "id": "uuid-v4",
  "text": "the actual message content",
  "lang": "en|hi|hinglish",
  "script": "latin|devanagari|mixed",
  
  "labels": {
    "decision": "ALLOW|WARN|BLOCK",
    "decision_code": 0|1|2,
    "category": "safe|harassment|hate_speech|threat|violence|sexual|self_harm|fraud_or_scam|other",
    "category_code": 0-8,
    "severity": 0-4,
    "targeted": true|false,
    "contains_profanity": true|false
  },
  
  "metadata": {
    "source": "gold|youtube|reddit|synthetic|consent_log",
    "domain": "finance|general",
    "created_at": "2025-02-16T00:00:00Z",
    "annotator": "human|claude|claude+human"
  },
  
  "annotation": {
    "claude_proposal": {
      "decision": "ALLOW|WARN|BLOCK",
      "category": "...",
      "confidence": 0.0-1.0,
      "rationale": "short explanation"
    },
    "human_verified": true|false,
    "human_modified": true|false,
    "notes": "optional annotator notes"
  }
}
```

---

## Field Definitions

### Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Unique identifier (UUID v4) |
| `text` | string | ✅ | The message content (5-500 chars) |
| `lang` | enum | ✅ | Language: `en`, `hi`, `hinglish` |
| `script` | enum | ✅ | Script: `latin`, `devanagari`, `mixed` |

### Label Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `decision` | enum | ✅ | `ALLOW`, `WARN`, `BLOCK` |
| `decision_code` | int | ✅ | 0=ALLOW, 1=WARN, 2=BLOCK |
| `category` | enum | ✅ | See category list |
| `category_code` | int | ✅ | 0-8 |
| `severity` | int | ✅ | 0-4 |
| `targeted` | bool | ✅ | Is it directed at a person? |
| `contains_profanity` | bool | ✅ | Contains profanity/slurs? |

### Category Codes

| Code | Category |
|------|----------|
| 0 | harassment |
| 1 | hate_speech |
| 2 | threat |
| 3 | violence |
| 4 | sexual |
| 5 | self_harm |
| 6 | fraud_or_scam |
| 7 | other |
| 8 | safe |

### Metadata Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | enum | ✅ | Where data came from |
| `domain` | enum | ❌ | `finance`, `general` |
| `created_at` | ISO datetime | ✅ | When created |
| `annotator` | enum | ✅ | Who labeled it |

### Annotation Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `claude_proposal` | object | ❌ | Claude's suggested label |
| `human_verified` | bool | ✅ | Was it reviewed by human? |
| `human_modified` | bool | ❌ | Did human change Claude's label? |
| `notes` | string | ❌ | Annotator notes |

---

## Example Records

### ALLOW Example
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "text": "My payment is stuck, please help",
  "lang": "en",
  "script": "latin",
  "labels": {
    "decision": "ALLOW",
    "decision_code": 0,
    "category": "safe",
    "category_code": 8,
    "severity": 0,
    "targeted": false,
    "contains_profanity": false
  },
  "metadata": {
    "source": "gold",
    "domain": "finance",
    "created_at": "2025-02-16T10:00:00Z",
    "annotator": "human"
  },
  "annotation": {
    "human_verified": true,
    "notes": "Standard customer support query"
  }
}
```

### WARN Example
```json
{
  "id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
  "text": "WTF is wrong with your service",
  "lang": "en",
  "script": "latin",
  "labels": {
    "decision": "WARN",
    "decision_code": 1,
    "category": "harassment",
    "category_code": 0,
    "severity": 1,
    "targeted": false,
    "contains_profanity": true
  },
  "metadata": {
    "source": "youtube",
    "domain": "general",
    "created_at": "2025-02-16T10:00:00Z",
    "annotator": "claude+human"
  },
  "annotation": {
    "claude_proposal": {
      "decision": "WARN",
      "category": "harassment",
      "confidence": 0.85,
      "rationale": "Profanity but not directed at person"
    },
    "human_verified": true,
    "human_modified": false
  }
}
```

### BLOCK Example
```json
{
  "id": "c3d4e5f6-a7b8-9012-cdef-345678901234",
  "text": "Tu chutiya hai BC",
  "lang": "hinglish",
  "script": "latin",
  "labels": {
    "decision": "BLOCK",
    "decision_code": 2,
    "category": "harassment",
    "category_code": 0,
    "severity": 4,
    "targeted": true,
    "contains_profanity": true
  },
  "metadata": {
    "source": "gold",
    "domain": "general",
    "created_at": "2025-02-16T10:00:00Z",
    "annotator": "human"
  },
  "annotation": {
    "human_verified": true,
    "notes": "Severe Hindi slurs, directed"
  }
}
```

---

## Validation Rules

### Text Validation
- Length: 5-500 characters
- Not empty/whitespace only
- UTF-8 encoded

### Label Validation
- If decision=ALLOW → category must be "safe"
- If decision=WARN or BLOCK → category must NOT be "safe"
- Severity must match decision:
  - ALLOW: severity 0-1
  - WARN: severity 1-2
  - BLOCK: severity 3-4

### Language/Script Validation
- lang=hi → script should be devanagari or mixed
- lang=en → script should be latin
- lang=hinglish → script should be latin or mixed

---

## File Naming Convention

```
data/
├── gold/
│   └── gold_v1.jsonl              # Hand-verified gold set
├── datasets/
│   └── v1/
│       ├── train.jsonl            # Training set
│       ├── val.jsonl              # Validation set
│       ├── test.jsonl             # Test set
│       └── challenge.jsonl        # Hard cases
└── raw/
    ├── youtube_raw.jsonl          # Before annotation
    └── reddit_raw.jsonl
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-02-16 | Initial schema |
