import time
import random

class MockExternalService:
    """
    Simulates a flaky external API (e.g., Vector DB or OpenAI) 
    that experiences random failures and latency.
    """
    
    def __init__(self, failure_rate: float = 0.3):
        self.failure_rate = failure_rate

    def perform_risky_operation(self, data: list, metadata: dict) -> dict:
        """
        Simulates processing data externally.
        Raises specific exceptions to test retry logic.
        """
        # Simulate network latency
        time.sleep(random.uniform(0.1, 0.5))

        # Simulate random failure
        if random.random() < self.failure_rate:
            # Simulate a transient connection error
            raise ConnectionError("Connection to external service timed out.")

        return {
            "status": "success",
            "processed_count": len(data),
            "external_id": f"ext-{random.randint(1000, 9999)}"
        }
