from app.worker import call_external_service_safely, service_breaker
import pybreaker
import time

def verify_resiliency():
    print("Starting Resiliency Verification...")
    
    # 1. Reset Breaker
    service_breaker.close()
    print(f"Breaker State: {service_breaker.current_state}")

    # 2. Test Success (hopefully, it's random but we can try)
    print("\n[Test] Attempting calls (Random Failures expected, should retry)...")
    try:
        # We run a loop to see retries in action (logs will show in worker, but here we just see result or exception)
        # Note: worker logs to DB/Standard out. Here we just see if function returns or raises.
        for i in range(5):
            try:
                result = call_external_service_safely([], {})
                print(f"Call {i+1}: Success ({result['external_id']})")
            except Exception as e:
                print(f"Call {i+1}: Failed with {e}")
    except Exception as e:
        print(f"Outer Exception: {e}")

    # 3. Force Open Circuit (Simulate Outage)
    print("\n[Test] Forcing repeated failures to trip breaker...")
    # We will manually modify the failure rate of the mock service to 100%
    from app.worker import mock_service
    mock_service.failure_rate = 1.0
    
    # Trip it
    try:
        for i in range(10):
            try:
                call_external_service_safely([], {})
                print(f"Trip Attempt {i+1}: Unexpected Success")
            except pybreaker.CircuitBreakerError:
                print(f"Trip Attempt {i+1}: Circuit Breaker Open! (Expected)")
                break
            except Exception as e:
                print(f"Trip Attempt {i+1}: Failed (Retrying...) : {e}")
    except Exception as e:
        print(f"Loop Exception: {e}")

    # 4. Verify Open State
    if service_breaker.current_state == "open":
        print("\nSUCCESS: Circuit Breaker is OPEN.")
    else:
        print(f"\nFAILURE: Circuit Breaker is {service_breaker.current_state} (Expected 'open')")

if __name__ == "__main__":
    verify_resiliency()
