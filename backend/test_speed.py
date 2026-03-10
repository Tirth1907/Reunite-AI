# ============================================================
# SPEED SELF-TEST
# Run after ANY change to video_processor.py or fallback_detector.py
# Usage: python test_speed.py
# Expected: fallback uses opencv, not retinaface
# ============================================================

import sys
import os
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_fallback_detector_import():
    print("[Test 1] Checking fallback_detector.py imports...")
    try:
        from pages.helper.fallback_detector import (
            detect_face_fallback,
            FALLBACK_DETECTOR_BACKEND,
            get_fallback_frame_interval
        )
        assert FALLBACK_DETECTOR_BACKEND == "opencv", (
            f"FAIL: Backend is {FALLBACK_DETECTOR_BACKEND}, "
            f"should be opencv"
        )
        print(f"  PASS: Backend = {FALLBACK_DETECTOR_BACKEND} ✓")
        return True
    except Exception as e:
        print(f"  FAIL: {e} ✗")
        return False


def test_frame_intervals():
    print("[Test 2] Checking fallback frame intervals...")
    try:
        from pages.helper.fallback_detector import get_fallback_frame_interval
        assert get_fallback_frame_interval(60) == 1, "30s should use 1s"
        assert get_fallback_frame_interval(93) == 1, "93s should use 1s"
        assert get_fallback_frame_interval(200) == 2, "200s should use 2s"
        assert get_fallback_frame_interval(400) == 4, "400s should use 4s"
        print("  PASS: All frame intervals correct ✓")
        return True
    except AssertionError as e:
        print(f"  FAIL: {e} ✗")
        return False
    except Exception as e:
        print(f"  FAIL: {e} ✗")
        return False


def test_single_frame_speed():
    print("[Test 3] Testing per-frame processing speed...")
    try:
        from pages.helper.fallback_detector import detect_face_fallback
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        start = time.time()
        for _ in range(5):
            detect_face_fallback(blank_frame)
        elapsed = (time.time() - start) / 5 * 1000
        print(f"  Per-frame time: {elapsed:.0f}ms")
        if elapsed < 200:
            print(f"  PASS: Under 200ms per frame ✓")
            return True
        else:
            print(f"  WARN: Over 200ms — may be using retinaface ✗")
            return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def test_no_retry_loops():
    print("[Test 4] Checking for retry loops in fallback_detector.py...")
    try:
        detector_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'pages', 'helper', 'fallback_detector.py'
        )
        with open(detector_path, 'r') as f:
            content = f.read()
        backends_list = 'backends_to_try' in content
        retry_loop = 'for backend in' in content
        if backends_list or retry_loop:
            print("  FAIL: Retry loop detected in fallback_detector.py ✗")
            return False
        print("  PASS: No retry loops found ✓")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def run_all_tests():
    print("=" * 50)
    print("REUNITE AI — SPEED SELF-TEST")
    print("=" * 50)
    results = [
        test_fallback_detector_import(),
        test_frame_intervals(),
        test_single_frame_speed(),
        test_no_retry_loops(),
    ]
    print("\n" + "=" * 50)
    if all(results):
        print("RESULT: ALL SPEED TESTS PASSED ✓")
    else:
        print("RESULT: SPEED TESTS FAILED ✗")
        print("Processing will be slow — fix before deploying.")
    print("=" * 50)
    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
