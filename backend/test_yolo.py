import numpy as np
from pages.helper.yolo_prescreener import (
    has_face_yolo,
    is_yolo_available,
    get_yolo_status
)

print('Status:', get_yolo_status())
print('Available:', is_yolo_available())

# Test with blank frame (should return False or True)
blank = np.zeros((480, 640, 3), dtype=np.uint8)
result = has_face_yolo(blank)
print(f'Blank frame result: {result} (should be False or True, not crash)')

# Test that it never crashes
try:
    bad_input = np.zeros((0, 0, 3), dtype=np.uint8)
    result2 = has_face_yolo(bad_input)
    print(f'Bad input result: {result2} (should be True, fail open)')
except Exception as e:
    print(f'CRASH on bad input: {e} — THIS IS A BUG, FIX IT')

print('yolo_prescreener.py verification complete')
