"""
Active Learning Module - Updates detection patterns from approved feedback.

This module:
1. Reads approved feedback marked "Ready for Training"
2. Analyzes false negatives to extract patterns
3. Updates escalation classifier with new patterns
4. Marks feedback as "included_in_training"
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TrainingResult:
    """Result of a training run."""
    feedback_processed: int
    patterns_added: int
    patterns_skipped: int
    errors: List[str]
    timestamp: str


class ActiveLearner:
    """
    Active learner that updates detection patterns from feedback.

    Supports:
    - False negatives: Adds new escalation patterns
    - False positives: Can adjust confidence thresholds (future)
    - Category corrections: Updates category mappings (future)
    """

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self._client = None
        self._connect()

        # Pattern extraction config
        self.min_pattern_length = 3
        self.max_pattern_length = 50

        # File to store learned patterns
        self.learned_patterns_file = os.path.join(
            os.path.dirname(__file__),
            "..", "detectors", "learned_patterns.json"
        )

    def _connect(self):
        """Connect to Redis."""
        if not self.redis_url:
            logger.warning("No REDIS_URL set for active learner")
            return
        try:
            import redis
            self._client = redis.from_url(self.redis_url)
            self._client.ping()
            logger.info("Active learner connected to Redis")
        except Exception as e:
            logger.error(f"Active learner Redis connection failed: {e}")
            self._client = None

    @property
    def is_connected(self) -> bool:
        if self._client is None:
            return False
        try:
            self._client.ping()
            return True
        except Exception:
            return False

    def get_training_feedback(self) -> List[Dict]:
        """Get approved feedback ready for training."""
        if not self.is_connected:
            return []

        try:
            feedback_ids = self._client.smembers("feedback:all")
            training_data = []

            for fid in feedback_ids:
                fid = fid.decode() if isinstance(fid, bytes) else fid
                data = self._client.get(f"feedback:{fid}")
                if data:
                    record = json.loads(data)
                    # Only get approved feedback not yet trained
                    if record.get("approved") and not record.get("included_in_training"):
                        training_data.append(record)

            logger.info(f"Found {len(training_data)} feedback items ready for training")
            return training_data

        except Exception as e:
            logger.error(f"Failed to get training feedback: {e}")
            return []

    def extract_patterns_from_text(self, text: str, category: str) -> List[Tuple[str, str]]:
        """
        Extract potential patterns from text.

        Returns list of (pattern_regex, pattern_name) tuples.
        """
        patterns = []
        text_lower = text.lower().strip()

        # Skip if too short or too long
        if len(text_lower) < self.min_pattern_length:
            return []
        if len(text_lower) > self.max_pattern_length:
            # Try to extract key phrases
            words = text_lower.split()
            if len(words) >= 2:
                # Take first few significant words
                text_lower = ' '.join(words[:4])

        # Create word-boundary pattern
        escaped = re.escape(text_lower)
        # Replace escaped spaces with flexible whitespace
        pattern = escaped.replace(r'\ ', r'\s+')
        pattern = f"(?i)\\b{pattern}\\b"

        # Generate pattern name from category and text
        safe_name = re.sub(r'[^a-z0-9_]', '_', text_lower[:20])
        pattern_name = f"learned_{category}_{safe_name}"

        patterns.append((pattern, pattern_name))

        return patterns

    def load_learned_patterns(self) -> Dict:
        """Load previously learned patterns."""
        if os.path.exists(self.learned_patterns_file):
            try:
                with open(self.learned_patterns_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load learned patterns: {e}")

        return {
            "patterns": [],
            "metadata": {
                "created": datetime.utcnow().isoformat(),
                "last_updated": None,
                "total_patterns": 0
            }
        }

    def save_learned_patterns(self, data: Dict):
        """Save learned patterns to file."""
        try:
            data["metadata"]["last_updated"] = datetime.utcnow().isoformat()
            data["metadata"]["total_patterns"] = len(data["patterns"])

            with open(self.learned_patterns_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(data['patterns'])} learned patterns")
        except Exception as e:
            logger.error(f"Failed to save learned patterns: {e}")

    def mark_feedback_as_trained(self, feedback_id: str):
        """Mark feedback as included in training."""
        if not self.is_connected:
            return

        try:
            key = f"feedback:{feedback_id}"
            data = self._client.get(key)
            if data:
                record = json.loads(data)
                record["included_in_training"] = True
                record["trained_at"] = datetime.utcnow().isoformat()
                self._client.set(key, json.dumps(record))
                logger.info(f"Marked feedback {feedback_id} as trained")
        except Exception as e:
            logger.error(f"Failed to mark feedback as trained: {e}")

    def run_training(self) -> TrainingResult:
        """
        Run training job to update patterns from feedback.

        Returns TrainingResult with stats.
        """
        result = TrainingResult(
            feedback_processed=0,
            patterns_added=0,
            patterns_skipped=0,
            errors=[],
            timestamp=datetime.utcnow().isoformat()
        )

        # Get feedback ready for training
        feedback_list = self.get_training_feedback()
        if not feedback_list:
            logger.info("No feedback ready for training")
            return result

        # Load existing patterns
        learned_data = self.load_learned_patterns()
        existing_patterns = {p["pattern"] for p in learned_data["patterns"]}

        for feedback in feedback_list:
            try:
                feedback_type = feedback.get("feedback_type")
                feedback_id = feedback.get("feedback_id")

                # Process based on feedback type
                if feedback_type == "false_negative":
                    # User says we missed something - add pattern
                    corrected_category = feedback.get("corrected_category", "unknown")
                    comment = feedback.get("comment", "")

                    # Extract patterns from the comment (user description)
                    if comment:
                        new_patterns = self.extract_patterns_from_text(comment, corrected_category)

                        for pattern, name in new_patterns:
                            if pattern not in existing_patterns:
                                learned_data["patterns"].append({
                                    "pattern": pattern,
                                    "name": name,
                                    "category": corrected_category,
                                    "source_feedback": feedback_id,
                                    "added_at": datetime.utcnow().isoformat()
                                })
                                existing_patterns.add(pattern)
                                result.patterns_added += 1
                                logger.info(f"Added pattern: {name}")
                            else:
                                result.patterns_skipped += 1

                elif feedback_type == "correct":
                    # Positive feedback - could use for confidence boosting (future)
                    pass

                elif feedback_type == "false_positive":
                    # We flagged something incorrectly - could add to whitelist (future)
                    pass

                elif feedback_type == "category_correction":
                    # Wrong category - could update mappings (future)
                    pass

                # Mark as processed
                self.mark_feedback_as_trained(feedback_id)
                result.feedback_processed += 1

            except Exception as e:
                error_msg = f"Error processing feedback {feedback.get('feedback_id')}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        # Save updated patterns
        if result.patterns_added > 0:
            self.save_learned_patterns(learned_data)

        logger.info(f"Training complete: {result.feedback_processed} processed, "
                    f"{result.patterns_added} patterns added")

        return result

    def get_learned_patterns(self) -> List[Tuple[str, str]]:
        """
        Get learned patterns for use by escalation classifier.

        Returns list of (pattern_regex, pattern_name) tuples.
        """
        learned_data = self.load_learned_patterns()
        return [(p["pattern"], p["name"]) for p in learned_data["patterns"]]


def run_training_job():
    """Run training job (can be called from CLI or scheduled)."""
    logger.info("Starting training job...")

    learner = ActiveLearner()
    result = learner.run_training()

    print(f"\n{'='*50}")
    print("Training Job Complete")
    print(f"{'='*50}")
    print(f"Feedback processed: {result.feedback_processed}")
    print(f"Patterns added:     {result.patterns_added}")
    print(f"Patterns skipped:   {result.patterns_skipped}")
    print(f"Errors:             {len(result.errors)}")
    print(f"Timestamp:          {result.timestamp}")

    if result.errors:
        print("\nErrors:")
        for err in result.errors:
            print(f"  - {err}")

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_training_job()
