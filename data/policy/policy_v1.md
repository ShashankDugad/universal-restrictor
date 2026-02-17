# Universal Restrictor - Content Moderation Policy v1.0

**Version:** 1.0  
**Date:** 2025-02-16  
**Author:** Shashank Dugad  
**Status:** Active

---

## 1. Purpose

This document defines the labeling standards for the Universal Restrictor content moderation system. All annotators (human or AI-assisted) must follow these guidelines to ensure consistent, high-quality labels.

---

## 2. Decision Levels

Every text sample receives ONE of three decisions:

| Decision | Code | Description | Action |
|----------|------|-------------|--------|
| **ALLOW** | 0 | Safe content, no issues | Pass through |
| **WARN** | 1 | Mild issues, flag but don't block | Flag + pass |
| **BLOCK** | 2 | Severe issues, must stop | Block + log |

### 2.1 ALLOW (Safe)

Content is ALLOW if it:
- Is neutral, polite, or constructive
- Contains no profanity, slurs, or hostile language
- Expresses frustration WITHOUT targeting a person
- Discusses sensitive topics factually/educationally

**Examples:**
```
✅ "My payment failed, please help"
✅ "I hate this app" (frustration, not directed at person)
✅ "This policy is unfair" (opinion, not attack)
✅ "kya haal hai bhai" (casual greeting)
✅ "yaar bahut mushkil hai ye" (frustration, no target)
```

### 2.2 WARN (Mild Issues)

Content is WARN if it:
- Contains profanity NOT directed at a person
- Has hostile/rude tone but no severe content
- Uses mild insults or name-calling
- Is borderline but not clearly harmful

**Examples:**
```
⚠️ "This is bullshit" (profanity, not directed)
⚠️ "WTF is wrong with this app" (frustration + profanity)
⚠️ "You guys are useless" (mild, directed at company)
⚠️ "Sala yeh kya bakwas hai" (mild Hindi frustration)
⚠️ "Are you stupid or what" (mild insult, question form)
```

### 2.3 BLOCK (Severe)

Content is BLOCK if it:
- Contains slurs or hate speech
- Threatens violence or harm
- Is severe harassment directed at a person
- Contains sexual content or exploitation
- Attempts fraud/scam/social engineering
- Encourages self-harm

**Examples:**
```
🚫 "I will kill you" (threat)
🚫 "bhenchod/madarchod" (severe Hindi slurs)
🚫 "You Muslims are terrorists" (hate speech)
🚫 "Send me your OTP for refund" (fraud attempt)
🚫 "I want to end my life" (self-harm)
🚫 "tujhe maar dunga" (Hindi threat)
🚫 "You worthless piece of shit, die" (severe + threat)
```

---

## 3. Categories

If decision is WARN or BLOCK, assign ONE category:

| Category | Code | Description |
|----------|------|-------------|
| **harassment** | 0 | Personal attacks, insults, bullying directed at individuals |
| **hate_speech** | 1 | Slurs, discrimination, attacks on protected groups |
| **threat** | 2 | Explicit or implied threats of violence/harm |
| **violence** | 3 | Glorification or incitement of violence |
| **sexual** | 4 | Explicit sexual content, harassment |
| **self_harm** | 5 | Suicide, self-injury content |
| **fraud_or_scam** | 6 | Phishing, social engineering, credential theft |
| **other** | 7 | Toxic but doesn't fit above categories |

If decision is ALLOW, category = **safe** (code: 8)

### 3.1 Category Definitions

#### harassment
Personal attacks on individuals. The target is a SPECIFIC PERSON.

```
🚫 "You are an idiot" (directed at person)
🚫 "Nobody likes you" (targeted)
🚫 "Tu toh chutiya hai" (Hindi, directed)
⚠️ "Your support team is useless" (directed at group/company = milder)
```

#### hate_speech
Attacks on GROUPS based on identity (race, religion, gender, nationality, caste, etc.)

```
🚫 "All Muslims are terrorists"
🚫 "Go back to Pakistan"
🚫 "These Biharis are all thieves"
🚫 "Women shouldn't work in finance"
```

#### threat
Explicit or implied threats of physical harm.

```
🚫 "I will find you and kill you"
🚫 "Tera address nikal, dekhta hoon"
🚫 "You better watch your back"
🚫 "Something bad will happen to you"
```

#### violence
Glorifying, encouraging, or describing violence (not a direct threat).

```
🚫 "People like him should be beaten"
🚫 "I hope someone shoots them"
🚫 "Isko maaro saale ko"
```

#### sexual
Explicit sexual content or sexual harassment.

```
🚫 "Send me nudes"
🚫 Explicit descriptions of sexual acts
🚫 Sexual threats or coercion
```

#### self_harm
Content about suicide or self-injury.

```
🚫 "I want to kill myself"
🚫 "Life is not worth living"
🚫 "How to end it all"
⚠️ "I'm feeling really depressed" (concerning but not explicit)
```

#### fraud_or_scam
Attempts to steal credentials, money, or personal information.

```
🚫 "Sir please share OTP for refund"
🚫 "Send ₹500 to unlock your account"
🚫 "Click this link to verify your UPI"
🚫 "I'm from bank, need your card number"
```

---

## 4. Severity Scale

Assign severity 0-4 for granularity:

| Severity | Description | Typical Decision |
|----------|-------------|------------------|
| **0** | Clean, neutral, safe | ALLOW |
| **1** | Mildly rude, profanity not directed | ALLOW or WARN |
| **2** | Directed insults, hostile tone | WARN |
| **3** | Slurs, implied threats, hate | BLOCK |
| **4** | Explicit threats, severe hate, violence | BLOCK |

---

## 5. Language-Specific Guidelines

### 5.1 Hindi Slur Severity

| Tier | Slurs | Severity | Decision |
|------|-------|----------|----------|
| **Tier 1 (Severe)** | madarchod, bhenchod, bhosdike | 4 | BLOCK |
| **Tier 2 (Strong)** | chutiya, gandu, randi | 3-4 | BLOCK |
| **Tier 3 (Moderate)** | sala, kamina, gadha, ullu | 2 | WARN |
| **Tier 4 (Mild)** | pagal, bewakoof | 1-2 | ALLOW or WARN |

### 5.2 Hinglish (Code-Mixed)

Hinglish combines Hindi and English. Apply the stricter interpretation.

```
🚫 "You bloody chutiya" → BLOCK (has severe slur)
⚠️ "Yaar this is so frustrating" → ALLOW (no slur)
🚫 "BC tu pagal hai kya" → BLOCK (BC = bhenchod)
```

### 5.3 Abbreviations & Obfuscation

Common obfuscations should be treated as the full word:

| Obfuscation | Meaning | Decision |
|-------------|---------|----------|
| BC, B.C. | bhenchod | BLOCK |
| MC, M.C. | madarchod | BLOCK |
| f*ck, f**k | fuck | Context-dependent |
| b!tch, b1tch | bitch | Context-dependent |
| ch*tiya | chutiya | BLOCK |

---

## 6. Edge Cases & Decision Rules

### 6.1 Frustration vs. Attack

| Text | Decision | Why |
|------|----------|-----|
| "I hate this app" | ALLOW | Frustration at thing, not person |
| "I hate you" | WARN/BLOCK | Directed at person |
| "This is so frustrating" | ALLOW | No target |
| "You frustrate me" | WARN | Directed but mild |

### 6.2 Quotes & Reporting

If someone is QUOTING or REPORTING toxic content:

```
"He called me a 'chutiya'" → WARN (reporting, not attacking)
"The message said 'I'll kill you'" → WARN (reporting threat)
```

### 6.3 Playful/Friendly Banter

Context matters. Friends joking ≠ harassment.

```
"haha tu pagal hai yaar 😂" → ALLOW (friendly, emoji indicates tone)
"birthday boy ki party kab hai BC" → WARN (casual BC among friends)
"oye sale kahan hai tu" → ALLOW (friendly greeting pattern)
```

**Default rule:** If uncertain whether playful, lean toward WARN.

### 6.4 News/Educational Content

Factual discussion of violence/hate is usually safe:

```
"The attack killed 50 people" → ALLOW (news)
"Hate speech laws in India" → ALLOW (educational)
"Statistics on domestic violence" → ALLOW (factual)
```

---

## 7. Annotation Process

### 7.1 Decision Flow

```
1. Read the text
2. Ask: Is there ANY harmful content?
   ├── NO → ALLOW (severity 0)
   └── YES → Continue
3. Ask: Is it directed at a person/group?
   ├── NO → Likely WARN (severity 1-2)
   └── YES → Continue
4. Ask: Is it severe? (slurs, threats, hate)
   ├── NO → WARN (severity 2)
   └── YES → BLOCK (severity 3-4)
5. Assign category
6. Add notes if edge case
```

### 7.2 Mandatory Review Triggers

These MUST be reviewed by a senior/second annotator:

- [ ] Profanity + ALLOW label
- [ ] Slur present + WARN label
- [ ] BLOCK decision + confidence < 0.8
- [ ] Annotator marked "uncertain"
- [ ] Text is in Hindi/Hinglish

---

## 8. Examples Bank

### ALLOW Examples (severity 0)

```json
{"text": "My payment is stuck, please help", "decision": "ALLOW", "category": "safe", "severity": 0}
{"text": "When will my refund be processed?", "decision": "ALLOW", "category": "safe", "severity": 0}
{"text": "I don't agree with this policy", "decision": "ALLOW", "category": "safe", "severity": 0}
{"text": "namaste, kaise ho", "decision": "ALLOW", "category": "safe", "severity": 0}
{"text": "yaar bahut mushkil hai yeh problem", "decision": "ALLOW", "category": "safe", "severity": 0}
{"text": "This app is not working properly", "decision": "ALLOW", "category": "safe", "severity": 0}
```

### WARN Examples (severity 1-2)

```json
{"text": "This is complete bullshit", "decision": "WARN", "category": "harassment", "severity": 1}
{"text": "WTF is wrong with your service", "decision": "WARN", "category": "harassment", "severity": 1}
{"text": "You people are useless", "decision": "WARN", "category": "harassment", "severity": 2}
{"text": "Kya bakwas hai yeh", "decision": "WARN", "category": "harassment", "severity": 1}
{"text": "Are you guys even trying?", "decision": "WARN", "category": "harassment", "severity": 1}
```

### BLOCK Examples (severity 3-4)

```json
{"text": "I will kill you", "decision": "BLOCK", "category": "threat", "severity": 4}
{"text": "Tu chutiya hai BC", "decision": "BLOCK", "category": "harassment", "severity": 4}
{"text": "All Muslims should be thrown out", "decision": "BLOCK", "category": "hate_speech", "severity": 4}
{"text": "Send me your OTP for refund", "decision": "BLOCK", "category": "fraud_or_scam", "severity": 3}
{"text": "Tujhe maar dunga saale", "decision": "BLOCK", "category": "threat", "severity": 4}
{"text": "I want to end my life", "decision": "BLOCK", "category": "self_harm", "severity": 4}
```

---

## 9. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-02-16 | Initial release |

---

## 10. Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    QUICK DECISION GUIDE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ALLOW if:                                                  │
│    ✓ No profanity/slurs                                    │
│    ✓ Frustration at THING (not person)                     │
│    ✓ Factual/educational                                   │
│                                                             │
│  WARN if:                                                   │
│    ⚠ Profanity but not directed                            │
│    ⚠ Mild insults                                          │
│    ⚠ Rude tone                                             │
│    ⚠ Uncertain/borderline                                  │
│                                                             │
│  BLOCK if:                                                  │
│    🚫 Slurs (BC, MC, chutiya, etc.)                        │
│    🚫 Threats ("I'll kill you")                            │
│    🚫 Hate speech (attacks on groups)                      │
│    🚫 Fraud attempts (OTP/UPI phishing)                    │
│    🚫 Self-harm                                            │
│                                                             │
│  When uncertain → WARN                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

**End of Policy Document**
