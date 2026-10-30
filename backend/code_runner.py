import subprocess
import sys
import json
import time
import os
import shutil
import uuid
import logging
import threading
from collections import defaultdict
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ==============================================================================
# Sandbox Configuration Constants
# ==============================================================================
SANDBOX_IMAGE = os.getenv("SANDBOX_DOCKER_IMAGE", "obepath-sandbox:1")
MAX_STDOUT_BYTES = 64 * 1024  # 64 KB cap
MAX_STDERR_BYTES = 64 * 1024  # 64 KB cap
MAX_CODE_CHARS = 10000        # Max 10,000 characters
MAX_TIMEOUT_SEC = 5.0
MIN_TIMEOUT_SEC = 0.5
DEFAULT_TIMEOUT_SEC = 3.5

# Global execution concurrency limit (max 4 simultaneous runs)
GLOBAL_EXECUTION_SEMAPHORE = threading.BoundedSemaphore(4)

# Per-user rate limiting: max 10 runs per minute
_user_execution_timestamps: Dict[int, List[float]] = defaultdict(list)
_rate_limit_lock = threading.Lock()
MAX_RUNS_PER_MINUTE = 10
RATE_LIMIT_WINDOW_SEC = 60.0

class DockerUnavailableError(Exception):
    """Raised when Docker daemon is not available and unsafe local execution is prohibited."""
    pass

class ExecutionConcurrencyError(Exception):
    """Raised when maximum concurrent executions are in progress."""
    pass

def reset_code_runner_rate_limits():
    """Clears in-memory compile rate limit records (used in tests)."""
    with _rate_limit_lock:
        _user_execution_timestamps.clear()

def check_and_record_user_rate_limit(user_id: int) -> Tuple[bool, int]:
    """
    Checks if user has exceeded 10 runs per minute.
    Returns (allowed, retry_after_seconds).
    """
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SEC
    with _rate_limit_lock:
        _user_execution_timestamps[user_id] = [
            t for t in _user_execution_timestamps[user_id] if t >= cutoff
        ]
        history = _user_execution_timestamps[user_id]
        if len(history) >= MAX_RUNS_PER_MINUTE:
            oldest = history[0]
            retry_after = max(1, int(oldest + RATE_LIMIT_WINDOW_SEC - now))
            return False, retry_after
        history.append(now)
        return True, 0

def check_docker_available() -> bool:
    """Checks whether docker CLI is present and the Docker daemon responds."""
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return False
    try:
        proc = subprocess.run(
            [docker_bin, "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            timeout=1.5
        )
        return proc.returncode == 0
    except Exception:
        return False

def is_unsafe_local_allowed() -> bool:
    """
    Returns True ONLY if SANDBOX_ALLOW_UNSAFE_LOCAL=true AND environment is NOT production.
    Strictly ignored in production.
    """
    env_val = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    is_prod = env_val in ("production", "prod")
    if is_prod:
        return False
    return os.getenv("SANDBOX_ALLOW_UNSAFE_LOCAL", "false").strip().lower() == "true"


# ==============================================================================
# 1. Topic-Mapped Coding Challenges Catalog (All OBE Courses & Topics)
# ==============================================================================

CODING_CHALLENGES: List[Dict[str, Any]] = [
    {
        "id": "ds_stack_parentheses",
        "course_id": 2,
        "topic_id": 1,
        "topic_title": "Stack Basics & Operations",
        "title": "Valid Balanced Parentheses with Stack",
        "difficulty": "Intermediate",
        "outcome_code": "CO2",
        "description": "Given a string `s` containing just the characters `'('`, `')'`, `'{'`, `'}'`, `'['` and `']'`, implement a function `is_valid_parentheses(s)` using a **Stack (LIFO)** data structure that determines if the input string is valid.\n\n**Rules:**\n1. Open brackets must be closed by the same type of brackets.\n2. Open brackets must be closed in the correct order.\n3. Every close bracket has a corresponding open bracket of the same type.\n\n**Example 1:** `is_valid_parentheses(\"()[]{}\")` -> `True`\n**Example 2:** `is_valid_parentheses(\"(]\")` -> `False`\n**Example 3:** `is_valid_parentheses(\"([{}])\")` -> `True`",
        "starter_code": "def is_valid_parentheses(s: str) -> bool:\n    # TODO: Implement stack-based parentheses matching (LIFO)\n    # Return True if parentheses are balanced, False otherwise\n    pass\n",
        "test_cases": [
            {
                "call": "is_valid_parentheses('()[]{}')",
                "expected": "True",
                "input_desc": "s = '()[]{}'"
            },
            {
                "call": "is_valid_parentheses('(]')",
                "expected": "False",
                "input_desc": "s = '(]'"
            },
            {
                "call": "is_valid_parentheses('([{}])')",
                "expected": "True",
                "input_desc": "s = '([{}])'"
            },
            {
                "call": "is_valid_parentheses('((')",
                "expected": "False",
                "input_desc": "s = '(('"
            }
        ],
        "reference_solution": "def is_valid_parentheses(s: str) -> bool:\n    # TODO: Implement stack-based parentheses matching\n    stack = []\n    matching = {')': '(', '}': '{', ']': '['}\n    for char in s:\n        if char in matching.values():\n            stack.append(char)\n        elif char in matching:\n            if not stack or stack[-1] != matching[char]:\n                return False\n            stack.pop()\n    return len(stack) == 0\n"
    },
    {
        "id": "ds_queue_first_unique",
        "course_id": 2,
        "topic_id": 2,
        "topic_title": "Queue Basics & Operations",
        "title": "First Non-Repeating Character Using Queue Buffer",
        "difficulty": "Intermediate",
        "outcome_code": "CO2",
        "description": "Given a string `s`, find the **first non-repeating character** in it using a FIFO Queue buffer mechanism. Return the character as a string. If every character repeats or the string is empty, return `\"\"`.\n\n**Example 1:** `first_unique_char(\"leetcode\")` -> `'l'`\n**Example 2:** `first_unique_char(\"loveleetcode\")` -> `'v'`\n**Example 3:** `first_unique_char(\"aabb\")` -> `\"\"`",
        "starter_code": "def first_unique_char(s: str) -> str:\n    # TODO: Find first non-repeating character using a queue/frequency buffer\n    # Return character or empty string '' if none exists\n    pass\n",
        "test_cases": [
            {
                "call": "first_unique_char('leetcode')",
                "expected": "l",
                "input_desc": "s = 'leetcode'"
            },
            {
                "call": "first_unique_char('loveleetcode')",
                "expected": "v",
                "input_desc": "s = 'loveleetcode'"
            },
            {
                "call": "first_unique_char('aabb')",
                "expected": "",
                "input_desc": "s = 'aabb'"
            },
            {
                "call": "first_unique_char('c')",
                "expected": "c",
                "input_desc": "s = 'c'"
            }
        ],
        "reference_solution": "def first_unique_char(s: str) -> str:\n    # TODO: Use FIFO queue / frequency count to find first unique character\n    from collections import Counter\n    counts = Counter(s)\n    for char in s:\n        if counts[char] == 1:\n            return char\n    return ''\n"
    },
    {
        "id": "ds_recursion_palindrome",
        "course_id": 2,
        "topic_id": 3,
        "topic_title": "Recursion Fundamentals",
        "title": "Recursive Palindrome Validator",
        "difficulty": "Intermediate",
        "outcome_code": "CO3",
        "description": "Implement a recursive function `is_palindrome_recursive(s)` that determines if string `s` is a palindrome. You must use recursion and proper base cases.\n\n**Base Cases:**\n- If string length is 0 or 1, return `True`.\n**Recursive Step:**\n- If `s[0] == s[-1]`, return `is_palindrome_recursive(s[1:-1])`.\n- Otherwise return `False`.\n\n**Example 1:** `is_palindrome_recursive(\"racecar\")` -> `True`\n**Example 2:** `is_palindrome_recursive(\"hello\")` -> `False`",
        "starter_code": "def is_palindrome_recursive(s: str) -> bool:\n    # TODO: Implement recursive palindrome validator\n    # Base case: string of length 0 or 1 is a palindrome\n    pass\n",
        "test_cases": [
            {
                "call": "is_palindrome_recursive('racecar')",
                "expected": "True",
                "input_desc": "s = 'racecar'"
            },
            {
                "call": "is_palindrome_recursive('hello')",
                "expected": "False",
                "input_desc": "s = 'hello'"
            },
            {
                "call": "is_palindrome_recursive('kayak')",
                "expected": "True",
                "input_desc": "s = 'kayak'"
            },
            {
                "call": "is_palindrome_recursive('a')",
                "expected": "True",
                "input_desc": "s = 'a'"
            }
        ],
        "reference_solution": "def is_palindrome_recursive(s: str) -> bool:\n    # Base case\n    if len(s) <= 1:\n        return True\n    # Recursive check\n    if s[0] != s[-1]:\n        return False\n    return is_palindrome_recursive(s[1:-1])\n"
    },
    {
        "id": "ds_tree_max_depth",
        "course_id": 2,
        "topic_id": 4,
        "topic_title": "Tree Basics",
        "title": "Calculate Maximum Depth of a Binary Tree",
        "difficulty": "Intermediate",
        "outcome_code": "CO1",
        "description": "Given the root of a binary tree represented as a dictionary `{'val': x, 'left': {...}, 'right': {...}}`, return its **maximum depth** (the number of nodes along the longest path from the root down to the farthest leaf node).\n\nIf `root` is `None` or empty dictionary, return `0`.\n\n**Example:**\n`max_depth({'val': 3, 'left': {'val': 9}, 'right': {'val': 20, 'left': {'val': 15}, 'right': {'val': 7}}})` -> `3`",
        "starter_code": "def max_depth(root: dict) -> int:\n    # TODO: Return maximum depth of binary tree represented as dict\n    # Return 0 if root is None or empty\n    pass\n",
        "test_cases": [
            {
                "call": "max_depth({'val': 3, 'left': {'val': 9}, 'right': {'val': 20, 'left': {'val': 15}, 'right': {'val': 7}}})",
                "expected": "3",
                "input_desc": "tree of depth 3"
            },
            {
                "call": "max_depth({'val': 1, 'right': {'val': 2}})",
                "expected": "2",
                "input_desc": "tree with 1 right child"
            },
            {
                "call": "max_depth(None)",
                "expected": "0",
                "input_desc": "root = None"
            },
            {
                "call": "max_depth({'val': 42})",
                "expected": "1",
                "input_desc": "single root node"
            }
        ],
        "reference_solution": "def max_depth(root: dict) -> int:\n    # TODO: Calculate maximum depth of binary tree\n    if not root:\n        return 0\n    left_depth = max_depth(root.get('left'))\n    right_depth = max_depth(root.get('right'))\n    return 1 + max(left_depth, right_depth)\n"
    },
    {
        "id": "ds_tree_inorder",
        "course_id": 2,
        "topic_id": 5,
        "topic_title": "Tree Traversal",
        "title": "Recursive Inorder Traversal of Binary Tree",
        "difficulty": "Intermediate",
        "outcome_code": "CO2",
        "description": "Implement a function `inorder_traversal(root)` that returns a list of node values visited in **Inorder Traversal** (Left Subtree \u2794 Root \u2794 Right Subtree).\n\nBinary tree nodes are represented as `{'val': int, 'left': dict, 'right': dict}`.\nIf `root` is `None` or empty, return `[]`.\n\n**Example:**\n`inorder_traversal({'val': 1, 'left': None, 'right': {'val': 2, 'left': {'val': 3}, 'right': None}})` -> `[1, 3, 2]`",
        "starter_code": "def inorder_traversal(root: dict) -> list:\n    # TODO: Return list of node values visited in Inorder (Left -> Root -> Right)\n    # Return [] if root is None or empty\n    pass\n",
        "test_cases": [
            {
                "call": "inorder_traversal({'val': 1, 'left': None, 'right': {'val': 2, 'left': {'val': 3}, 'right': None}})",
                "expected": "[1, 3, 2]",
                "input_desc": "root = [1, null, 2, 3]"
            },
            {
                "call": "inorder_traversal({'val': 4, 'left': {'val': 2, 'left': {'val': 1}, 'right': {'val': 3}}, 'right': {'val': 5}})",
                "expected": "[1, 2, 3, 4, 5]",
                "input_desc": "balanced tree 1..5"
            },
            {
                "call": "inorder_traversal(None)",
                "expected": "[]",
                "input_desc": "empty tree"
            }
        ],
        "reference_solution": "def inorder_traversal(root: dict) -> list:\n    # TODO: Implement recursive Inorder Traversal (L -> Root -> R)\n    if not root:\n        return []\n    res = []\n    res.extend(inorder_traversal(root.get('left')))\n    res.append(root.get('val'))\n    res.extend(inorder_traversal(root.get('right')))\n    return res\n"
    },
    {
        "id": "ds_recursive_sum_nested",
        "course_id": 2,
        "topic_id": 6,
        "topic_title": "Recursive Practice",
        "title": "Sum of Integers in Deeply Nested List",
        "difficulty": "Intermediate",
        "outcome_code": "CO2",
        "description": "Write a recursive function `sum_nested_list(lst)` that computes the sum of all integers in an arbitrarily nested list structure.\n\n**Example 1:** `sum_nested_list([1, [2, [3, 4], 5], 6])` -> `21`\n**Example 2:** `sum_nested_list([[1, 2], [3, [4]]])` -> `10`\n**Example 3:** `sum_nested_list([])` -> `0`",
        "starter_code": "def sum_nested_list(lst: list) -> int:\n    # TODO: Recursively compute the sum of all numbers in nested list\n    pass\n",
        "test_cases": [
            {
                "call": "sum_nested_list([1, [2, [3, 4], 5], 6])",
                "expected": "21",
                "input_desc": "[1, [2, [3, 4], 5], 6]"
            },
            {
                "call": "sum_nested_list([[1, 2], [3, [4]]])",
                "expected": "10",
                "input_desc": "[[1, 2], [3, [4]]]"
            },
            {
                "call": "sum_nested_list([])",
                "expected": "0",
                "input_desc": "[]"
            }
        ],
        "reference_solution": "def sum_nested_list(lst: list) -> int:\n    # TODO: Recursively sum nested items\n    total = 0\n    for item in lst:\n        if isinstance(item, list):\n            total += sum_nested_list(item)\n        elif isinstance(item, (int, float)):\n            total += item\n    return total\n"
    },
    {
        "id": "ds_bst_search",
        "course_id": 2,
        "topic_id": 7,
        "topic_title": "Tree Problems & Applications",
        "title": "Binary Search Tree (BST) Value Lookup",
        "difficulty": "Intermediate",
        "outcome_code": "CO2",
        "description": "Write a function `search_bst(root, val)` that searches for a key `val` in a Binary Search Tree (BST).\nIn a valid BST, for any node:\n- All keys in the left subtree are smaller than `node['val']`.\n- All keys in the right subtree are greater than `node['val']`.\n\nReturn `True` if `val` is found, otherwise `False`.\n\n**Example:** `search_bst({'val': 4, 'left': {'val': 2, 'left': {'val': 1}, 'right': {'val': 3}}, 'right': {'val': 7}}, 2)` -> `True`",
        "starter_code": "def search_bst(root: dict, val: int) -> bool:\n    # TODO: Binary Search Tree lookup exploiting BST invariant\n    # Return True if val is in tree, False otherwise\n    pass\n",
        "test_cases": [
            {
                "call": "search_bst({'val': 4, 'left': {'val': 2, 'left': {'val': 1}, 'right': {'val': 3}}, 'right': {'val': 7}}, 2)",
                "expected": "True",
                "input_desc": "BST search val = 2"
            },
            {
                "call": "search_bst({'val': 4, 'left': {'val': 2, 'left': {'val': 1}, 'right': {'val': 3}}, 'right': {'val': 7}}, 5)",
                "expected": "False",
                "input_desc": "BST search val = 5 (absent)"
            },
            {
                "call": "search_bst(None, 10)",
                "expected": "False",
                "input_desc": "root = None"
            }
        ],
        "reference_solution": "def search_bst(root: dict, val: int) -> bool:\n    # TODO: Binary Search Tree lookup exploiting BST invariant\n    if not root:\n        return False\n    if root.get('val') == val:\n        return True\n    elif val < root.get('val'):\n        return search_bst(root.get('left'), val)\n    else:\n        return search_bst(root.get('right'), val)\n"
    },
    {
        "id": "ds_binary_search_steps",
        "course_id": 2,
        "topic_id": 8,
        "topic_title": "Algorithm Complexity & Big-O",
        "title": "Binary Search Comparison Step Counter",
        "difficulty": "Intermediate",
        "outcome_code": "CO3",
        "description": "Write a function `binary_search_steps(arr, target)` that performs binary search on a sorted list `arr` and counts how many loop iterations / comparisons it took to find `target` or confirm absence.\n\nEach iteration of `while low <= high:` counts as 1 step.\n\n**Example:**\n`binary_search_steps([1, 3, 5, 7, 9, 11, 13, 15], 7)` -> `1`",
        "starter_code": "def binary_search_steps(arr: list, target: int) -> int:\n    # TODO: Implement binary search and return comparison step count\n    pass\n",
        "test_cases": [
            {
                "call": "binary_search_steps([1, 3, 5, 7, 9, 11, 13, 15], 7)",
                "expected": "1",
                "input_desc": "arr = [1..15], target = 7"
            },
            {
                "call": "binary_search_steps([2, 4, 6, 8, 10], 2)",
                "expected": "2",
                "input_desc": "arr = [2, 4, 6, 8, 10], target = 2"
            },
            {
                "call": "binary_search_steps([1, 2, 3, 4, 5], 99)",
                "expected": "3",
                "input_desc": "arr = [1..5], target = 99 (absent)"
            }
        ],
        "reference_solution": "def binary_search_steps(arr: list, target: int) -> int:\n    # TODO: Implement binary search and count steps\n    low = 0\n    high = len(arr) - 1\n    steps = 0\n    while low <= high:\n        steps += 1\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return steps\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return steps\n"
    },
    {
        "id": "py_temp_converter",
        "course_id": 1,
        "topic_id": 9,
        "topic_title": "Variables, Data Types & Basic I/O",
        "title": "Temperature Converter (Celsius to Fahrenheit)",
        "difficulty": "Beginner",
        "outcome_code": "CO1",
        "description": "Write a function `celsius_to_fahrenheit(c)` that converts temperature in Celsius to Fahrenheit.\nFormula: `F = (C * 9/5) + 32`.\nReturn the result rounded to 1 decimal place.",
        "starter_code": "def celsius_to_fahrenheit(c: float) -> float:\n    # TODO: Convert Celsius to Fahrenheit and round to 1 decimal place\n    pass\n",
        "test_cases": [
            {
                "call": "celsius_to_fahrenheit(0)",
                "expected": "32.0",
                "input_desc": "c = 0"
            },
            {
                "call": "celsius_to_fahrenheit(100)",
                "expected": "212.0",
                "input_desc": "c = 100"
            },
            {
                "call": "celsius_to_fahrenheit(37)",
                "expected": "98.6",
                "input_desc": "c = 37"
            }
        ],
        "reference_solution": "def celsius_to_fahrenheit(c: float) -> float:\n    # TODO: Convert Celsius to Fahrenheit\n    return round((c * 9.0 / 5.0) + 32.0, 1)\n"
    },
    {
        "id": "py_classify_number",
        "course_id": 1,
        "topic_id": 10,
        "topic_title": "Conditional Statements & Branching",
        "title": "Multi-Criteria Number Classifier",
        "difficulty": "Beginner",
        "outcome_code": "CO2",
        "description": "Write a function `classify_number(n)` that returns:\n- `'POSITIVE_EVEN'` if n > 0 and even\n- `'POSITIVE_ODD'` if n > 0 and odd\n- `'ZERO'` if n == 0\n- `'NEGATIVE'` if n < 0",
        "starter_code": "def classify_number(n: int) -> str:\n    # TODO: Return 'POSITIVE_EVEN', 'POSITIVE_ODD', 'ZERO', or 'NEGATIVE'\n    pass\n",
        "test_cases": [
            {
                "call": "classify_number(4)",
                "expected": "POSITIVE_EVEN",
                "input_desc": "n = 4"
            },
            {
                "call": "classify_number(7)",
                "expected": "POSITIVE_ODD",
                "input_desc": "n = 7"
            },
            {
                "call": "classify_number(0)",
                "expected": "ZERO",
                "input_desc": "n = 0"
            },
            {
                "call": "classify_number(-5)",
                "expected": "NEGATIVE",
                "input_desc": "n = -5"
            }
        ],
        "reference_solution": "def classify_number(n: int) -> str:\n    if n == 0:\n        return 'ZERO'\n    elif n < 0:\n        return 'NEGATIVE'\n    elif n % 2 == 0:\n        return 'POSITIVE_EVEN'\n    else:\n        return 'POSITIVE_ODD'\n"
    },
    {
        "id": "py_sum_evens",
        "course_id": 1,
        "topic_id": 11,
        "topic_title": "Loops & Iterative Control",
        "title": "Sum of Even Numbers in a List",
        "difficulty": "Beginner",
        "outcome_code": "CO2",
        "description": "Write a Python function `sum_even_numbers(numbers)` that takes a list of integers and returns the sum of all **even numbers** in the list.\n\n**Constraints:**\n- If the list contains no even numbers or is empty, return `0`.\n- Handle negative numbers properly (e.g. `-2` is even).",
        "starter_code": "def sum_even_numbers(numbers: list) -> int:\n    # TODO: Return sum of all even numbers in the list\n    pass\n",
        "test_cases": [
            {
                "call": "sum_even_numbers([1, 2, 3, 4, 5, 6])",
                "expected": "12",
                "input_desc": "[1, 2, 3, 4, 5, 6]"
            },
            {
                "call": "sum_even_numbers([1, 3, 5, 7])",
                "expected": "0",
                "input_desc": "[1, 3, 5, 7]"
            },
            {
                "call": "sum_even_numbers([10, -2, 3, 8])",
                "expected": "16",
                "input_desc": "[10, -2, 3, 8]"
            },
            {
                "call": "sum_even_numbers([])",
                "expected": "0",
                "input_desc": "[]"
            }
        ],
        "reference_solution": "def sum_even_numbers(numbers: list) -> int:\n    # TODO: Iterate and sum even numbers\n    total = 0\n    for n in numbers:\n        if n % 2 == 0:\n            total += n\n    return total\n"
    },
    {
        "id": "py_list_freq",
        "course_id": 1,
        "topic_id": 12,
        "topic_title": "Python Lists & Tuples",
        "title": "Remove Duplicates While Preserving Order",
        "difficulty": "Beginner",
        "outcome_code": "CO2",
        "description": "Write a function `remove_duplicates(items)` that removes duplicate elements from a list while **preserving the original relative order** of their first appearances.",
        "starter_code": "def remove_duplicates(items: list) -> list:\n    # TODO: Remove duplicates while preserving original relative order\n    pass\n",
        "test_cases": [
            {
                "call": "remove_duplicates([4, 2, 4, 5, 2, 3, 1])",
                "expected": "[4, 2, 5, 3, 1]",
                "input_desc": "[4, 2, 4, 5, 2, 3, 1]"
            },
            {
                "call": "remove_duplicates(['a', 'b', 'a', 'c'])",
                "expected": "['a', 'b', 'c']",
                "input_desc": "['a', 'b', 'a', 'c']"
            },
            {
                "call": "remove_duplicates([1, 1, 1, 1])",
                "expected": "[1]",
                "input_desc": "[1, 1, 1, 1]"
            }
        ],
        "reference_solution": "def remove_duplicates(items: list) -> list:\n    seen = set()\n    res = []\n    for x in items:\n        if x not in seen:\n            seen.add(x)\n            res.append(x)\n    return res\n"
    },
    {
        "id": "py_word_counter",
        "course_id": 1,
        "topic_id": 13,
        "topic_title": "Dictionaries, Sets & Hash Collections",
        "title": "Word Frequency Counter",
        "difficulty": "Intermediate",
        "outcome_code": "CO3",
        "description": "Write a function `word_frequency(text)` that splits words by spaces, converts to lowercase, and returns a dictionary mapping each unique word to its count.",
        "starter_code": "def word_frequency(text: str) -> dict:\n    # TODO: Count word frequencies (case-insensitive) and return dict\n    pass\n",
        "test_cases": [
            {
                "call": "word_frequency('apple banana apple orange')",
                "expected": "{'apple': 2, 'banana': 1, 'orange': 1}",
                "input_desc": "'apple banana apple orange'"
            },
            {
                "call": "word_frequency('test Test test')",
                "expected": "{'test': 3}",
                "input_desc": "'test Test test'"
            }
        ],
        "reference_solution": "def word_frequency(text: str) -> dict:\n    counts = {}\n    for w in text.lower().split():\n        counts[w] = counts.get(w, 0) + 1\n    return counts\n"
    },
    {
        "id": "py_calc_stats",
        "course_id": 1,
        "topic_id": 14,
        "topic_title": "Functions, Scope & Parameter Passing",
        "title": "Statistical Metrics Calculator (Mean & Range)",
        "difficulty": "Intermediate",
        "outcome_code": "CO3",
        "description": "Write a function `calc_stats(nums)` that returns a dictionary `{'mean': float, 'range': float}` where `mean` is the average rounded to 2 decimal places, and `range` is `max(nums) - min(nums)`. If `nums` is empty, return `{'mean': 0.0, 'range': 0.0}`.",
        "starter_code": "def calc_stats(nums: list) -> dict:\n    # TODO: Return {'mean': round(mean, 2), 'range': round(max - min, 2)}\n    pass\n",
        "test_cases": [
            {
                "call": "calc_stats([10, 20, 30, 40, 50])",
                "expected": "{'mean': 30.0, 'range': 40.0}",
                "input_desc": "[10, 20, 30, 40, 50]"
            },
            {
                "call": "calc_stats([5, 5, 5])",
                "expected": "{'mean': 5.0, 'range': 0.0}",
                "input_desc": "[5, 5, 5]"
            }
        ],
        "reference_solution": "def calc_stats(nums: list) -> dict:\n    if not nums:\n        return {'mean': 0.0, 'range': 0.0}\n    mean = round(sum(nums) / len(nums), 2)\n    rng = round(float(max(nums) - min(nums)), 2)\n    return {'mean': mean, 'range': rng}\n"
    },
    {
        "id": "py_safe_divide",
        "course_id": 1,
        "topic_id": 15,
        "topic_title": "File I/O & Exception Handling",
        "title": "Safe Division with Exception Handling",
        "difficulty": "Intermediate",
        "outcome_code": "CO4",
        "description": "Write a function `safe_divide(a, b)` that performs division `a / b` using a `try-except` block. If `ZeroDivisionError` occurs, return `'DIV_BY_ZERO'`. If successful, return `round(a / b, 2)`.",
        "starter_code": "def safe_divide(a: float, b: float):\n    # TODO: Return round(a / b, 2), or 'DIV_BY_ZERO' if b == 0\n    pass\n",
        "test_cases": [
            {
                "call": "safe_divide(10, 2)",
                "expected": "5.0",
                "input_desc": "a=10, b=2"
            },
            {
                "call": "safe_divide(5, 0)",
                "expected": "DIV_BY_ZERO",
                "input_desc": "a=5, b=0"
            },
            {
                "call": "safe_divide(10, 3)",
                "expected": "3.33",
                "input_desc": "a=10, b=3"
            }
        ],
        "reference_solution": "def safe_divide(a: float, b: float):\n    try:\n        return round(a / b, 2)\n    except ZeroDivisionError:\n        return 'DIV_BY_ZERO'\n"
    },
    {
        "id": "py_bank_account",
        "course_id": 1,
        "topic_id": 16,
        "topic_title": "Object-Oriented Programming in Python",
        "title": "Bank Account Class Operations",
        "difficulty": "Intermediate",
        "outcome_code": "CO4",
        "description": "Write a function `simulate_bank_transactions(initial_balance, transactions)`.\n`transactions` is a list of tuples like `('deposit', 50)` or `('withdraw', 20)`.\nIf withdrawal exceeds current balance, ignore that withdrawal. Return the final balance.",
        "starter_code": "def simulate_bank_transactions(initial_balance: int, transactions: list) -> int:\n    # TODO: Process list of ('deposit'|'withdraw', amount) and return final balance\n    pass\n",
        "test_cases": [
            {
                "call": "simulate_bank_transactions(100, [('deposit', 50), ('withdraw', 30)])",
                "expected": "120",
                "input_desc": "balance=100, +50, -30"
            },
            {
                "call": "simulate_bank_transactions(50, [('withdraw', 100), ('deposit', 20)])",
                "expected": "70",
                "input_desc": "balance=50, -100 (rejected), +20"
            }
        ],
        "reference_solution": "def simulate_bank_transactions(initial_balance: int, transactions: list) -> int:\n    balance = initial_balance\n    for action, amt in transactions:\n        if action == 'deposit':\n            balance += amt\n        elif action == 'withdraw' and balance >= amt:\n            balance -= amt\n    return balance\n"
    },
    {
        "id": "ml_min_max_scale",
        "course_id": 3,
        "topic_id": 17,
        "topic_title": "Statistical Learning & Feature Engineering",
        "title": "Min-Max Feature Scaler",
        "difficulty": "Intermediate",
        "outcome_code": "CO1",
        "description": "Write a function `min_max_scale(values)` that scales numeric values into the range `[0.0, 1.0]`.\nFormula: `(x - min) / (max - min)`. Return rounded to 2 decimal places. If max == min, return all 0.0.",
        "starter_code": "def min_max_scale(values: list) -> list:\n    # TODO: Scale values to [0.0, 1.0] using (x - min) / (max - min) rounded to 2 decimals\n    pass\n",
        "test_cases": [
            {
                "call": "min_max_scale([10, 20, 30, 40, 50])",
                "expected": "[0.0, 0.25, 0.5, 0.75, 1.0]",
                "input_desc": "[10, 20, 30, 40, 50]"
            },
            {
                "call": "min_max_scale([5, 5, 5])",
                "expected": "[0.0, 0.0, 0.0]",
                "input_desc": "[5, 5, 5]"
            }
        ],
        "reference_solution": "def min_max_scale(values: list) -> list:\n    if not values:\n        return []\n    mn = min(values)\n    mx = max(values)\n    if mx == mn:\n        return [0.0] * len(values)\n    return [round((x - mn) / (mx - mn), 2) for x in values]\n"
    },
    {
        "id": "ml_loss_mse",
        "course_id": 3,
        "topic_id": 18,
        "topic_title": "Linear & Polynomial Regression",
        "title": "Mean Squared Error (MSE) Calculator",
        "difficulty": "Intermediate",
        "outcome_code": "CO2",
        "description": "Write a function `mean_squared_error(y_true, y_pred)` that computes the Mean Squared Error.\n$$\\text{MSE} = \\frac{1}{N} \\sum_{i=1}^N (y_{\\text{true}, i} - y_{\\text{pred}, i})^2$$\nReturn the calculated MSE rounded to **3 decimal places**.",
        "starter_code": "def mean_squared_error(y_true: list, y_pred: list) -> float:\n    # TODO: Compute Mean Squared Error rounded to 3 decimal places\n    pass\n",
        "test_cases": [
            {
                "call": "mean_squared_error([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])",
                "expected": "0.0",
                "input_desc": "exact predictions"
            },
            {
                "call": "mean_squared_error([3.0, -0.5, 2.0, 7.0], [2.5, 0.0, 2.0, 8.0])",
                "expected": "0.375",
                "input_desc": "varied errors"
            }
        ],
        "reference_solution": "def mean_squared_error(y_true: list, y_pred: list) -> float:\n    if not y_true or len(y_true) != len(y_pred):\n        return 0.0\n    n = len(y_true)\n    sq_err = sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred))\n    return round(sq_err / n, 3)\n"
    },
    {
        "id": "db_pk_validator",
        "course_id": 4,
        "topic_id": 25,
        "topic_title": "Relational Data Model & Schemas",
        "title": "Primary Key Uniqueness & Not-Null Validator",
        "difficulty": "Intermediate",
        "outcome_code": "CO1",
        "description": "Write a function `validate_primary_key(records, pk_field)` that inspects a list of record dictionaries.\nReturn `True` if `pk_field` exists in every record, is never `None`, and all values are unique. Otherwise `False`.",
        "starter_code": "def validate_primary_key(records: list, pk_field: str) -> bool:\n    # TODO: Return True if pk_field is non-null and unique in every record\n    pass\n",
        "test_cases": [
            {
                "call": "validate_primary_key([{'id': 1, 'name': 'A'}, {'id': 2, 'name': 'B'}], 'id')",
                "expected": "True",
                "input_desc": "valid PKs"
            },
            {
                "call": "validate_primary_key([{'id': 1, 'name': 'A'}, {'id': 1, 'name': 'B'}], 'id')",
                "expected": "False",
                "input_desc": "duplicate PK id=1"
            },
            {
                "call": "validate_primary_key([{'name': 'A'}], 'id')",
                "expected": "False",
                "input_desc": "missing PK"
            }
        ],
        "reference_solution": "def validate_primary_key(records: list, pk_field: str) -> bool:\n    seen = set()\n    for r in records:\n        if pk_field not in r or r[pk_field] is None:\n            return False\n        val = r[pk_field]\n        if val in seen:\n            return False\n        seen.add(val)\n    return True\n"
    },
    {
        "id": "ml_sigmoid_classification",
        "course_id": 3,
        "topic_id": 19,
        "topic_title": "Logistic Regression & Classification",
        "title": "Sigmoid Activation Function for Logistic Regression",
        "difficulty": "Intermediate",
        "outcome_code": "CO2",
        "description": "Implement `sigmoid_activation(logits: list) -> list` that calculates the Sigmoid activation function $\\sigma(z) = \\frac{1}{1 + e^{-z}}$ for a list of linear logits.\nReturn a list of probability values rounded to **4 decimal places**.\n\n**Example 1:** `sigmoid_activation([0.0, 2.0, -2.0])` -> `[0.5, 0.8808, 0.1192]`\n**Example 2:** `sigmoid_activation([])` -> `[]`",
        "starter_code": "import math\n\ndef sigmoid_activation(logits: list) -> list:\n    # TODO: Calculate sigmoid probability 1 / (1 + exp(-z)) rounded to 4 decimals\n    pass\n",
        "test_cases": [
            {
                "call": "sigmoid_activation([0.0, 2.0, -2.0])",
                "expected": "[0.5, 0.8808, 0.1192]",
                "input_desc": "[0.0, 2.0, -2.0]"
            },
            {
                "call": "sigmoid_activation([])",
                "expected": "[]",
                "input_desc": "empty list"
            },
            {
                "call": "sigmoid_activation([1.0, -1.0])",
                "expected": "[0.7311, 0.2689]",
                "input_desc": "[1.0, -1.0]"
            }
        ],
        "reference_solution": "import math\n\ndef sigmoid_activation(logits: list) -> list:\n    return [round(1.0 / (1.0 + math.exp(-z)), 4) for z in logits]\n"
    },
    {
        "id": "ml_gini_impurity",
        "course_id": 3,
        "topic_id": 20,
        "topic_title": "Decision Trees & Random Forests",
        "title": "Gini Impurity Split Criterion Calculator",
        "difficulty": "Intermediate",
        "outcome_code": "CO2",
        "description": "Implement `calculate_gini_impurity(labels: list) -> float` to measure the split purity of a decision tree node using Gini Impurity:\n$$I_G(p) = 1 - \\sum_{i=1}^J p_i^2$$\nwhere $p_i$ is the relative frequency of class $i$ in `labels`. Return the impurity rounded to **3 decimal places**. If `labels` is empty, return `0.0`.\n\n**Example 1:** `calculate_gini_impurity(['A', 'A', 'A'])` -> `0.0` (pure node)\n**Example 2:** `calculate_gini_impurity([1, 1, 0, 0])` -> `0.5`",
        "starter_code": "def calculate_gini_impurity(labels: list) -> float:\n    # TODO: Calculate Gini Impurity rounded to 3 decimal places\n    pass\n",
        "test_cases": [
            {
                "call": "calculate_gini_impurity(['A', 'A', 'A'])",
                "expected": "0.0",
                "input_desc": "pure node"
            },
            {
                "call": "calculate_gini_impurity([1, 1, 0, 0])",
                "expected": "0.5",
                "input_desc": "balanced binary split"
            },
            {
                "call": "calculate_gini_impurity(['cat', 'cat', 'dog', 'cat'])",
                "expected": "0.375",
                "input_desc": "3 cats, 1 dog"
            }
        ],
        "reference_solution": "def calculate_gini_impurity(labels: list) -> float:\n    if not labels:\n        return 0.0\n    total = len(labels)\n    counts = {}\n    for l in labels:\n        counts[l] = counts.get(l, 0) + 1\n    sum_sq = sum((cnt / total) ** 2 for cnt in counts.values())\n    return round(1.0 - sum_sq, 3)\n"
    },
    {
        "id": "ml_confusion_matrix_metrics",
        "course_id": 3,
        "topic_id": 21,
        "topic_title": "Model Evaluation & Validation",
        "title": "Binary Classification Evaluation Metrics (Precision, Recall, F1)",
        "difficulty": "Intermediate",
        "outcome_code": "CO4",
        "description": "Write `evaluate_classification(tp: int, fp: int, fn: int, tn: int) -> dict` computing Precision, Recall, and F1-Score from confusion matrix counts.\n- Precision = $\\frac{TP}{TP + FP}$\n- Recall = $\\frac{TP}{TP + FN}$\n- F1 = $\\frac{2 \\times P \\times R}{P + R}$\nRound each metric to **3 decimal places**. If any denominator is 0, set that metric to `0.0`.\nReturn dict: `{'precision': p, 'recall': r, 'f1': f1}`.",
        "starter_code": "def evaluate_classification(tp: int, fp: int, fn: int, tn: int) -> dict:\n    # TODO: Compute precision, recall, and f1-score rounded to 3 decimal places\n    pass\n",
        "test_cases": [
            {
                "call": "evaluate_classification(80, 20, 10, 90)",
                "expected": "{'precision': 0.8, 'recall': 0.889, 'f1': 0.842}",
                "input_desc": "TP=80, FP=20, FN=10, TN=90"
            },
            {
                "call": "evaluate_classification(0, 5, 5, 90)",
                "expected": "{'precision': 0.0, 'recall': 0.0, 'f1': 0.0}",
                "input_desc": "TP=0"
            }
        ],
        "reference_solution": "def evaluate_classification(tp: int, fp: int, fn: int, tn: int) -> dict:\n    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0\n    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0\n    f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0\n    return {'precision': round(p, 3), 'recall': round(r, 3), 'f1': round(f1, 3)}\n"
    },
    {
        "id": "ml_kmeans_assign_clusters",
        "course_id": 3,
        "topic_id": 22,
        "topic_title": "Clustering & K-Means",
        "title": "K-Means Nearest Centroid Assignment",
        "difficulty": "Intermediate",
        "outcome_code": "CO3",
        "description": "Write `assign_to_nearest_centroid(points: list, centroids: list) -> list` that assigns each 2D point `[x, y]` to the index of its closest centroid `[cx, cy]` based on squared Euclidean distance $(x - cx)^2 + (y - cy)^2$.\nReturn a list containing the centroid index `0 <= idx < len(centroids)` for each point.",
        "starter_code": "def assign_to_nearest_centroid(points: list, centroids: list) -> list:\n    # TODO: Return list of nearest centroid index (0-based) for each point\n    pass\n",
        "test_cases": [
            {
                "call": "assign_to_nearest_centroid([[1, 1], [9, 9], [1, 2]], [[0, 0], [10, 10]])",
                "expected": "[0, 1, 0]",
                "input_desc": "3 points, 2 centroids"
            },
            {
                "call": "assign_to_nearest_centroid([[5, 5]], [[2, 2], [6, 6]])",
                "expected": "[1]",
                "input_desc": "1 point closer to centroid 1"
            }
        ],
        "reference_solution": "def assign_to_nearest_centroid(points: list, centroids: list) -> list:\n    assignments = []\n    for p in points:\n        best_idx = 0\n        min_dist_sq = float('inf')\n        for c_idx, c in enumerate(centroids):\n            dist_sq = (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2\n            if dist_sq < min_dist_sq:\n                min_dist_sq = dist_sq\n                best_idx = c_idx\n        assignments.append(best_idx)\n    return assignments\n"
    },
    {
        "id": "ml_explained_variance_ratio",
        "course_id": 3,
        "topic_id": 23,
        "topic_title": "Dimensionality Reduction & PCA",
        "title": "PCA Explained Variance Ratio Calculator",
        "difficulty": "Intermediate",
        "outcome_code": "CO3",
        "description": "In Principal Component Analysis (PCA), the proportion of variance explained by the $i$-th principal component is $\\frac{\\lambda_i}{\\sum_{j=1}^k \\lambda_j}$, where $\\lambda$ are eigenvalues.\nWrite `explained_variance_ratio(eigenvalues: list) -> list` returning the ratio for each eigenvalue rounded to **3 decimal places**. If list is empty or sum is 0, return `[]`.",
        "starter_code": "def explained_variance_ratio(eigenvalues: list) -> list:\n    # TODO: Compute explained variance ratio rounded to 3 decimal places\n    pass\n",
        "test_cases": [
            {
                "call": "explained_variance_ratio([5.0, 3.0, 2.0])",
                "expected": "[0.5, 0.3, 0.2]",
                "input_desc": "[5.0, 3.0, 2.0]"
            },
            {
                "call": "explained_variance_ratio([7.5, 2.5])",
                "expected": "[0.75, 0.25]",
                "input_desc": "[7.5, 2.5]"
            }
        ],
        "reference_solution": "def explained_variance_ratio(eigenvalues: list) -> list:\n    total = sum(eigenvalues)\n    if not eigenvalues or total == 0:\n        return []\n    return [round(ev / total, 3) for ev in eigenvalues]\n"
    },
    {
        "id": "ml_relu_forward",
        "course_id": 3,
        "topic_id": 24,
        "topic_title": "Neural Networks & Backpropagation",
        "title": "Rectified Linear Unit (ReLU) Forward Activation",
        "difficulty": "Beginner",
        "outcome_code": "CO4",
        "description": "Write `relu_forward(inputs: list) -> list` simulating the forward pass of the ReLU activation function $f(x) = \\max(0.0, x)$.\nReturn a list of activated floats rounded to **2 decimal places**.",
        "starter_code": "def relu_forward(inputs: list) -> list:\n    # TODO: Apply ReLU activation max(0.0, x) rounded to 2 decimal places\n    pass\n",
        "test_cases": [
            {
                "call": "relu_forward([-3.5, 0.0, 4.2, -0.1, 7.8])",
                "expected": "[0.0, 0.0, 4.2, 0.0, 7.8]",
                "input_desc": "mixed inputs"
            },
            {
                "call": "relu_forward([-10, -5])",
                "expected": "[0.0, 0.0]",
                "input_desc": "all negative"
            }
        ],
        "reference_solution": "def relu_forward(inputs: list) -> list:\n    return [round(max(0.0, float(x)), 2) for x in inputs]\n"
    },
    {
        "id": "db_check_constraint_validator",
        "course_id": 4,
        "topic_id": 26,
        "topic_title": "SQL DDL & Integrity Constraints",
        "title": "Database DDL Integrity & Constraint Enforcer",
        "difficulty": "Intermediate",
        "outcome_code": "CO2",
        "description": "Simulate SQL DDL integrity constraints `NOT NULL` and `CHECK (age >= min_age)`.\nWrite `validate_table_constraints(records: list, required_fields: list, min_age: int) -> list` that filters a list of record dictionaries, returning only rows where all fields in `required_fields` are present and not `None`, and `record.get('age', 0) >= min_age`.",
        "starter_code": "def validate_table_constraints(records: list, required_fields: list, min_age: int) -> list:\n    # TODO: Return rows that satisfy NOT NULL and age >= min_age constraints\n    pass\n",
        "test_cases": [
            {
                "call": "validate_table_constraints([{'id': 1, 'name': 'Alice', 'age': 20}, {'id': 2, 'name': None, 'age': 25}, {'id': 3, 'name': 'Charlie', 'age': 16}], ['id', 'name'], 18)",
                "expected": "[{'id': 1, 'name': 'Alice', 'age': 20}]",
                "input_desc": "validates not null and age >= 18"
            },
            {
                "call": "validate_table_constraints([{'id': 1}], ['id', 'name'], 18)",
                "expected": "[]",
                "input_desc": "missing required name field"
            }
        ],
        "reference_solution": "def validate_table_constraints(records: list, required_fields: list, min_age: int) -> list:\n    valid = []\n    for r in records:\n        if all(f in r and r[f] is not None for f in required_fields) and r.get('age', 0) >= min_age:\n            valid.append(r)\n    return valid\n"
    },
    {
        "id": "db_group_by_aggregate",
        "course_id": 4,
        "topic_id": 27,
        "topic_title": "SQL DML & Aggregation Queries",
        "title": "SQL GROUP BY & Aggregation Simulation",
        "difficulty": "Intermediate",
        "outcome_code": "CO2",
        "description": "Simulate SQL `SELECT dept, SUM(amount) AS total FROM transactions GROUP BY dept`.\nWrite `aggregate_sales_by_department(transactions: list) -> dict` returning a dict mapping each department name to the total sum of amounts. If empty, return `{}`.",
        "starter_code": "def aggregate_sales_by_department(transactions: list) -> dict:\n    # TODO: Group by dept and sum amounts\n    pass\n",
        "test_cases": [
            {
                "call": "aggregate_sales_by_department([{'dept': 'A', 'amount': 100}, {'dept': 'B', 'amount': 50}, {'dept': 'A', 'amount': 25}])",
                "expected": "{'A': 125, 'B': 50}",
                "input_desc": "aggregates 3 transactions"
            },
            {
                "call": "aggregate_sales_by_department([])",
                "expected": "{}",
                "input_desc": "empty transactions"
            }
        ],
        "reference_solution": "def aggregate_sales_by_department(transactions: list) -> dict:\n    res = {}\n    for t in transactions:\n        dept = t.get('dept')\n        amt = t.get('amount', 0)\n        if dept:\n            res[dept] = res.get(dept, 0) + amt\n    return res\n"
    },
    {
        "id": "db_inner_join_simulator",
        "course_id": 4,
        "topic_id": 28,
        "topic_title": "Complex SQL Joins & Subqueries",
        "title": "Relational Table Inner Join Operation",
        "difficulty": "Intermediate",
        "outcome_code": "CO2",
        "description": "Simulate SQL `SELECT * FROM table_a INNER JOIN table_b ON table_a[join_key] = table_b[join_key]`.\nWrite `inner_join(table_a: list, table_b: list, join_key: str) -> list`. For every matching row between `table_a` and `table_b` sharing the same value for `join_key`, merge the dicts `{**row_a, **row_b}` and append to the result list.",
        "starter_code": "def inner_join(table_a: list, table_b: list, join_key: str) -> list:\n    # TODO: Perform inner join on table_a and table_b by join_key\n    pass\n",
        "test_cases": [
            {
                "call": "inner_join([{'id': 1, 'user': 'Alice'}, {'id': 2, 'user': 'Bob'}], [{'id': 1, 'city': 'NY'}, {'id': 3, 'city': 'LA'}], 'id')",
                "expected": "[{'id': 1, 'user': 'Alice', 'city': 'NY'}]",
                "input_desc": "matching id=1"
            },
            {
                "call": "inner_join([{'id': 1}], [{'id': 2}], 'id')",
                "expected": "[]",
                "input_desc": "no matching keys"
            }
        ],
        "reference_solution": "def inner_join(table_a: list, table_b: list, join_key: str) -> list:\n    result = []\n    for a in table_a:\n        for b in table_b:\n            if join_key in a and join_key in b and a[join_key] == b[join_key]:\n                merged = dict(a)\n                merged.update(b)\n                result.append(merged)\n    return result\n"
    },
    {
        "id": "db_relational_project_select",
        "course_id": 4,
        "topic_id": 29,
        "topic_title": "Relational Algebra Operations",
        "title": "Relational Algebra Selection & Projection Simulator",
        "difficulty": "Intermediate",
        "outcome_code": "CO1",
        "description": "Simulate relational algebra $\\Pi_{\\text{project\\_cols}}(\\sigma_{\\text{predicate\\_col} = \\text{predicate\\_val}}(R))$.\nWrite `relational_select_project(relation: list, predicate_col: str, predicate_val: any, project_cols: list) -> list` that filters rows where `row[predicate_col] == predicate_val`, and for each matching row retains only the columns specified in `project_cols`.",
        "starter_code": "def relational_select_project(relation: list, predicate_col: str, predicate_val: any, project_cols: list) -> list:\n    # TODO: Perform selection (sigma) and projection (pi)\n    pass\n",
        "test_cases": [
            {
                "call": "relational_select_project([{'id': 1, 'role': 'admin', 'name': 'Ada'}, {'id': 2, 'role': 'user', 'name': 'Bob'}], 'role', 'admin', ['id', 'name'])",
                "expected": "[{'id': 1, 'name': 'Ada'}]",
                "input_desc": "filters role=admin and projects id, name"
            },
            {
                "call": "relational_select_project([{'id': 1, 'dept': 'HR', 'sal': 50}], 'dept', 'ENG', ['id'])",
                "expected": "[]",
                "input_desc": "no matching selection"
            }
        ],
        "reference_solution": "def relational_select_project(relation: list, predicate_col: str, predicate_val: any, project_cols: list) -> list:\n    result = []\n    for r in relation:\n        if r.get(predicate_col) == predicate_val:\n            projected = {k: r[k] for k in project_cols if k in r}\n            result.append(projected)\n    return result\n"
    },
    {
        "id": "db_fd_closure",
        "course_id": 4,
        "topic_id": 30,
        "topic_title": "Functional Dependencies & 1NF-3NF",
        "title": "Functional Dependency Attribute Closure Calculator",
        "difficulty": "Intermediate",
        "outcome_code": "CO3",
        "description": "In database normalization, given a set of attributes $X$ and a set of functional dependencies $F$, compute the attribute closure $X^+$.\nWrite `compute_attribute_closure(attributes: list, functional_dependencies: list) -> list`. Each FD is a dict `{'from': [...], 'to': [...]}`. Return a **sorted list** of all attributes in the closure.",
        "starter_code": "def compute_attribute_closure(attributes: list, functional_dependencies: list) -> list:\n    # TODO: Compute attribute closure X+ and return sorted list\n    pass\n",
        "test_cases": [
            {
                "call": "compute_attribute_closure(['A'], [{'from': ['A'], 'to': ['B']}, {'from': ['B'], 'to': ['C']}])",
                "expected": "['A', 'B', 'C']",
                "input_desc": "A -> B and B -> C"
            },
            {
                "call": "compute_attribute_closure(['X'], [{'from': ['A'], 'to': ['B']}])",
                "expected": "['X']",
                "input_desc": "no applicable FDs"
            }
        ],
        "reference_solution": "def compute_attribute_closure(attributes: list, functional_dependencies: list) -> list:\n    closure = set(attributes)\n    changed = True\n    while changed:\n        changed = False\n        for fd in functional_dependencies:\n            lhs = set(fd.get('from', []))\n            rhs = set(fd.get('to', []))\n            if lhs.issubset(closure) and not rhs.issubset(closure):\n                closure.update(rhs)\n                changed = True\n    return sorted(list(closure))\n"
    },
    {
        "id": "db_index_range_scan",
        "course_id": 4,
        "topic_id": 31,
        "topic_title": "Indexing & B-Tree Storage",
        "title": "B-Tree Leaf Node Range Scan Simulator",
        "difficulty": "Intermediate",
        "outcome_code": "CO3",
        "description": "Simulate an index range scan in a B-Tree storage engine. Given a list of sorted `(key, record_id)` tuples, write `b_tree_range_scan(indexed_records: list, low_key: int, high_key: int) -> list` returning the list of `record_id`s whose key satisfies `low_key <= key <= high_key`.",
        "starter_code": "def b_tree_range_scan(indexed_records: list, low_key: int, high_key: int) -> list:\n    # TODO: Return record_ids where low_key <= key <= high_key\n    pass\n",
        "test_cases": [
            {
                "call": "b_tree_range_scan([(10, 1), (20, 2), (30, 3), (40, 4), (50, 5)], 20, 40)",
                "expected": "[2, 3, 4]",
                "input_desc": "scan between 20 and 40 inclusive"
            },
            {
                "call": "b_tree_range_scan([(5, 10), (15, 20)], 50, 100)",
                "expected": "[]",
                "input_desc": "no records in range"
            }
        ],
        "reference_solution": "def b_tree_range_scan(indexed_records: list, low_key: int, high_key: int) -> list:\n    return [rec_id for key, rec_id in indexed_records if low_key <= key <= high_key]\n"
    },
    {
        "id": "db_acid_validator",
        "course_id": 4,
        "topic_id": 32,
        "topic_title": "Transactions, ACID & Concurrency",
        "title": "ACID Account Balance Transfer Validator",
        "difficulty": "Intermediate",
        "outcome_code": "CO4",
        "description": "Write a function `execute_transfer(balance_a, balance_b, amount)` simulating an atomic transaction.\nIf `balance_a >= amount and amount > 0`, deduct from A, credit B, and return `{'status': 'COMMITTED', 'a': balance_a - amount, 'b': balance_b + amount}`.\nOtherwise, rollback without changes and return `{'status': 'ROLLEDBACK', 'a': balance_a, 'b': balance_b}`.",
        "starter_code": "def execute_transfer(balance_a: int, balance_b: int, amount: int) -> dict:\n    # TODO: Simulate atomic transaction transfer between accounts A and B\n    pass\n",
        "test_cases": [
            {
                "call": "execute_transfer(100, 50, 40)",
                "expected": "{'status': 'COMMITTED', 'a': 60, 'b': 90}",
                "input_desc": "balance_a=100, balance_b=50, amount=40"
            },
            {
                "call": "execute_transfer(30, 50, 40)",
                "expected": "{'status': 'ROLLEDBACK', 'a': 30, 'b': 50}",
                "input_desc": "balance_a=30, balance_b=50, amount=40"
            }
        ],
        "reference_solution": "def execute_transfer(balance_a: int, balance_b: int, amount: int) -> dict:\n    if balance_a >= amount and amount > 0:\n        return {'status': 'COMMITTED', 'a': balance_a - amount, 'b': balance_b + amount}\n    return {'status': 'ROLLEDBACK', 'a': balance_a, 'b': balance_b}\n"
    }
]

# ==============================================================================
# Helper: Challenge Selector
# ==============================================================================

def get_coding_challenge(course_id: int = 2, topic_id: Optional[int] = None, topic_title: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Selects the best matching coding challenge for a course or specific topic.
    Strictly prevents cross-course challenge fallback.
    Returns None if no matching challenge exists for the topic in this course.
    """
    # 1. Exact match on both course_id and topic_id
    if topic_id is not None:
        for c in CODING_CHALLENGES:
            if c.get("course_id") == course_id and c.get("topic_id") == topic_id:
                return c

    # 2. Match topic title keyword within the SAME course
    if topic_title:
        title_lower = topic_title.lower()
        for c in CODING_CHALLENGES:
            if c.get("course_id") == course_id:
                c_title = c.get("topic_title", "").lower()
                if c_title in title_lower or title_lower in c_title:
                    return c
        for c in CODING_CHALLENGES:
            if c.get("course_id") == course_id:
                words = [w for w in title_lower.split() if len(w) > 3]
                for w in words:
                    if w in c.get("topic_title", "").lower() or w in c.get("title", "").lower():
                        return c

    # NO CROSS-COURSE FALLBACK! Return None if no challenge matches this topic in this course
    return None

# ==============================================================================
# 2. Container-Isolated Code Execution Sandbox & Automated Test Harness
# ==============================================================================

# Friendly early-rejection pattern list (UX guidance only, NOT the security boundary).
# The security boundary is strict container isolation with dropped capabilities and no network.
DANGEROUS_PATTERNS = [
    "import os", "from os", "import sys", "from sys",
    "import subprocess", "from subprocess",
    "import shutil", "from shutil", "import socket", "from socket",
    "open(", "__import__", "exec(", "eval(", "input("
]

def generate_container_test_harness(code: str, test_cases: List[Dict[str, Any]]) -> str:
    """
    Constructs the self-contained Python test harness to be executed inside the container.
    Student code is compiled and executed first; validated test cases are then evaluated
    strictly inside the container. Student prints are capped at 64 KB.
    """
    code_repr = repr(code)
    tc_json = json.dumps(test_cases)

    return f"""import sys
import json
import io
import traceback

MAX_OUTPUT = 65536

# Capture student print outputs to avoid interfering with harness protocol
_user_stdout_capture = io.StringIO()
_orig_stdout = sys.stdout
sys.stdout = _user_stdout_capture

_student_code_raw = {code_repr}

try:
    _compiled_student_code = compile(_student_code_raw, "<student_code>", "exec")
    exec(_compiled_student_code, globals())
except Exception as _compile_err:
    sys.stdout = _orig_stdout
    tb = traceback.format_exc()
    lines = tb.splitlines()
    clean_err = "\\n".join(lines[-4:]) if len(lines) >= 4 else tb
    print(clean_err[:MAX_OUTPUT], file=sys.stderr)
    sys.exit(1)

sys.stdout = _orig_stdout
_raw_user_stdout = _user_stdout_capture.getvalue()
if len(_raw_user_stdout) > MAX_OUTPUT:
    _raw_user_stdout = _raw_user_stdout[:MAX_OUTPUT] + "\\n... [STDOUT TRUNCATED AT 64KB] ..."

# Automated Test Case Evaluation (Strictly evaluated INSIDE the isolated container)
results = []
test_cases = {tc_json}

for idx, tc in enumerate(test_cases):
    call_expr = tc.get('call', '')
    expected_str = str(tc.get('expected', '')).strip()
    try:
        # Client call expression is evaluated strictly within this isolated container
        actual_val = eval(call_expr, globals())
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
            'actual': actual_str[:4096],
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
            'error': str(e)[:1024]
        }})

print(_raw_user_stdout)
print("---JSON_OUTPUT_DELIMITER---")
print(json.dumps(results))
"""

def _parse_harness_output(
    stdout_full: str,
    stderr_full: str,
    returncode: int,
    test_cases: List[Dict[str, Any]],
    elapsed_ms: int
) -> Dict[str, Any]:
    """Parses harness stdout/stderr and returns structured compile test results."""
    if "---JSON_OUTPUT_DELIMITER---" not in stdout_full:
        error_message = stderr_full.strip() or stdout_full.strip() or "Syntax or Runtime Error occurred."
        clean_error = error_message
        if "Traceback" in error_message:
            lines = error_message.splitlines()
            clean_error = "\n".join(lines[-4:])

        return {
            "success": False,
            "all_passed": False,
            "passed_count": 0,
            "total_count": len(test_cases),
            "percentage": 0.0,
            "stdout": stdout_full[:MAX_STDOUT_BYTES],
            "stderr": clean_error[:MAX_STDERR_BYTES],
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

    parts = stdout_full.split("---JSON_OUTPUT_DELIMITER---")
    user_stdout = parts[0].strip()[:MAX_STDOUT_BYTES]
    json_results_str = parts[1].strip()
    try:
        parsed_results = json.loads(json_results_str)
    except Exception as json_err:
        return {
            "success": False,
            "all_passed": False,
            "passed_count": 0,
            "total_count": len(test_cases),
            "percentage": 0.0,
            "stdout": user_stdout,
            "stderr": f"Failed to parse test execution results: {str(json_err)}"[:MAX_STDERR_BYTES],
            "results": [],
            "execution_time_ms": elapsed_ms
        }

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
        "stderr": stderr_full.strip()[:MAX_STDERR_BYTES] if returncode != 0 else "",
        "results": parsed_results,
        "execution_time_ms": elapsed_ms
    }

def _run_in_docker_container(
    harness_script: str,
    test_cases: List[Dict[str, Any]],
    timeout_sec: float
) -> Dict[str, Any]:
    """
    Executes the harness script inside a fresh, isolated Docker container with strict constraints:
    - --network none
    - --read-only
    - --tmpfs /tmp:rw,noexec,nosuid,size=16m
    - --memory 128m --memory-swap 128m
    - --cpus 0.5
    - --pids-limit 64
    - --cap-drop ALL
    - --security-opt no-new-privileges
    - --user sandboxuser
    - --rm
    - No host volume mounts (passed via stdin)
    """
    start_time = time.time()
    container_name = f"obepath-sandbox-{uuid.uuid4().hex[:12]}"
    docker_bin = shutil.which("docker") or "docker"

    cmd = [
        docker_bin, "run",
        "-i",
        "--name", container_name,
        "--network", "none",
        "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
        "--memory", "128m",
        "--memory-swap", "128m",
        "--cpus", "0.5",
        "--pids-limit", "64",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--user", "sandboxuser",
        "--rm",
        SANDBOX_IMAGE
    ]

    try:
        proc = subprocess.run(
            cmd,
            input=harness_script.encode("utf-8"),
            capture_output=True,
            timeout=timeout_sec
        )
        elapsed_ms = round((time.time() - start_time) * 1000)
        stdout_full = proc.stdout.decode("utf-8", errors="replace")[:MAX_STDOUT_BYTES]
        stderr_full = proc.stderr.decode("utf-8", errors="replace")[:MAX_STDERR_BYTES]

        # Check for OOM kill (exit code 137)
        if proc.returncode == 137:
            return {
                "success": False,
                "all_passed": False,
                "passed_count": 0,
                "total_count": len(test_cases),
                "percentage": 0.0,
                "stdout": stdout_full,
                "stderr": "Memory Limit Exceeded (128 MB limit reached). Code execution terminated.",
                "results": [
                    {
                        "test_idx": i + 1,
                        "call": tc.get("call"),
                        "input_desc": tc.get("input_desc"),
                        "expected": tc.get("expected"),
                        "actual": "Memory Limit Exceeded",
                        "passed": False,
                        "error": "OOMKilled"
                    }
                    for i, tc in enumerate(test_cases)
                ],
                "execution_time_ms": elapsed_ms
            }

        return _parse_harness_output(stdout_full, stderr_full, proc.returncode, test_cases, elapsed_ms)

    except subprocess.TimeoutExpired:
        elapsed_ms = round((time.time() - start_time) * 1000)
        # Ensure container is forcefully killed and removed on timeout
        try:
            subprocess.run([docker_bin, "kill", container_name], capture_output=True, timeout=2.0)
        except Exception:
            pass
        try:
            subprocess.run([docker_bin, "rm", "-f", container_name], capture_output=True, timeout=2.0)
        except Exception:
            pass

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
        elapsed_ms = round((time.time() - start_time) * 1000)
        return {
            "success": False,
            "all_passed": False,
            "passed_count": 0,
            "total_count": len(test_cases),
            "percentage": 0.0,
            "stdout": "",
            "stderr": f"Sandbox Execution Error: {str(e)}"[:MAX_STDERR_BYTES],
            "results": [],
            "execution_time_ms": elapsed_ms
        }

def _run_in_local_subprocess(
    harness_script: str,
    test_cases: List[Dict[str, Any]],
    timeout_sec: float
) -> Dict[str, Any]:
    """
    Dev-only local subprocess fallback when SANDBOX_ALLOW_UNSAFE_LOCAL=true in non-production.
    Emits loud security warning.
    """
    logger.warning(
        "CRITICAL SECURITY WARNING: Docker is unavailable. Running code in UNSAFE host mode "
        "because SANDBOX_ALLOW_UNSAFE_LOCAL=true. THIS MUST NEVER BE USED IN PRODUCTION!"
    )
    start_time = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, "-c", harness_script],
            capture_output=True,
            timeout=timeout_sec
        )
        elapsed_ms = round((time.time() - start_time) * 1000)
        stdout_full = proc.stdout.decode("utf-8", errors="replace")[:MAX_STDOUT_BYTES]
        stderr_full = proc.stderr.decode("utf-8", errors="replace")[:MAX_STDERR_BYTES]
        return _parse_harness_output(stdout_full, stderr_full, proc.returncode, test_cases, elapsed_ms)
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
        elapsed_ms = round((time.time() - start_time) * 1000)
        return {
            "success": False,
            "all_passed": False,
            "passed_count": 0,
            "total_count": len(test_cases),
            "percentage": 0.0,
            "stdout": "",
            "stderr": f"Execution Error: {str(e)}"[:MAX_STDERR_BYTES],
            "results": [],
            "execution_time_ms": elapsed_ms
        }

def execute_code_submission(
    code: str,
    test_cases: List[Dict[str, Any]],
    timeout_sec: float = DEFAULT_TIMEOUT_SEC
) -> Dict[str, Any]:
    """
    Executes student python code in the secure container sandbox and validates against test cases.
    Fails closed if Docker is unavailable unless SANDBOX_ALLOW_UNSAFE_LOCAL=true in development.
    """
    # 1. Cap inputs
    if not isinstance(code, str) or len(code) > MAX_CODE_CHARS:
        return {
            "success": False,
            "all_passed": False,
            "passed_count": 0,
            "total_count": len(test_cases),
            "percentage": 0.0,
            "stdout": "",
            "stderr": f"Code length exceeds maximum allowed limit of {MAX_CODE_CHARS} characters.",
            "results": [],
            "execution_time_ms": 0
        }

    try:
        timeout_sec = min(max(float(timeout_sec), MIN_TIMEOUT_SEC), MAX_TIMEOUT_SEC)
    except (ValueError, TypeError):
        timeout_sec = DEFAULT_TIMEOUT_SEC

    # 2. Friendly early-rejection blacklist (UX notice only, not security boundary)
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

    # 3. Fail closed if Docker is unavailable
    docker_available = check_docker_available()
    if not docker_available:
        env_val = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
        if env_val in ("production", "prod"):
            raise DockerUnavailableError("Server-side execution is disabled; use in-browser runner")
        if is_unsafe_local_allowed():
            harness = generate_container_test_harness(code, test_cases)
            return _run_in_local_subprocess(harness, test_cases, timeout_sec)
        else:
            raise DockerUnavailableError("Code execution temporarily unavailable")

    # 4. Run in fresh isolated Docker container
    harness = generate_container_test_harness(code, test_cases)
    return _run_in_docker_container(harness, test_cases, timeout_sec)

