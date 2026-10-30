import sys
import json
import sqlite3

def unlock_and_seed_courses():
    conn = sqlite3.connect("obe_learning.db")
    c = conn.cursor()

    # 1. Update all courses to is_active = 1
    c.execute("UPDATE courses SET is_active = 1")
    conn.commit()
    print("Updated all courses to is_active = 1")

    # Fetch existing courses
    courses = c.execute("SELECT id, code, title FROM courses").fetchall()
    c_dict = {code: cid for cid, code, title in courses}
    print("Existing courses:", c_dict)

    # 2. Add Outcomes for CS101, AI301, CS302 if not present
    outcomes_to_seed = [
        # CS101 Python
        ("CS101", "CO1", "Understand fundamental Python programming syntax & procedural logic", 75.0),
        ("CS101", "CO2", "Apply conditional constructs, iteration, and algorithmic patterns", 70.0),
        ("CS101", "CO3", "Implement functions, modular code design, and data structures in Python", 70.0),
        ("CS101", "CO4", "Develop programs to solve real-world computational challenges", 70.0),

        # AI301 ML
        ("AI301", "CO1", "Understand foundations of statistical learning, features & loss functions", 75.0),
        ("AI301", "CO2", "Implement supervised learning models (Regression, Classifiers, Trees)", 70.0),
        ("AI301", "CO3", "Apply unsupervised clustering, dimensionality reduction & PCA", 70.0),
        ("AI301", "CO4", "Evaluate neural architectures and continuous model optimization", 70.0),

        # CS302 DBMS
        ("CS302", "CO1", "Understand relational database architectures, relational algebra & schemas", 75.0),
        ("CS302", "CO2", "Construct complex SQL queries, views, subqueries, and join operations", 70.0),
        ("CS302", "CO3", "Apply normalization theories (1NF through BCNF) and indexing strategies", 70.0),
        ("CS302", "CO4", "Analyze transaction concurrency, ACID properties & failure recovery", 70.0),
    ]

    co_map = {} # (course_code, co_code) -> co_id
    # First record existing outcomes
    for cid, code, desc in c.execute("SELECT course_id, code, description FROM course_outcomes").fetchall():
        # find course code
        for ccode, c_id in c_dict.items():
            if c_id == cid:
                co_map[(ccode, code)] = cid

    for ccode, code, desc, target in outcomes_to_seed:
        cid = c_dict.get(ccode)
        if not cid:
            continue
        existing = c.execute("SELECT id FROM course_outcomes WHERE course_id = ? AND code = ?", (cid, code)).fetchone()
        if not existing:
            c.execute("INSERT INTO course_outcomes (course_id, code, description, target_attainment_pct) VALUES (?, ?, ?, ?)",
                      (cid, code, desc, target))
            co_map[(ccode, code)] = c.lastrowid
        else:
            co_map[(ccode, code)] = existing[0]
    conn.commit()

    # 3. Seed Topics for CS101, AI301, CS302
    topics_to_seed = {
        "CS101": [
            ("PY-1", "Variables, Data Types & Basic I/O", 1, "Variables, dynamic typing, primitive data types, input/output operations.", "Understand Python variables, type casting, and standard I/O mechanics.", "Beginner", 40, ["CO1"]),
            ("PY-2", "Conditional Statements & Branching", 2, "Boolean logic, if-elif-else branching, and conditional control flows.", "Formulate multi-way branch logic to direct program execution.", "Beginner", 45, ["CO1", "CO2"]),
            ("PY-3", "Loops & Iterative Control", 3, "While loops, for-in iterators, range generator, and break/continue statements.", "Implement algorithmic iteration and state accumulation using loops.", "Beginner", 45, ["CO2"]),
            ("PY-4", "Python Lists & Tuples", 4, "Indexed sequences, mutability, slicing, list comprehensions, and tuple unpacking.", "Manipulate ordered sequence collections and optimize array operations.", "Beginner", 40, ["CO1", "CO2"]),
            ("PY-5", "Dictionaries, Sets & Hash Collections", 5, "Key-value mapping, hashing mechanics, set operations, and membership tests.", "Apply hash tables and unique sets for O(1) key lookups.", "Intermediate", 45, ["CO2", "CO3"]),
            ("PY-6", "Functions, Scope & Parameter Passing", 6, "Function definition, positional/keyword args, return values, and local/global scope.", "Design modular, reusable functions and manage variable lifecycles.", "Intermediate", 50, ["CO3"]),
            ("PY-7", "File I/O & Exception Handling", 7, "File context managers, text streams, try-except-finally blocks, and error handling.", "Read/write persistent file data safely with robust exception handling.", "Intermediate", 45, ["CO3", "CO4"]),
            ("PY-8", "Object-Oriented Programming in Python", 8, "Classes, instances, __init__ constructor, encapsulation, and inheritance.", "Construct object-oriented models representing domain entities.", "Intermediate", 60, ["CO4"])
        ],
        "AI301": [
            ("ML-1", "Statistical Learning & Feature Engineering", 1, "Features, targets, train/test splits, data scaling, and loss functions.", "Understand foundational ML workflows and data representation matrices.", "Beginner", 45, ["CO1"]),
            ("ML-2", "Linear & Polynomial Regression", 2, "Ordinary least squares, gradient descent, cost minimization, and regression curves.", "Implement linear and polynomial models for continuous numerical prediction.", "Beginner", 50, ["CO1", "CO2"]),
            ("ML-3", "Logistic Regression & Classification", 3, "Sigmoid function, log-loss, decision boundaries, and binary classification.", "Formulate classification models and interpret probabilistic outcomes.", "Intermediate", 45, ["CO2"]),
            ("ML-4", "Decision Trees & Random Forests", 4, "Information gain, Gini impurity, entropy, decision trees, and bagging ensembles.", "Build decision trees and ensemble classifiers for non-linear decision spaces.", "Intermediate", 50, ["CO2"]),
            ("ML-5", "Model Evaluation & Validation", 5, "Confusion matrix, precision, recall, F1-score, ROC-AUC, and k-fold cross-validation.", "Evaluate machine learning performance systematically across validation splits.", "Intermediate", 40, ["CO2", "CO4"]),
            ("ML-6", "Clustering & K-Means", 6, "Unsupervised grouping, centroid assignment, inertia, and elbow method evaluation.", "Cluster unlabeled multi-dimensional data into cohesive semantic clusters.", "Intermediate", 45, ["CO3"]),
            ("ML-7", "Dimensionality Reduction & PCA", 7, "Principal Component Analysis, covariance matrices, eigenvectors, and variance retention.", "Reduce feature dimensionality while preserving critical variance signal.", "Intermediate", 45, ["CO3"]),
            ("ML-8", "Neural Networks & Backpropagation", 8, "Perceptrons, multi-layer networks, activation functions, forward pass, and backprop.", "Trace forward propagation and gradient updates in neural architectures.", "Advanced", 60, ["CO4"])
        ],
        "CS302": [
            ("DB-1", "Relational Data Model & Schemas", 1, "Tables, rows, attributes, primary keys, foreign keys, and relational integrity.", "Understand relational architecture, entity-relationship models, and constraints.", "Beginner", 40, ["CO1"]),
            ("DB-2", "SQL DDL & Integrity Constraints", 2, "CREATE, ALTER, DROP, primary/foreign key definitions, and check constraints.", "Write DDL commands to establish normalized relational schemas.", "Beginner", 40, ["CO1", "CO2"]),
            ("DB-3", "SQL DML & Aggregation Queries", 3, "SELECT, INSERT, UPDATE, DELETE, GROUP BY, HAVING, and aggregate math functions.", "Query and aggregate relational records across large datasets.", "Beginner", 45, ["CO2"]),
            ("DB-4", "Complex SQL Joins & Subqueries", 4, "INNER, LEFT, RIGHT, FULL OUTER joins, correlated subqueries, and table aliases.", "Execute multi-table joins and nested queries for data synthesis.", "Intermediate", 50, ["CO2"]),
            ("DB-5", "Relational Algebra Operations", 5, "Selection, projection, Cartesian product, set union/difference, and natural join.", "Express computational query requirements using formal relational algebra.", "Intermediate", 45, ["CO1", "CO2"]),
            ("DB-6", "Functional Dependencies & 1NF-3NF", 6, "Anomalies, functional dependencies, Armstrong axioms, 1NF, 2NF, and 3NF.", "Decompose relation tables to eliminate insertion and deletion anomalies.", "Intermediate", 55, ["CO3"]),
            ("DB-7", "Indexing & B-Tree Storage", 7, "Dense/sparse indexes, primary vs secondary indexes, B-Trees, and query cost.", "Select and configure indexing strategies to minimize disk I/O latency.", "Intermediate", 50, ["CO3"]),
            ("DB-8", "Transactions, ACID & Concurrency", 8, "Atomicity, Consistency, Isolation, Durability, write-ahead logs, and two-phase locking.", "Analyze transaction schedules and manage concurrency anomalies.", "Advanced", 60, ["CO4"])
        ]
    }

    for ccode, topic_list in topics_to_seed.items():
        cid = c_dict[ccode]
        for tcode, title, order, desc, obj, diff, mins, mapped_cos in topic_list:
            existing = c.execute("SELECT id FROM topics WHERE course_id = ? AND code = ?", (cid, tcode)).fetchone()
            if not existing:
                c.execute("""
                    INSERT INTO topics (course_id, code, title, order_index, description, learning_objective, difficulty, est_minutes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (cid, tcode, title, order, desc, obj, diff, mins))
                tid = c.lastrowid
            else:
                tid = existing[0]

            # Map to COs
            for co_code in mapped_cos:
                co_id_row = c.execute("SELECT id FROM course_outcomes WHERE course_id = ? AND code = ?", (cid, co_code)).fetchone()
                if co_id_row:
                    co_id = co_id_row[0]
                    mapping_exist = c.execute("SELECT id FROM topic_outcome_mappings WHERE topic_id = ? AND outcome_id = ?", (tid, co_id)).fetchone()
                    if not mapping_exist:
                        c.execute("INSERT INTO topic_outcome_mappings (topic_id, outcome_id, weight) VALUES (?, ?, 1.0)", (tid, co_id))

            # Initialize baseline mastery score if not present
            for uid in [1, 2, 3]:
                m_exist = c.execute("SELECT id FROM mastery_scores WHERE user_id = ? AND topic_id = ?", (uid, tid)).fetchone()
                if not m_exist:
                    # Give realistic starting mastery
                    base_m = 40.0 if order <= 2 else (25.0 if order <= 4 else 0.0)
                    c.execute("""
                        INSERT INTO mastery_scores (user_id, topic_id, overall_mastery, diagnostic_score, practice_score, quiz_score, completion_score, classification, updated_at)
                        VALUES (?, ?, ?, ?, 0.0, 0.0, 0.0, 'Needs Improvement', datetime('now'))
                    """, (uid, tid, base_m, base_m))

    conn.commit()

    # 4. Generate Learning Paths for all courses for user 1
    for cid, code, title in courses:
        path_exist = c.execute("SELECT id FROM learning_paths WHERE user_id = 1 AND course_id = ? AND status = 'ACTIVE'", (cid,)).fetchone()
        if not path_exist:
            c.execute("""
                INSERT INTO learning_paths (user_id, course_id, status, adaptation_reason, generated_at, updated_at)
                VALUES (?, ?, 'ACTIVE', 'Curriculum trajectory initialized for all enrolled courses.', datetime('now'), datetime('now'))
            """, (1, cid))
            lid = c.lastrowid

            # Add items
            topic_rows = c.execute("SELECT id, order_index, title FROM topics WHERE course_id = ? ORDER BY order_index", (cid,)).fetchall()
            for tid, ord_idx, ttitle in topic_rows:
                status = "IN_PROGRESS" if ord_idx == 1 else "NOT_STARTED"
                c.execute("""
                    INSERT INTO learning_path_items (learning_path_id, topic_id, sequence_order, status, recommendation_reason, is_remedial)
                    VALUES (?, ?, ?, ?, 'Standard curriculum milestone in personalized sequence.', 0)
                """, (lid, tid, ord_idx, status))

    conn.commit()
    print("Successfully seeded topics, outcomes, and active paths for all courses!")

    # Summary
    res = c.execute("SELECT c.id, c.code, c.title, c.is_active, count(t.id) FROM courses c LEFT JOIN topics t ON t.course_id = c.id GROUP BY c.id").fetchall()
    print("Course summary now:", res)
    conn.close()

if __name__ == "__main__":
    unlock_and_seed_courses()
