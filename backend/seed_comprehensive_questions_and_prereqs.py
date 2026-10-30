import sqlite3
import json
from datetime import datetime

def setup_prerequisites_and_questions():
    conn = sqlite3.connect("backend/obe_learning.db")
    c = conn.cursor()

    # =========================================================================
    # 1. PREREQUISITES FOR ALL COURSES
    # =========================================================================
    print("Setting up prerequisites for all courses...")
    # Clear existing prerequisites to establish clean graph
    c.execute("DELETE FROM topic_prerequisites")

    prereqs = [
        # Course 2 (CS201 Data Structures)
        (5, 3, 60.0), # Tree Traversal -> Recursion Fundamentals
        (5, 4, 60.0), # Tree Traversal -> Tree Basics
        (6, 3, 60.0), # Recursive Practice -> Recursion Fundamentals
        (7, 5, 60.0), # Tree Problems -> Tree Traversal
        (8, 1, 60.0), # Algorithm Complexity -> Stack Basics

        # Course 1 (CS101 Python Programming)
        (10, 9, 60.0),  # Conditionals -> Variables & Basic I/O
        (11, 10, 60.0), # Loops -> Conditionals
        (12, 11, 60.0), # Lists & Tuples -> Loops
        (13, 12, 60.0), # Dictionaries & Sets -> Lists & Tuples
        (14, 12, 60.0), # Functions -> Lists & Tuples
        (15, 14, 60.0), # File I/O & Exceptions -> Functions
        (16, 14, 60.0), # OOP in Python -> Functions

        # Course 3 (AI301 Machine Learning)
        (18, 17, 60.0), # Linear Regression -> Statistical Learning
        (19, 18, 60.0), # Logistic Regression -> Linear Regression
        (20, 19, 60.0), # Decision Trees -> Logistic Regression
        (21, 19, 60.0), # Model Evaluation -> Logistic Regression
        (22, 17, 60.0), # Clustering & K-Means -> Statistical Learning
        (23, 17, 60.0), # PCA -> Statistical Learning
        (24, 18, 60.0), # Neural Networks -> Linear Regression
        (24, 21, 60.0), # Neural Networks -> Model Evaluation

        # Course 4 (CS302 DBMS)
        (26, 25, 60.0), # SQL DDL -> Relational Data Model
        (27, 26, 60.0), # SQL DML -> SQL DDL
        (28, 27, 60.0), # SQL Joins & Subqueries -> SQL DML
        (29, 25, 60.0), # Relational Algebra -> Relational Data Model
        (30, 25, 60.0), # Functional Dependencies -> Relational Data Model
        (31, 28, 60.0), # Indexing & B-Trees -> SQL Joins & Subqueries
        (32, 28, 60.0), # Transactions & ACID -> SQL Joins & Subqueries
    ]

    for tid, ptid, req in prereqs:
        c.execute("""
            INSERT INTO topic_prerequisites (topic_id, prerequisite_topic_id, required_mastery_pct)
            VALUES (?, ?, ?)
        """, (tid, ptid, req))

    conn.commit()
    print(f"Inserted {len(prereqs)} prerequisites across 4 courses.")

    # =========================================================================
    # 2. SEED QUESTION BANK FOR CS101, AI301, CS302 (5 QUESTIONS PER TOPIC)
    # =========================================================================
    print("Expanding Question Bank to ensure at least 5 questions per topic...")

    # helper to insert if not exist
    def insert_qb(course_id, topic_id, co_id, sub_concept, diff, qtype, qtext, snippet, options, answer, explanation):
        exists = c.execute("SELECT id FROM question_bank WHERE topic_id = ? AND question_text = ?", (topic_id, qtext)).fetchone()
        if not exists:
            c.execute("""
                INSERT INTO question_bank (course_id, topic_id, outcome_id, sub_concept, difficulty, question_type, question_text, code_snippet, options_json, correct_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (course_id, topic_id, co_id, sub_concept, diff, qtype, qtext, snippet, json.dumps(options), answer, explanation))


    # Fetch CO IDs for each course
    cos = {}
    for cid in [1, 2, 3, 4]:
        for co_id, code in c.execute("SELECT id, code FROM course_outcomes WHERE course_id = ?", (cid,)).fetchall():
            cos[(cid, code)] = co_id

    # -------------------------------------------------------------------------
    # COURSE 1: CS101 (Topics 9 to 16)
    # -------------------------------------------------------------------------
    cs101_questions = [
        # Topic 9: Variables, Data Types & Basic I/O (PY-1)
        (1, 9, cos.get((1, "CO1"), 1), "Variables & Types", "Beginner", "mcq",
         "Which function is used to take textual user input from the console in Python 3?",
         None, ["input()", "read()", "scan()", "get()"], "input()",
         "input() reads a line from input and converts it into a string."),
        (1, 9, cos.get((1, "CO1"), 1), "Type Casting", "Beginner", "code_logic",
         "What is the output of `type(int('42'))`?",
         "type(int('42'))", ["<class 'int'>", "<class 'str'>", "<class 'float'>", "ValueError"], "<class 'int'>",
         "int('42') parses the string literal into a Python integer."),
        (1, 9, cos.get((1, "CO1"), 1), "Data Types", "Intermediate", "mcq",
         "Which of the following creates a boolean False value in Python?",
         None, ["bool(0)", "bool('False')", "bool([0])", "bool(-1)"], "bool(0)",
         "In Python, 0, empty sequences, and None evaluate to False in boolean contexts."),
        (1, 9, cos.get((1, "CO2"), 2), "Formatted Strings", "Intermediate", "code_logic",
         "What does the expression `f'{3.14159:.2f}'` evaluate to?",
         "val = 3.14159\nprint(f'{val:.2f}')", ["'3.14'", "'3.15'", "'3.141'", "'3.1'"], "'3.14'",
         "The format specifier .2f rounds to 2 decimal places."),

        # Topic 10: Conditional Statements & Branching (PY-2)
        (1, 10, cos.get((1, "CO1"), 1), "Logical Operators", "Beginner", "mcq",
         "Which logical operator in Python returns True only if BOTH operands evaluate to True?",
         None, ["and", "or", "not", "xor"], "and",
         "The and operator requires both operands to be truthy."),
        (1, 10, cos.get((1, "CO2"), 2), "Branch Execution", "Beginner", "code_logic",
         "What is the output of `x = 10; print('A' if x > 15 else 'B')`?",
         "x = 10\nprint('A' if x > 15 else 'B')", ["B", "A", "None", "SyntaxError"], "B",
         "Because 10 > 15 is False, the ternary expression evaluates to the else clause 'B'."),
        (1, 10, cos.get((1, "CO2"), 2), "Nested Conditionals", "Intermediate", "code_logic",
         "What prints when `score = 75` in: `if score >= 80: print('A') elif score >= 70: print('B') else: print('C')`?",
         "score = 75\nif score >= 80:\n    print('A')\nelif score >= 70:\n    print('B')\nelse:\n    print('C')", ["B", "A", "C", "A and B"], "B",
         "75 is not >= 80, but it satisfies >= 70, matching the elif block."),
        (1, 10, cos.get((1, "CO2"), 2), "Short-circuit Evaluation", "Advanced", "mcq",
         "Why does `False and undefined_variable` NOT raise a NameError in Python?",
         None, ["Short-circuit evaluation stops as soon as the first operand is False", "Python defines all variables automatically", "Logical operators run at compile time", "Undefined variables are treated as False"],
         "Short-circuit evaluation stops as soon as the first operand is False",
         "The and operator aborts evaluation immediately if the left operand is falsy."),

        # Topic 11: Loops & Iterative Control (PY-3)
        (1, 11, cos.get((1, "CO2"), 2), "While Loops", "Beginner", "code_logic",
         "How many times will `i = 0; while i < 3: i += 1` loop?",
         "i = 0\nwhile i < 3:\n    i += 1", ["3 times", "2 times", "4 times", "Infinite loop"], "3 times",
         "The loop executes for i=0, i=1, and i=2, terminating when i becomes 3."),
        (1, 11, cos.get((1, "CO2"), 2), "Loop Continue", "Intermediate", "code_logic",
         "What is the sum computed by: `s = 0; for i in range(5): if i % 2 == 0: continue; s += i`?",
         "s = 0\nfor i in range(5):\n    if i % 2 == 0:\n        continue\n    s += i\nprint(s)", ["4", "6", "10", "0"], "4",
         "The continue skips even numbers (0, 2, 4); sum is 1 + 3 = 4."),
        (1, 11, cos.get((1, "CO2"), 2), "For-Else Construct", "Intermediate", "mcq",
         "When does the `else` block of a Python `for` loop execute?",
         None, ["When the loop finishes normally without encountering a break", "Whenever the loop body executes at least once", "Only when the loop encounters an exception", "It never executes after a for loop"],
         "When the loop finishes normally without encountering a break",
         "In Python, for-else executes if the loop terminates via iterator exhaustion."),
        (1, 11, cos.get((1, "CO2"), 2), "Nested Loop Complexity", "Advanced", "code_logic",
         "What is the total number of iterations in `for i in range(4): for j in range(i): pass`?",
         "count = 0\nfor i in range(4):\n    for j in range(i):\n        count += 1", ["6", "12", "16", "4"], "6",
         "i=0: 0, i=1: 1, i=2: 2, i=3: 3. Total iterations: 0 + 1 + 2 + 3 = 6."),

        # Topic 12: Python Lists & Tuples (PY-4)
        (1, 12, cos.get((1, "CO1"), 1), "List Appending", "Beginner", "code_logic",
         "What does `arr = [1, 2]; arr.append(3); print(arr)` output?",
         "arr = [1, 2]\narr.append(3)\nprint(arr)", ["[1, 2, 3]", "[3, 1, 2]", "[1, 2]", "None"], "[1, 2, 3]",
         "append() adds an item to the end of a mutable list."),
        (1, 12, cos.get((1, "CO2"), 2), "Tuple Immutability", "Beginner", "mcq",
         "What happens when executing `t = (1, 2); t[0] = 99`?",
         None, ["TypeError: 'tuple' object does not support item assignment", "t becomes (99, 2)", "IndexError: index out of range", "SyntaxError"],
         "TypeError: 'tuple' object does not support item assignment",
         "Tuples are immutable; their elements cannot be reassigned."),
        (1, 12, cos.get((1, "CO2"), 2), "List Comprehensions", "Intermediate", "code_logic",
         "What is the value of `[x * 2 for x in [1, 2, 3] if x > 1]`?",
         "[x * 2 for x in [1, 2, 3] if x > 1]", ["[4, 6]", "[2, 4, 6]", "[2, 4]", "[6]"], "[4, 6]",
         "Only 2 and 3 satisfy x > 1, producing 2*2=4 and 3*2=6."),
        (1, 12, cos.get((1, "CO3"), 3), "Negative Slicing", "Advanced", "code_logic",
         "What does `arr = [10, 20, 30, 40]; print(arr[::-1])` produce?",
         "arr = [10, 20, 30, 40]\nprint(arr[::-1])", ["[40, 30, 20, 10]", "[10, 20, 30, 40]", "[-10, -20, -30, -40]", "IndexError"], "[40, 30, 20, 10]",
         "A slice step of -1 reverses the sequence."),

        # Topic 13: Dictionaries, Sets & Hash Collections (PY-5)
        (1, 13, cos.get((1, "CO2"), 2), "Set Uniqueness", "Beginner", "code_logic",
         "What is `len(set([1, 2, 2, 3, 3, 3]))`?",
         "s = set([1, 2, 2, 3, 3, 3])\nprint(len(s))", ["3", "6", "1", "TypeError"], "3",
         "Sets eliminate duplicates, leaving unique elements {1, 2, 3}."),
        (1, 13, cos.get((1, "CO3"), 3), "Dictionary Get Method", "Intermediate", "code_logic",
         "What does `d = {'a': 1}; print(d.get('b', 0))` output?",
         "d = {'a': 1}\nprint(d.get('b', 0))", ["0", "None", "KeyError", "1"], "0",
         "get() returns the fallback default (0) when the requested key is absent."),
        (1, 13, cos.get((1, "CO3"), 3), "Dict Comprehension", "Intermediate", "code_logic",
         "What is `{x: x**2 for x in (1, 2, 3)}[2]`?",
         "squares = {x: x**2 for x in (1, 2, 3)}\nprint(squares[2])", ["4", "2", "9", "KeyError"], "4",
         "Key 2 maps to 2**2 = 4."),
        (1, 13, cos.get((1, "CO3"), 3), "Hashability Rule", "Advanced", "mcq",
         "Which of the following CANNOT be used as a key in a Python dictionary?",
         None, ["A Python list `[1, 2]`", "A tuple `(1, 2)`", "An integer `42`", "A string `'key'`"], "A Python list `[1, 2]`",
         "Dictionary keys must be hashable and immutable; lists are mutable and unhashable."),

        # Topic 14: Functions, Scope & Parameter Passing (PY-6)
        (1, 14, cos.get((1, "CO3"), 3), "Return Values", "Beginner", "code_logic",
         "What does a Python function return if it lacks an explicit `return` statement?",
         "def foo():\n    pass\nprint(foo())", ["None", "0", "False", "Undefined"], "None",
         "Python functions without a return statement return None by default."),
        (1, 14, cos.get((1, "CO3"), 3), "Arbitrary Arguments *args", "Intermediate", "code_logic",
         "In `def fn(*args): return sum(args)`, what type is `args` inside the function?",
         "def fn(*args):\n    return type(args)", ["<class 'tuple'>", "<class 'list'>", "<class 'set'>", "<class 'dict'>"], "<class 'tuple'>",
         "*args packs variable positional arguments into a tuple."),
        (1, 14, cos.get((1, "CO3"), 3), "Keyword Arguments **kwargs", "Intermediate", "mcq",
         "What does `**kwargs` do in a Python function parameter list?",
         None, ["Collects extra keyword arguments into a dictionary", "Packs extra positional arguments into a list", "Forces arguments to be integer types", "Calculates keyword frequency"],
         "Collects extra keyword arguments into a dictionary",
         "**kwargs collects arbitrary keyword arguments into a dict."),
        (1, 14, cos.get((1, "CO4"), 4), "Lambda Expressions", "Advanced", "code_logic",
         "What is the output of `f = lambda x, y: x * y; print(f(3, 4))`?",
         "f = lambda x, y: x * y\nprint(f(3, 4))", ["12", "7", "34", "SyntaxError"], "12",
         "The lambda takes x=3, y=4 and returns 3 * 4 = 12."),

        # Topic 15: File I/O & Exception Handling (PY-7)
        (1, 15, cos.get((1, "CO3"), 3), "Context Managers", "Beginner", "mcq",
         "What is the primary advantage of using `with open(...) as f:` to handle files?",
         None, ["Automatically closes the file stream even if an exception occurs", "Compresses file contents automatically", "Prevents all syntax errors", "Runs file writes asynchronously"],
         "Automatically closes the file stream even if an exception occurs",
         "Context managers guarantee file handle cleanup upon exiting the block."),
        (1, 15, cos.get((1, "CO3"), 3), "Catching Exceptions", "Intermediate", "code_logic",
         "What does this print: `try: 1/0 except ZeroDivisionError: print('E') else: print('O')`?",
         "try:\n    1 / 0\nexcept ZeroDivisionError:\n    print('E')\nelse:\n    print('O')", ["E", "O", "ZeroDivisionError", "E then O"], "E",
         "Division by zero raises ZeroDivisionError, which executes the except block."),
        (1, 15, cos.get((1, "CO4"), 4), "File Reading Modes", "Intermediate", "mcq",
         "Which mode opens a file for writing, truncating existing content, and creating the file if missing?",
         None, ["'w'", "'r'", "'a'", "'x'"], "'w'",
         "'w' opens for writing, truncating existing data; 'a' appends without truncating."),
        (1, 15, cos.get((1, "CO4"), 4), "Custom Exceptions", "Advanced", "code_logic",
         "How do you define a custom exception class `InvalidAgeError` in Python?",
         None, ["class InvalidAgeError(Exception): pass", "def InvalidAgeError(): raise Error", "class InvalidAgeError: pass", "new Error InvalidAgeError"], "class InvalidAgeError(Exception): pass",
         "Custom exceptions should inherit from the built-in Exception class."),

        # Topic 16: Object-Oriented Programming in Python (PY-8)
        (1, 16, cos.get((1, "CO4"), 4), "Encapsulation & Attributes", "Beginner", "code_logic",
         "Given `class Dog: def __init__(self, name): self.name = name; d = Dog('Rex'); print(d.name)`?",
         "class Dog:\n    def __init__(self, name):\n        self.name = name\nd = Dog('Rex')\nprint(d.name)", ["Rex", "Dog", "None", "AttributeError"], "Rex",
         "Instance attribute name is initialized to 'Rex'."),
        (1, 16, cos.get((1, "CO4"), 4), "Class Inheritance", "Intermediate", "mcq",
         "Which function is used to invoke a method of the parent superclass from a child class?",
         None, ["super()", "parent()", "base()", "inherit()"], "super()",
         "super() delegates method calls to a parent or sibling class in the MRO."),
        (1, 16, cos.get((1, "CO4"), 4), "Dunder __str__ Method", "Intermediate", "code_logic",
         "What is the purpose of defining `__str__(self)` in a Python class?",
         None, ["Return an informal string representation when str() or print() is called", "Converts the object to an integer", "Allocates heap memory for strings", "Destroys string attributes"],
         "Return an informal string representation when str() or print() is called",
         "__str__ provides the human-readable string representation of the instance."),
        (1, 16, cos.get((1, "CO4"), 4), "Static and Class Methods", "Advanced", "mcq",
         "Which decorator is used to define a method that receives the class `cls` as its first argument instead of `self`?",
         None, ["@classmethod", "@staticmethod", "@property", "@abstractmethod"], "@classmethod",
         "@classmethod binds the class object as the first parameter.")
    ]

    for q in cs101_questions:
        insert_qb(*q)

    # -------------------------------------------------------------------------
    # COURSE 3: AI301 Machine Learning Fundamentals (Topics 17 to 24)
    # -------------------------------------------------------------------------
    ai301_questions = [
        # Topic 17: Statistical Learning & Feature Engineering (ML-1)
        (3, 17, cos.get((3, "CO1"), 1), "Train Test Split", "Beginner", "mcq",
         "Why is a dataset split into training and testing subsets?",
         None, ["To evaluate model generalization on unseen data and prevent data leakage", "To speed up CPU clock cycles", "To remove outliers automatically", "To double the number of samples"],
         "To evaluate model generalization on unseen data and prevent data leakage",
         "Independent test sets measure real-world generalization performance."),
        (3, 17, cos.get((3, "CO1"), 1), "One-Hot Encoding", "Beginner", "mcq",
         "What is the purpose of One-Hot Encoding in feature preprocessing?",
         None, ["Convert categorical text variables into binary dummy vectors", "Normalize continuous numerical features to [0, 1]", "Impute missing null values with the mean", "Perform dimensionality reduction"],
         "Convert categorical text variables into binary dummy vectors",
         "One-hot encoding maps nominal categorical levels into binary columns."),
        (3, 17, cos.get((3, "CO1"), 1), "Bias-Variance Tradeoff", "Intermediate", "mcq",
         "A model with high bias and low variance is typically suffering from what condition?",
         None, ["Underfitting", "Overfitting", "Data Leakage", "Gradient Explosion"], "Underfitting",
         "High bias implies the model is too simple to capture the underlying data patterns."),
        (3, 17, cos.get((3, "CO1"), 1), "Feature Scaling", "Advanced", "mcq",
         "Which algorithm is largely invariant to monotonic feature scaling?",
         None, ["Decision Trees", "K-Nearest Neighbors (KNN)", "Support Vector Machines (SVM)", "Logistic Regression with L2 Regularization"],
         "Decision Trees",
         "Decision trees split on orthogonal thresholds per feature, making them invariant to scale."),

        # Topic 18: Linear & Polynomial Regression (ML-2)
        (3, 18, cos.get((3, "CO1"), 1), "Residuals Definition", "Beginner", "mcq",
         "In regression analysis, what is a 'residual'?",
         None, ["The difference between the observed true target and predicted value (y - y_hat)", "The ratio of input features to targets", "The learning rate multiplier", "The intercept value"],
         "The difference between the observed true target and predicted value (y - y_hat)",
         "Residuals quantify individual prediction errors."),
        (3, 18, cos.get((3, "CO2"), 2), "R-Squared Metric", "Intermediate", "mcq",
         "What does an R^2 (coefficient of determination) score of 0.85 indicate?",
         None, ["85% of the target variance is explained by the regression features", "The model error is exactly 15%", "85% of predictions are perfectly accurate", "The learning rate was 0.85"],
         "85% of the target variance is explained by the regression features",
         "R^2 measures the proportion of variance in the dependent variable explained by model features."),
        (3, 18, cos.get((3, "CO2"), 2), "Gradient Descent", "Intermediate", "mcq",
         "What happens if the learning rate alpha in gradient descent is set too large?",
         None, ["Optimization may oscillate wildly and diverge away from the minimum", "Training will finish in 1 iteration", "The loss function becomes convex", "Weights stay constant at zero"],
         "Optimization may oscillate wildly and diverge away from the minimum",
         "Excessive learning rate overshoots valleys and causes loss divergence."),
        (3, 18, cos.get((3, "CO2"), 2), "Regularization Lasso vs Ridge", "Advanced", "mcq",
         "Which regularization technique uses an L1 penalty to drive irrelevant feature weights strictly to zero (sparse selection)?",
         None, ["Lasso Regression (L1)", "Ridge Regression (L2)", "Ordinary Least Squares", "Polynomial Regression"],
         "Lasso Regression (L1)",
         "L1 penalty induces sparsity in weights, effectively conducting feature selection."),

        # Topic 19: Logistic Regression & Classification (ML-3)
        (3, 19, cos.get((3, "CO2"), 2), "Logistic Hypothesis", "Beginner", "mcq",
         "What range of values does the standard Logistic/Sigmoid function output?",
         None, ["Between 0.0 and 1.0", "Between -1.0 and 1.0", "Between -infinity and +infinity", "Between 0 and 100"],
         "Between 0.0 and 1.0",
         "Sigmoid maps real inputs to probabilities in the open interval (0, 1)."),
        (3, 19, cos.get((3, "CO2"), 2), "Decision Boundary", "Intermediate", "mcq",
         "If the sigmoid probability threshold is set to 0.5, when is an instance classified as class 1?",
         None, ["When P(y=1|x) >= 0.5 (i.e. z >= 0)", "When P(y=1|x) < 0.25", "Only when P(y=1|x) == 1.0", "When the loss is zero"],
         "When P(y=1|x) >= 0.5 (i.e. z >= 0)",
         "Standard thresholding assigns class 1 when estimated probability meets or exceeds 0.5."),
        (3, 19, cos.get((3, "CO2"), 2), "Cross-Entropy Loss", "Intermediate", "mcq",
         "Why is Mean Squared Error (MSE) generally avoided when training Logistic Regression with Gradient Descent?",
         None, ["It yields a non-convex loss surface with multiple suboptimal local minima", "It cannot be calculated for fractions", "It always equals zero", "It is only defined for integers"],
         "It yields a non-convex loss surface with multiple suboptimal local minima",
         "Binary cross-entropy produces a convex loss surface for logistic models."),
        (3, 19, cos.get((3, "CO2"), 2), "Multiclass Logistic", "Advanced", "mcq",
         "Which function generalizes the Sigmoid function for multi-class classification distributions?",
         None, ["Softmax function", "ReLU function", "Linear activation", "Step function"], "Softmax function",
         "Softmax normalizes unnormalized logits into a multi-class probability distribution summing to 1."),

        # Topic 20: Decision Trees & Random Forests (ML-4)
        (3, 20, cos.get((3, "CO2"), 2), "Decision Tree Splitting", "Beginner", "mcq",
         "Which metric measures impurity in a set of class labels for CART decision trees?",
         None, ["Gini Impurity", "Mean Absolute Error", "Euclidean Distance", "Cosine Similarity"], "Gini Impurity",
         "Gini impurity measures the probability of misclassifying a randomly chosen element."),
        (3, 20, cos.get((3, "CO2"), 2), "Entropy & Information Gain", "Intermediate", "mcq",
         "In ID3 decision trees, what does 'Information Gain' represent?",
         None, ["The reduction in entropy achieved after splitting on a feature", "The increase in model training time", "The number of new leaf nodes created", "The depth of the root node"],
         "The reduction in entropy achieved after splitting on a feature",
         "Information gain measures the difference between parent entropy and weighted child entropy."),
        (3, 20, cos.get((3, "CO2"), 2), "Random Forest Bagging", "Intermediate", "mcq",
         "How does a Random Forest reduce the variance of individual high-variance decision trees?",
         None, ["By training multiple trees on bootstrap samples with random feature subsets and averaging their predictions", "By pruning every tree down to a single root node", "By training all trees on identical data", "By converting trees into neural networks"],
         "By training multiple trees on bootstrap samples with random feature subsets and averaging their predictions",
         "Bootstrap aggregating (bagging) and random feature subspace de-correlates trees to minimize variance."),
        (3, 20, cos.get((3, "CO4"), 4), "Tree Pruning", "Advanced", "mcq",
         "Why is cost-complexity pruning applied to deep decision trees?",
         None, ["To curb overfitting and improve generalization on test data", "To increase training accuracy to 100%", "To add more leaf nodes", "To remove all decision paths"],
         "To curb overfitting and improve generalization on test data",
         "Pruning removes noisy leaves that model random sample noise."),

        # Topic 21: Model Evaluation & Validation (ML-5)
        (3, 21, cos.get((3, "CO2"), 2), "Confusion Matrix", "Beginner", "mcq",
         "In medical disease diagnosis, what does a 'False Negative' represent?",
         None, ["A sick patient incorrectly predicted as healthy", "A healthy patient predicted as sick", "A correctly diagnosed healthy patient", "A correctly diagnosed sick patient"],
         "A sick patient incorrectly predicted as healthy",
         "A false negative occurs when the true positive condition is missed."),
        (3, 21, cos.get((3, "CO2"), 2), "Precision vs Recall", "Intermediate", "mcq",
         "When fraud detection demands identifying nearly all fraudulent transactions even if some false alarms occur, which metric should be maximized?",
         None, ["Recall (Sensitivity)", "Precision", "Specificity", "Inverted Error"], "Recall (Sensitivity)",
         "High recall minimizes false negatives, capturing maximum positive events."),
        (3, 21, cos.get((3, "CO4"), 4), "K-Fold Cross Validation", "Intermediate", "mcq",
         "How does 5-Fold Cross Validation work?",
         None, ["The dataset is split into 5 equal folds; the model is trained on 4 and tested on 1, repeated 5 times", "The model is trained 5 times on the exact same full dataset", "5 different algorithms compete on 1 split", "The training dataset is duplicated 5 times"],
         "The dataset is split into 5 equal folds; the model is trained on 4 and tested on 1, repeated 5 times",
         "K-fold cross-validation averages performance across k independent test splits."),
        (3, 21, cos.get((3, "CO4"), 4), "ROC-AUC Score", "Advanced", "mcq",
         "What does an ROC-AUC of 0.5 represent?",
         None, ["Performance equivalent to random guessing", "Perfect classification performance", "Inverted predictions", "Zero false positives"],
         "Performance equivalent to random guessing",
         "An AUC of 0.5 represents a diagonal line with no discriminative power."),

        # Topic 22: Clustering & K-Means (ML-6)
        (3, 22, cos.get((3, "CO3"), 3), "Unsupervised Clustering", "Beginner", "mcq",
         "What distinguishes unsupervised clustering from supervised classification?",
         None, ["Clustering operates on unlabeled data without pre-existing target categories", "Clustering requires ground-truth training labels", "Clustering only works with text data", "Clustering never calculates distance metrics"],
         "Clustering operates on unlabeled data without pre-existing target categories",
         "Clustering identifies intrinsic groupings in data without label guidance."),
        (3, 22, cos.get((3, "CO3"), 3), "K-Means Centroid Step", "Intermediate", "mcq",
         "In K-Means, how are cluster centroids updated at the end of each iteration?",
         None, ["By calculating the mean coordinates of all data points assigned to each cluster", "By moving them randomly across the feature space", "By selecting the furthest outlier", "By deleting empty clusters"],
         "By calculating the mean coordinates of all data points assigned to each cluster",
         "Centroid updates compute the center of gravity of assigned member points."),
        (3, 22, cos.get((3, "CO3"), 3), "The Elbow Method", "Intermediate", "mcq",
         "What does the 'Elbow Method' evaluate to select an optimal number of clusters K?",
         None, ["The point of diminishing return where inertia (within-cluster sum of squares) slows its rate of decrease", "The maximum number of features", "The highest possible training accuracy", "The point where k equals the sample size"],
         "The point of diminishing return where inertia (within-cluster sum of squares) slows its rate of decrease",
         "The elbow point balances cluster compact cohesion against model complexity."),
        (3, 22, cos.get((3, "CO3"), 3), "K-Means Sensitivity", "Advanced", "mcq",
         "Why is K-Means clustering sensitive to outlier data points?",
         None, ["Outliers substantially distort the calculation of cluster centroid means", "Outliers prevent distance metrics from executing", "Outliers force k to become zero", "K-Means ignores outliers completely"],
         "Outliers substantially distort the calculation of cluster centroid means",
         "Means are vulnerable to extreme values, skewing cluster positions."),

        # Topic 23: Dimensionality Reduction & PCA (ML-7)
        (3, 23, cos.get((3, "CO3"), 3), "Curse of Dimensionality", "Beginner", "mcq",
         "What is the 'Curse of Dimensionality' in machine learning?",
         None, ["As feature dimensions grow, sample space expands exponentially and data points become sparse", "Computers crash when handling more than 5 features", "High dimensional data always produces zero error", "Features become correlated automatically"],
         "As feature dimensions grow, sample space expands exponentially and data points become sparse",
         "High dimensionality leads to severe sparsity, hindering distance-based algorithms."),
        (3, 23, cos.get((3, "CO3"), 3), "Principal Components", "Intermediate", "mcq",
         "In Principal Component Analysis (PCA), what property does the First Principal Component (PC1) satisfy?",
         None, ["It accounts for the maximum possible variance in the dataset", "It is identical to the first feature column", "It has zero variance", "It minimizes eigenvalues"],
         "It accounts for the maximum possible variance in the dataset",
         "PC1 captures the axis of greatest directional variance."),
        (3, 23, cos.get((3, "CO3"), 3), "Orthogonality in PCA", "Intermediate", "mcq",
         "What is the geometric relationship between any two distinct Principal Components in PCA?",
         None, ["They are strictly orthogonal (mutually perpendicular and uncorrelated)", "They are parallel to each other", "They intersect at 45 degrees", "They have equal eigenvalues"],
         "They are strictly orthogonal (mutually perpendicular and uncorrelated)",
         "Principal components form an orthogonal basis."),
        (3, 23, cos.get((3, "CO4"), 4), "Explained Variance Ratio", "Advanced", "mcq",
         "When selecting the number of components in PCA, what criterion is typically used?",
         None, ["Retaining enough components to explain a target cumulative variance (e.g. 90-95%)", "Retaining only 1 component always", "Retaining all components without compression", "Choosing components with negative eigenvalues"],
         "Retaining enough components to explain a target cumulative variance (e.g. 90-95%)",
         "Cumulative explained variance guarantees signal preservation while compressing dimensions."),

        # Topic 24: Neural Networks & Backpropagation (ML-8)
        (3, 24, cos.get((3, "CO4"), 4), "Perceptron Architecture", "Beginner", "mcq",
         "What are the three fundamental components of an artificial neuron (Perceptron)?",
         None, ["Weighted inputs, bias addition, and a non-linear activation function", "Decision trees, bagging, and boosting", "Database tables, rows, and columns", "Clusters, centroids, and inertia"],
         "Weighted inputs, bias addition, and a non-linear activation function",
         "Neurons compute z = W*x + b followed by activation a = f(z)."),
        (3, 24, cos.get((3, "CO4"), 4), "ReLU Activation", "Intermediate", "mcq",
         "What is the mathematical definition of the Rectified Linear Unit (ReLU) activation function?",
         None, ["f(x) = max(0, x)", "f(x) = 1 / (1 + e^-x)", "f(x) = tanh(x)", "f(x) = x^2"], "f(x) = max(0, x)",
         "ReLU outputs 0 for negative inputs and x for positive inputs, avoiding gradient saturation."),
        (3, 24, cos.get((3, "CO4"), 4), "Backpropagation Chain Rule", "Intermediate", "mcq",
         "Which mathematical principle enables the Backpropagation algorithm to compute partial derivatives of loss with respect to layer weights?",
         None, ["The Calculus Chain Rule", "Euler's Totient Theorem", "Bayes' Theorem", "Relational Algebra"],
         "The Calculus Chain Rule",
         "Chain rule back-propagates error gradients through composite nested functions."),
        (3, 24, cos.get((3, "CO4"), 4), "Vanishing Gradients", "Advanced", "mcq",
         "Why does the 'Vanishing Gradient Problem' occur in deep networks using deep stacks of Sigmoid activations?",
         None, ["Sigmoid derivative peaks at 0.25, causing gradients to diminish exponentially toward earlier layers", "Weights become infinite during forward pass", "ReLU destroys positive activations", "Loss functions become negative"],
         "Sigmoid derivative peaks at 0.25, causing gradients to diminish exponentially toward earlier layers",
         "Successive multiplications of fractions < 0.25 diminish gradients to zero in deep networks.")
    ]

    for q in ai301_questions:
        insert_qb(*q)

    # -------------------------------------------------------------------------
    # COURSE 4: CS302 Database Management Systems (Topics 25 to 32)
    # -------------------------------------------------------------------------
    cs302_questions = [
        # Topic 25: Relational Data Model & Schemas (DB-1)
        (4, 25, cos.get((4, "CO1"), 1), "Relational Tuples", "Beginner", "mcq",
         "In relational database terminology, what corresponds to a single row in a table?",
         None, ["A Tuple", "An Attribute", "A Domain", "A Relation Schema"], "A Tuple",
         "A tuple represents an individual record (row) in a relation."),
        (4, 25, cos.get((4, "CO1"), 1), "Foreign Key Integrity", "Beginner", "mcq",
         "What constraint ensures that a Foreign Key value must match an existing Primary Key in the referenced relation or be NULL?",
         None, ["Referential Integrity", "Entity Integrity", "Domain Integrity", "Key Uniqueness"], "Referential Integrity",
         "Referential integrity guarantees relationships between tables remain consistent."),
        (4, 25, cos.get((4, "CO1"), 1), "Candidate Keys", "Intermediate", "mcq",
         "What is a 'Candidate Key'?",
         None, ["A minimal superkey capable of uniquely identifying every tuple in a relation", "Any attribute that contains numbers", "A key generated exclusively by foreign users", "A key that permits duplicate entries"],
         "A minimal superkey capable of uniquely identifying every tuple in a relation",
         "Candidate keys are minimal sets of attributes uniquely distinguishing tuples."),
        (4, 25, cos.get((4, "CO1"), 1), "Schema vs Instance", "Advanced", "mcq",
         "What is the difference between a Database Schema and a Database Instance?",
         None, ["Schema is the structural blueprint; instance is the collection of data at a given moment in time", "Schema contains rows; instance contains columns", "Schema changes with every query; instance is static", "They are identical terms"],
         "Schema is the structural blueprint; instance is the collection of data at a given moment in time",
         "Schema represents structural definition; instance represents the state of data."),

        # Topic 26: SQL DDL & Integrity Constraints (DB-2)
        (4, 26, cos.get((4, "CO1"), 1), "ALTER TABLE Command", "Beginner", "mcq",
         "Which SQL command is used to add a new column to an existing table?",
         None, ["ALTER TABLE students ADD COLUMN email VARCHAR(255);", "UPDATE TABLE students ADD email;", "MODIFY students INSERT email;", "INSERT INTO students COLUMN email;"],
         "ALTER TABLE students ADD COLUMN email VARCHAR(255);",
         "ALTER TABLE modifies existing table schemas."),
        (4, 26, cos.get((4, "CO2"), 2), "CHECK Constraints", "Intermediate", "mcq",
         "What is the role of a CHECK constraint in SQL DDL?",
         None, ["Validates that attribute values satisfy a specified boolean condition upon insert or update", "Checks spelling in text columns", "Verifies network connection to database", "Limits table size to 100 rows"],
         "Validates that attribute values satisfy a specified boolean condition upon insert or update",
         "CHECK constraints enforce domain-level business logic (e.g. CHECK (age >= 18))."),
        (4, 26, cos.get((4, "CO2"), 2), "CASCADE Deletion", "Intermediate", "mcq",
         "What does `ON DELETE CASCADE` specified on a Foreign Key mean?",
         None, ["When a parent row is deleted, matching child rows are automatically deleted as well", "Parent deletions are prevented if child rows exist", "Child rows are updated to NULL", "The table schema is dropped"],
         "When a parent row is deleted, matching child rows are automatically deleted as well",
         "ON DELETE CASCADE propagates parent deletions downward."),
        (4, 26, cos.get((4, "CO2"), 2), "DROP vs TRUNCATE", "Advanced", "mcq",
         "How does `TRUNCATE TABLE` differ from `DROP TABLE`?",
         None, ["TRUNCATE removes all rows while preserving the schema; DROP destroys both data and schema", "TRUNCATE deletes the schema; DROP deletes data", "TRUNCATE requires a WHERE clause", "They behave identically"],
         "TRUNCATE removes all rows while preserving the schema; DROP destroys both data and schema",
         "TRUNCATE empties the table structure; DROP drops the relation completely."),

        # Topic 27: SQL DML & Aggregation Queries (DB-3)
        (4, 27, cos.get((4, "CO2"), 2), "SELECT DISTINCT", "Beginner", "code_logic",
         "What does `SELECT COUNT(DISTINCT dept) FROM employees;` compute?",
         None, ["The number of unique departments in the table", "The total count of all employee rows", "The name of the highest department", "The average department size"],
         "The number of unique departments in the table",
         "DISTINCT eliminates duplicate department names before counting."),
        (4, 27, cos.get((4, "CO2"), 2), "GROUP BY Rule", "Intermediate", "mcq",
         "When using `GROUP BY dept`, which columns can appear in the SELECT list?",
         None, ["The grouped column (dept) and aggregate expressions (SUM, AVG, COUNT, etc.)", "Any column from the table regardless of aggregation", "Only columns with primary keys", "No columns are allowed"],
         "The grouped column (dept) and aggregate expressions (SUM, AVG, COUNT, etc.)",
         "Standard SQL requires non-aggregate SELECT columns to be part of the GROUP BY clause."),
        (4, 27, cos.get((4, "CO2"), 2), "WHERE vs HAVING", "Intermediate", "code_logic",
         "Which clause filters groups having `COUNT(*) > 5` after aggregation?",
         "SELECT dept, COUNT(*) FROM emp GROUP BY dept HAVING COUNT(*) > 5;", ["HAVING COUNT(*) > 5", "WHERE COUNT(*) > 5", "FILTER COUNT(*) > 5", "LIMIT 5"], "HAVING COUNT(*) > 5",
         "HAVING filters aggregated groups; WHERE filters row-level tuples prior to grouping."),
        (4, 27, cos.get((4, "CO2"), 2), "NULL Handling in Aggregates", "Advanced", "mcq",
         "How do SQL aggregate functions like `AVG(salary)` handle NULL values in the salary column?",
         None, ["NULL values are ignored and excluded from both numerator and denominator", "NULL is converted to 0", "The query returns NULL immediately", "An error is thrown"],
         "NULL values are ignored and excluded from both numerator and denominator",
         "Aggregate math functions (except COUNT(*)) disregard NULL entries."),

        # Topic 28: Complex SQL Joins & Subqueries (DB-4)
        (4, 28, cos.get((4, "CO2"), 2), "INNER JOIN", "Beginner", "mcq",
         "What does an `INNER JOIN` between orders and customers return?",
         None, ["Only orders that have matching customer IDs in the customers table", "All customers regardless of whether they placed orders", "All orders regardless of whether a customer exists", "Cartesian product of all rows"],
         "Only orders that have matching customer IDs in the customers table",
         "INNER JOIN matches tuples satisfying the ON join predicate in both relations."),
        (4, 28, cos.get((4, "CO2"), 2), "Correlated Subquery", "Intermediate", "mcq",
         "What characterizes a 'Correlated Subquery' in SQL?",
         None, ["The subquery references a column from the outer query and executes once for each outer row", "The subquery runs once independently before the outer query starts", "The subquery uses no tables", "The subquery is cached as a static table"],
         "The subquery references a column from the outer query and executes once for each outer row",
         "Correlated subqueries depend on the outer tuple context."),
        (4, 28, cos.get((4, "CO2"), 2), "FULL OUTER JOIN", "Intermediate", "mcq",
         "What is returned by a `FULL OUTER JOIN` between Table A and Table B?",
         None, ["All rows from A and B, filling in NULL for missing matches on either side", "Only rows that match in both tables", "Only rows from Table A", "Only rows where both tables have NULLs"],
         "All rows from A and B, filling in NULL for missing matches on either side",
         "FULL OUTER JOIN retains all tuples from both left and right relations."),
        (4, 28, cos.get((4, "CO2"), 2), "EXISTS Operator", "Advanced", "mcq",
         "How does `WHERE EXISTS (SELECT 1 FROM ...)` optimize execution compared to `IN`?",
         None, ["It terminates evaluation as soon as the first matching tuple is found (Boolean short-circuit)", "It loads all subquery rows into RAM memory", "It sorts the subquery results ascendingly", "It requires fewer indexes"],
         "It terminates evaluation as soon as the first matching tuple is found (Boolean short-circuit)",
         "EXISTS performs boolean verification without consuming all candidate records."),

        # Topic 29: Relational Algebra Operations (DB-5)
        (4, 29, cos.get((4, "CO1"), 1), "Selection Operator", "Beginner", "mcq",
         "In relational algebra, which Greek letter denotes the Selection operator (horizontal row filtering)?",
         None, ["Sigma (σ)", "Pi (π)", "Rho (ρ)", "Gamma (γ)"], "Sigma (σ)",
         "Sigma denotes selection σ_condition(R)."),
        (4, 29, cos.get((4, "CO1"), 1), "Projection Operator", "Beginner", "mcq",
         "Which relational algebra operator selects specific columns (vertical filtering) from a relation?",
         None, ["Projection (π)", "Selection (σ)", "Natural Join (⋈)", "Cartesian Product (×)"], "Projection (π)",
         "Pi denotes vertical column projection π_attributes(R)."),
        (4, 29, cos.get((4, "CO2"), 2), "Cartesian Product vs Natural Join", "Intermediate", "mcq",
         "Given relation R with 4 tuples and relation S with 3 tuples, how many tuples does R × S (Cartesian Product) have?",
         None, ["12 tuples", "7 tuples", "1 tuple", "4 tuples"], "12 tuples",
         "Cartesian product cardinality is |R| * |S| = 4 * 3 = 12 tuples."),
        (4, 29, cos.get((4, "CO2"), 2), "Set Difference Compatibility", "Advanced", "mcq",
         "What condition must relations R and S satisfy to permit Set Difference (R - S)?",
         None, ["Union Compatibility: Same number of attributes with identical pairwise domains", "Both relations must share primary keys", "R must have more rows than S", "No attributes can overlap"],
         "Union Compatibility: Same number of attributes with identical pairwise domains",
         "Set operations require union-compatible operand schemas."),

        # Topic 30: Functional Dependencies & 1NF-3NF (DB-6)
        (4, 30, cos.get((4, "CO3"), 3), "First Normal Form (1NF)", "Beginner", "mcq",
         "What is the foundational requirement of First Normal Form (1NF)?",
         None, ["All column values must be atomic (no repeating groups or multi-valued sets)", "Every table must have a foreign key", "No transitive dependencies can exist", "All tables must have at least 3 columns"],
         "All column values must be atomic (no repeating groups or multi-valued sets)",
         "1NF disallows composite or multi-valued repeating attributes."),
        (4, 30, cos.get((4, "CO3"), 3), "Second Normal Form (2NF)", "Intermediate", "mcq",
         "What anomaly does Second Normal Form (2NF) eliminate?",
         None, ["Partial Functional Dependencies (where non-prime attributes depend on a subset of a composite candidate key)", "Transitive dependencies", "Multi-valued dependencies", "Missing primary keys"],
         "Partial Functional Dependencies (where non-prime attributes depend on a subset of a composite candidate key)",
         "2NF requires full functional dependency on candidate keys."),
        (4, 30, cos.get((4, "CO3"), 3), "Third Normal Form (3NF)", "Intermediate", "mcq",
         "A relation is in 3NF if it is in 2NF and has no:",
         None, ["Transitive dependencies (non-prime attribute determining another non-prime attribute)", "Foreign keys", "Composite keys", "Atomic values"],
         "Transitive dependencies (non-prime attribute determining another non-prime attribute)",
         "3NF eliminates X -> Y where neither is a candidate key nor Y is prime."),
        (4, 30, cos.get((4, "CO3"), 3), "BCNF Condition", "Advanced", "mcq",
         "What strict requirement defines Boyce-Codd Normal Form (BCNF)?",
         None, ["For every non-trivial functional dependency X -> Y, X must be a superkey", "Every key must be a single column", "No deletions can occur", "Tables cannot be decomposed"],
         "For every non-trivial functional dependency X -> Y, X must be a superkey",
         "BCNF requires the determinant X to be a superkey for every dependency."),

        # Topic 31: Indexing & B-Tree Storage (DB-7)
        (4, 31, cos.get((4, "CO3"), 3), "B-Tree Search Efficiency", "Beginner", "mcq",
         "What is the average search time complexity in a balanced B-Tree index with N records?",
         None, ["O(log N)", "O(1)", "O(N)", "O(N log N)"], "O(log N)",
         "Balanced multi-way search trees maintain logarithmic depth O(log N)."),
        (4, 31, cos.get((4, "CO3"), 3), "Clustered vs Non-Clustered Index", "Intermediate", "mcq",
         "How many Clustered Indexes can exist on a single table?",
         None, ["Only 1, because the physical ordering of records on disk matches the clustered index", "As many as there are columns", "Exactly 2", "Zero"],
         "Only 1, because the physical ordering of records on disk matches the clustered index",
         "Physical rows on disk can only be stored in one sorted sequence."),
        (4, 31, cos.get((4, "CO3"), 3), "B+ Tree Leaf Nodes", "Intermediate", "mcq",
         "Why are B+ Trees preferred over standard B-Trees for database indexing?",
         None, ["Leaf nodes are linked in a sequential doubly-linked list, accelerating range queries", "They use no disk space", "They avoid balancing operations", "They store data only in RAM"],
         "Leaf nodes are linked in a sequential doubly-linked list, accelerating range queries",
         "Linked leaf nodes facilitate high-speed sequential range scans."),
        (4, 31, cos.get((4, "CO3"), 3), "Index Trade-offs", "Advanced", "mcq",
         "While secondary indexes speed up SELECT queries, what is their negative impact?",
         None, ["They increase storage overhead and slow down INSERT, UPDATE, and DELETE operations", "They reduce database security", "They cause table corruption on reads", "They disable primary keys"],
         "They increase storage overhead and slow down INSERT, UPDATE, and DELETE operations",
         "Every data modification requires updating corresponding index trees."),

        # Topic 32: Transactions, ACID & Concurrency (DB-8)
        (4, 32, cos.get((4, "CO4"), 4), "ACID Consistency", "Beginner", "mcq",
         "In ACID properties, what does 'Consistency' guarantee?",
         None, ["A transaction transitions the database from one valid state satisfying all schema rules to another", "Data is replicated across 3 servers", "Transactions execute in parallel", "Reads never block writes"],
         "A transaction transitions the database from one valid state satisfying all schema rules to another",
         "Consistency ensures database integrity constraints are preserved."),
        (4, 32, cos.get((4, "CO4"), 4), "Dirty Read Anomaly", "Intermediate", "mcq",
         "What is a 'Dirty Read' concurrency phenomenon?",
         None, ["A transaction reads uncommitted modifications made by another concurrent transaction", "Reading from an unplugged drive", "A transaction reads duplicate rows", "Reading deleted schemas"],
         "A transaction reads uncommitted modifications made by another concurrent transaction",
         "Dirty reads occur when transaction A reads dirty data from uncommitted transaction B."),
        (4, 32, cos.get((4, "CO4"), 4), "Isolation Levels", "Intermediate", "mcq",
         "Which SQL isolation level provides the highest protection against all concurrency anomalies (Dirty Read, Non-repeatable Read, Phantom Read)?",
         None, ["SERIALIZABLE", "READ COMMITTED", "REPEATABLE READ", "READ UNCOMMITTED"], "SERIALIZABLE",
         "SERIALIZABLE guarantees serial execution semantics without concurrency anomalies."),
        (4, 32, cos.get((4, "CO4"), 4), "Two-Phase Locking (2PL)", "Advanced", "mcq",
         "What rule governs Two-Phase Locking (2PL)?",
         None, ["Once a transaction releases a lock (shrinking phase), it cannot acquire any new locks", "All transactions must lock every table at startup", "Locks are held for exactly 2 seconds", "Transactions run in pairs"],
         "Once a transaction releases a lock (shrinking phase), it cannot acquire any new locks",
         "2PL requires a growing phase followed by a shrinking phase to guarantee serializability.")
    ]

    for q in cs302_questions:
        insert_qb(*q)

    conn.commit()

    # Verify counts
    print("\n=== VERIFIED QUESTION COUNTS PER COURSE ===")
    for row in c.execute("SELECT c.id, c.code, c.title, count(qb.id) FROM courses c LEFT JOIN question_bank qb ON qb.course_id = c.id GROUP BY c.id").fetchall():
        print(f"Course {row[0]} ({row[1]}): {row[3]} questions in QuestionBank")

    print("\n=== VERIFIED QUESTION COUNTS PER TOPIC ===")
    for row in c.execute("SELECT t.course_id, t.id, t.order_index, t.title, count(qb.id) FROM topics t LEFT JOIN question_bank qb ON qb.topic_id = t.id GROUP BY t.id ORDER BY t.course_id, t.order_index").fetchall():
        print(f"Course {row[0]} Topic {row[2]} (id={row[1]}): {row[4]} questions")

    # =========================================================================
    # 3. NORMALIZE LEARNING PATH STATUSES FOR ALL COURSES
    # =========================================================================
    print("\nNormalizing Learning Path items to standard TopicPathStatus...")
    import sys
    sys.path.insert(0, 'backend')
    from database import SessionLocal
    from progress_engine import generate_adapted_learning_path

    db = SessionLocal()
    try:
        for cid in [1, 2, 3, 4]:
            generate_adapted_learning_path(db, user_id=1, course_id=cid, reason="Systematic baseline initialization")
            print(f"Regenerated active learning path for user 1 in course {cid}")
    finally:
        db.close()

    conn.close()
    print("Done! Prerequisites, dynamic questions, and learning paths successfully seeded.")

if __name__ == "__main__":
    setup_prerequisites_and_questions()
