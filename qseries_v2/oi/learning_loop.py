"""
OI-010 Oracle Learning Loop

Connects:
Learning Ledger -> Performance Review -> Learning Feedback

This closes Oracle's first measurable learning cycle.
Oracle learns from resolved markets but never executes trades.
"""

from .performance_review import performance_review_engine
from .learning_feedback import learning_feedback_engine


class OracleLearningLoop:

    def run(self, records):
        performance = performance_review_engine.review(records)
        feedback = learning_feedback_engine.feedback(performance)

        return {
            "performance": performance,
            "feedback": feedback,
            "oracle_executes": False,
        }


oracle_learning_loop = OracleLearningLoop()
