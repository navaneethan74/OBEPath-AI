import json
import sqlite3
import os

def expand_batch_2():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "obe_learning.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    def insert_q(course_id, topic_id, outcome_id, sub_concept, diff, qtype, qtext, snippet, options, answer, explanation, bloom="Understand"):
        exists = c.execute("SELECT id FROM question_bank WHERE topic_id = ? AND question_text = ?", (topic_id, qtext)).fetchone()
        if not exists:
            c.execute("""
                INSERT INTO question_bank (course_id, topic_id, outcome_id, sub_concept, difficulty, question_type, question_text, code_snippet, options_json, correct_answer, explanation, bloom_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (course_id, topic_id, outcome_id, sub_concept, diff, qtype, qtext, snippet, json.dumps(options), answer, explanation, bloom))
            return 1
        return 0

    inserted = 0

    cs201_extra = [
        # Topic 1: Stack
        (2, 1, 1, "Stack Peek", "Beginner", "code_logic",
         "What does the `peek()` or `top()` operation perform on a non-empty stack?",
         None, ["Returns the top element without removing it from the stack", "Removes the top element and returns it", "Clears all elements from the stack", "Returns the bottom element"],
         "Returns the top element without removing it from the stack",
         "peek() inspects the current top element non-destructively, preserving stack size.", "Remember"),
        (2, 1, 2, "String Reversal with Stack", "Beginner", "code_logic",
         "If the string 'ALGORITHM' is pushed onto a stack character by character from left to right, in what order are characters popped?",
         "for char in 'ALGORITHM': stack.push(char)",
         ["M, I, H, T, I, R, O, G, L, A (Reversed)", "A, L, G, O, R, I, T, H, M (Original)", "Random order", "Vowels first then consonants"],
         "M, I, H, T, I, R, O, G, L, A (Reversed)",
         "Because the last pushed character 'M' is popped first, popping reverses the character sequence.", "Apply"),
        (2, 1, 2, "Monotonic Stack Next Greater Element", "Advanced", "code_logic",
         "To solve the 'Next Greater Element' problem for an array in O(n) total time, what type of stack is maintained?",
         None, ["A monotonic decreasing stack storing indices", "A priority stack sorted by frequency", "A circular array stack", "A double-ended stack"],
         "A monotonic decreasing stack storing indices",
         "A monotonic decreasing stack lets incoming larger elements resolve the next greater element for elements popped from the stack.", "Analyze"),

        # Topic 2: Queue
        (2, 2, 1, "Queue IsEmpty Check", "Beginner", "code_logic",
         "In a linear array queue where front and rear both start at -1, what condition represents an empty queue?",
         None, ["front == -1 or front > rear", "front == 0", "rear == capacity - 1", "front == rear"],
         "front == -1 or front > rear",
         "When front remains -1, or when dequeues advance front past rear, the queue contains no elements.", "Remember"),
        (2, 2, 2, "BFS using Queue", "Intermediate", "mcq",
         "Why does Breadth-First Search (BFS) on graphs and trees fundamentally require a Queue rather than a Stack?",
         None, ["Nodes must be visited in order of their graph distance from the starting node (FIFO level expansion)", "Queues consume less memory than stacks", "Stacks cannot hold graph vertex pointers", "BFS requires recursive backtracking"],
         "Nodes must be visited in order of their graph distance from the starting node (FIFO level expansion)",
         "FIFO ordering ensures that all vertices at distance k are dequeued and processed before any vertex at distance k+1.", "Understand"),
        (2, 2, 4, "Circular Buffer Overwrite Mode", "Advanced", "mcq",
         "In high-speed audio streaming or logging circular buffers, what happens when a new item arrives and the buffer is full?",
         None, ["The oldest unread item at front is overwritten and front advances", "A fatal buffer overflow exception halts the system", "The item is dropped into disk swap space", "The buffer automatically doubles in physical RAM size"],
         "The oldest unread item at front is overwritten and front advances",
         "Streaming ring buffers overwrite the oldest sample when full, advancing front to keep the most recent window of data.", "Analyze"),
        (2, 2, 2, "Queue Peek", "Beginner", "code_logic",
         "What does inspecting the queue's front element without removing it return?",
         None, ["The oldest inserted element currently remaining in the queue", "The most recently enqueued element", "The middle element", "Null"],
         "The oldest inserted element currently remaining in the queue",
         "Front represents the head of the FIFO queue, which holds the earliest arrived element.", "Remember"),

        # Topic 3: Recursion
        (2, 3, 1, "Stack Overflow Cause", "Beginner", "mcq",
         "What is the most frequent cause of a `RecursionError: maximum recursion depth exceeded` in Python?",
         None, ["A missing or unreachable base condition causing unbounded self-calls", "Declaring too many local variables", "Using float numbers as arguments", "Passing default parameters"],
         "A missing or unreachable base condition causing unbounded self-calls",
         "Unbounded recursive calls continuously push new stack frames until exceeding system recursion limits.", "Understand"),
        (2, 3, 2, "Binary Search Recursive", "Intermediate", "code_logic",
         "In recursive binary search on sorted array `arr` with bounds `low` and `high`, how is the mid index computed without integer overflow?",
         None, ["mid = low + (high - low) // 2", "mid = (low + high) // 2", "mid = high // 2", "mid = low * 2"],
         "mid = low + (high - low) // 2",
         "low + (high - low) // 2 prevents potential integer overflow that can occur when adding two large indices.", "Apply"),
        (2, 3, 3, "Tower of Hanoi Moves", "Intermediate", "code_logic",
         "What is the minimum number of disk moves required to solve the Tower of Hanoi puzzle with N disks?",
         None, ["2^N - 1 moves", "N^2 moves", "2*N moves", "N! moves"],
         "2^N - 1 moves",
         "T(N) = 2T(N-1) + 1. Solving this recurrence yields 2^N - 1 moves, growing exponentially.", "Analyze"),
        (2, 3, 4, "Memoization vs Tabulation", "Advanced", "mcq",
         "What distinguishes Memoization from Tabulation in dynamic programming?",
         None, ["Memoization is top-down recursive caching; Tabulation is bottom-up iterative table filling", "Memoization uses matrices; Tabulation uses hash sets", "Memoization cannot be used on DAGs", "Tabulation requires recursion stacks"],
         "Memoization is top-down recursive caching; Tabulation is bottom-up iterative table filling",
         "Top-down memoization caches recursive subproblem results on demand; bottom-up tabulation computes from base cases iteratively.", "Understand"),
        (2, 3, 2, "Sum of Array Recursive", "Beginner", "code_logic",
         "What is the return statement for recursively computing the sum of elements in a list `arr`?",
         "def list_sum(arr):\n    if not arr: return 0\n    return arr[0] + list_sum(arr[1:])",
         ["arr[0] + list_sum(arr[1:])", "arr[0] * list_sum(arr[1:])", "list_sum(arr[1:])", "arr[-1]"],
         "arr[0] + list_sum(arr[1:])",
         "The total sum equals the head element plus the recursive sum of the tail sublist.", "Apply"),

        # Topic 4: Tree Basics
        (2, 4, 1, "Degree of Node", "Beginner", "mcq",
         "What does the 'degree' of a node signify in tree terminology?",
         None, ["The number of direct children that node has", "The distance from the root to the node", "The total number of ancestors", "The value stored in the node"],
         "The number of direct children that node has",
         "The degree of a node is defined as the count of subtrees attached to it (its number of children).", "Remember"),
        (2, 4, 2, "Strict Binary Tree", "Intermediate", "mcq",
         "What defines a 'Strict' (or 'Full') Binary Tree?",
         None, ["Every node has either exactly 0 or exactly 2 children", "Every node has exactly 1 child", "All leaves are on level 1", "The tree is balanced to height 2"],
         "Every node has either exactly 0 or exactly 2 children",
         "In a strict binary tree, no node has only a single child; every vertex is either a leaf (0 children) or an internal node (2 children).", "Understand"),
        (2, 4, 3, "Relations between Nodes and Edges", "Intermediate", "code_logic",
         "In any connected tree containing N nodes, how many total edges are present?",
         None, ["N - 1 edges", "N edges", "N + 1 edges", "2N edges"],
         "N - 1 edges",
         "Every node except the root has exactly one incoming edge from its parent, giving exactly N - 1 edges.", "Apply"),
        (2, 4, 4, "Minimum Height of Binary Tree", "Advanced", "code_logic",
         "What is the theoretical minimum height of a binary tree containing N nodes?",
         None, ["floor(log_2(N))", "N / 2", "sqrt(N)", "log_10(N)"],
         "floor(log_2(N))",
         "A completely packed balanced binary tree achieves minimal height proportional to floor(log_2(N)).", "Analyze"),
        (2, 4, 2, "Subtree Definition", "Beginner", "mcq",
         "What constitutes a subtree in a hierarchical tree data structure?",
         None, ["Any node in the tree together with all of its descendants", "Any two adjacent leaf nodes", "The path between two sibling nodes", "Only the left child of the root"],
         "Any node in the tree together with all of its descendants",
         "A subtree is a tree formed by choosing any node as local root along with all descendant nodes under it.", "Remember"),

        # Topic 5: Tree Traversal
        (2, 5, 2, "Inorder on Expression Tree", "Intermediate", "code_logic",
         "Performing Inorder traversal on an arithmetic expression tree (where operators are internal nodes and operands are leaves) generates which notation?",
         None, ["Infix notation", "Postfix (RPN) notation", "Prefix (Polish) notation", "Bytecode"],
         "Infix notation",
         "Left-Root-Right processes operand-operator-operand, which produces standard parenthesized infix mathematical notation.", "Understand"),
        (2, 5, 2, "Postorder on Expression Tree", "Intermediate", "code_logic",
         "Performing Postorder traversal on an expression tree generates which notation?",
         None, ["Postfix (Reverse Polish) notation", "Infix notation", "Prefix notation", "Assembly code"],
         "Postfix (Reverse Polish) notation",
         "Left-Right-Root visits operands first, followed by their operator, generating postfix notation.", "Understand"),
        (2, 5, 4, "Morris Traversal", "Advanced", "mcq",
         "What is the key advantage of Morris Inorder Traversal over standard recursion or stack-based traversal?",
         None, ["It achieves O(1) auxiliary space without recursion or stack by temporarily threading leaf pointers", "It runs in O(log n) time", "It sorts unsorted arrays without comparisons", "It prevents duplicate keys"],
         "It achieves O(1) auxiliary space without recursion or stack by temporarily threading leaf pointers",
         "Morris traversal creates temporary threaded edges from predecessor nodes back to current nodes, eliminating memory overhead.", "Analyze"),
        (2, 5, 3, "Boundary Traversal", "Advanced", "code_logic",
         "In Boundary Traversal of a binary tree, in what sequence are boundary components visited?",
         None, ["Left boundary (top-down), then all Leaf nodes (left-to-right), then Right boundary (bottom-up)", "Leaves only", "Root followed by all internal nodes", "Right boundary then Left boundary"],
         "Left boundary (top-down), then all Leaf nodes (left-to-right), then Right boundary (bottom-up)",
         "Boundary traversal traces the outer perimeter counterclockwise: left boundary down, leaves left-to-right, right boundary up.", "Apply"),
        (2, 5, 2, "Zigzag Level Order", "Intermediate", "code_logic",
         "In Zigzag (Spiral) Level Order Traversal, how does node visitation alternate across successive levels?",
         None, ["Left-to-right on even levels, right-to-left on odd levels", "Top-to-bottom only", "Outside-in on every level", "Ascending numerical order"],
         "Left-to-right on even levels, right-to-left on odd levels",
         "Zigzag reverses reading direction at every alternating level depth.", "Apply"),

        # Topic 6: Recursive Practice
        (2, 6, 2, "Invert/Flip Binary Tree", "Beginner", "code_logic",
         "What operations are needed to invert (mirror) a binary tree at each node?",
         "def invertTree(root):\n    if not root: return None\n    root.left, root.right = invertTree(root.right), invertTree(root.left)\n    return root",
         ["Swap root.left and root.right recursively for all nodes", "Reverse only the leaf node values", "Rotate the root 90 degrees", "Sort the left and right values"],
         "Swap root.left and root.right recursively for all nodes",
         "Recursively swapping the left and right children at every node creates the exact mirror reflection of the tree.", "Apply"),
        (2, 6, 3, "Tree Diameter Definition", "Intermediate", "mcq",
         "What is the 'diameter' of a binary tree?",
         None, ["The length of the longest path between any two nodes in the tree (which may or may not pass through root)", "The total count of leaf nodes", "The maximum width of any single level", "The height of the root node multiplied by 2"],
         "The length of the longest path between any two nodes in the tree (which may or may not pass through root)",
         "Diameter measures the longest edge path connecting any pair of vertices in the tree graph.", "Understand"),
        (2, 6, 4, "Maximum Path Sum", "Advanced", "code_logic",
         "In finding the Maximum Path Sum in a binary tree (where node values can be negative), how should negative branch contributions be handled?",
         None, ["Clamp negative child subtree returns to 0 (ignore negative branches)", "Multiply them by -1", "Immediately return 0 for the whole tree", "Square the branch sum"],
         "Clamp negative child subtree returns to 0 (ignore negative branches)",
         "`max(0, gain(child))` ensures that paths are not dragged down by subtrees with negative net sums.", "Analyze"),
        (2, 6, 3, "Is Balanced Binary Tree Check", "Intermediate", "code_logic",
         "To verify if a binary tree is height-balanced in O(n) time, what should the helper function return?",
         None, ["The height if balanced, or -1 as a sentinel if any subtree is unbalanced", "True or False only without height", "The count of leaf nodes", "The difference between left and right root depths"],
         "The height if balanced, or -1 as a sentinel if any subtree is unbalanced",
         "Bottom-up checks propagate -1 immediately upon detecting any unbalanced child, computing height and balance concurrently in O(n).", "Apply"),
        (2, 6, 2, "Count Leaves Recursively", "Beginner", "code_logic",
         "What is the base case for counting leaves in a binary tree?",
         "if not root.left and not root.right:\n    return 1",
         ["return 1 if both left and right children are null", "return 0 when node is null", "return 2 for every node", "return root.val"],
         "return 1 if both left and right children are null",
         "A leaf node has neither left nor right child, contributing exactly 1 to the leaf count.", "Apply"),

        # Topic 7: Tree Problems
        (2, 7, 1, "BST Insertion Rule", "Beginner", "code_logic",
         "Where is a new key inserted into a standard Binary Search Tree?",
         None, ["Always as a new leaf node at an appropriate empty child reference maintaining BST order", "At the root, pushing old root down", "At the leftmost index of the array", "At random vacant spots"],
         "Always as a new leaf node at an appropriate empty child reference maintaining BST order",
         "BST insertion navigates left/right based on comparisons until reaching a null spot where the new leaf attaches.", "Remember"),
        (2, 7, 2, "BST Deletion with Two Children", "Intermediate", "code_logic",
         "When deleting a node that has TWO children from a BST, what replaces the deleted node's key?",
         None, ["Its in-order successor (smallest node in right subtree) OR in-order predecessor", "Its immediate left child directly", "Its parent node", "A null pointer"],
         "Its in-order successor (smallest node in right subtree) OR in-order predecessor",
         "The in-order successor has at most one child and maintains the BST ordering property for all remaining nodes.", "Understand"),
        (2, 7, 3, "Kth Smallest Element in BST", "Intermediate", "code_logic",
         "What traversal yields the Kth smallest element of a BST in O(k) stops?",
         None, ["Inorder traversal (Left, Root, Right) keeping a counter", "Preorder traversal", "Postorder traversal", "Level-order traversal"],
         "Inorder traversal (Left, Root, Right) keeping a counter",
         "Inorder visits BST nodes in sorted ascending order; the Kth node visited is precisely the Kth smallest element.", "Apply"),
        (2, 7, 4, "Red-Black Tree Properties", "Advanced", "mcq",
         "Which property of Red-Black Trees guarantees that no path from root to leaf is more than twice as long as any other?",
         None, ["Every red node must have black children (no two consecutive red nodes) AND every path has the same number of black nodes", "All leaves are red", "The root must be red", "Every node must have balance factor 0"],
         "Every red node must have black children (no two consecutive red nodes) AND every path has the same number of black nodes",
         "Black-height equality paired with the restriction against adjacent red nodes bounds height to 2 * log_2(n+1).", "Analyze"),
        (2, 7, 4, "Serialize and Deserialize Tree", "Advanced", "code_logic",
         "When serializing a binary tree to a string for network transmission, why are null child references preserved (e.g. as '#')?",
         None, ["To uniquely distinguish structural shape without ambiguity during deserialization", "To compress string size", "To encrypt the tree values", "To sort the data during transfer"],
         "To uniquely distinguish structural shape without ambiguity during deserialization",
         "Marking null children explicitly allows a single preorder or level-order sequence to reconstruct the tree structure unambiguously.", "Analyze"),

        # Topic 8: Algorithm Complexity
        (2, 8, 1, "Best vs Worst Case", "Beginner", "mcq",
         "What is the Best-case time complexity of Linear Search in an unsorted array of N elements?",
         None, ["O(1) (target found at the very first index)", "O(n)", "O(log n)", "O(n^2)"],
         "O(1) (target found at the very first index)",
         "If the sought element is positioned at index 0, linear search completes in a single comparison = O(1).", "Remember"),
        (2, 8, 2, "Space Complexity Definition", "Beginner", "mcq",
         "What is 'Auxiliary Space' when calculating space complexity of an algorithm?",
         None, ["The extra temporary space used by the algorithm, excluding the space taken by the input data itself", "The total size of the input dataset in bytes", "The disk swap space on the operating system", "The size of the source code file"],
         "The extra temporary space used by the algorithm, excluding the space taken by the input data itself",
         "Auxiliary space measures only working memory (call stack, buffers, variables) allocated beyond the input parameters.", "Understand"),
        (2, 8, 3, "Sorting Complexity Comparison", "Intermediate", "mcq",
         "What is the average-case time complexity of QuickSort vs MergeSort?",
         None, ["Both have O(n log n) average time complexity", "QuickSort is O(n^2), MergeSort is O(n)", "QuickSort is O(n), MergeSort is O(n log n)", "MergeSort is O(n^2), QuickSort is O(log n)"],
         "Both have O(n log n) average time complexity",
         "Both algorithms run in O(n log n) on average, though QuickSort does so in-place and MergeSort requires O(n) auxiliary memory.", "Understand"),
        (2, 8, 4, "NP-Complete Concept", "Advanced", "mcq",
         "What characterizes an 'NP-Complete' computational problem?",
         None, ["Any candidate solution can be verified in polynomial time O(n^k), but no known polynomial time algorithm exists to find solutions", "It can be solved in O(log n) time", "It cannot be verified by computers", "It requires quantum processors"],
         "Any candidate solution can be verified in polynomial time O(n^k), but no known polynomial time algorithm exists to find solutions",
         "NP-Complete problems are the hardest problems in NP; verifying a given solution is fast (polynomial), but solving is intractable.", "Analyze"),
        (2, 8, 3, "Master Theorem Case 1", "Advanced", "code_logic",
         "What is the solution to `T(n) = 8T(n/2) + O(n^2)`?",
         "T(n) = 8T(n/2) + O(n^2)",
         ["O(n^3)", "O(n^2 log n)", "O(n^2)", "O(n log n)"],
         "O(n^3)",
         "log_b(a) = log_2(8) = 3. Since f(n) = n^2 = O(n^(3 - epsilon)), Master Theorem Case 1 applies: T(n) = Theta(n^3).", "Analyze")
    ]

    for q in cs201_extra:
        inserted += insert_q(*q)

    conn.commit()
    print(f"Batch 2 complete! Inserted {inserted} additional questions.")

    c.execute("SELECT topic_id, count(*) FROM question_bank WHERE course_id = 2 GROUP BY topic_id ORDER BY topic_id")
    print("Course 2 Questions per topic now:")
    for row in c.fetchall():
        print(f"  Topic {row[0]}: {row[1]} questions")

    c.execute("SELECT count(*) FROM question_bank")
    print("Total QuestionBank count across all courses:", c.fetchone()[0])
    conn.close()

if __name__ == "__main__":
    expand_batch_2()
