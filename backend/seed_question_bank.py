import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal, Base
from models import (
    Course, CourseOutcome, Topic, TopicPrerequisite, TopicOutcomeMapping,
    QuestionBank, DiagnosticQuestion
)

def seed_question_bank():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        ds_course = db.query(Course).filter(Course.code == "CS201").first()
        if not ds_course:
            print("CS201 not found, creating...")
            ds_course = Course(
                code="CS201",
                title="Data Structures",
                description="Algorithmic problem solving, linear and non-linear data structures, trees, graphs, and complexity.",
                category="Computer Science",
                level="Beginner to Intermediate",
                is_active=True
            )
            db.add(ds_course)
            db.commit()

        # Ensure CO1, CO2, CO3, CO4 exist
        co1 = db.query(CourseOutcome).filter(CourseOutcome.course_id == ds_course.id, CourseOutcome.code == "CO1").first()
        if not co1:
            co1 = CourseOutcome(
                course_id=ds_course.id,
                code="CO1",
                description="Fundamental concepts of data structures (Stack, Queue, Tree basics)",
                target_attainment_pct=75.0
            )
            db.add(co1)

        co2 = db.query(CourseOutcome).filter(CourseOutcome.course_id == ds_course.id, CourseOutcome.code == "CO2").first()
        if not co2:
            co2 = CourseOutcome(
                course_id=ds_course.id,
                code="CO2",
                description="Apply data structures to solve problems (Push/Pop, Enqueue/Dequeue, Traversal)",
                target_attainment_pct=70.0
            )
            db.add(co2)

        co3 = db.query(CourseOutcome).filter(CourseOutcome.course_id == ds_course.id, CourseOutcome.code == "CO3").first()
        if not co3:
            co3 = CourseOutcome(
                course_id=ds_course.id,
                code="CO3",
                description="Implement and trace algorithms / data structures (Recursion, Traversal, Search)",
                target_attainment_pct=70.0
            )
            db.add(co3)

        co4 = db.query(CourseOutcome).filter(CourseOutcome.course_id == ds_course.id, CourseOutcome.code == "CO4").first()
        if not co4:
            co4 = CourseOutcome(
                course_id=ds_course.id,
                code="CO4",
                description="Solve real-world computational problems & complexity analysis (Big-O, BST, Optimization)",
                target_attainment_pct=70.0
            )
            db.add(co4)

        db.commit()

        topics = db.query(Topic).filter(Topic.course_id == ds_course.id).order_by(Topic.order_index).all()
        t_map = {t.order_index: t for t in topics}

        # Topic outcome mappings for all 4 COs:
        # Stack (1) -> CO1, CO2
        # Queue (2) -> CO1, CO2
        # Recursion (3) -> CO1, CO2, CO3
        # Tree Basics (4) -> CO1, CO2
        # Tree Traversal (5) -> CO2, CO3
        # Recursive Practice (6) -> CO2, CO3
        # Tree Problems (7) -> CO2, CO4
        # Algorithm Complexity (8) -> CO3, CO4
        co_map_data = [
            (1, co1.id), (1, co2.id),
            (2, co1.id), (2, co2.id),
            (3, co1.id), (3, co2.id), (3, co3.id),
            (4, co1.id), (4, co2.id),
            (5, co2.id), (5, co3.id),
            (6, co2.id), (6, co3.id),
            (7, co2.id), (7, co4.id),
            (8, co3.id), (8, co4.id)
        ]
        for ord_idx, cid in co_map_data:
            if ord_idx in t_map:
                existing = db.query(TopicOutcomeMapping).filter(
                    TopicOutcomeMapping.topic_id == t_map[ord_idx].id,
                    TopicOutcomeMapping.outcome_id == cid
                ).first()
                if not existing:
                    db.add(TopicOutcomeMapping(topic_id=t_map[ord_idx].id, outcome_id=cid, weight=1.0))
        db.commit()

        # Seed QuestionBank (Rich pool of 24+ questions across difficulties)
        if db.query(QuestionBank).count() >= 20:
            print(f"QuestionBank already contains {db.query(QuestionBank).count()} questions.")
            return

        print("Seeding QuestionBank...")
        bank_questions = [
            # 1. Stack Basics & Operations
            (
                t_map[1].id, co1.id, "Stack Principles", "Beginner", "mcq",
                "What fundamental access discipline does a Stack data structure enforce?",
                None,
                ["LIFO (Last In First Out)", "FIFO (First In First Out)", "Random Access", "Priority Order"],
                "LIFO (Last In First Out)",
                "A stack is a linear collection where elements are added and removed from the same top end, strictly following Last-In-First-Out."
            ),
            (
                t_map[1].id, co2.id, "Stack Simulation", "Intermediate", "code_logic",
                "Given an empty stack, perform: push(10), push(20), pop(), push(30). What element is now at the top of the stack?",
                "push(10)\npush(20)\npop()\npush(30)",
                ["30", "20", "10", "Empty"],
                "30",
                "push(10) -> [10], push(20) -> [10, 20], pop() removes 20 -> [10], push(30) -> [10, 30]. Top element is 30."
            ),
            (
                t_map[1].id, co2.id, "Stack Applications", "Advanced", "mcq",
                "Which application is fundamentally implemented using a Call Stack in computer architecture?",
                None,
                ["Function call execution and recursion memory frames", "Round-robin CPU task scheduling", "Printer spooling buffer", "Breadth-first graph traversal"],
                "Function call execution and recursion memory frames",
                "Call stacks preserve activation records, return addresses, and local variables for nested and recursive subroutine calls."
            ),

            # 2. Queue Basics & Operations
            (
                t_map[2].id, co1.id, "Queue Principles", "Beginner", "mcq",
                "Which operation removes an element from the front of a standard Queue following the FIFO principle?",
                None,
                ["Dequeue", "Enqueue", "Pop", "Peek"],
                "Dequeue",
                "In a Queue, enqueue appends to the rear, while dequeue removes and returns the frontmost element."
            ),
            (
                t_map[2].id, co2.id, "Queue Operations", "Intermediate", "code_logic",
                "Starting with an empty queue, execute: enqueue('A'), enqueue('B'), dequeue(), enqueue('C'). What element is at the front?",
                "q = Queue()\nq.enqueue('A')\nq.enqueue('B')\nq.dequeue()\nq.enqueue('C')",
                ["B", "A", "C", "Empty"],
                "B",
                "enqueue('A') -> [A], enqueue('B') -> [A, B], dequeue() removes 'A' -> [B], enqueue('C') -> [B, C]. Front element is 'B'."
            ),
            (
                t_map[2].id, co2.id, "Circular Queue", "Advanced", "mcq",
                "In a circular queue of capacity N with front and rear pointers, what formula calculates the next insertion index?",
                None,
                ["(rear + 1) % N", "rear + 1", "(rear - 1) % N", "rear * 2 % N"],
                "(rear + 1) % N",
                "Modulo arithmetic wraps the rear pointer around to index 0 when it reaches capacity N."
            ),

            # 3. Recursion Fundamentals
            (
                t_map[3].id, co1.id, "Recursion Base Case", "Beginner", "mcq",
                "What essential component must every recursive function define to prevent infinite recursion and stack overflow?",
                None,
                ["Base condition / stopping case", "Global counter variable", "For loop iterator", "Catch block"],
                "Base condition / stopping case",
                "The base condition specifies when recursive branching stops, allowing the call stack frames to resolve and unwind."
            ),
            (
                t_map[3].id, co2.id, "Recursion Call Stack", "Intermediate", "code_logic",
                "What does the function mystery(3) return?",
                "def mystery(n):\n    if n <= 1:\n        return 1\n    return n + mystery(n - 1)",
                ["6", "3", "5", "Infinite Recursion"],
                "6",
                "mystery(3) = 3 + mystery(2) = 3 + (2 + mystery(1)) = 3 + 2 + 1 = 6."
            ),
            (
                t_map[3].id, co3.id, "Recursion Tree", "Advanced", "code_logic",
                "How many total recursive calls are made when computing fib(4) with naive recursion?",
                "def fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)",
                ["9", "5", "4", "7"],
                "9",
                "The call tree for fib(4) makes calls for fib(3) and fib(2), spawning 9 total function evaluations."
            ),

            # 4. Tree Basics
            (
                t_map[4].id, co1.id, "Binary Tree Node", "Beginner", "mcq",
                "What is the maximum number of children any single node can have in a Binary Tree?",
                None,
                ["2", "1", "3", "Unlimited"],
                "2",
                "By mathematical definition, every node in a binary tree has at most two children (designated left and right)."
            ),
            (
                t_map[4].id, co1.id, "Tree Terminology", "Intermediate", "mcq",
                "What is a node called that has degree 0 (no children) in a rooted tree?",
                None,
                ["Leaf node", "Root node", "Internal node", "Ancestor node"],
                "Leaf node",
                "A leaf (terminal) node has no outgoing edges to child nodes."
            ),
            (
                t_map[4].id, co2.id, "Tree Height", "Advanced", "mcq",
                "What is the maximum number of nodes in a full binary tree of height h (where a tree with 1 node has height 1)?",
                None,
                ["2^h - 1", "2^h", "2^(h-1)", "h^2"],
                "2^h - 1",
                "Summing powers of 2 from level 0 to h-1 yields 2^h - 1 nodes."
            ),

            # 5. Tree Traversal
            (
                t_map[5].id, co2.id, "Inorder Traversal", "Beginner", "mcq",
                "What is the correct node visitation order in an Inorder depth-first traversal?",
                None,
                ["Left Subtree -> Root -> Right Subtree", "Root -> Left Subtree -> Right Subtree", "Left Subtree -> Right Subtree -> Root", "Right Subtree -> Root -> Left Subtree"],
                "Left Subtree -> Root -> Right Subtree",
                "Inorder systematically evaluates the left child first, then visits the root, then processes the right child."
            ),
            (
                t_map[5].id, co3.id, "Traversal Output", "Intermediate", "code_logic",
                "Given a tree with Root 1, Left 2, Right 3, what is the Preorder traversal sequence?",
                "    1\n   / \\\n  2   3",
                ["1, 2, 3", "2, 1, 3", "2, 3, 1", "3, 2, 1"],
                "1, 2, 3",
                "Preorder visits Root (1) first, followed by Left (2), and then Right (3)."
            ),
            (
                t_map[5].id, co3.id, "BST Inorder Property", "Advanced", "mcq",
                "What guaranteed mathematical property does the Inorder traversal of a Binary Search Tree (BST) exhibit?",
                None,
                ["Visits keys in strictly ascending sorted order", "Visits nodes in decreasing order", "Visits all leaf nodes first", "Always balances the tree height"],
                "Visits keys in strictly ascending sorted order",
                "Because left < root < right in a BST, in-order traversal (L, Root, R) yields values in sorted non-decreasing order."
            ),

            # 6. Recursive Practice
            (
                t_map[6].id, co2.id, "Recursive Tree Traversal", "Beginner", "mcq",
                "When implementing tree traversal recursively, what serves as the base case?",
                None,
                ["if node is None: return", "if node.left == node.right", "while node != None", "if stack.isEmpty()"],
                "if node is None: return",
                "Checking whether the current node pointer is null/None acts as the boundary condition where tree traversal recursion stops."
            ),
            (
                t_map[6].id, co3.id, "Recursive Tree Accumulation", "Intermediate", "code_logic",
                "What does the following recursive function compute on a binary tree?",
                "def count_nodes(node):\n    if not node:\n        return 0\n    return 1 + count_nodes(node.left) + count_nodes(node.right)",
                ["Total number of nodes in the tree", "Height of the tree", "Number of leaf nodes only", "Sum of key values"],
                "Total number of nodes in the tree",
                "It counts 1 for the current node and recursively adds all nodes in both left and right subtrees."
            ),
            (
                t_map[6].id, co3.id, "Recursive Path Sum", "Advanced", "code_logic",
                "In a recursive max_depth algorithm, what is returned when reaching a non-null single leaf node?",
                "def max_depth(node):\n    if not node: return 0\n    return 1 + max(max_depth(node.left), max_depth(node.right))",
                ["1", "0", "2", "None"],
                "1",
                "For a leaf node, both left and right return 0, resulting in 1 + max(0, 0) = 1."
            ),

            # 7. Tree Problems & Applications
            (
                t_map[7].id, co2.id, "Binary Search Tree Search", "Beginner", "mcq",
                "In a valid Binary Search Tree, if target key K is greater than root key R, which subtree must be searched?",
                None,
                ["Right subtree", "Left subtree", "Both subtrees concurrently", "Neither (target not found)"],
                "Right subtree",
                "By BST invariant, all elements in the right subtree are strictly greater than the root."
            ),
            (
                t_map[7].id, co4.id, "BST Search Complexity", "Intermediate", "mcq",
                "What is the average-case time complexity for searching an element in a balanced Binary Search Tree?",
                None,
                ["O(log n)", "O(n)", "O(1)", "O(n^2)"],
                "O(log n)",
                "Each comparison eliminates half of the remaining subtrees, achieving logarithmic O(log n) efficiency."
            ),
            (
                t_map[7].id, co4.id, "Unbalanced BST Degeneracy", "Advanced", "mcq",
                "What is the worst-case time complexity of searching in a completely skewed BST with N nodes?",
                None,
                ["O(n)", "O(log n)", "O(1)", "O(n log n)"],
                "O(n)",
                "A skewed BST degrades into a linear singly-linked list where each node has only one child, taking linear O(n) search time."
            ),

            # 8. Algorithm Complexity & Big-O
            (
                t_map[8].id, co3.id, "Big-O Linear vs Constant", "Beginner", "mcq",
                "What is the time complexity of pushing an element onto an array-based Stack with pre-allocated capacity?",
                None,
                ["O(1) Constant Time", "O(n) Linear Time", "O(log n)", "O(n^2)"],
                "O(1) Constant Time",
                "Pushing to the top involves a single index increment and memory write, requiring O(1) time."
            ),
            (
                t_map[8].id, co4.id, "Search Complexity Comparison", "Intermediate", "mcq",
                "How does Binary Search on a sorted array compare with Linear Search on an unsorted array for N = 1,000,000 items?",
                None,
                ["Binary Search takes ~20 comparisons vs up to 1,000,000 for Linear Search", "Both take exactly the same number of steps", "Linear Search is faster for large arrays", "Binary Search takes 500,000 comparisons on average"],
                "Binary Search takes ~20 comparisons vs up to 1,000,000 for Linear Search",
                "log2(1,000,000) is approximately 20, making O(log n) dramatically more efficient than O(n)."
            ),
            (
                t_map[8].id, co4.id, "Asymptotic Analysis", "Advanced", "mcq",
                "Which Big-O runtime class represents exponential computational growth that becomes intractable for moderate N?",
                None,
                ["O(2^n)", "O(n log n)", "O(n^2)", "O(n^3)"],
                "O(2^n)",
                "Exponential growth doubles with every increment of N, making it computationally infeasible for large inputs."
            )
        ]

        for tid, oid, sub_c, diff, qtype, qtext, snippet, opts, correct, expl in bank_questions:
            q = QuestionBank(
                course_id=ds_course.id,
                topic_id=tid,
                outcome_id=oid,
                sub_concept=sub_c,
                difficulty=diff,
                question_type=qtype,
                question_text=qtext,
                code_snippet=snippet,
                options_json=json.dumps(opts),
                correct_answer=correct,
                explanation=expl
            )
            db.add(q)
        db.commit()
        print(f"Successfully seeded {len(bank_questions)} questions into QuestionBank.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_question_bank()
