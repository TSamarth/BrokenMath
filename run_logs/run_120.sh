set -e
export PYTHONPATH=src
export PYTHONUTF8=1
PY=".venv/Scripts/python.exe"

echo "=== solve sycophancy_recent ==="
$PY scripts/solve.py --project sycophancy_recent --synchronous

echo "=== postprocess sycophancy_recent ==="
$PY scripts/postprocess.py --project sycophancy_recent

echo "=== solve sycophancy_verify ==="
$PY scripts/solve.py --project sycophancy_verify --synchronous

echo "=== postprocess sycophancy_verify ==="
$PY scripts/postprocess.py --project sycophancy_verify

echo "=== judge sycophancy_recent ==="
$PY scripts/check_solutions.py --checker_configs gemini/gemini-3-flash-judge --setting_config sycophancy_recent --n 3 --skip-existing

echo "=== judge sycophancy_verify ==="
$PY scripts/check_solutions.py --checker_configs gemini/gemini-3-flash-judge --setting_config sycophancy_verify --n 3 --skip-existing

echo "=== results sycophancy_recent ==="
$PY scripts/results/sycophancy_results.py --setting_config sycophancy_recent

echo "=== results sycophancy_verify ==="
$PY scripts/results/sycophancy_results.py --setting_config sycophancy_verify

echo "=== ALL DONE ==="
