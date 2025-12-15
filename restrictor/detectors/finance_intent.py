"""
Finance Intent Detector - Detects trading signals, insider info, investment advice.

This is NOVEL and hard to copy - requires domain expertise.

Detects:
- Trading intent (buy/sell recommendations)
- Potential insider information
- Unregistered investment advice
- Loan/credit discussions
"""

import re
from typing import List, Dict, Tuple

from ..models import Detection, Category, Severity


# Stock symbols - NSE/BSE top stocks
STOCK_SYMBOLS = {
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR',
    'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'LT', 'AXISBANK',
    'ASIANPAINT', 'MARUTI', 'TITAN', 'SUNPHARMA', 'BAJFINANCE',
    'WIPRO', 'HCLTECH', 'ULTRACEMCO', 'ONGC', 'NTPC', 'POWERGRID',
    'TATAMOTORS', 'TATASTEEL', 'JSWSTEEL', 'ADANIENT', 'ADANIPORTS',
    'BAJAJFINSV', 'TECHM', 'INDUSINDBK', 'HINDALCO', 'COALINDIA',
    'NIFTY', 'BANKNIFTY', 'SENSEX', 'FINNIFTY',
}

# Index names
INDEX_NAMES = {'NIFTY', 'SENSEX', 'BANKNIFTY', 'NIFTY50', 'FINNIFTY', 'MIDCAP'}

FINANCE_INTENT_PATTERNS: Dict[Category, List[Tuple[str, str, float]]] = {
    
    Category.FINANCE_TRADING_INTENT: [
        # Direct buy/sell recommendations
        (r'(?i)\b(buy|sell|short|long)\s+(RELIANCE|TCS|HDFCBANK|INFY|ICICIBANK|SBIN|BHARTIARTL|KOTAKBANK|AXISBANK|TATAMOTORS|TATASTEEL|WIPRO|HCLTECH|NIFTY|BANKNIFTY|SENSEX)\b', 
         "Trading recommendation detected", 0.95),
        
        # Price targets
        (r'(?i)\b(target|tp|sl|stoploss|stop.?loss)\s*[:=]?\s*(?:rs\.?|₹|inr)?\s*\d+', 
         "Price target/stoploss detected", 0.90),
        
        # Entry/exit signals
        (r'(?i)\b(entry|exit|book\s*profit|add\s*more|accumulate)\s+(?:at|@|near)?\s*(?:rs\.?|₹)?\s*\d+', 
         "Entry/exit signal detected", 0.90),
        
        # Options trading
        (r'(?i)\b(call|put)\s*\d+\s*(ce|pe|strike)', 
         "Options trading signal detected", 0.95),
        (r'(?i)\b\d+\s*(ce|pe)\s+(buy|sell)', 
         "Options trading signal detected", 0.95),
        
        # Generic trading language with stocks
        (r'(?i)\b(going\s+(?:up|down)|bullish|bearish|breakout|breakdown)\s+(?:on|in|for)?\s*(RELIANCE|TCS|HDFCBANK|INFY|NIFTY|BANKNIFTY)', 
         "Market prediction detected", 0.85),
    ],
    
    Category.FINANCE_INSIDER_INFO: [
        # Results/earnings before announcement
        (r'(?i)\b(results?|earnings?|quarter(?:ly)?)\s+(?:will\s+be|expected|likely)\s+(good|bad|strong|weak|better|worse)', 
         "Potential insider info - results prediction", 0.80),
        
        # Merger/acquisition hints
        (r'(?i)\b(merger|acquisition|takeover|buyout)\s+(?:is\s+)?(?:coming|likely|expected|happening)', 
         "Potential insider info - M&A", 0.85),
        
        # Board meeting hints
        (r'(?i)\b(board\s+meeting|dividend|bonus|split)\s+(?:will|expected|likely|coming)', 
         "Potential insider info - corporate action", 0.80),
        
        # Confidential/not public
        (r'(?i)\b(confidential|not\s+(?:yet\s+)?(?:public|announced)|inside\s+info|tip\s+from)', 
         "Potential insider information language", 0.90),
        
        # "I heard" patterns
        (r'(?i)\b(heard\s+from|source\s+(?:says?|told)|reliable\s+info)\b', 
         "Unverified source claim", 0.75),
    ],
    
    Category.FINANCE_INVESTMENT_ADVICE: [
        # Guaranteed returns
        (r'(?i)\b(guaranteed|assured|definite|sure\s*shot)\s+(?:returns?|profit|gains?)', 
         "Guaranteed returns claim (likely unregistered advice)", 0.95),
        
        # Percentage promises
        (r'(?i)\b(\d+\s*%|double|triple)\s+(?:returns?|profit|in\s+\d+\s+(?:days?|weeks?|months?))', 
         "Return promise detected", 0.90),
        
        # Advisory language
        (r'(?i)\b(invest\s+(?:now|today|immediately)|don\'?t\s+miss|last\s+chance|urgent\s+buy)', 
         "Urgent investment advice", 0.85),
        
        # SEBI disclaimer absence indicators
        (r'(?i)\b(not\s+sebi|no\s+sebi|without\s+sebi)\s+(?:registered|registration)', 
         "Unregistered advisor indication", 0.95),
    ],
    
    Category.FINANCE_LOAN_DISCUSSION: [
        # Loan amount discussions
        (r'(?i)\b(loan|emi|credit|borrow)\s+(?:of|for|amount)?\s*(?:rs\.?|₹|inr)?\s*\d+(?:\s*(?:lakh|lac|crore|cr|k|L))?\b', 
         "Loan amount discussion", 0.85),
        
        # Interest rate discussions
        (r'(?i)\b(interest\s+rate|roi|rate\s+of\s+interest)\s*[:=]?\s*\d+(?:\.\d+)?\s*%', 
         "Interest rate discussion", 0.80),
        
        # Loan approval
        (r'(?i)\b(loan\s+(?:approved|sanctioned|disbursed)|sanction\s+letter)', 
         "Loan approval discussion", 0.85),
        
        # Credit score
        (r'(?i)\b(cibil|credit\s*score|bureau\s*score)\s*[:=]?\s*\d{3}', 
         "Credit score detected", 0.90),
    ],
}


class FinanceIntentDetector:
    """
    Detect finance-related intents that may violate compliance.
    
    This is specialized for Indian financial markets and regulations:
    - SEBI guidelines on investment advice
    - Insider trading regulations
    - RBI guidelines on loan discussions
    """
    
    def __init__(self):
        self.name = "finance_intent"
        self._compiled_patterns: Dict[Category, List[Tuple[re.Pattern, str, float]]] = {}
        
        for category, patterns in FINANCE_INTENT_PATTERNS.items():
            self._compiled_patterns[category] = [
                (re.compile(pattern), explanation, confidence)
                for pattern, explanation, confidence in patterns
            ]
        
        # Build stock symbol pattern dynamically
        symbols_pattern = '|'.join(STOCK_SYMBOLS)
        self._stock_pattern = re.compile(rf'\b({symbols_pattern})\b', re.IGNORECASE)
    
    def detect(self, text: str) -> List[Detection]:
        detections = []
        
        for category, patterns in self._compiled_patterns.items():
            for pattern, explanation, confidence in patterns:
                for match in pattern.finditer(text):
                    matched_text = match.group(0)
                    
                    # Determine severity based on category
                    if category == Category.FINANCE_INSIDER_INFO:
                        severity = Severity.CRITICAL
                    elif category == Category.FINANCE_TRADING_INTENT:
                        severity = Severity.HIGH
                    elif category == Category.FINANCE_INVESTMENT_ADVICE:
                        severity = Severity.HIGH
                    else:
                        severity = Severity.MEDIUM
                    
                    detections.append(Detection(
                        category=category,
                        severity=severity,
                        confidence=confidence,
                        matched_text=matched_text,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        explanation=explanation,
                        detector=self.name
                    ))
        
        # Deduplicate
        seen = set()
        unique = []
        for d in detections:
            key = (d.category, d.matched_text.lower())
            if key not in seen:
                seen.add(key)
                unique.append(d)
        
        return unique
    
    def has_stock_mention(self, text: str) -> bool:
        """Check if text mentions any stock symbols."""
        return bool(self._stock_pattern.search(text))
