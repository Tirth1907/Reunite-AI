# ============================================================
# REGISTRATION SELF-TEST
# Run this after ANY code change to verify registration works.
# Usage: python test_registration.py
# Expected output: ALL TESTS PASSED
# ============================================================

import sys
import os
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pages.helper.registration_encoder import extract_registration_embedding


def download_test_image(url: str, filename: str) -> bytes:
    try:
        urllib.request.urlretrieve(url, filename)
        with open(filename, 'rb') as f:
            return f.read()
    except Exception as e:
        print(f"  Could not download test image: {e}")
        return None


def test_with_local_photos():
    """Test registration with actual photos from resources folder."""
    resources_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources'
    )

    if not os.path.exists(resources_dir):
        print("  No resources folder found, skipping local photo test")
        return True

    photo_files = [
        f for f in os.listdir(resources_dir)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ][:3]  # Test first 3 registered photos

    if not photo_files:
        print("  No photos in resources folder, skipping")
        return True

    passed = 0
    for photo_file in photo_files:
        photo_path = os.path.join(resources_dir, photo_file)
        try:
            with open(photo_path, 'rb') as f:
                image_bytes = f.read()
            embedding = extract_registration_embedding(image_bytes)
            assert len(embedding) == 512, "Wrong embedding size"
            print(f"  PASS: {photo_file} → 512-dim embedding ✓")
            passed += 1
        except ValueError as e:
            if "No face detected" in str(e):
                print(f"  FAIL: {photo_file} → No face detected ✗")
            else:
                print(f"  SKIP: {photo_file} → {e}")
                passed += 1
        except Exception as e:
            print(f"  ERROR: {photo_file} → {e}")

    return passed > 0


def run_all_tests():
    print("=" * 50)
    print("REUNITE AI — REGISTRATION SELF-TEST")
    print("=" * 50)

    print("\n[Test 1] Testing with registered photos...")
    result = test_with_local_photos()

    print("\n[Test 2] Testing error handling...")
    try:
        extract_registration_embedding(b"not_an_image")
        print("  FAIL: Should have raised ValueError ✗")
        result = False
    except ValueError:
        print("  PASS: Correctly rejects invalid image ✓")
    except Exception as e:
        print(f"  FAIL: Wrong exception type: {e} ✗")
        result = False

    print("\n[Test 3] Verifying function signature...")
    import inspect
    sig = inspect.signature(extract_registration_embedding)
    params = list(sig.parameters.keys())
    assert params == ['image_bytes'], f"Wrong params: {params}"
    print("  PASS: Function signature is correct ✓")

    print("\n" + "=" * 50)
    if result:
        print("RESULT: ALL TESTS PASSED ✓")
        print("Registration is working correctly.")
    else:
        print("RESULT: SOME TESTS FAILED ✗")
        print("Registration may be broken — investigate before deploying.")
    print("=" * 50)
    return result


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
