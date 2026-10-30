import json
import sqlite3

def seed_questions():
    conn = sqlite3.connect("obe_learning.db")
    c = conn.cursor()

    # Diagnostic Questions for CS101 (course_id = 1), AI301 (course_id = 3), CS302 (course_id = 4)
    diag_data = [
        # CS101 Python
        (1, 9, "Which of the following data types in Python is immutable?", None, "mcq", "Variables & Types",
         json.dumps(["Tuple", "List", "Dictionary", "Set"]), "Tuple", "Tuples cannot be altered after creation."),
        (1, 10, "What is the output of: `if 5 > 3 and 2 < 1: print('Yes') else: print('No')`?", "if 5 > 3 and 2 < 1:\n    print('Yes')\nelse:\n    print('No')", "code_logic", "Conditionals",
         json.dumps(["No", "Yes", "SyntaxError", "None"]), "No", "Because 2 < 1 is False, the 'and' evaluates to False."),
        (1, 11, "What does `range(1, 5)` generate when converted to a list?", None, "mcq", "Loops",
         json.dumps(["[1, 2, 3, 4]", "[1, 2, 3, 4, 5]", "[0, 1, 2, 3, 4]", "[2, 3, 4, 5]"]), "[1, 2, 3, 4]", "range stop parameter is exclusive."),
        (1, 14, "Which keyword in Python is used to define a function?", None, "mcq", "Functions",
         json.dumps(["def", "function", "func", "define"]), "def", "'def' initiates a function definition."),
        (1, 16, "What is the first parameter typically passed to instance methods in Python classes?", None, "mcq", "OOP",
         json.dumps(["self", "this", "cls", "instance"]), "self", "'self' binds the instance to the method call."),

        # AI301 Machine Learning
        (3, 17, "What is the primary objective of Supervised Learning?", None, "mcq", "Statistical Learning",
         json.dumps(["Learn a mapping function from input features to labeled targets", "Find hidden clusters in unlabeled datasets", "Maximize reward via agent trial and error", "Compress data without loss"]), "Learn a mapping function from input features to labeled targets", "Supervised learning relies on ground-truth labeled training pairs."),
        (3, 18, "In Ordinary Least Squares Linear Regression, what loss metric is minimized?", None, "mcq", "Regression",
         json.dumps(["Mean Squared Error (MSE)", "Cross-Entropy Loss", "Hinge Loss", "Kullback-Leibler Divergence"]), "Mean Squared Error (MSE)", "OLS minimizes the sum of squared differences between predictions and actual values."),
        (3, 19, "Which activation function is standardly used to produce binary probability outputs in Logistic Regression?", None, "mcq", "Classification",
         json.dumps(["Sigmoid (Logistic) function", "ReLU", "Step function", "Tanh"]), "Sigmoid (Logistic) function", "The sigmoid function squashes any real value into the (0, 1) probability range."),
        (3, 21, "Which metric is the harmonic mean of Precision and Recall?", None, "mcq", "Validation",
         json.dumps(["F1-Score", "ROC-AUC", "Accuracy", "Mean Absolute Error"]), "F1-Score", "F1 score balances precision and recall symmetrically."),
        (3, 22, "What type of machine learning algorithm is K-Means?", None, "mcq", "Clustering",
         json.dumps(["Unsupervised clustering", "Supervised classification", "Reinforcement learning", "Semi-supervised regression"]), "Unsupervised clustering", "K-Means groups unlabeled observations into k cohesive clusters."),

        # CS302 Database Management Systems
        (4, 25, "In a relational schema, what property must every Primary Key uphold?", None, "mcq", "Relational Model",
         json.dumps(["Uniqueness and non-nullability (Entity Integrity)", "Can contain duplicates", "Must reference another table", "Optional value allowed"]), "Uniqueness and non-nullability (Entity Integrity)", "Entity integrity requires primary keys to be strictly unique and not null."),
        (4, 26, "Which SQL command is classified as Data Definition Language (DDL)?", None, "mcq", "DDL",
         json.dumps(["CREATE TABLE", "SELECT", "UPDATE", "INSERT INTO"]), "CREATE TABLE", "CREATE TABLE defines table structure and constraints."),
        (4, 27, "Which SQL clause is used to filter aggregated group records produced by GROUP BY?", None, "mcq", "Aggregation",
         json.dumps(["HAVING", "WHERE", "FILTER", "ORDER BY"]), "HAVING", "WHERE filters row-level records before grouping; HAVING filters groups after aggregation."),
        (4, 28, "Which JOIN returns all rows from the left table and matched rows from the right table?", None, "mcq", "Joins",
         json.dumps(["LEFT OUTER JOIN", "INNER JOIN", "CROSS JOIN", "RIGHT OUTER JOIN"]), "LEFT OUTER JOIN", "LEFT JOIN preserves all records from the left relation."),
        (4, 32, "In ACID transaction properties, what does 'A' stand for?", None, "mcq", "Transactions",
         json.dumps(["Atomicity", "Availability", "Authentication", "Accuracy"]), "Atomicity", "Atomicity guarantees that transactions either execute entirely or abort with zero partial side effects.")
    ]

    for cid, tid, qtext, snippet, qtype, sub, opts, ans, exp in diag_data:
        exists = c.execute("SELECT id FROM diagnostic_questions WHERE course_id = ? AND question_text = ?", (cid, qtext)).fetchone()
        if not exists:
            c.execute("""
                INSERT INTO diagnostic_questions (course_id, topic_id, question_text, code_snippet, question_type, sub_concept, options_json, correct_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cid, tid, qtext, snippet, qtype, sub, opts, ans, exp))

    # Question Bank for CS101, AI301, CS302
    qb_data = [
        # CS101
        (1, 9, "Variables & Types", "Beginner", "mcq", "What is the result of `type(3.14)` in Python?", None,
         json.dumps(["<class 'float'>", "<class 'int'>", "<class 'double'>", "<class 'number'>"]), "<class 'float'>", "Python denotes decimal numbers as float."),
        (1, 9, "Type Casting", "Intermediate", "code_logic", "What is the result of `str(10) + str(20)`?", "str(10) + str(20)",
         json.dumps(["'1020'", "30", "'30'", "TypeError"]), "'1020'", "String concatenation joins the string literals."),
        (1, 10, "Branching Logic", "Beginner", "mcq", "Which Python keyword handles multiple conditional branches?", None,
         json.dumps(["elif", "else if", "elseif", "case"]), "elif", "Python uses elif for secondary conditional branches."),
        (1, 11, "Iterators", "Beginner", "mcq", "Which keyword terminates a loop immediately?", None,
         json.dumps(["break", "continue", "pass", "exit"]), "break", "break exits the nearest enclosing loop."),
        (1, 12, "Lists & Slicing", "Intermediate", "code_logic", "Given `nums = [10, 20, 30, 40, 50]`, what does `nums[1:4]` return?", "nums = [10, 20, 30, 40, 50]\nnums[1:4]",
         json.dumps(["[20, 30, 40]", "[10, 20, 30]", "[20, 30, 40, 50]", "[10, 20, 30, 40]"]), "[20, 30, 40]", "Slicing is start-inclusive and stop-exclusive."),
        (1, 13, "Hash Maps & Dicts", "Intermediate", "mcq", "What is the average time complexity of a key lookup in a Python dictionary?", None,
         json.dumps(["O(1)", "O(n)", "O(log n)", "O(n^2)"]), "O(1)", "Python dictionaries are implemented as hash tables with O(1) average lookup."),
        (1, 14, "Functions & Scope", "Intermediate", "code_logic", "What does this function return: `def add(a, b=5): return a + b; print(add(3))`?", "def add(a, b=5):\n    return a + b\nprint(add(3))",
         json.dumps(["8", "3", "5", "TypeError"]), "8", "Default argument b=5 is used when only a=3 is provided."),
        (1, 15, "Exception Handling", "Advanced", "mcq", "Which block in a try-except statement executes regardless of whether an exception occurred?", None,
         json.dumps(["finally", "else", "except", "catch"]), "finally", "finally always executes cleanup logic."),
        (1, 16, "OOP & Classes", "Advanced", "code_logic", "What is `__init__` in a Python class?", None,
         json.dumps(["Constructor method called when a new instance is created", "Destructor method", "Static method", "Private method"]), "Constructor method called when a new instance is created", "__init__ initializes instance attributes upon object instantiation."),

        # AI301
        (3, 17, "Feature Scaling", "Beginner", "mcq", "Why is feature standardization (e.g. Z-score scaling) important in gradient descent based models?", None,
         json.dumps(["It prevents features with large numeric scales from dominating gradients", "It guarantees 100% accuracy", "It reduces the number of features", "It turns non-linear data into linear data"]), "It prevents features with large numeric scales from dominating gradients", "Features on comparable scales allow gradient descent to converge smoothly."),
        (3, 18, "Linear Regression", "Beginner", "mcq", "What does the slope coefficient in simple linear regression y = mx + b represent?", None,
         json.dumps(["The expected change in y for a one-unit increase in x", "The value of y when x is 0", "The error variance", "The correlation coefficient squared"]), "The expected change in y for a one-unit increase in x", "The slope indicates marginal rate of change."),
        (3, 19, "Classification Metrics", "Intermediate", "mcq", "What is the probability output range of a standard Sigmoid activation function?", None,
         json.dumps(["0 to 1", "-1 to 1", "0 to infinity", "-infinity to +infinity"]), "0 to 1", "Sigmoid squashes input into the valid probability range [0, 1]."),
        (3, 20, "Decision Trees", "Intermediate", "mcq", "What measure of node impurity is commonly calculated to choose optimal decision tree splits?", None,
         json.dumps(["Gini Impurity or Information Gain (Entropy)", "Mean Squared Error", "Cosine Similarity", "Euclidean Distance"]), "Gini Impurity or Information Gain (Entropy)", "Decision tree algorithms choose splits that maximize information gain / minimize impurity."),
        (3, 21, "Overfitting & Regularization", "Intermediate", "mcq", "Which technique helps prevent a model from overfitting to training data?", None,
         json.dumps(["L2 Regularization (Ridge) and Dropout", "Training for infinitely many epochs", "Removing validation sets", "Increasing model parameters indefinitely"]), "L2 Regularization (Ridge) and Dropout", "Regularization penalizes overly complex weights to enhance generalizability."),
        (3, 22, "K-Means Clustering", "Intermediate", "mcq", "How is the optimal number of clusters k frequently selected in K-Means?", None,
         json.dumps(["Elbow method using sum of squared errors (inertia)", "P-value testing", "Gradient descent step size", "Confusion matrix"]), "Elbow method using sum of squared errors (inertia)", "The elbow method plots inertia vs k and identifies diminishing returns."),
        (3, 23, "Dimensionality Reduction", "Advanced", "mcq", "What is the mathematical goal of Principal Component Analysis (PCA)?", None,
         json.dumps(["Find orthogonal axes of maximal variance in the feature space", "Classify data points into discrete labels", "Compute cluster centroids", "Fit linear boundary lines"]), "Find orthogonal axes of maximal variance in the feature space", "PCA projects data onto principal components that retain maximum variance."),
        (3, 24, "Deep Learning & Backprop", "Advanced", "mcq", "What algorithm computes partial derivatives of the loss with respect to each weight in neural networks?", None,
         json.dumps(["Backpropagation via the Chain Rule of Calculus", "K-Nearest Neighbors", "Markov Decision Process", "Support Vector Machines"]), "Backpropagation via the Chain Rule of Calculus", "Backpropagation computes loss gradients backwards through layers using chain rule."),

        # CS302
        (4, 25, "Relational Model", "Beginner", "mcq", "What constraint ensures that a foreign key matches a valid primary key in the parent table?", None,
         json.dumps(["Referential Integrity", "Entity Integrity", "Domain Integrity", "User-defined Integrity"]), "Referential Integrity", "Referential integrity maintains consistent relationships across relations."),
        (4, 26, "DDL Commands", "Beginner", "mcq", "Which statement alters the structure of an existing table by adding a column?", None,
         json.dumps(["ALTER TABLE table_name ADD column_name datatype;", "UPDATE table_name ADD column_name;", "MODIFY TABLE table_name INSERT column_name;", "CHANGE table_name column_name;"]), "ALTER TABLE table_name ADD column_name datatype;", "ALTER TABLE modifies table definitions."),
        (4, 27, "SQL Aggregation", "Intermediate", "mcq", "What aggregate function calculates the total number of non-null rows matching a criteria?", None,
         json.dumps(["COUNT()", "SUM()", "AVG()", "TOTAL()"]), "COUNT()", "COUNT() tallies matching rows."),
        (4, 28, "Complex Joins", "Intermediate", "mcq", "What does an INNER JOIN between Table A and Table B produce?", None,
         json.dumps(["Only records with matching keys in both Table A and Table B", "All records from Table A regardless of match", "Cartesian product of all rows", "All records from Table B regardless of match"]), "Only records with matching keys in both Table A and Table B", "INNER JOIN filters strictly for overlapping matches."),
        (4, 29, "Relational Algebra", "Intermediate", "mcq", "Which relational algebra operator selects a subset of rows that satisfy a given predicate?", None,
         json.dumps(["Sigma (Selection σ)", "Pi (Projection π)", "Rho (Rename ρ)", "Join (⨝)"]), "Sigma (Selection σ)", "Sigma represents horizontal row selection."),
        (4, 30, "Database Normalization", "Advanced", "mcq", "A relation is in First Normal Form (1NF) if and only if:", None,
         json.dumps(["All attribute values are atomic and there are no repeating groups", "Every non-key attribute is fully functionally dependent on the primary key", "There are no transitive dependencies", "All determinants are candidate keys"]), "All attribute values are atomic and there are no repeating groups", "1NF enforces atomicity of attribute domains."),
        (4, 31, "Indexing & B-Trees", "Advanced", "mcq", "Why are B+ Trees preferred over binary search trees for database index storage on disk?", None,
         json.dumps(["High branching factor (fan-out) minimizes disk I/O operations", "They require zero disk space", "They only store integers", "They are strictly linear arrays"]), "High branching factor (fan-out) minimizes disk I/O operations", "High fan-out leads to shallow trees requiring few disk block reads."),
        (4, 32, "Transactions & ACID", "Advanced", "mcq", "Which ACID property ensures that committed transactions survive subsequent system crashes?", None,
         json.dumps(["Durability", "Isolation", "Atomicity", "Consistency"]), "Durability", "Durability ensures committed data is safely persisted via logs.")
    ]

    for cid, tid, sub, diff, qtype, qtext, snippet, opts, ans, exp in qb_data:
        exists = c.execute("SELECT id FROM question_bank WHERE topic_id = ? AND question_text = ?", (tid, qtext)).fetchone()
        if not exists:
            c.execute("""
                INSERT INTO question_bank (course_id, topic_id, sub_concept, difficulty, question_type, question_text, code_snippet, options_json, correct_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cid, tid, sub, diff, qtype, qtext, snippet, opts, ans, exp))

    conn.commit()
    print("Seeded diagnostic questions and question bank successfully!")
    print("Diagnostic count:", c.execute("SELECT course_id, count(*) FROM diagnostic_questions GROUP BY course_id").fetchall())
    print("QuestionBank count:", c.execute("SELECT course_id, count(*) FROM question_bank GROUP BY course_id").fetchall())
    conn.close()

if __name__ == "__main__":
    seed_questions()
