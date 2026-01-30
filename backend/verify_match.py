import sys
import logging
from pages.helper.match_algo import match_one_against_all

# Configure logging to verify execution
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("verify_output.txt", mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)

if __name__ == "__main__":
    case_id = "ec63b015-a96e-44ba-958a-2698e03de615"
    print(f"--- TRIGGERING MANUAL MATCH FOR {case_id} ---")
    
    # Try treating it as a Public Case first (most likely scenario for user report)
    print("\nAttempting as PUBLIC case...")
    result = match_one_against_all(case_id, case_type="public")
    print(f"Result: {result}")
    
    if result.get("message") == "Case not found":
        print("\nAttempting as REGISTERED case...")
        result = match_one_against_all(case_id, case_type="registered")
        print(f"Result: {result}")
