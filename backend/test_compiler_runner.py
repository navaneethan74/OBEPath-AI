import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from code_runner import execute_code_submission

# Test 1: Skeleton with pass
res1 = execute_code_submission(
    "def is_valid_parentheses(s: str) -> bool:\n    pass\n",
    [{"call": "is_valid_parentheses('()')", "expected": "True", "input_desc": "s = '()'"}],
    timeout_sec=3.0
)
print("1. Pass Code:", "passed:", res1["passed_count"], "/", res1["total_count"], "percentage:", res1["percentage"])

# Test 2: Correct solution
correct = """def is_valid_parentheses(s: str) -> bool:
    stack = []
    m = {')': '(', '}': '{', ']': '['}
    for c in s:
        if c in m.values():
            stack.append(c)
        elif c in m:
            if not stack or stack[-1] != m[c]:
                return False
            stack.pop()
    return len(stack) == 0
"""
res2 = execute_code_submission(
    correct,
    [
        {"call": "is_valid_parentheses('()')", "expected": "True", "input_desc": "s = '()'"},
        {"call": "is_valid_parentheses('(')", "expected": "False", "input_desc": "s = '('"}
    ],
    timeout_sec=3.0
)
print("2. Correct Code:", "passed:", res2["passed_count"], "/", res2["total_count"], "percentage:", res2["percentage"])

# Test 3: Incorrect logic
wrong = "def is_valid_parentheses(s: str) -> bool:\n    return len(s) == 0\n"
res3 = execute_code_submission(
    wrong,
    [
        {"call": "is_valid_parentheses('()')", "expected": "True", "input_desc": "s = '()'"},
        {"call": "is_valid_parentheses('(')", "expected": "False", "input_desc": "s = '('"}
    ],
    timeout_sec=3.0
)
print("3. Incorrect Code:", "passed:", res3["passed_count"], "/", res3["total_count"], "percentage:", res3["percentage"])

# Test 4: Syntax error
syntax_err = "def is_valid_parentheses(s: str) -> bool:\n  if (\n"
res4 = execute_code_submission(
    syntax_err,
    [{"call": "is_valid_parentheses('()')", "expected": "True", "input_desc": "s = '()'"}],
    timeout_sec=3.0
)
print("4. Syntax Error:", "success:", res4["success"], "stderr snippet:", res4["stderr"][:50].strip())

# Test 5: Infinite loop / Timeout
infinite = "def is_valid_parentheses(s: str) -> bool:\n    while True:\n        pass\n"
res5 = execute_code_submission(
    infinite,
    [{"call": "is_valid_parentheses('()')", "expected": "True", "input_desc": "s = '()'"}],
    timeout_sec=1.5
)
print("5. Timeout Handling:", "success:", res5["success"], "stderr:", res5["stderr"])
