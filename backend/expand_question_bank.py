import json
import sqlite3

def expand_questions():
    conn = sqlite3.connect("obe_learning.db")
    c = conn.cursor()

    # Course 2 (CS201) topics 1..8
    # Topic 1: Stack Basics (CO1=1, CO2=2)
    # Topic 2: Queue Basics (CO1=1, CO2=2)
    # Topic 3: Recursion Fundamentals (CO1=1, CO2=2, CO3=3)
    # Topic 4: Tree Basics (CO1=1, CO2=2)
    # Topic 5: Tree Traversal (CO2=2, CO3=3)
    # Topic 6: Recursive Practice (CO2=2, CO3=3)
    # Topic 7: Tree Problems (CO2=2, CO4=4)
    # Topic 8: Algorithm Complexity (CO3=3, CO4=4)

    extra_questions = [
        # Topic 1: Stack
        (2, 1, 2, "Stack Overflow", "Intermediate", "mcq",
         "In a bounded array-based stack implementation of capacity 5, what happens if push() is called when the stack pointer top == 4?",
         None,
         json.dumps(["Stack Overflow error", "Stack Underflow error", "Element is overwritten at index 0", "Capacity automatically doubles without error"]),
         "Stack Overflow error",
         "Attempting to push an element into a statically bounded stack that is already full triggers a Stack Overflow condition."),
        (2, 1, 2, "Postfix Evaluation", "Advanced", "code_logic",
         "How is the postfix expression '5 3 + 2 *' evaluated using an operand stack?",
         "Expression: 5 3 + 2 *",
         json.dumps(["16", "11", "13", "30"]),
         "16",
         "5 and 3 are pushed, '+' pops them and pushes 8; 2 is pushed, '*' pops them and computes 8 * 2 = 16."),

        # Topic 2: Queue
        (2, 2, 1, "Priority Queue", "Beginner", "mcq",
         "In a priority queue, elements are dequeued according to what criteria?",
         None,
         json.dumps(["Element priority/value", "Arrival time only", "Random order", "Storage address"]),
         "Element priority/value",
         "A priority queue serves elements with highest priority before elements with lower priority regardless of arrival sequence."),
        (2, 2, 2, "Queue Efficiency", "Intermediate", "mcq",
         "What is the time complexity of enqueue and dequeue operations in an optimal doubly-linked queue with head and tail pointers?",
         None,
         json.dumps(["O(1) time complexity", "O(n) time complexity", "O(log n) time complexity", "O(n^2) time complexity"]),
         "O(1) time complexity",
         "Maintaining direct pointers to both head and tail allows constant-time O(1) insertions and removals."),

        # Topic 3: Recursion
        (2, 3, 1, "Base Condition", "Beginner", "mcq",
         "What is the base case in a recursive function that calculates the sum of numbers from n down to 1?",
         None,
         json.dumps(["if n <= 1: return 1", "if n > 1: return n", "while n > 0: n -= 1", "return n * (n - 1)"]),
         "if n <= 1: return 1",
         "The base case is the halting condition where no further recursive calls are triggered."),
        (2, 3, 3, "Tail Recursion", "Advanced", "mcq",
         "What is 'Tail Recursion' and why is it optimized by modern compilers?",
         None,
         json.dumps(["The recursive call is the very last operation, allowing stack frame reuse", "The recursive call occurs before any local variables are declared", "The function calls two recursive subproblems simultaneously", "The recursion uses a loop instead of a call stack"]),
         "The recursive call is the very last operation, allowing stack frame reuse",
         "Tail call elimination allows compilers to reuse the current stack frame rather than growing new stack frames for each call."),

        # Topic 4: Tree Basics
        (2, 4, 1, "Tree Depth", "Beginner", "mcq",
         "What is the depth of the root node in a standard tree hierarchy?",
         None,
         json.dumps(["0", "1", "-1", "Equal to the tree height"]),
         "0",
         "By standard convention, the root node has depth 0 (distance 0 edges from itself)."),
        (2, 4, 2, "Full Binary Tree", "Intermediate", "mcq",
         "In a strictly full binary tree with L leaf nodes, how many internal (non-leaf) nodes exist?",
         None,
         json.dumps(["L - 1", "2L", "L / 2", "L + 1"]),
         "L - 1",
         "In any full binary tree (where each internal node has exactly 2 children), the number of internal nodes is strictly L - 1."),

        # Topic 5: Tree Traversal
        (2, 5, 2, "BST Inorder Traversal", "Beginner", "mcq",
         "In a Binary Search Tree (BST), which traversal produces the values in strictly sorted ascending order?",
         None,
         json.dumps(["Inorder traversal (Left, Root, Right)", "Preorder traversal (Root, Left, Right)", "Postorder traversal (Left, Right, Root)", "Level-order traversal (Breadth-First)"]),
         "Inorder traversal (Left, Root, Right)",
         "Inorder visits left subtree (< root), current root, then right subtree (> root), yielding elements in ascending order."),
        (2, 5, 3, "Postorder Sequence", "Intermediate", "code_logic",
         "For a tree with root 4, left child 2, and right child 5, what is the Postorder traversal sequence?",
         "    4\n   / \\\n  2   5",
         json.dumps(["2, 5, 4", "4, 2, 5", "2, 4, 5", "5, 2, 4"]),
         "2, 5, 4",
         "Postorder visits left subtree (2), right subtree (5), and finally the root (4)."),

        # Topic 6: Recursive Practice
        (2, 6, 2, "Sum Recursion Trace", "Intermediate", "code_logic",
         "What does the function `def f(n): return 1 if n<=1 else n + f(n-1)` compute for n = 4?",
         "def f(n):\n    if n <= 1:\n        return 1\n    return n + f(n - 1)\n\nprint(f(4))",
         json.dumps(["10", "24", "15", "8"]),
         "10",
         "4 + 3 + 2 + 1 = 10. This computes the triangular sum of positive integers up to n."),
        (2, 6, 3, "Fibonacci Call Tree", "Advanced", "code_logic",
         "How many total function calls are executed when calculating fib(3) with naive recursion fib(n) = fib(n-1) + fib(n-2) with base cases fib(0)=0, fib(1)=1?",
         None,
         json.dumps(["5 calls", "3 calls", "7 calls", "4 calls"]),
         "5 calls",
         "fib(3) calls fib(2) and fib(1). fib(2) calls fib(1) and fib(0). Total calls = 1 + 2 + 2 = 5 calls."),

        # Topic 7: Tree Problems
        (2, 7, 2, "BST Invariant", "Beginner", "mcq",
         "What structural invariant defines a valid Binary Search Tree (BST)?",
         None,
         json.dumps(["All left descendants < root and all right descendants > root", "All leaf nodes must reside at the exact same depth", "Every node must have exactly two child nodes", "Nodes are stored in sequential heap array indices"]),
         "All left descendants < root and all right descendants > root",
         "The BST invariant requires all nodes in the left subtree to be strictly less than the root, and all in the right subtree to be greater."),
        (2, 7, 4, "Degenerate BST", "Intermediate", "mcq",
         "What is the worst-case search time complexity in an unbalanced, degenerate BST resembling a linked list?",
         None,
         json.dumps(["O(n)", "O(log n)", "O(1)", "O(n log n)"]),
         "O(n)",
         "When an unbalanced BST degrades into a skewed single chain of n nodes, search degrades to linear traversal O(n)."),

        # Topic 8: Algorithm Complexity
        (2, 8, 3, "Linear Growth", "Beginner", "mcq",
         "If an algorithm doubles its execution time whenever the input size n doubles, what is its Big-O time complexity?",
         None,
         json.dumps(["O(n) - Linear", "O(1) - Constant", "O(n^2) - Quadratic", "O(log n) - Logarithmic"]),
         "O(n) - Linear",
         "A proportional 1-to-1 relationship between input size and runtime indicates linear O(n) algorithmic complexity."),
        (2, 8, 4, "Balanced Search Complexity", "Intermediate", "mcq",
         "What is the time complexity of searching for an element in a balanced binary search tree of n nodes?",
         None,
         json.dumps(["O(log n)", "O(n)", "O(1)", "O(n^2)"]),
         "O(log n)",
         "Each step eliminates half the remaining subtree, yielding logarithmic O(log n) search time.")
    ]

    for cid, tid, oid, sub, diff, qtype, qtext, snippet, opts, ans, exp in extra_questions:
        exists = c.execute("SELECT id FROM question_bank WHERE topic_id = ? AND question_text = ?", (tid, qtext)).fetchone()
        if not exists:
            c.execute("""
                INSERT INTO question_bank (course_id, topic_id, outcome_id, sub_concept, difficulty, question_type, question_text, code_snippet, options_json, correct_answer, explanation, bloom_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Understand')
            """, (cid, tid, oid, sub, diff, qtype, qtext, snippet, opts, ans, exp))

    # Also make sure questions in course 1, 3, 4 have outcome_id populated
    # Course 1 outcomes: 5, 6, 7, 8
    c.execute("UPDATE question_bank SET outcome_id = 5 WHERE course_id = 1 AND topic_id IN (9, 10) AND outcome_id IS NULL")
    c.execute("UPDATE question_bank SET outcome_id = 6 WHERE course_id = 1 AND topic_id IN (11, 12) AND outcome_id IS NULL")
    c.execute("UPDATE question_bank SET outcome_id = 7 WHERE course_id = 1 AND topic_id IN (13, 14) AND outcome_id IS NULL")
    c.execute("UPDATE question_bank SET outcome_id = 8 WHERE course_id = 1 AND topic_id IN (15, 16) AND outcome_id IS NULL")

    # Course 3 outcomes: 9, 10, 11, 12
    c.execute("UPDATE question_bank SET outcome_id = 9 WHERE course_id = 3 AND topic_id IN (17, 18) AND outcome_id IS NULL")
    c.execute("UPDATE question_bank SET outcome_id = 10 WHERE course_id = 3 AND topic_id IN (19, 20) AND outcome_id IS NULL")
    c.execute("UPDATE question_bank SET outcome_id = 11 WHERE course_id = 3 AND topic_id IN (21, 22) AND outcome_id IS NULL")
    c.execute("UPDATE question_bank SET outcome_id = 12 WHERE course_id = 3 AND topic_id IN (23, 24) AND outcome_id IS NULL")

    # Course 4 outcomes: 13, 14, 15, 16
    c.execute("UPDATE question_bank SET outcome_id = 13 WHERE course_id = 4 AND topic_id IN (25, 26) AND outcome_id IS NULL")
    c.execute("UPDATE question_bank SET outcome_id = 14 WHERE course_id = 4 AND topic_id IN (27, 28) AND outcome_id IS NULL")
    c.execute("UPDATE question_bank SET outcome_id = 15 WHERE course_id = 4 AND topic_id IN (29, 30) AND outcome_id IS NULL")
    c.execute("UPDATE question_bank SET outcome_id = 16 WHERE course_id = 4 AND topic_id IN (31, 32) AND outcome_id IS NULL")

    conn.commit()
    print("Question bank successfully expanded!")
    c.execute("SELECT topic_id, count(*) FROM question_bank WHERE course_id = 2 GROUP BY topic_id")
    print("Course 2 counts per topic:", c.fetchall())
    c.execute("SELECT course_id, count(*), sum(case when outcome_id is not null then 1 else 0 end) FROM question_bank GROUP BY course_id")
    print("Questions per course and outcome mapping:", c.fetchall())
    conn.close()

if __name__ == "__main__":
    expand_questions()
