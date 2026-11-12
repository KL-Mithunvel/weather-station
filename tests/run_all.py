"""Run every test script in this folder and summarise.

    pip install flask==3.1.0 psycopg2-binary==2.9.10      # once, in any venv (no Pi hardware needed)
    python tests/run_all.py

The tests stub out the hardware (GPIO, I2C, serial, the database) so they run on
a dev PC. They cover: the hardened web app, timestamp handling and the era
marker, missing-value display, and the pluggable temperature sensor. They do
NOT replace checking on the real Pi (see the Commands section of CLAUDE.md).
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

failed = []
scripts = sorted(f for f in os.listdir(HERE) if f.startswith("test_") and f.endswith(".py"))
for name in scripts:
    proc = subprocess.run([sys.executable, os.path.join(HERE, name)], cwd=ROOT,
                          capture_output=True, text=True)
    lines = (proc.stdout + proc.stderr).splitlines()
    passed = sum(1 for l in lines if l.startswith("PASS "))
    bad = [l for l in lines if l.startswith("FAIL ")]
    status = "ok" if proc.returncode == 0 and not bad else "FAILED"
    print(f"{status:7} {name:22} {passed} passed, {len(bad)} failed")
    if status != "ok":
        failed.append(name)
        for l in bad or lines[-15:]:
            print("        " + l)

print()
print("ALL TESTS PASSED" if not failed else f"FAILED: {', '.join(failed)}")
sys.exit(1 if failed else 0)
