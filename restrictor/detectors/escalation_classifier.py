"""
Escalation Classifier - Flags suspicious text for Claude API review.

Strategy:
1. Check for suspicious patterns (veiled threats, hate indicators, etc.)
2. If patterns found → escalate to Claude API
3. If not → allow (fast path)

This saves Claude API costs by only escalating ambiguous cases.
"""

import re
from typing import List
from dataclasses import dataclass


@dataclass
class EscalationResult:
    """Result of escalation check."""
    needs_escalation: bool
    reason: str
    confidence: float
    triggered_patterns: List[str]


class EscalationClassifier:
    """
    Lightweight classifier to determine if text needs premium LLM review.
    
    Goal: High recall (catch potential threats) with reasonable precision.
    """
    
    def __init__(self):
        self.name = "escalation_classifier"
        
        # Patterns that suggest potential threat but aren't explicit
        self.suspicious_patterns = [
            # Veiled threats
            (r'(?i)\b(something|things?)\s+(bad|terrible|awful)\s+(will|might|could)\s+happen', "veiled_threat"),
            (r'(?i)\b(watch|watching)\s+(your|out|yourself)', "surveillance_threat"),
            (r'(?i)\b(know|knows?)\s+where\s+(you|he|she|they)\s+(live|work|stay)', "location_threat"),
            (r'(?i)\bwon\'?t\s+(be\s+)?(around|here|alive)\s+(much\s+)?longer', "death_implication"),
            (r'(?i)\b(days?|time)\s+(is|are)\s+numbered', "death_implication"),
            (r'(?i)\bregret\s+(this|it|what)', "threat_implication"),
            (r'(?i)\b(pay|paying)\s+for\s+(this|what|it)', "revenge_threat"),
            (r'(?i)\bconsequences\b', "threat_implication"),
            (r'(?i)\btaught\s+a\s+lesson', "violence_implication"),
            (r'(?i)\bput\s+(you|him|her|them)\s+in\s+(your|his|her|their)\s+place', "dominance_threat"),
            (r'(?i)\bcoming\s+for\s+(you|him|her|them)', "pursuit_threat"),
            (r'(?i)\bfind\s+(you|him|her|them)', "pursuit_threat"),
            (r'(?i)\bnowhere\s+(to\s+)?(run|hide)', "pursuit_threat"),
            (r'(?i)\bcan\'?t\s+(run|hide|escape)', "pursuit_threat"),
            (r'(?i)\bdealt\s+with', "veiled_threat"),
            (r'(?i)\btake\s+care\s+of\s+(you|him|her|them)', "veiled_threat"),
            (r'(?i)\bneed.{0,10}(dealt|handled|eliminated)', "veiled_threat"),
            (r'(?i)\bsleep\s+with\s+(one\s+)?eye\s+open', "surveillance_threat"),
            
            # Hate speech indicators
            (r'(?i)\b(those|these|them)\s+people\s+(are|is)', "othering_language"),
            (r'(?i)\bdon\'?t\s+belong\s+here', "exclusion_speech"),
            (r'(?i)\bsend\s+(them|him|her)\s+back', "exclusion_speech"),
            (r'(?i)\b(taking|took)\s+over', "invasion_rhetoric"),
            (r'(?i)\b(our|my)\s+(kind|people|country|neighborhood)', "in_group_language"),
            (r'(?i)\bnot\s+like\s+us', "othering_language"),
            (r'(?i)\bruining\s+(our|the|this)', "blame_rhetoric"),
            (r'(?i)\b(problem|issue)\s+with\s+(society|this\s+country)', "blame_rhetoric"),
            (r'(?i)\bkeep\s+(them|him|her)\s+out', "exclusion_speech"),
            (r'(?i)\bstay\s+with\s+(their|your)\s+own', "segregation_speech"),
            (r'(?i)\bgo\s+back\s+to', "exclusion_speech"),
            (r'(?i)\bdon\'?t\s+want\s+(them|their\s+kind)\s+here', "exclusion_speech"),
            (r'(?i)\binfest', "dehumanizing_language"),
            (r'(?i)\bbreed(ing)?\s+like', "dehumanizing_language"),
            (r'(?i)\bvermin|parasites?|cockroach', "dehumanizing_language"),
            
            # Self-harm indicators  
            (r'(?i)\bcan\'?t\s+(go\s+on|take\s+(it|this)\s+anymore)', "distress_signal"),
            (r'(?i)\bnobody\s+(would\s+)?(miss|care)', "isolation_signal"),
            (r'(?i)\bworld\s+(would\s+be\s+)?better\s+without\s+me', "suicidal_ideation"),
            (r'(?i)\bwant\s+(the\s+)?pain\s+to\s+stop', "distress_signal"),
            (r'(?i)\bno\s+point\s+(in\s+)?(living|life|anymore)', "suicidal_ideation"),
            (r'(?i)\bhad\s+enough\s+of\s+(this\s+)?life', "suicidal_ideation"),
            (r'(?i)\b(it|this)\s+will\s+(all\s+)?be\s+over\s+soon', "suicidal_ideation"),
            (r'(?i)\bplanning\s+(my\s+)?(exit|end|way\s+out)', "suicidal_ideation"),
            (r'(?i)\b(this\s+is\s+)?(my\s+)?(last|final)\s+(message|goodbye|note)', "suicidal_ideation"),
            (r'(?i)\bgoodbye\s+(everyone|all|world|forever)', "farewell_message"),
            (r'(?i)\bdon\'?t\s+want\s+to\s+(be\s+here|exist|live)', "suicidal_ideation"),
            (r'(?i)\bwish\s+I\s+(was|were)\s+(dead|never\s+born)', "suicidal_ideation"),
            
            # Grooming indicators
            (r'(?i)\bmature\s+for\s+(your|his|her)\s+age', "grooming_language"),
            (r'(?i)\b(our|my)\s+(little\s+)?secret', "secrecy_pressure"),
            (r'(?i)\bdon\'?t\s+tell\s+(your\s+)?(parents|mom|dad|anyone)', "secrecy_pressure"),
            (r'(?i)\badults?\s+(don\'?t|wouldn\'?t)\s+understand', "isolation_tactic"),
            (r'(?i)\bteach\s+you\s+(things|something\s+special)', "grooming_language"),
            (r'(?i)\bmeet\s+(me\s+)?somewhere\s+private', "isolation_tactic"),
            (r'(?i)\btrust\s+me\s*.{0,10}(different|special)', "manipulation_language"),
            (r'(?i)\bunderstand\s+you\s+better\s+than', "manipulation_language"),
            (r'(?i)\b(parents?|family)\s+(don\'?t|doesn\'?t)\s+(really\s+)?(care|love)', "isolation_tactic"),
            (r'(?i)\bonly\s+I\s+(truly\s+)?(love|understand|care)', "manipulation_language"),
            (r'(?i)\bspecial\s+(relationship|bond|connection)', "grooming_language"),
            
            # Radicalization indicators
            (r'(?i)\bsystem\s+is\s+(your|the|our)\s+enemy', "radicalization_language"),
            (r'(?i)\bviolence\s+is\s+(the\s+)?(only|answer)', "violence_advocacy"),
            (r'(?i)\bthey\s+want\s+to\s+silence\s+us', "persecution_narrative"),
            (r'(?i)\bjoin\s+(the\s+)?(cause|movement|us)\s+or', "coercion_language"),
            (r'(?i)\brevolution\s+is\s+coming', "radicalization_language"),
            (r'(?i)\bfight\s+back\s+by\s+any\s+means', "violence_advocacy"),
            (r'(?i)\bsacrifice\s+is\s+necessary', "extremist_language"),
            (r'(?i)\bends?\s+justify\s+(the\s+)?means', "extremist_language"),
            (r'(?i)\btrue\s+believers?\s+must\s+act', "extremist_language"),
            (r'(?i)\benemies?\s+must\s+be\s+(destroyed|eliminated)', "violence_advocacy"),
            (r'(?i)\bwake\s+up\s+sheeple', "conspiracy_language"),
            (r'(?i)\bopen\s+your\s+eyes', "recruitment_language"),
            
            # Hate/harassment expressions
            (r'(?i)\bi\s+hate\s+(you|him|her|them|everyone)', "hate_expression"),
            (r'(?i)\byou\s+(suck|are\s+worthless|are\s+trash)', "harassment"),
            (r'(?i)\b(loser|idiot|moron|pathetic)\b', "insult"),
            (r'(?i)\bgo\s+(to\s+hell|die)', "hostile_expression"),
            (r'(?i)\bshut\s+up', "hostile_expression"),
            (r'(?i)\b(hate|despise|loathe)\s+(you|him|her|them)', "hate_expression"),
            (r'(?i)\byou\s+deserve\s+to\s+(die|suffer)', "threat"),
            (r'(?i)\bwish\s+(you|he|she|they)\s+(were\s+)?dead', "death_wish"),
            (r'(?i)\bkill\s+yourself', "self_harm_encouragement"),
        ]
        
        # Compile patterns
        self._compiled_patterns = [
            (re.compile(pattern), category)
            for pattern, category in self.suspicious_patterns
        ]
        
        # Load learned patterns from active learning
        self._load_learned_patterns()
        
        # Safe patterns - definitely safe, don't escalate
        self.safe_patterns = [
            r'(?i)^(hi|hello|hey|thanks|thank you|please|okay|ok|yes|no|sure)[\s\.\!\?]*$',
            r'(?i)^what\s+(is|are|was|were|time|day|date)',
            r'(?i)^(how|who|when|where|why)\s+(do|does|did|is|are|can|could|would|should)',
            r'(?i)^(tell|show|explain|describe|help)\s+me',
            r'(?i)\b(weather|recipe|movie|book|song|restaurant|directions)\b',
            r'(?i)\b(beautiful|wonderful|great|amazing|love|enjoy|happy|excited|proud|grateful)\b',
            r'(?i)\b(family|friend|vacation|birthday|weekend|holiday)\b',
        ]
        self._safe_patterns = [re.compile(p) for p in self.safe_patterns]
    
    def _is_clearly_safe(self, text: str) -> bool:
        """Check if text is clearly safe."""
        for pattern in self._safe_patterns:
            if pattern.search(text):
                return True
        return False
    
    def classify(self, text: str) -> EscalationResult:
        """
        Classify if text needs escalation to Claude API.
        
        Returns:
            EscalationResult with needs_escalation flag and details
        """
        # Quick check for clearly safe text
        if self._is_clearly_safe(text):
            return EscalationResult(
                needs_escalation=False,
                reason="clearly_safe",
                confidence=0.95,
                triggered_patterns=[]
            )
        
        # Check for suspicious patterns
        triggered = []
        for pattern, category in self._compiled_patterns:
            if pattern.search(text):
                triggered.append(category)
        
        if triggered:
            confidence = min(0.6 + (len(triggered) * 0.1), 0.95)
            
            return EscalationResult(
                needs_escalation=True,
                reason="suspicious_patterns_detected",
                confidence=confidence,
                triggered_patterns=list(set(triggered))
            )
        
        # No triggers - but still might need review for very short/ambiguous text
        if len(text.split()) < 5:
            return EscalationResult(
                needs_escalation=False,
                reason="short_text_no_patterns",
                confidence=0.8,
                triggered_patterns=[]
            )
        
        return EscalationResult(
            needs_escalation=False,
            reason="no_suspicious_patterns",
            confidence=0.7,
            triggered_patterns=[]
        )


    def _load_learned_patterns(self):
        """Load patterns from active learning."""
        try:
            from ..training.active_learner import ActiveLearner
            learner = ActiveLearner()
            learned = learner.get_learned_patterns()
            
            if learned:
                for pattern, name in learned:
                    try:
                        compiled = re.compile(pattern)
                        self.suspicious_patterns.append((compiled, name))
                    except re.error as e:
                        logger.warning(f"Invalid learned pattern {name}: {e}")
                
                logger.info(f"Loaded {len(learned)} learned patterns")
        except Exception as e:
            logger.warning(f"Could not load learned patterns: {e}")
    
    def reload_patterns(self):
        """Reload all patterns including learned ones."""
        # Re-initialize base patterns
        self.__init__()
