import sys
import test_registration

with open("wrapper_output.log", "w", encoding="utf-8") as f:
    sys.stdout = f
    sys.stderr = f
    try:
        success = test_registration.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
