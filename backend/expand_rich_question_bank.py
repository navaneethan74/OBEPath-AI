import json
import sqlite3
import os

def expand_all_questions():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "obe_learning.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Helper function to insert question if it doesn't already exist
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

    # =========================================================================
    # COURSE 2: DATA STRUCTURES (CS201) - Topics 1 to 8
    # CO1 = 1, CO2 = 2, CO3 = 3, CO4 = 4
    # =========================================================================

    cs201_questions = [
        # --- TOPIC 1: Stack Basics & Operations ---
        (2, 1, 1, "Stack Concept", "Beginner", "mcq",
         "Which pointer variable is used in array-based stack implementations to track the most recently inserted item?",
         None, ["top", "front", "rear", "head"], "top",
         "The 'top' pointer stores the index of the highest element in the stack and decrements on pop operations.", "Remember"),

        (2, 1, 1, "Stack Underflow", "Beginner", "mcq",
         "What occurs when an operation attempts to pop an element from a stack that has no items?",
         None, ["Stack Underflow", "Stack Overflow", "Segmentation Fault", "NullPointer Return"], "Stack Underflow",
         "Stack Underflow is the error condition raised when attempting to remove or inspect an item from an empty stack.", "Understand"),

        (2, 1, 2, "Stack Evaluation", "Intermediate", "code_logic",
         "What will the stack contain after executing: push(5), push(12), push(8), pop(), push(3)? (Bottom to Top)",
         "s = Stack()\ns.push(5)\ns.push(12)\ns.push(8)\ns.pop()\ns.push(3)",
         ["[5, 12, 3]", "[5, 8, 3]", "[5, 12, 8]", "[3, 12, 5]"], "[5, 12, 3]",
         "5 and 12 are pushed; 8 is pushed then immediately removed by pop(); 3 is pushed on top of 12.", "Apply"),

        (2, 1, 2, "Parentheses Balancing", "Intermediate", "mcq",
         "Why is a stack the ideal data structure for validating balanced parentheses in compiler syntax checkers?",
         None, ["The most recently opened parenthesis must be the first one closed (LIFO matching)", "It accesses elements in first-come first-served order", "It sorts opening and closing brackets automatically", "It consumes O(1) memory regardless of expression length"],
         "The most recently opened parenthesis must be the first one closed (LIFO matching)",
         "Nested structures require matching the innermost/most recent bracket first, which perfectly matches LIFO semantics.", "Understand"),

        (2, 1, 2, "Postfix Conversion", "Intermediate", "code_logic",
         "What is the equivalent postfix (RPN) representation of the infix expression: `(A + B) * C`?",
         "Infix: (A + B) * C",
         ["A B + C *", "A B C + *", "* + A B C", "A B + * C"], "A B + C *",
         "Parentheses force A + B into postfix 'A B +', then multiplication with C produces 'A B + C *'.", "Apply"),

        (2, 1, 4, "Two Stacks in One Array", "Advanced", "code_logic",
         "How can two stacks efficiently share a single static array of size N without false overflows?",
         None, ["Grow Stack 1 from index 0 upwards and Stack 2 from index N-1 downwards", "Allocate alternating even indices to Stack 1 and odd to Stack 2", "Split the array into two fixed halves of size N/2", "Maintain a linked list of array segment blocks"],
         "Grow Stack 1 from index 0 upwards and Stack 2 from index N-1 downwards",
         "Growing from opposite ends utilizes the array space dynamically until the two top pointers meet.", "Analyze"),

        (2, 1, 3, "Stack Complexity", "Advanced", "mcq",
         "What is the amortized time complexity of push() in a dynamic array-backed stack that doubles its capacity upon reaching capacity?",
         None, ["O(1) amortized", "O(n) amortized", "O(log n) amortized", "O(n^2) amortized"], "O(1) amortized",
         "Although occasional resizing takes O(n), doubling ensures that N pushes cost roughly 2N operations, yielding O(1) amortized.", "Analyze"),

        (2, 1, 2, "Min Stack Design", "Advanced", "code_logic",
         "To implement a MinStack where getMin() takes O(1) time without searching, what auxiliary structure is optimal?",
         None, ["An auxiliary stack storing the current minimum at each push level", "A binary search tree storing all elements", "A min-heap rebalanced on each pop", "A single integer tracking the minimum seen so far"],
         "An auxiliary stack storing the current minimum at each push level",
         "An auxiliary stack tracks minimums corresponding to each stack depth, surviving pops in O(1) time.", "Create"),

        # --- TOPIC 2: Queue Basics & Operations ---
        (2, 2, 1, "Queue Principle", "Beginner", "mcq",
         "Which real-world analogy best describes the operational behavior of a Standard Queue?",
         None, ["People standing in a ticket counter line", "A stack of dinner plates in a cafeteria", "A deck of cards being reshuffled", "A web browser back button history"],
         "People standing in a ticket counter line",
         "A queue serves the first person who arrives first, representing First-In-First-Out (FIFO) processing.", "Remember"),

        (2, 2, 1, "Queue Terminology", "Beginner", "mcq",
         "At which ends of a linear queue do insertion and deletion operations take place?",
         None, ["Insertion at Rear, Deletion at Front", "Insertion at Front, Deletion at Rear", "Insertion and Deletion both at Front", "Insertion and Deletion both at Rear"],
         "Insertion at Rear, Deletion at Front",
         "Enqueue inserts new items at the rear/tail, and Dequeue removes existing items from the front/head.", "Remember"),

        (2, 2, 2, "Circular Queue Logic", "Intermediate", "code_logic",
         "In a circular queue of capacity 6 with front = 4 and rear = 5, what is the next rear index after enqueuing one element?",
         "capacity = 6\nrear = (rear + 1) % capacity",
         ["0", "6", "1", "5"], "0",
         "(5 + 1) % 6 = 0. The modulo operation wraps the index back to the beginning of the circular buffer.", "Apply"),

        (2, 2, 2, "Deque Concept", "Intermediate", "mcq",
         "What distinguishes a Double-Ended Queue (Deque) from a standard FIFO Queue?",
         None, ["Elements can be inserted and deleted from both the front and rear ends", "It maintains elements in sorted numerical order automatically", "It restricts deletions to odd-numbered indices", "It can only store paired key-value data"],
         "Elements can be inserted and deleted from both the front and rear ends",
         "A deque (double-ended queue) supports push_front, pop_front, push_back, and pop_back all in O(1) time.", "Understand"),

        (2, 2, 3, "Queue using Stacks", "Advanced", "code_logic",
         "When implementing a FIFO Queue using two LIFO Stacks (in_stack and out_stack), what is the amortized cost per dequeue?",
         None, ["O(1) amortized", "O(n) worst-case and amortized", "O(log n)", "O(n^2)"], "O(1) amortized",
         "Each element is pushed to in_stack once, moved to out_stack once, and popped once; 3 operations total per item = O(1) amortized.", "Analyze"),

        (2, 2, 4, "Monotonic Queue", "Advanced", "mcq",
         "For which classic algorithmic problem is a monotonic deque optimal for achieving O(n) total runtime?",
         None, ["Sliding Window Maximum", "Shortest path in unweighted DAG", "Topological sorting of nodes", "Matrix chain multiplication"],
         "Sliding Window Maximum",
         "A monotonic decreasing deque retains only candidate maximums within the sliding window, processing each element in O(1) amortized.", "Apply"),

        (2, 2, 2, "Circular Queue Full Condition", "Intermediate", "mcq",
         "In a circular queue using an array of size N where one slot is left empty to distinguish full from empty, what is the full condition?",
         None, ["(rear + 1) % N == front", "front == rear", "rear == N - 1", "front == (rear + 1)"],
         "(rear + 1) % N == front",
         "When the next rear index wraps to front, the queue is considered full with N-1 items.", "Understand"),

        # --- TOPIC 3: Recursion Fundamentals ---
        (2, 3, 1, "Base Case Purpose", "Beginner", "mcq",
         "What critical role does the base condition play in any recursive algorithm?",
         None, ["It terminates recursive execution and prevents infinite call stack recursion", "It allocates heap memory for the call stack", "It doubles the execution speed of the function", "It converts the recursive function into an iterative loop automatically"],
         "It terminates recursive execution and prevents infinite call stack recursion",
         "Without a base case, recursive calls continue indefinitely until a StackOverflowError occurs.", "Remember"),

        (2, 3, 2, "Recursion Trace", "Intermediate", "code_logic",
         "What does the function `f(3)` return?",
         "def f(n):\n    if n <= 1:\n        return 1\n    return n * f(n - 1)",
         ["6", "3", "2", "24"], "6",
         "f(3) = 3 * f(2) = 3 * (2 * f(1)) = 3 * 2 * 1 = 6 (calculates 3 factorial).", "Apply"),

        (2, 3, 2, "Fibonacci Call Tree", "Intermediate", "code_logic",
         "How many times is `fib(1)` evaluated in naive recursive `fib(4)`?",
         "def fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)",
         ["3 times", "1 time", "2 times", "5 times"], "3 times",
         "fib(4) calls fib(3) and fib(2). Expanding the call tree shows fib(1) is redundantly evaluated 3 separate times.", "Analyze"),

        (2, 3, 3, "Recursion Memory Footprint", "Advanced", "mcq",
         "What determines the auxiliary memory space complexity of a recursive function?",
         None, ["The maximum depth of the active call stack at any point", "The total number of recursive function calls made over all time", "The number of parameters passed in the signature", "The size of the heap memory allocated"],
         "The maximum depth of the active call stack at any point",
         "Auxiliary space equals the height of the recursion tree, as only active stack frames consume memory concurrently.", "Analyze"),

        (2, 3, 3, "Divide and Conquer Recurrence", "Advanced", "code_logic",
         "According to the Master Theorem, what is the asymptotic solution to `T(n) = 2T(n/2) + O(n)`?",
         "T(n) = 2T(n/2) + O(n)",
         ["O(n log n)", "O(n)", "O(n^2)", "O(log n)"], "O(n log n)",
         "Here a=2, b=2, d=1. Since log_b(a) = log_2(2) = 1 == d, the solution falls into case 2: O(n log n) (Merge Sort).", "Analyze"),

        (2, 3, 1, "Direct vs Indirect Recursion", "Beginner", "mcq",
         "What is 'indirect recursion' in programming?",
         None, ["Function A calls Function B, which in turn calls Function A", "A function that calls itself multiple times in its body", "A recursive function that contains a while loop", "A function that has no return value"],
         "Function A calls Function B, which in turn calls Function A",
         "Indirect recursion occurs when two or more functions call each other in a cyclic dependency.", "Understand"),

        # --- TOPIC 4: Tree Basics ---
        (2, 4, 1, "Tree Terminology", "Beginner", "mcq",
         "What is a node in a tree called if it has no children?",
         None, ["Leaf node", "Root node", "Internal node", "Sibling node"], "Leaf node",
         "A leaf node (or external node) is any node having degree 0 (no child nodes).", "Remember"),

        (2, 4, 1, "Binary Tree Definition", "Beginner", "mcq",
         "What is the maximum number of children any node can have in a Binary Tree?",
         None, ["2 children", "1 child", "3 children", "Unlimited"], "2 children",
         "By definition, every node in a binary tree has at most two children, typically termed left and right child.", "Remember"),

        (2, 4, 2, "Height and Depth", "Intermediate", "code_logic",
         "What is the depth of the root node in conventional zero-indexed tree terminology?",
         None, ["0", "1", "-1", "Equal to the total height of the tree"], "0",
         "The depth of a node is the number of edges from the root to that node; hence root depth is 0.", "Understand"),

        (2, 4, 2, "Max Nodes at Level", "Intermediate", "code_logic",
         "What is the maximum number of nodes possible at level `i` (where root is level 0) of a binary tree?",
         "Level i (i >= 0)",
         ["2^i", "2^(i+1)", "2^i - 1", "i^2"], "2^i",
         "Level 0 has 2^0 = 1 node (root), level 1 has 2^1 = 2, level 2 has 2^2 = 4, generalizing to 2^i.", "Apply"),

        (2, 4, 3, "Complete Binary Tree", "Advanced", "mcq",
         "How is a 'Complete Binary Tree' defined in data structure theory?",
         None, [
             "All levels are completely filled except possibly the last, which is filled from left to right",
             "Every non-leaf node has exactly two children and all leaves are at the same depth",
             "Every node has at most one child",
             "All left subtrees have greater values than their respective right subtrees"
         ],
         "All levels are completely filled except possibly the last, which is filled from left to right",
         "A complete binary tree fills all levels completely, with any missing nodes strictly at the right of the bottom level.", "Analyze"),

        (2, 4, 3, "Array Representation of Tree", "Advanced", "code_logic",
         "In a 0-indexed array representation of a complete binary tree, what are the indices of the children of node at index `i`?",
         "Node index = i",
         ["Left: 2i + 1, Right: 2i + 2", "Left: 2i, Right: 2i + 1", "Left: i/2, Right: i/2 + 1", "Left: i + 1, Right: i + 2"],
         "Left: 2i + 1, Right: 2i + 2",
         "For 0-based indexing, the left child is located at 2i + 1 and the right child at 2i + 2.", "Apply"),

        # --- TOPIC 5: Tree Traversal ---
        (2, 5, 2, "Preorder Traversal", "Beginner", "mcq",
         "What is the visit order of nodes in Preorder traversal?",
         None, ["Root -> Left -> Right", "Left -> Root -> Right", "Left -> Right -> Root", "Right -> Root -> Left"],
         "Root -> Left -> Right",
         "Preorder processes the current root node first ('pre'), followed by its left and right subtrees.", "Remember"),

        (2, 5, 2, "Postorder Traversal", "Beginner", "mcq",
         "Which traversal is most naturally suited for deleting or freeing memory in an allocated binary tree?",
         None, ["Postorder (Left -> Right -> Root)", "Preorder (Root -> Left -> Right)", "Inorder (Left -> Root -> Right)", "Breadth-First Search"],
         "Postorder (Left -> Right -> Root)",
         "Postorder ensures that child nodes are deleted before their parent node is freed, preventing dangling pointer bugs.", "Understand"),

        (2, 5, 3, "BST Inorder Property", "Intermediate", "mcq",
         "What mathematical guarantee is provided when performing an Inorder traversal on a Binary Search Tree (BST)?",
         None, ["The visited node values appear in strictly sorted ascending order", "The visited node values appear in descending order", "Nodes are grouped by their depth levels", "Leaves appear before internal nodes"],
         "The visited node values appear in strictly sorted ascending order",
         "Because BST maintains Left < Root < Right, inorder traversal Left-Root-Right naturally generates sorted order.", "Understand"),

        (2, 5, 3, "Level Order Traversal", "Intermediate", "code_logic",
         "Which auxiliary data structure is fundamentally required to perform a Level-Order (Breadth-First) tree traversal?",
         None, ["Queue", "Stack", "Priority Queue", "Disjoint Set"], "Queue",
         "Level order traversal visits nodes horizontally level-by-level, which requires a FIFO Queue to schedule discovered children.", "Apply"),

        (2, 5, 4, "Reconstruct Tree from Traversals", "Advanced", "code_logic",
         "Which pair of traversals is sufficient to uniquely reconstruct any binary tree?",
         None, ["Inorder and Preorder", "Preorder and Postorder", "Level-order and Preorder", "Postorder and Level-order"],
         "Inorder and Preorder",
         "Preorder identifies the root node, and Inorder splits the remaining elements into left and right subtrees unambiguously.", "Analyze"),

        (2, 5, 4, "Iterative Inorder with Stack", "Advanced", "code_logic",
         "In an iterative inorder traversal without recursion, what do you do after pushing all left nodes onto a stack until reaching null?",
         None, ["Pop the stack, visit the node, and move to its right child", "Clear the entire stack and restart at root", "Push the right child immediately before popping", "Pop all nodes at once and print them in reverse"],
         "Pop the stack, visit the node, and move to its right child",
         "Popping retrieves the deepest left node; processing it and stepping right mirrors the recursive Inorder pattern.", "Analyze"),

        # --- TOPIC 6: Recursive Practice & Tree Processing ---
        (2, 6, 2, "Max Depth Calculation", "Beginner", "code_logic",
         "What is the recursive formula for computing the maximum depth (height) of a binary tree?",
         "def maxDepth(root):\n    if not root: return 0\n    return 1 + max(maxDepth(root.left), maxDepth(root.right))",
         ["1 + max(depth(left), depth(right))", "depth(left) + depth(right)", "max(depth(left), depth(right)) - 1", "2 * max(depth(left), depth(right))"],
         "1 + max(depth(left), depth(right))",
         "The height of a tree node is 1 (for current node) plus the maximum height among its two child subtrees.", "Apply"),

        (2, 6, 2, "Count Nodes Recursively", "Intermediate", "code_logic",
         "What base case and return statement correctly counts total nodes in a binary tree?",
         "def countNodes(root):\n    if not root: return 0\n    return 1 + countNodes(root.left) + countNodes(root.right)",
         ["1 + countNodes(root.left) + countNodes(root.right)", "countNodes(root.left) * countNodes(root.right)", "max(countNodes(root.left), countNodes(root.right))", "1 + max(countNodes(left), countNodes(right))"],
         "1 + countNodes(root.left) + countNodes(root.right)",
         "Every existing node contributes 1, plus the total count of its left and right subtrees.", "Apply"),

        (2, 6, 3, "Symmetric Tree Check", "Intermediate", "mcq",
         "To verify if a tree is symmetric (a mirror of itself), which two subtrees must be compared recursively?",
         None, ["t1.left with t2.right AND t1.right with t2.left", "t1.left with t2.left AND t1.right with t2.right", "t1.val with root.val", "Left subtree height with right subtree height"],
         "t1.left with t2.right AND t1.right with t2.left",
         "Mirror reflection requires that outer children match (left with right) and inner children match (right with left).", "Analyze"),

        (2, 6, 4, "Lowest Common Ancestor (BST)", "Advanced", "code_logic",
         "In a BST, if `p.val < root.val` and `q.val < root.val`, where does the Lowest Common Ancestor (LCA) reside?",
         "if p.val < root.val and q.val < root.val:",
         ["In root.left (left subtree)", "In root.right (right subtree)", "At the root node itself", "Cannot be determined without a full search"],
         "In root.left (left subtree)",
         "Since both query values are smaller than root in a BST, both nodes lie exclusively in the left subtree.", "Analyze"),

        (2, 6, 4, "Path Sum Problem", "Advanced", "code_logic",
         "In the Path Sum problem (hasPathSum(root, targetSum)), what should the function check when reaching a leaf node?",
         "if not root.left and not root.right:",
         ["return targetSum == root.val", "return targetSum == 0", "return targetSum < 0", "return True unconditionally"],
         "return targetSum == root.val",
         "At a leaf, the remaining required targetSum must equal the leaf node's value for a valid root-to-leaf path.", "Apply"),

        # --- TOPIC 7: Tree Problems & Applications ---
        (2, 7, 2, "Validate BST Rule", "Beginner", "mcq",
         "In a valid Binary Search Tree (BST), what relation must hold for every node X?",
         None, ["All nodes in X.left < X.val AND all nodes in X.right > X.val", "Only the immediate left child < X.val and immediate right child > X.val", "X.left.val + X.right.val == X.val", "Root is always the largest node in the entire tree"],
         "All nodes in X.left < X.val AND all nodes in X.right > X.val",
         "The BST invariant applies globally: every descendant in the left subtree must be less, and in the right must be greater.", "Understand"),

        (2, 7, 2, "Search in BST Complexity", "Intermediate", "mcq",
         "What is the average and worst-case time complexity for searching a key in a BST of N nodes?",
         None, ["Average O(log n), Worst O(n)", "Average O(1), Worst O(n)", "Average O(n), Worst O(n log n)", "Average O(log n), Worst O(log n)"],
         "Average O(log n), Worst O(n)",
         "Balanced BSTs halve search space per step yielding O(log n); skewed linear trees degenerate into linked lists of O(n).", "Understand"),

        (2, 7, 3, "AVL Tree Balance Factor", "Intermediate", "code_logic",
         "In an AVL Tree, what are the only permissible balance factors for any node?",
         "Balance Factor = height(left) - height(right)",
         ["-1, 0, or +1", "-2, 0, or +2", "0 only", "Any integer >= 0"], "-1, 0, or +1",
         "AVL invariant mandates that subtrees differ in height by at most 1 at every single node.", "Apply"),

        (2, 7, 4, "Trie (Prefix Tree) Application", "Advanced", "mcq",
         "Why is a Trie (Prefix Tree) preferred over a Hash Table for implementing search-engine autocomplete features?",
         None, ["It efficiently retrieves all strings sharing a given prefix in O(prefix_length) time", "It uses strictly less memory than any hash table", "It computes cryptographic hashes of keys", "It guarantees O(1) worst case insertions for any length text"],
         "It efficiently retrieves all strings sharing a given prefix in O(prefix_length) time",
         "Tries structure shared prefixes along node branches, making prefix lookups and autocomplete traversals direct and fast.", "Analyze"),

        (2, 7, 4, "Binary Heap as Tree", "Advanced", "code_logic",
         "Which property allows a Min-Heap to be stored efficiently in a contiguous array without pointers?",
         None, ["It is a complete binary tree, guaranteeing no gaps between elements in array order", "It is an AVL balanced tree", "Its height is strictly 2", "All elements have identical keys"],
         "It is a complete binary tree, guaranteeing no gaps between elements in array order",
         "Completeness ensures child indices 2i+1 and 2i+2 map sequentially to contiguous array indices without vacant cells.", "Understand"),

        # --- TOPIC 8: Algorithm Complexity & Big-O ---
        (2, 8, 3, "Big-O Definition", "Beginner", "mcq",
         "What does Big-O notation mathematically represent when analyzing algorithm performance?",
         None, ["An asymptotic upper bound on the growth rate of runtime or memory as input size N grows", "The exact clock runtime in milliseconds on a specific processor", "The minimum number of CPU instructions needed in the best case", "The average number of bugs per 100 lines of code"],
         "An asymptotic upper bound on the growth rate of runtime or memory as input size N grows",
         "Big-O characterizes how runtime scales asymptotically in the worst-case ceiling as N approaches infinity.", "Remember"),

        (2, 8, 3, "Binary Search Complexity", "Beginner", "mcq",
         "What is the time complexity of Binary Search on a sorted array of size N?",
         None, ["O(log n)", "O(n)", "O(1)", "O(n log n)"], "O(log n)",
         "Binary search discards half the search range in each iteration, running in logarithmic time.", "Remember"),

        (2, 8, 3, "Nested Loop Analysis", "Intermediate", "code_logic",
         "What is the Big-O time complexity of this code segment?",
         "for i in range(n):\n    for j in range(n):\n        total += 1",
         ["O(n^2)", "O(n)", "O(2n)", "O(n log n)"], "O(n^2)",
         "The inner loop runs n times for each of the n outer iterations, executing n * n = n^2 operations.", "Apply"),

        (2, 8, 3, "Logarithmic Loop Analysis", "Intermediate", "code_logic",
         "What is the time complexity of the following loop?",
         "i = 1\nwhile i < n:\n    i = i * 2",
         ["O(log n)", "O(n)", "O(n / 2)", "O(1)"], "O(log n)",
         "Doubling the iterator in each step requires approximately log_2(n) iterations before exceeding n.", "Apply"),

        (2, 8, 4, "Space Complexity of Recursion", "Advanced", "code_logic",
         "What is the auxiliary space complexity of Merge Sort on an array of size N?",
         None, ["O(n) auxiliary space", "O(1) in-place", "O(n^2)", "O(log n)"], "O(n) auxiliary space",
         "Standard merge sort requires a temporary buffer of size n during the merge phase, yielding O(n) auxiliary space.", "Analyze"),

        (2, 8, 4, "Comparing Growth Rates", "Advanced", "mcq",
         "Arrange the following complexities in order from fastest growing (slowest algorithm) to slowest growing (fastest algorithm): O(n!), O(n^2), O(2^n), O(n log n)",
         None, ["O(n!) > O(2^n) > O(n^2) > O(n log n)", "O(2^n) > O(n!) > O(n^2) > O(n log n)", "O(n^2) > O(n log n) > O(2^n) > O(n!)", "O(n!) > O(n^2) > O(2^n) > O(n log n)"],
         "O(n!) > O(2^n) > O(n^2) > O(n log n)",
         "Factorial growth O(n!) dominates exponential O(2^n), followed by polynomial O(n^2) and linearithmic O(n log n).", "Analyze")
    ]

    for q in cs201_questions:
        inserted += insert_q(*q)

    # =========================================================================
    # COURSE 1: PROGRAMMING IN PYTHON (CS101) - Topics 9 to 16
    # CO1 = 5, CO2 = 6, CO3 = 7, CO4 = 8
    # =========================================================================

    cs101_questions = [
        # Topic 9: Variables & Types
        (1, 9, 5, "Mutable vs Immutable", "Beginner", "mcq",
         "Which of the following built-in Python data types is mutable?",
         None, ["list", "tuple", "str", "int"], "list",
         "Lists can be modified in-place via append, pop, and index assignment; tuples, strings, and ints are immutable.", "Remember"),
        (1, 9, 5, "F-Strings", "Intermediate", "code_logic",
         "What does `f'{3.14159:.2f}'` evaluate to in Python 3.6+?",
         "val = 3.14159\nprint(f'{val:.2f}')",
         ["'3.14'", "'3.14159'", "'3.1'", "SyntaxError"], "'3.14'",
         "The format specifier `:.2f` formats the float rounded to 2 decimal places.", "Apply"),
        (1, 9, 5, "Deep Copy vs Shallow Copy", "Advanced", "code_logic",
         "What is the effect of `copy.deepcopy()` on nested lists in Python?",
         None, ["It recursively clones both the outer and all inner nested objects into new memory", "It copies only references to inner lists", "It converts all inner elements into tuples", "It throws a TypeError on nested collections"],
         "It recursively clones both the outer and all inner nested objects into new memory",
         "deepcopy duplicates the full recursive graph of objects, ensuring mutations to copies do not affect the original.", "Analyze"),

        # Topic 10: Conditionals
        (1, 10, 6, "Ternary Operator", "Beginner", "code_logic",
         "How is the conditional ternary expression structured in Python?",
         None, ["x if condition else y", "condition ? x : y", "if condition then x else y", "select(condition, x, y)"],
         "x if condition else y",
         "Python expresses ternary logic with the syntax `value_if_true if condition else value_if_false`.", "Remember"),
        (1, 10, 6, "Short-Circuit Evaluation", "Intermediate", "code_logic",
         "What is the output of `False and print('Hello')` in Python?",
         "res = False and print('Hello')",
         ["False (and 'Hello' is NOT printed)", "None", "'Hello' is printed then False", "Error"],
         "False (and 'Hello' is NOT printed)",
         "Python short-circuits the `and` operator: because the left operand is False, the right expression is never evaluated.", "Understand"),

        # Topic 11: Loops & Iteration
        (1, 11, 6, "For-Else Loop", "Intermediate", "code_logic",
         "In Python, when does the `else` block attached to a `for` loop execute?",
         "for x in items:\n    if x == target: break\nelse:\n    print('Not found')",
         ["Only when the loop finishes without hitting a `break` statement", "Always after the loop finishes regardless of break", "Only when the items collection is initially empty", "Whenever an unhandled exception occurs inside the loop"],
         "Only when the loop finishes without hitting a `break` statement",
         "The `else` clause of a loop runs only if the loop terminates normally (exhausted without encountering a `break`).", "Analyze"),
        (1, 11, 6, "Enumerate Function", "Beginner", "code_logic",
         "What does `enumerate(['a', 'b', 'c'])` yield in each iteration?",
         "for item in enumerate(['a', 'b', 'c']):",
         ["Tuples of (index, value)", "Values only", "Indices only", "A dictionary mapping"],
         "Tuples of (index, value)",
         "enumerate yields pairs containing a zero-based counter index alongside the respective collection item.", "Remember"),

        # Topic 12: Lists & Tuples
        (1, 12, 7, "List Comprehensions", "Beginner", "code_logic",
         "What list does `[x**2 for x in range(4) if x % 2 == 0]` generate?",
         "[x**2 for x in range(4) if x % 2 == 0]",
         ["[0, 4]", "[0, 1, 4, 9]", "[1, 9]", "[4]"], "[0, 4]",
         "range(4) produces 0, 1, 2, 3. The even numbers are 0 and 2. Squaring them produces [0, 4].", "Apply"),
        (1, 12, 7, "Tuple Immutability", "Intermediate", "mcq",
         "Why can a tuple `(1, 2, 3)` be used as a dictionary key, but a list `[1, 2, 3]` cannot?",
         None, ["Tuples are hashable because they are immutable; lists are unhashable because they are mutable", "Lists are too large for dictionary buckets", "Tuples have faster string conversions", "Python dicts accept only strings as keys"],
         "Tuples are hashable because they are immutable; lists are unhashable because they are mutable",
         "Dictionary keys require constant hash values throughout their lifetime; mutable lists cannot provide this guarantee.", "Understand"),

        # Topic 13: Dictionaries & Sets
        (1, 13, 7, "Dict Get Method", "Beginner", "code_logic",
         "What does `d.get('age', 25)` return if `'age'` is not a key in dictionary `d`?",
         "d = {'name': 'Alice'}\nprint(d.get('age', 25))",
         ["25", "KeyError: 'age'", "None", "0"], "25",
         "`dict.get(key, default)` returns the specified fallback default value if the key does not exist.", "Apply"),
        (1, 13, 7, "Set Operations", "Intermediate", "code_logic",
         "What does `{1, 2, 3} & {2, 3, 4}` calculate?",
         "{1, 2, 3} & {2, 3, 4}",
         ["{2, 3} (Set intersection)", "{1, 2, 3, 4} (Set union)", "{1} (Set difference)", "{1, 4} (Symmetric difference)"],
         "{2, 3} (Set intersection)",
         "The `&` operator computes set intersection, returning only elements present in both sets.", "Apply"),

        # Topic 14: Functions & Scope
        (1, 14, 7, "LEGB Rule", "Intermediate", "mcq",
         "What order does Python follow when resolving variable names according to the LEGB rule?",
         None, ["Local -> Enclosing -> Global -> Built-in", "Local -> Global -> Enclosing -> Built-in", "Global -> Local -> Built-in -> Enclosing", "Built-in -> Global -> Enclosing -> Local"],
         "Local -> Enclosing -> Global -> Built-in",
         "Python searches the Local scope first, then any Enclosing functions, then Global module scope, and finally Built-ins.", "Remember"),
        (1, 14, 7, "Lambda Functions", "Beginner", "code_logic",
         "What is a Python `lambda` expression?",
         "add = lambda a, b: a + b",
         ["An anonymous inline function restricted to a single expression", "A function that runs asynchronously in a separate thread", "A function with no arguments", "A function that cannot return values"],
         "An anonymous inline function restricted to a single expression",
         "Lambdas provide concise syntax for creating small, anonymous callable objects.", "Understand"),

        # Topic 15: File I/O & Exceptions
        (1, 15, 8, "Context Managers", "Beginner", "code_logic",
         "What is the primary advantage of opening files using the `with` statement (`with open(...) as f:`)?",
         None, ["It automatically closes the file descriptor even if an exception is raised", "It encrypts file contents on disk", "It increases read throughput by 10x", "It disables write permissions on the file"],
         "It automatically closes the file descriptor even if an exception is raised",
         "The `with` statement leverages context managers to guarantee cleanup via `__exit__`.", "Understand"),
        (1, 15, 8, "Exception Hierarchy", "Intermediate", "mcq",
         "Which built-in class should custom user-defined exceptions inherit from in modern Python?",
         None, ["Exception", "BaseException", "StandardError", "SystemExit"], "Exception",
         "User exceptions should inherit from `Exception`, leaving `BaseException` for system-exiting signals like KeyboardInterrupt.", "Understand"),

        # Topic 16: OOP & Classes
        (1, 16, 8, "Self Parameter", "Beginner", "mcq",
         "What does the `self` parameter represent inside instance methods of a Python class?",
         None, ["A reference to the specific object instance invoking the method", "A global pointer to the class definition", "A copy of all class variables", "A keyword that creates a new thread"],
         "A reference to the specific object instance invoking the method",
         "When an instance method is called, Python automatically passes the instance object as the first argument (`self`).", "Understand"),
        (1, 16, 8, "Dunder Str vs Repr", "Intermediate", "code_logic",
         "What is the pedagogical difference between `__str__` and `__repr__` in Python classes?",
         None, ["__str__ is for human-readable end-user display; __repr__ is for unambiguous developer debugging", "__str__ is called by compiler; __repr__ is called by garbage collector", "They are identical synonyms", "__repr__ only works on numbers"],
         "__str__ is for human-readable end-user display; __repr__ is for unambiguous developer debugging",
         "`__repr__` aims to be unambiguous and often executable code; `__str__` provides a clean, readable summary for users.", "Analyze")
    ]

    for q in cs101_questions:
        inserted += insert_q(*q)

    # =========================================================================
    # COURSE 3: AI & MACHINE LEARNING (AI301) - Topics 17 to 24
    # CO1 = 9, CO2 = 10, CO3 = 11, CO4 = 12
    # =========================================================================

    ai301_questions = [
        # Topic 17: Statistical Learning
        (3, 17, 9, "Overfitting", "Beginner", "mcq",
         "What is 'overfitting' in machine learning models?",
         None, ["High training accuracy but poor generalization to unseen test data", "Low accuracy on both training and test data", "A model that trains too quickly", "A dataset with missing feature labels"],
         "High training accuracy but poor generalization to unseen test data",
         "Overfitting occurs when a model memorizes noise and quirks in the training dataset rather than true underlying patterns.", "Understand"),
        (3, 17, 9, "Standardization", "Intermediate", "code_logic",
         "What formula transforms a feature X into standard normal distribution (Z-score)?",
         "z = (x - mu) / sigma",
         ["z = (x - mean) / std_dev", "z = x / max(x)", "z = (x - min) / (max - min)", "z = log(x)"],
         "z = (x - mean) / std_dev",
         "Z-score standardization subtracts the feature mean and divides by standard deviation, giving zero mean and unit variance.", "Apply"),

        # Topic 18: Linear Regression
        (3, 18, 10, "Mean Squared Error", "Beginner", "mcq",
         "What loss function is standard for evaluating continuous predictions in Ordinary Least Squares (OLS) Regression?",
         None, ["Mean Squared Error (MSE)", "Cross-Entropy Loss", "Hinge Loss", "Dice Coefficient"],
         "Mean Squared Error (MSE)",
         "MSE penalizes larger prediction residuals quadratically, making it the primary objective function for linear regression.", "Remember"),

        # Topic 19: Classification
        (3, 19, 10, "Sigmoid Function", "Beginner", "code_logic",
         "What is the mathematical range of the logistic Sigmoid activation function `sigma(z) = 1 / (1 + e^-z)`?",
         "sigma(z) = 1 / (1 + exp(-z))",
         ["(0, 1)", "[-1, 1]", "(-infinity, +infinity)", "[0, infinity)"],
         "(0, 1)",
         "The sigmoid maps any real-valued number into a smooth probability curve strictly between 0 and 1.", "Understand"),

        # Topic 20: Decision Trees
        (3, 20, 10, "Gini Impurity", "Intermediate", "mcq",
         "In Decision Tree algorithms (e.g. CART), what does a Gini Impurity of 0.0 indicate for a split node?",
         None, ["The node is completely pure (all samples belong to one single class)", "The node contains a 50/50 split of two classes", "The tree cannot be split any further", "The dataset contains corrupted labels"],
         "The node is completely pure (all samples belong to one single class)",
         "Gini impurity is 0 when all instances in that node belong to the exact same target classification.", "Understand"),

        # Topic 21: Model Evaluation
        (3, 21, 11, "Precision vs Recall", "Intermediate", "mcq",
         "In medical diagnostics for cancer detection where false negatives are dangerous, which metric should be maximized?",
         None, ["Recall (Sensitivity)", "Precision", "Specificity", "Raw Accuracy"],
         "Recall (Sensitivity)",
         "Recall = TP / (TP + FN). Maximizing recall minimizes false negatives, ensuring fewer malignant cases are overlooked.", "Analyze"),

        # Topic 22: Clustering
        (3, 22, 11, "K-Means Algorithm", "Beginner", "mcq",
         "What type of machine learning task is K-Means clustering?",
         None, ["Unsupervised Learning", "Supervised Learning", "Reinforcement Learning", "Semi-Supervised Regression"],
         "Unsupervised Learning",
         "K-Means groups unlabeled input samples into K spatial clusters based solely on distance metrics without target labels.", "Remember"),

        # Topic 23: PCA
        (3, 23, 11, "Dimensionality Reduction", "Advanced", "mcq",
         "What is the primary geometric objective of Principal Component Analysis (PCA)?",
         None, ["To find orthogonal axes that maximize the variance of projected data points", "To classify non-linear data into binary classes", "To train neural weights via gradient descent", "To impute missing data values"],
         "To find orthogonal axes that maximize the variance of projected data points",
         "PCA calculates eigenvectors of the covariance matrix to identify directional axes of greatest data spread/variance.", "Analyze"),

        # Topic 24: Neural Networks
        (3, 24, 12, "Backpropagation", "Intermediate", "mcq",
         "What calculus rule enables the backpropagation algorithm to compute partial derivatives through deep network layers?",
         None, ["The Chain Rule of calculus", "L'Hopital's Rule", "The Product Rule only", "Taylor Series Expansion"],
         "The Chain Rule of calculus",
         "Backprop recursively applies the chain rule from output loss backward to calculate weight gradients efficiently.", "Understand")
    ]

    for q in ai301_questions:
        inserted += insert_q(*q)

    # =========================================================================
    # COURSE 4: DATABASE MANAGEMENT SYSTEMS (CS302) - Topics 25 to 32
    # CO1 = 13, CO2 = 14, CO3 = 15, CO4 = 16
    # =========================================================================

    cs302_questions = [
        # Topic 25: Relational Model
        (4, 25, 13, "Primary Key", "Beginner", "mcq",
         "What two fundamental constraints must every Primary Key column satisfy in relational database schemas?",
         None, ["Unique and NOT NULL", "Foreign and Indexed", "Auto-incrementing and Numeric", "Encrypted and Clustered"],
         "Unique and NOT NULL",
         "A primary key uniquely distinguishes each tuple in a relation and cannot contain NULL values.", "Remember"),

        # Topic 26: SQL DDL
        (4, 26, 13, "DROP vs TRUNCATE", "Intermediate", "mcq",
         "What is the operational difference between SQL `DROP TABLE` and `TRUNCATE TABLE`?",
         None, ["DROP removes both table data and schema definition; TRUNCATE deletes all rows while preserving schema structure", "TRUNCATE deletes the table completely; DROP only clears records", "They are identical keywords", "TRUNCATE can be rolled back without transaction logs"],
         "DROP removes both table data and schema definition; TRUNCATE deletes all rows while preserving schema structure",
         "TRUNCATE empties the relation of data rapidly, while DROP destroys the relation catalog definition entirely.", "Analyze"),

        # Topic 27: SQL DML
        (4, 27, 14, "HAVING vs WHERE", "Intermediate", "code_logic",
         "What distinguishes the `HAVING` clause from the `WHERE` clause in SQL queries?",
         "SELECT dept, COUNT(*) FROM emp WHERE salary > 50000 GROUP BY dept HAVING COUNT(*) > 5",
         ["WHERE filters individual rows before grouping; HAVING filters aggregated groups after GROUP BY", "WHERE filters groups; HAVING filters rows", "HAVING is used only with subqueries", "WHERE can only be used with primary keys"],
         "WHERE filters individual rows before grouping; HAVING filters aggregated groups after GROUP BY",
         "WHERE operates on base table rows prior to aggregation; HAVING applies conditions to aggregated group records.", "Understand"),

        # Topic 28: Complex Joins
        (4, 28, 14, "LEFT OUTER JOIN", "Beginner", "mcq",
         "What rows does a `LEFT OUTER JOIN` return?",
         None, ["All rows from the left table, matched with corresponding right table rows, filling NULLs for unmatched right entries", "Only rows that have matches in both tables", "All rows from the right table only", "Cartesian cross product of both tables"],
         "All rows from the left table, matched with corresponding right table rows, filling NULLs for unmatched right entries",
         "A LEFT JOIN preserves every row from the left operand regardless of whether a matching record exists on the right.", "Understand"),

        # Topic 29: Relational Algebra
        (4, 29, 13, "Projection Operator", "Intermediate", "mcq",
         "Which relational algebra operator (symbol Pi) selects specific attribute columns while discarding duplicate tuples?",
         None, ["Projection (Pi)", "Selection (Sigma)", "Cartesian Product (X)", "Natural Join (|><|)"],
         "Projection (Pi)",
         "Projection (Pi) selects specified columns across all rows, functioning like `SELECT DISTINCT col1, col2`.", "Remember"),

        # Topic 30: Normalization
        (4, 30, 15, "Third Normal Form (3NF)", "Intermediate", "mcq",
         "What condition must a relation satisfy to achieve Third Normal Form (3NF)?",
         None, ["It must be in 2NF and contain NO transitive functional dependencies of non-prime attributes on candidate keys", "Every non-key attribute must depend on part of a composite key", "It must have exactly 3 columns", "All attributes must allow null values"],
         "It must be in 2NF and contain NO transitive functional dependencies of non-prime attributes on candidate keys",
         "3NF eliminates transitive dependencies (X -> Y -> Z), ensuring all non-prime attributes depend solely on candidate keys.", "Understand"),

        # Topic 31: Indexing & B-Trees
        (4, 31, 15, "B+ Tree Indexing", "Advanced", "mcq",
         "Why are B+ Trees favored over Binary Search Trees for disk-based database indexes?",
         None, ["High fan-out yields short tree height, drastically minimizing disk I/O read operations, and leaf nodes form a linked list for range queries", "They consume zero disk memory", "They guarantee O(1) worst-case updates", "They require no rebalancing"],
         "High fan-out yields short tree height, drastically minimizing disk I/O read operations, and leaf nodes form a linked list for range queries",
         "High branching factors fit block sizes nicely, keeping depth to 3-4 levels for millions of records with sequential range scans.", "Analyze"),

        # Topic 32: Transactions & ACID
        (4, 32, 16, "ACID Isolation", "Beginner", "mcq",
         "What does the 'I' (Isolation) in database ACID transaction properties guarantee?",
         None, ["Concurrent transactions execute without interfering with one another as if executed serially", "Transactions are stored in isolated hardware chips", "Data changes survive system crashes", "All or nothing execution of database operations"],
         "Concurrent transactions execute without interfering with one another as if executed serially",
         "Isolation ensures that intermediate states of uncommitted concurrent transactions remain shielded from other operations.", "Remember")
    ]

    for q in cs302_questions:
        inserted += insert_q(*q)

    conn.commit()
    print(f"Successfully inserted {inserted} new questions into question_bank!")

    # Print summary counts per topic for Course 2
    c.execute("SELECT topic_id, count(*) FROM question_bank WHERE course_id = 2 GROUP BY topic_id ORDER BY topic_id")
    print("Course 2 Questions per topic now:", c.fetchall())

    # Total question count
    c.execute("SELECT count(*) FROM question_bank")
    print("Total QuestionBank count now:", c.fetchone()[0])

    conn.close()

if __name__ == "__main__":
    expand_all_questions()
