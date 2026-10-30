import re
import json

with open("backend/code_runner.py", "r", encoding="utf-8") as f:
    content = f.read()

# Challenge skeleton mappings:
skeletons = {
    "ds_stack_parentheses": (
        "def is_valid_parentheses(s: str) -> bool:\n"
        "    # TODO: Implement stack-based parentheses matching (LIFO)\n"
        "    # Return True if parentheses are balanced, False otherwise\n"
        "    pass\n"
    ),
    "ds_queue_first_unique": (
        "def first_unique_char(s: str) -> str:\n"
        "    # TODO: Find first non-repeating character using a queue/frequency buffer\n"
        "    # Return character or empty string '' if none exists\n"
        "    pass\n"
    ),
    "ds_recursion_palindrome": (
        "def is_palindrome_recursive(s: str) -> bool:\n"
        "    # TODO: Implement recursive palindrome validator\n"
        "    # Base case: string of length 0 or 1 is a palindrome\n"
        "    pass\n"
    ),
    "ds_tree_max_depth": (
        "def max_depth(root: dict) -> int:\n"
        "    # TODO: Return maximum depth of binary tree represented as dict\n"
        "    # Return 0 if root is None or empty\n"
        "    pass\n"
    ),
    "ds_tree_inorder": (
        "def inorder_traversal(root: dict) -> list:\n"
        "    # TODO: Return list of node values visited in Inorder (Left -> Root -> Right)\n"
        "    # Return [] if root is None or empty\n"
        "    pass\n"
    ),
    "ds_recursive_sum_nested": (
        "def sum_nested_list(lst: list) -> int:\n"
        "    # TODO: Recursively compute the sum of all numbers in nested list\n"
        "    pass\n"
    ),
    "ds_bst_search": (
        "def search_bst(root: dict, val: int) -> bool:\n"
        "    # TODO: Binary Search Tree lookup exploiting BST invariant\n"
        "    # Return True if val is in tree, False otherwise\n"
        "    pass\n"
    ),
    "ds_binary_search_steps": (
        "def binary_search_steps(arr: list, target: int) -> int:\n"
        "    # TODO: Implement binary search and return comparison step count\n"
        "    pass\n"
    ),
    "py_temp_converter": (
        "def celsius_to_fahrenheit(c: float) -> float:\n"
        "    # TODO: Convert Celsius to Fahrenheit and round to 1 decimal place\n"
        "    pass\n"
    ),
    "py_classify_number": (
        "def classify_number(n: int) -> str:\n"
        "    # TODO: Return 'POSITIVE_EVEN', 'POSITIVE_ODD', 'ZERO', or 'NEGATIVE'\n"
        "    pass\n"
    ),
    "py_sum_evens": (
        "def sum_even_numbers(numbers: list) -> int:\n"
        "    # TODO: Return sum of all even numbers in the list\n"
        "    pass\n"
    ),
    "py_list_freq": (
        "def remove_duplicates(items: list) -> list:\n"
        "    # TODO: Remove duplicates while preserving original relative order\n"
        "    pass\n"
    ),
    "py_word_counter": (
        "def word_frequency(text: str) -> dict:\n"
        "    # TODO: Count word frequencies (case-insensitive) and return dict\n"
        "    pass\n"
    ),
    "py_calc_stats": (
        "def calc_stats(nums: list) -> dict:\n"
        "    # TODO: Return {'mean': round(mean, 2), 'range': round(max - min, 2)}\n"
        "    pass\n"
    ),
    "py_safe_divide": (
        "def safe_divide(a: float, b: float):\n"
        "    # TODO: Return round(a / b, 2), or 'DIV_BY_ZERO' if b == 0\n"
        "    pass\n"
    ),
    "py_bank_account": (
        "def simulate_bank_transactions(initial_balance: int, transactions: list) -> int:\n"
        "    # TODO: Process list of ('deposit'|'withdraw', amount) and return final balance\n"
        "    pass\n"
    ),
    "ml_min_max_scale": (
        "def min_max_scale(values: list) -> list:\n"
        "    # TODO: Scale values to [0.0, 1.0] using (x - min) / (max - min) rounded to 2 decimals\n"
        "    pass\n"
    ),
    "ml_loss_mse": (
        "def mean_squared_error(y_true: list, y_pred: list) -> float:\n"
        "    # TODO: Compute Mean Squared Error rounded to 3 decimal places\n"
        "    pass\n"
    ),
    "db_pk_validator": (
        "def validate_primary_key(records: list, pk_field: str) -> bool:\n"
        "    # TODO: Return True if pk_field is non-null and unique in every record\n"
        "    pass\n"
    ),
    "db_acid_validator": (
        "def execute_transfer(balance_a: int, balance_b: int, amount: int) -> dict:\n"
        "    # TODO: Simulate atomic transaction transfer between accounts A and B\n"
        "    pass\n"
    )
}

# Replace starter_code in CODING_CHALLENGES
import sys
sys.path.insert(0, 'backend')
from code_runner import CODING_CHALLENGES

for c in CODING_CHALLENGES:
    cid = c["id"]
    if cid in skeletons:
        c["reference_solution"] = c["starter_code"]
        c["starter_code"] = skeletons[cid]

# Write updated code_runner.py with sandbox security
updated_code = '''import subprocess
import sys
import json
import time
from typing import Dict, Any, List, Optional

# ==============================================================================
# 1. Topic-Mapped Coding Challenges Catalog (All OBE Courses & Topics)
# ==============================================================================

CODING_CHALLENGES: List[Dict[str, Any]] = ''' + json.dumps(CODING_CHALLENGES, indent=4) + '''

# ==============================================================================
# Helper: Challenge Selector
# ==============================================================================

def get_coding_challenge(course_id: int = 2, topic_id: Optional[int] = None, topic_title: Optional[str] = None) -> Dict[str, Any]:
    """
    Selects the best matching coding challenge for a course or specific topic.
    """
    # 1. Exact match on both course_id and topic_id
    if topic_id is not None:
        for c in CODING_CHALLENGES:
            if c.get("course_id") == course_id and c.get("topic_id") == topic_id:
                return c

        for c in CODING_CHALLENGES:
            if c.get("topic_id") == topic_id:
                return c

    # 2. Match topic title keyword
    if topic_title:
        title_lower = topic_title.lower()
        for c in CODING_CHALLENGES:
            c_title = c.get("topic_title", "").lower()
            if c_title in title_lower or title_lower in c_title:
                return c
        for c in CODING_CHALLENGES:
            words = [w for w in title_lower.split() if len(w) > 3]
            for w in words:
                if w in c.get("topic_title", "").lower() or w in c.get("title", "").lower():
                    return c

    # 3. Match course_id
    for c in CODING_CHALLENGES:
        if c.get("course_id") == course_id:
            return c

    # 4. Default fallback
    return CODING_CHALLENGES[0]

# ==============================================================================
# 2. Safe Subprocess Code Execution & Test Evaluator
# ==============================================================================

DANGEROUS_PATTERNS = [
    "import os", "from os", "import sys", "from sys",
    "import subprocess", "from subprocess",
    "import shutil", "from shutil", "import socket", "from socket",
    "open(", "__import__", "exec(", "eval(", "input("
]

def execute_code_submission(
    code: str,
    test_cases: List[Dict[str, Any]],
    timeout_sec: float = 3.5
) -> Dict[str, Any]:
    """
    Executes student python code in a sandboxed subprocess and validates against test cases.
    """
    start_time = time.time()

    # Security sandbox check
    lower_code = code.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern in lower_code:
            return {
                "success": False,
                "all_passed": False,
                "passed_count": 0,
                "total_count": len(test_cases),
                "percentage": 0.0,
                "stdout": "",
                "stderr": f"Security Notice: '{pattern}' is not permitted in the educational compiler sandbox.",
                "results": [
                    {
                        "test_idx": i + 1,
                        "call": tc.get("call"),
                        "input_desc": tc.get("input_desc"),
                        "expected": tc.get("expected"),
                        "actual": "Security Error",
                        "passed": False,
                        "error": "Restricted Operation"
                    }
                    for i, tc in enumerate(test_cases)
                ],
                "execution_time_ms": 0
            }

    # Build wrapped python test harness
    wrapper_script = f"""
import sys, json

# 1. Student Submission
{code}

# 2. Automated Test Case Harness
results = []
test_cases = {json.dumps(test_cases)}

for idx, tc in enumerate(test_cases):
    call_expr = tc.get('call', '')
    expected_str = str(tc.get('expected', '')).strip()
    try:
        actual_val = eval(call_expr)
        actual_str = str(actual_val).strip()
        passed = (actual_str == expected_str)
        if not passed:
            try:
                norm_actual = json.loads(actual_str.replace("'", '"'))
                norm_expected = json.loads(expected_str.replace("'", '"'))
                passed = (norm_actual == norm_expected)
            except Exception:
                pass
        results.append({{
            'test_idx': idx + 1,
            'call': call_expr,
            'input_desc': tc.get('input_desc', call_expr),
            'expected': expected_str,
            'actual': actual_str,
            'passed': passed,
            'error': None
        }})
    except Exception as e:
        results.append({{
            'test_idx': idx + 1,
            'call': call_expr,
            'input_desc': tc.get('input_desc', call_expr),
            'expected': expected_str,
            'actual': None,
            'passed': False,
            'error': f"{type(e).__name__}: {str(e)}"
        }})

print("---JSON_OUTPUT_DELIMITER---")
print(json.dumps(results))
"""

    try:
        proc = subprocess.run(
            [sys.executable, "-c", wrapper_script],
            capture_output=True,
            text=True,
            timeout=timeout_sec
        )
        elapsed_ms = round((time.time() - start_time) * 1000)

        stdout_full = proc.stdout
        stderr_full = proc.stderr

        # Check for compilation or runtime crash before tests ran
        if "---JSON_OUTPUT_DELIMITER---" not in stdout_full:
            error_message = stderr_full.strip() or stdout_full.strip() or "Syntax or Import Error occurred."
            clean_error = error_message
            if "Traceback" in error_message:
                lines = error_message.splitlines()
                clean_error = "\\n".join(lines[-4:])

            return {
                "success": False,
                "all_passed": False,
                "passed_count": 0,
                "total_count": len(test_cases),
                "percentage": 0.0,
                "stdout": stdout_full,
                "stderr": clean_error,
                "results": [
                    {
                        "test_idx": i + 1,
                        "call": tc.get("call"),
                        "input_desc": tc.get("input_desc"),
                        "expected": tc.get("expected"),
                        "actual": "Syntax / Compilation Error",
                        "passed": False,
                        "error": clean_error
                    }
                    for i, tc in enumerate(test_cases)
                ],
                "execution_time_ms": elapsed_ms
            }

        # Parse test results
        parts = stdout_full.split("---JSON_OUTPUT_DELIMITER---")
        user_stdout = parts[0].strip()
        json_results_str = parts[1].strip()
        parsed_results = json.loads(json_results_str)

        passed_count = sum(1 for r in parsed_results if r.get("passed"))
        total_count = len(parsed_results)
        percentage = round((passed_count / max(total_count, 1)) * 100.0, 1)

        return {
            "success": True,
            "all_passed": (passed_count == total_count and total_count > 0),
            "passed_count": passed_count,
            "total_count": total_count,
            "percentage": percentage,
            "stdout": user_stdout,
            "stderr": stderr_full.strip() if proc.returncode != 0 else "",
            "results": parsed_results,
            "execution_time_ms": elapsed_ms
        }

    except subprocess.TimeoutExpired:
        elapsed_ms = round((time.time() - start_time) * 1000)
        return {
            "success": False,
            "all_passed": False,
            "passed_count": 0,
            "total_count": len(test_cases),
            "percentage": 0.0,
            "stdout": "",
            "stderr": f"Execution Timed Out ({timeout_sec}s limit exceeded). Please check for infinite loops.",
            "results": [
                {
                    "test_idx": i + 1,
                    "call": tc.get("call"),
                    "input_desc": tc.get("input_desc"),
                    "expected": tc.get("expected"),
                    "actual": "Time Limit Exceeded",
                    "passed": False,
                    "error": "TimeoutExpired"
                }
                for i, tc in enumerate(test_cases)
            ],
            "execution_time_ms": elapsed_ms
        }
    except Exception as e:
        return {
            "success": False,
            "all_passed": False,
            "passed_count": 0,
            "total_count": len(test_cases),
            "percentage": 0.0,
            "stdout": "",
            "stderr": f"Execution Error: {str(e)}",
            "results": [],
            "execution_time_ms": 0
        }
'''

with open("backend/code_runner.py", "w", encoding="utf-8") as f:
    f.write(updated_code)
print("Updated code_runner.py with clean skeletons and security checks!")
