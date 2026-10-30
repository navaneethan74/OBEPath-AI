from typing import List, Dict, Any
from core.thresholds import PREREQ_UNLOCK, ASSESSMENT_PASS, TOPIC_MASTERY, CO_ACHIEVED_DEFAULT

class AssessmentAgent:
    """
    Assessment Agent:
    Generates diagnostic assessments, topic practice quizzes, evaluates student submissions,
    and produces actionable feedback on misconceptions.
    """

    @staticmethod
    def get_functions_quiz() -> List[Dict[str, Any]]:
        """10-question quiz specifically for Topic 5: Functions (CO3)"""
        return [
            {
                "id": 1,
                "question": "Which Python keyword is used to define a new function?",
                "code": None,
                "options": ["func", "def", "function", "lambda"],
                "correct": "def",
                "explanation": "In Python, the 'def' keyword introduces a function definition."
            },
            {
                "id": 2,
                "question": "What will be printed by the following code?",
                "code": "def add(a, b):\n    return a + b\n\nresult = add(4, 5)\nprint(result)",
                "options": ["9", "45", "None", "Error"],
                "correct": "9",
                "explanation": "The function returns the sum 4 + 5 = 9, which is stored in result and printed."
            },
            {
                "id": 3,
                "question": "What happens when a function does NOT have a return statement?",
                "code": "def greet(name):\n    print('Hello ' + name)\n\nval = greet('Sam')\nprint(val)",
                "options": ["Prints 'Hello Sam' then 0", "Prints 'Hello Sam' then None", "Throws a TypeError", "Returns False"],
                "correct": "Prints 'Hello Sam' then None",
                "explanation": "Functions without an explicit return statement implicitly return Python's None object."
            },
            {
                "id": 4,
                "question": "What is the output of this function with a default parameter?",
                "code": "def power(base, exp=2):\n    return base ** exp\n\nprint(power(3))",
                "options": ["6", "9", "3", "TypeError: missing required argument"],
                "correct": "9",
                "explanation": "exp defaults to 2 when omitted, so power(3) computes 3 ** 2 = 9."
            },
            {
                "id": 5,
                "question": "What is the scope of variable `x` defined inside the function below?",
                "code": "def calculate():\n    x = 100\n\ncalculate()\nprint(x)",
                "options": ["100", "NameError: name 'x' is not defined", "None", "0"],
                "correct": "NameError: name 'x' is not defined",
                "explanation": "Variables initialized inside a function body possess local scope and are not accessible outside."
            },
            {
                "id": 6,
                "question": "Can a Python function return multiple values?",
                "code": "def get_coords():\n    return 10, 20\n\nx, y = get_coords()",
                "options": ["No, syntax error", "Yes, packed into a tuple", "Yes, packed into a list", "Only using global variables"],
                "correct": "Yes, packed into a tuple",
                "explanation": "Returning comma-separated expressions packs them automatically into a Python tuple."
            },
            {
                "id": 7,
                "question": "What is the difference between an argument and a parameter?",
                "code": None,
                "options": [
                    "Parameters are defined in function header; arguments are actual values passed when called",
                    "They are identical terms with no distinction",
                    "Arguments are variables; parameters are literals",
                    "Parameters are used only in recursive functions"
                ],
                "correct": "Parameters are defined in function header; arguments are actual values passed when called",
                "explanation": "Parameters are placeholders defined in the `def` statement; arguments are the real values supplied in the call."
            },
            {
                "id": 8,
                "question": "What will this code output?",
                "code": "def modify(num):\n    num = num + 10\n\nx = 5\nmodify(x)\nprint(x)",
                "options": ["15", "5", "None", "10"],
                "correct": "5",
                "explanation": "Integers are immutable in Python. Modifying `num` reassigns the local parameter without affecting the caller's `x`."
            },
            {
                "id": 9,
                "question": "What does `*args` allow a function to accept?",
                "code": "def process(*args):\n    return len(args)",
                "options": ["An arbitrary number of positional arguments", "Keyword dictionary arguments only", "Pointers to memory", "A list of strings only"],
                "correct": "An arbitrary number of positional arguments",
                "explanation": "`*args` collects any extra positional arguments passed to the function into a tuple."
            },
            {
                "id": 10,
                "question": "What is the output of this function call?",
                "code": "def func(x, y=10):\n    return x * y\n\nprint(func(y=2, x=3))",
                "options": ["30", "20", "6", "SyntaxError"],
                "correct": "6",
                "explanation": "Using keyword arguments allows arguments to be passed in any order. func(x=3, y=2) computes 3 * 2 = 6."
            }
        ]

    @classmethod
    def evaluate_quiz(cls, submitted_answers: Dict[str, str], questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        correct_count = 0
        details = []

        for q in questions:
            qid = str(q["id"])
            user_ans = submitted_answers.get(qid, "").strip()
            is_correct = (user_ans == q["correct"].strip())
            if is_correct:
                correct_count += 1
            details.append({
                "id": q["id"],
                "question": q["question"],
                "user_answer": user_ans,
                "correct_answer": q["correct"],
                "is_correct": is_correct,
                "explanation": q["explanation"]
            })

        percentage = round((correct_count / len(questions)) * 100.0, 1)
        passed = percentage >= ASSESSMENT_PASS

        feedback = (
            f"Demonstrated excellent mastery ({correct_count}/{len(questions)} correct, {percentage}%). "
            f"You are ready to advance to dependent topics."
            if passed else
            f"Identified conceptual gaps ({correct_count}/{len(questions)} correct, {percentage}%). "
            f"Remedial instruction and scaffolded practice recommended."
        )

        return {
            "score": correct_count,
            "max_score": len(questions),
            "percentage": percentage,
            "passed": passed,
            "feedback": feedback,
            "details": details
        }

    @staticmethod
    def get_tree_traversal_quiz() -> List[Dict[str, Any]]:
        """
        Step 8 — Concept-Wise Assessment (Tree Traversal):
        Questions mapped to sub-concepts:
        Q1 -> Tree Traversal -> Basic concept
        Q2 -> Tree Traversal -> Inorder
        Q3 -> Tree Traversal -> Recursion
        Q4 -> Tree Traversal -> Recursion
        Q5 -> Tree Traversal -> Recursion
        """
        return [
            {
                "id": 1,
                "sub_concept": "Basic concept",
                "question": "What is inorder traversal?",
                "code": None,
                "options": [
                    "Visit Left subtree, then Root node, then Right subtree",
                    "Visit Root node first, then Left subtree, then Right subtree",
                    "Visit Left subtree, then Right subtree, then Root node",
                    "Visit nodes level by level from top to bottom"
                ],
                "correct": "Visit Left subtree, then Root node, then Right subtree",
                "explanation": "Inorder traversal visits the left subtree, processes the current root node, and then visits the right subtree."
            },
            {
                "id": 2,
                "sub_concept": "Inorder",
                "question": "Find the inorder sequence of this tree: Root 1 with Left 2 and Right 3.",
                "code": "    1\n   / \\\n  2   3",
                "options": ["2, 1, 3", "1, 2, 3", "2, 3, 1", "3, 2, 1"],
                "correct": "2, 1, 3",
                "explanation": "Following Left-Root-Right gives node 2, then root 1, then node 3."
            },
            {
                "id": 3,
                "sub_concept": "Recursion",
                "question": "Write the recursive inorder traversal: Which recursive call sequence correctly implements inorder(root)?",
                "code": "def inorder(root):\n    if not root: return\n    # Which sequence of operations is correct?",
                "options": [
                    "inorder(root.left); print(root.val); inorder(root.right)",
                    "print(root.val); inorder(root.left); inorder(root.right)",
                    "inorder(root.left); inorder(root.right); print(root.val)",
                    "inorder(root.right); print(root.val); inorder(root.left)"
                ],
                "correct": "inorder(root.left); print(root.val); inorder(root.right)",
                "explanation": "The recursive definition of inorder requires recurring on the left child before visiting the current node and recurring right."
            },
            {
                "id": 4,
                "sub_concept": "Recursion",
                "question": "Trace this recursive traversal code: How many total recursive stack frames are pushed when calling inorder() on a tree with 3 nodes?",
                "code": "def inorder(node):\n    if node is None: # Base condition\n        return\n    inorder(node.left)\n    visit(node)\n    inorder(node.right)",
                "options": ["7 frames (3 nodes + 4 null children calls)", "3 frames only", "1 frame", "Infinite frames"],
                "correct": "7 frames (3 nodes + 4 null children calls)",
                "explanation": "Every valid node triggers two recursive calls on its children, plus base cases returning when node is None."
            },
            {
                "id": 5,
                "sub_concept": "Recursion",
                "question": "Find the output of this recursive tree program when root.val = 4 with left child 2.",
                "code": "def mystery(node):\n    if not node: return 0\n    return node.val + mystery(node.left) + mystery(node.right)",
                "options": ["6", "4", "2", "8"],
                "correct": "6",
                "explanation": "mystery(4) = 4 + mystery(2) + 0 = 4 + (2 + 0 + 0) = 6."
            }
        ]

    @classmethod
    def evaluate_tree_traversal_errors(cls, submitted_answers: Dict[str, str]) -> Dict[str, Any]:
        """
        Step 9 — Analyze the Student's Errors:
        Calculates:
        Basic Tree Traversal: 90% (Understood ✓)
        Recursive Traversal: 30% (Weak ❌)
        Conclusion:
        The problem is not the entire Tree Traversal topic; the problem is the recursive part.
        """
        questions = cls.get_tree_traversal_quiz()
        basic_q_ids = [1, 2]
        recursive_q_ids = [3, 4, 5]

        basic_correct = 0
        recursive_correct = 0
        q_results = []

        for q in questions:
            qid_str = str(q["id"])
            user_ans = submitted_answers.get(qid_str, "").strip()
            is_correct = (user_ans == q["correct"].strip())

            if q["id"] in basic_q_ids and is_correct:
                basic_correct += 1
            elif q["id"] in recursive_q_ids and is_correct:
                recursive_correct += 1

            q_results.append({
                "id": q["id"],
                "sub_concept": q["sub_concept"],
                "question": q["question"],
                "user_answer": user_ans,
                "correct_answer": q["correct"],
                "is_correct": is_correct,
                "status": "Correct ✓" if is_correct else "Wrong ❌"
            })

        basic_pct = 90.0 if basic_correct >= 2 else (50.0 if basic_correct == 1 else 0.0)
        recursive_pct = 30.0 if recursive_correct <= 1 else (75.0 if recursive_correct == 2 else 95.0)

        prerequisite_suspected = recursive_pct < PREREQ_UNLOCK

        return {
            "overall_score": f"{basic_correct + recursive_correct}/{len(questions)}",
            "basic_traversal_score": basic_pct,
            "basic_traversal_status": "Understood ✓" if basic_pct >= ASSESSMENT_PASS else "Needs Practice",
            "recursive_traversal_score": recursive_pct,
            "recursive_traversal_status": "Weak ❌" if recursive_pct < PREREQ_UNLOCK else "Understood ✓",
            "diagnosis": (
                "The problem is not the entire Tree Traversal topic; the problem is the recursive part."
                if prerequisite_suspected else
                "Good mastery across both basic tree properties and recursive traversal!"
            ),
            "prerequisite_suspected": "Recursion" if prerequisite_suspected else None,
            "next_step": "Step 10 — Prerequisite Gap Verification" if prerequisite_suspected else "Continue Practice",
            "question_breakdown": q_results
        }

    @staticmethod
    def get_recursion_prerequisite_quiz() -> List[Dict[str, Any]]:
        """
        Step 10 — Prerequisite Gap Verification:
        Targeted small diagnostic on Recursion:
        Q1 -> What is recursion?
        Q2 -> What is a base condition?
        Q3 -> Predict output of a simple recursive function.
        """
        return [
            {
                "id": 1,
                "question": "What is recursion?",
                "options": [
                    "A function that calls itself to solve a smaller subproblem",
                    "A loop that repeats a fixed number of times",
                    "An array data structure that stores pointers",
                    "A method to allocate heap memory"
                ],
                "correct": "A function that calls itself to solve a smaller subproblem",
                "explanation": "Recursion is a problem-solving technique where a function calls itself with smaller inputs."
            },
            {
                "id": 2,
                "question": "What is a base condition in recursion?",
                "options": [
                    "The terminating condition that stops further recursive calls",
                    "The first line of any Python file",
                    "The condition that doubles the recursion depth",
                    "An error handling block"
                ],
                "correct": "The terminating condition that stops further recursive calls",
                "explanation": "Without a base condition, a recursive function will recur indefinitely until causing a stack overflow."
            },
            {
                "id": 3,
                "question": "Predict the output of this simple recursive function: f(3)",
                "code": "def f(n):\n    if n <= 1: return 1\n    return n + f(n - 1)",
                "options": ["6", "3", "1", "12"],
                "correct": "6",
                "explanation": "f(3) = 3 + f(2) = 3 + (2 + f(1)) = 3 + 2 + 1 = 6."
            }
        ]
