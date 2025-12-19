"""
Finance Intent Detector - Detects trading intent, insider info, investment advice.
"""

import re
from typing import List, Tuple

from ..models import Category, Detection, Severity

# Stock symbols
STOCK_SYMBOLS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN', 'BHARTIARTL',
    'KOTAKBANK', 'AXISBANK', 'TATAMOTORS', 'WIPRO', 'MARUTI', 'TATASTEEL',
    'ADANIPORTS', 'POWERGRID', 'NTPC', 'SUNPHARMA', 'ULTRACEMCO', 'TECHM',
    'HINDUNILVR', 'BAJFINANCE', 'ASIANPAINT', 'NIFTY', 'BANKNIFTY', 'SENSEX'
]

STOCK_PATTERN = '|'.join(STOCK_SYMBOLS)

FINANCE_PATTERNS: List[Tuple[str, Category, Severity, str]] = [
    # Trading intent - buy/sell recommendations
    (rf'(?i)\b(buy|sell|short|long|accumulate)\s+({STOCK_PATTERN})',
     Category.FINANCE_TRADING_INTENT, Severity.HIGH, "Trading recommendation detected"),

    (rf'(?i)\b({STOCK_PATTERN})\s+(is\s+)?(very\s+)?(bullish|bearish|breaking|breakout)',
     Category.FINANCE_TRADING_INTENT, Severity.HIGH, "Market analysis with stock"),

    (rf'(?i)\b({STOCK_PATTERN})\s+.{{0,20}}(target|tp|sl|stoploss)',
     Category.FINANCE_TRADING_INTENT, Severity.HIGH, "Price target detected"),

    (r'(?i)\b(entry|exit|book\s+profit)\s*(at|@)?\s*₹?\d+',
     Category.FINANCE_TRADING_INTENT, Severity.HIGH, "Entry/exit signal detected"),

    (rf'(?i)\b({STOCK_PATTERN})\s+\d+\s*(CE|PE|call|put)',
     Category.FINANCE_TRADING_INTENT, Severity.HIGH, "Options trading detected"),

    (rf'(?i)\b({STOCK_PATTERN})\s+(going|headed|will\s+go)\s+(to|up|down)',
     Category.FINANCE_TRADING_INTENT, Severity.HIGH, "Price prediction detected"),

    (rf'(?i)\bbook\s+profit\s+(in\s+)?({STOCK_PATTERN})',
     Category.FINANCE_TRADING_INTENT, Severity.HIGH, "Profit booking recommendation"),

    (rf'(?i)\baccumulate\s+({STOCK_PATTERN})',
     Category.FINANCE_TRADING_INTENT, Severity.HIGH, "Accumulation recommendation"),

    # Insider info
    (r'(?i)\b(results?|earnings?)\s+(will\s+be|are|expected)\s+(good|bad|strong|weak|positive|negative)',
     Category.FINANCE_INSIDER_INFO, Severity.CRITICAL, "Insider info: Results prediction"),

    (r'(?i)\b(merger|acquisition|buyback|takeover)\s+(is\s+)?(coming|likely|expected|happening)',
     Category.FINANCE_INSIDER_INFO, Severity.CRITICAL, "Insider info: M&A"),

    (r'(?i)\bsource\s+(told|says?|informed)',
     Category.FINANCE_INSIDER_INFO, Severity.CRITICAL, "Insider info: Unverified source"),

    (r'(?i)\b(confidential|private|inside|insider)\s+(info|information|tip)',
     Category.FINANCE_INSIDER_INFO, Severity.CRITICAL, "Insider info: Confidential"),

    (r'(?i)\b(board\s+meeting|dividend|bonus|stock\s+split)\s+(tomorrow|expected|coming)',
     Category.FINANCE_INSIDER_INFO, Severity.CRITICAL, "Insider info: Corporate action"),

    (r'(?i)\bnot\s+(yet\s+)?public',
     Category.FINANCE_INSIDER_INFO, Severity.CRITICAL, "Insider info: Non-public"),

    (r'(?i)\bheard\s+from\s+(management|source|insider)',
     Category.FINANCE_INSIDER_INFO, Severity.CRITICAL, "Insider info: Management source"),

    (r'(?i)\breliable\s+source\s+says',
     Category.FINANCE_INSIDER_INFO, Severity.CRITICAL, "Insider info: Reliable source claim"),

    (r'(?i)\btip\s+from\s+insider',
     Category.FINANCE_INSIDER_INFO, Severity.CRITICAL, "Insider info: Insider tip"),

    (r'(?i)\bprivate\s+information',
     Category.FINANCE_INSIDER_INFO, Severity.CRITICAL, "Insider info: Private information"),

    # Investment advice
    (r'(?i)\b(guaranteed|assured)\s+.{0,20}(returns?|profit)',
     Category.FINANCE_INVESTMENT_ADVICE, Severity.HIGH, "Investment advice: Guaranteed returns"),

    (r'(?i)\b(double|triple)\s+(your\s+)?money\s+(in\s+)?\d+\s*(months?|weeks?|days?|years?)',
     Category.FINANCE_INVESTMENT_ADVICE, Severity.HIGH, "Investment advice: Unrealistic returns"),

    (r'(?i)\binvest\s+now\s+(for|and)',
     Category.FINANCE_INVESTMENT_ADVICE, Severity.HIGH, "Investment advice: Urgency"),

    (r'(?i)\b\d+%\s+returns?\s+(in|within)\s+\d+',
     Category.FINANCE_INVESTMENT_ADVICE, Severity.HIGH, "Investment advice: Return promise"),

    # Loan discussion
    (r'(?i)\bloan\s+(of\s+)?(rs\.?|₹|inr)?\s*\d+\s*(lakh|crore|k)?',
     Category.FINANCE_LOAN_DISCUSSION, Severity.MEDIUM, "Loan discussion: Amount"),

    (r'(?i)\b(emi|installment)\s+(will\s+be|is|of)\s*(rs\.?|₹)?\s*\d+',
     Category.FINANCE_LOAN_DISCUSSION, Severity.MEDIUM, "Loan discussion: EMI"),

    (r'(?i)\b(interest\s+rate|rate\s+of\s+interest)\s+(is|at|of)\s*\d+\.?\d*\s*%',
     Category.FINANCE_LOAN_DISCUSSION, Severity.MEDIUM, "Loan discussion: Interest rate"),
]


class FinanceIntentDetector:
    """Detect finance-related intent and potential compliance issues."""

    def __init__(self):
        self.name = "finance_intent"
        self._patterns = [
            (re.compile(pattern), category, severity, explanation)
            for pattern, category, severity, explanation in FINANCE_PATTERNS
        ]

    def detect(self, text: str) -> List[Detection]:
        """Detect finance intent in text."""
        detections = []

        for pattern, category, severity, explanation in self._patterns:
            match = pattern.search(text)
            if match:
                detections.append(Detection(
                    category=category,
                    severity=severity,
                    confidence=0.90,
                    matched_text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    explanation=explanation,
                    detector=self.name
                ))

        # Deduplicate by category
        seen = set()
        unique = []
        for d in sorted(detections, key=lambda x: x.severity.value, reverse=True):
            if d.category not in seen:
                seen.add(d.category)
                unique.append(d)

        return unique
