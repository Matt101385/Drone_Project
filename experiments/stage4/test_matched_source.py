"""Source-contract test; imports no drone/vision/hardware libraries."""
from pathlib import Path
import ast
import unittest

HERE = Path(__file__).resolve().parent

class MatchedPairSourceTests(unittest.TestCase):
    def test_valid_python_and_only_controller_mode_differs(self):
        p = (HERE / "position_matched.py").read_text(encoding="utf-8")
        v = (HERE / "velocity_matched.py").read_text(encoding="utf-8")
        ast.parse(p, filename="position_matched.py")
        ast.parse(v, filename="velocity_matched.py")
        self.assertIn('STAGE4_CONTROL_MODE = "position"', p)
        self.assertIn('STAGE4_CONTROL_MODE = "velocity"', v)
        self.assertEqual(
            v.replace('STAGE4_CONTROL_MODE = "velocity"',
                      'STAGE4_CONTROL_MODE = "position"'),
            p,
        )
        for needle in (
            "TARGET_DIST_M = 2.0",
            "CAMERA_TILT_DEG = 30.0",
            "DIST_RATE_KD_S = 0.35",
            "STAGE4_SITL_ACK",
            "set_velocity_body(",
            "set_position_ned(",
        ):
            self.assertIn(needle, p)

if __name__ == "__main__":
    unittest.main()
