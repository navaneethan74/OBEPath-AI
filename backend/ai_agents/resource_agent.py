"""
Resource Retrieval Agent
Provides verified, outcome-aligned educational resources across all 4 core OBE courses.
"""

import urllib.parse
from typing import List, Dict, Any

class ResourceAgent:
    """
    Resource Retrieval Agent:
    Retrieves high-quality learning resources aligned with Course Outcomes
    and targeted topic mastery needs for all 4 OBE courses:
    - CS101: Python Programming
    - CS201: Data Structures
    - AI301: Machine Learning Fundamentals
    - CS302: Database Management Systems
    Categorized into Reading Material (Documentation), Watch Video (Video), and Practice.
    """

    RESOURCES_CATALOG: Dict[str, List[Dict[str, Any]]] = {
        'Variables, Data Types & Basic I/O': [
            {
                "title": 'Python 3 Official Tutorial: Numbers, Strings & Input/Output',
                "website_name": 'Python Official Docs',
                "url": 'https://docs.python.org/3/tutorial/introduction.html',
                "description": 'Official documentation covering numeric types, string operations, variables, and console I/O.',
                "difficulty": 'Beginner',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Python Strings: Working with Textual Data',
                "website_name": 'Corey Schafer (YouTube)',
                "url": 'https://www.youtube.com/watch?v=k9TUPpGqYTo',
                "description": 'Comprehensive video guide to Python string methods, formatting, slicing, and print operations.',
                "difficulty": 'Beginner',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Python Variables & Data Types Exercises',
                "website_name": 'W3Schools',
                "url": 'https://www.w3schools.com/python/exercise.asp?filename=exercise_variables1',
                "description": 'Interactive browser exercises testing variable assignment, casting, and data type recognition.',
                "difficulty": 'Beginner',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Conditional Statements & Branching': [
            {
                "title": 'Control Flow: If, Elif, and Boolean Expressions',
                "website_name": 'Python Official Docs',
                "url": 'https://docs.python.org/3/tutorial/controlflow.html#if-statements',
                "description": 'Official guide on branching logic, comparison operators, and truth-value testing.',
                "difficulty": 'Beginner',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Conditionals and Booleans: If, Else, and Elif Statements',
                "website_name": 'Corey Schafer (YouTube)',
                "url": 'https://www.youtube.com/watch?v=DZwmZ8Usvnk',
                "description": 'Video walkthrough of boolean operators, comparisons, object identity vs equality, and short-circuit evaluation.',
                "difficulty": 'Beginner',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Python If...Else Interactive Exercises',
                "website_name": 'W3Schools',
                "url": 'https://www.w3schools.com/python/exercise.asp?filename=exercise_conditions1',
                "description": 'Interactive coding challenges applying conditional branching and logical operators.',
                "difficulty": 'Beginner',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Loops & Iterative Control': [
            {
                "title": 'For Statements, range() & While Loops',
                "website_name": 'Python Official Docs',
                "url": 'https://docs.python.org/3/tutorial/controlflow.html#for-statements',
                "description": 'Official reference on sequence iteration, range generator functions, break, and continue.',
                "difficulty": 'Beginner',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Loops and Iterations: For and While Loops',
                "website_name": 'Corey Schafer (YouTube)',
                "url": 'https://www.youtube.com/watch?v=6iF8Xb7Z3wQ',
                "description": 'Visual explanation of loop flow control, break, continue, range indices, and nested loops.',
                "difficulty": 'Beginner',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Python While Loops Exercises',
                "website_name": 'W3Schools',
                "url": 'https://www.w3schools.com/python/exercise.asp?filename=exercise_while_loops1',
                "description": 'Interactive practice writing while loops, condition guards, and counter variables.',
                "difficulty": 'Beginner',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Python Lists & Tuples': [
            {
                "title": 'Data Structures: List Methods, Slicing & Tuples',
                "website_name": 'Python Official Docs',
                "url": 'https://docs.python.org/3/tutorial/datastructures.html',
                "description": 'Official documentation covering append, pop, sort, list comprehensions, and immutable tuples.',
                "difficulty": 'Beginner',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Lists, Tuples, and Sets Tutorial',
                "website_name": 'Corey Schafer (YouTube)',
                "url": 'https://www.youtube.com/watch?v=W8KRzm-HUcc',
                "description": 'Detailed video walkthrough of list slicing, mutability, sorting, and tuple immutability.',
                "difficulty": 'Beginner',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Python Lists Interactive Exercises',
                "website_name": 'W3Schools',
                "url": 'https://www.w3schools.com/python/exercise.asp?filename=exercise_lists1',
                "description": 'Hands-on coding exercises practicing list indexing, item modification, and built-in sequence functions.',
                "difficulty": 'Beginner',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Dictionaries, Sets & Hash Collections': [
            {
                "title": 'Dictionaries and Sets in Python',
                "website_name": 'Python Official Docs',
                "url": 'https://docs.python.org/3/tutorial/datastructures.html#dictionaries',
                "description": 'Official documentation on dictionary keys, values, hash lookups, and set algebra.',
                "difficulty": 'Intermediate',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Dictionaries: Working with Key-Value Pairs',
                "website_name": 'Corey Schafer (YouTube)',
                "url": 'https://www.youtube.com/watch?v=daefaLgNkw0',
                "description": 'Video tutorial covering dictionary creation, key lookup, get() fallbacks, updates, and key deletion.',
                "difficulty": 'Intermediate',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Python Dictionaries Exercises',
                "website_name": 'W3Schools',
                "url": 'https://www.w3schools.com/python/exercise.asp?filename=exercise_dictionaries1',
                "description": 'Interactive exercises for dictionary manipulation, keys iteration, and set operations.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Functions, Scope & Parameter Passing': [
            {
                "title": 'Defining Functions, Default Arguments & Scope',
                "website_name": 'Python Official Docs',
                "url": 'https://docs.python.org/3/tutorial/controlflow.html#defining-functions',
                "description": 'Official guide on function definitions, return statements, arbitrary arguments, and LEGB scope.',
                "difficulty": 'Intermediate',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Functions and Modular Programming',
                "website_name": 'Corey Schafer (YouTube)',
                "url": 'https://www.youtube.com/watch?v=9Os0o3wzS_I',
                "description": 'Video guide to function structure, DRY code, positional vs keyword arguments, and *args/**kwargs.',
                "difficulty": 'Intermediate',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Python Functions Exercises',
                "website_name": 'W3Schools',
                "url": 'https://www.w3schools.com/python/exercise.asp?filename=exercise_functions1',
                "description": 'Interactive exercises testing function invocation, argument passing, and return value handling.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'File I/O & Exception Handling': [
            {
                "title": 'Errors and Exceptions in Python',
                "website_name": 'Python Official Docs',
                "url": 'https://docs.python.org/3/tutorial/errors.html',
                "description": 'Official guide to syntax errors, exception handling with try/except, and raising exceptions.',
                "difficulty": 'Intermediate',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Using Try/Except Blocks for Error Handling',
                "website_name": 'Corey Schafer (YouTube)',
                "url": 'https://www.youtube.com/watch?v=NIWwJbo-9_8',
                "description": 'Video covering specific vs broad exceptions, else blocks, finally cleanup, and custom errors.',
                "difficulty": 'Intermediate',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Python Try...Except Exercises',
                "website_name": 'W3Schools',
                "url": 'https://www.w3schools.com/python/exercise.asp?filename=exercise_try_except1',
                "description": 'Interactive coding challenges handling runtime exceptions and defensive programming.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Object-Oriented Programming in Python': [
            {
                "title": 'Python Classes and Object-Oriented Programming',
                "website_name": 'Python Official Docs',
                "url": 'https://docs.python.org/3/tutorial/classes.html',
                "description": 'Official documentation covering classes, namespaces, instances, inheritance, and dunder methods.',
                "difficulty": 'Advanced',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Python OOP Tutorial: Classes and Instances',
                "website_name": 'Corey Schafer (YouTube)',
                "url": 'https://www.youtube.com/watch?v=ZDa-Z5JzLYM',
                "description": 'Essential video explaining self, __init__, instance vs class variables, and encapsulation.',
                "difficulty": 'Advanced',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Python Classes and Objects Exercises',
                "website_name": 'W3Schools',
                "url": 'https://www.w3schools.com/python/exercise.asp?filename=exercise_classes1',
                "description": 'Interactive exercises creating classes, instantiating objects, and calling member methods.',
                "difficulty": 'Advanced',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Stack Basics & Operations': [
            {
                "title": 'Stack Data Structure: Push, Pop & LIFO Principles',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/stack-data-structure/',
                "description": 'Complete guide on stack mechanics, top pointer, time complexity, and array vs linked list backing.',
                "difficulty": 'Beginner',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Stacks Data Structure & Implementation',
                "website_name": 'FreeCodeCamp (YouTube)',
                "url": 'https://www.youtube.com/watch?v=sFVxsglODoo',
                "description": 'Video walkthrough showing stack memory representation, function calls, and push/pop operations.',
                "difficulty": 'Beginner',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Interactive Visualizer: Stack Execution & Trace',
                "website_name": 'VisuAlgo',
                "url": 'https://visualgo.net/en/list',
                "description": 'Animated visualizer allowing step-by-step push, pop, peek, and overflow/underflow inspection.',
                "difficulty": 'Beginner',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Queue Basics & Operations': [
            {
                "title": 'Queue Data Structure: Enqueue, Dequeue, FIFO',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/queue-data-structure/',
                "description": 'Guide on FIFO queue operations, front/rear pointers, and circular buffer implementations.',
                "difficulty": 'Beginner',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Queues Data Structure & Circular Buffer',
                "website_name": 'FreeCodeCamp (YouTube)',
                "url": 'https://www.youtube.com/watch?v=bK7I79hcm08',
                "description": 'Video lesson detailing queue operations, time complexity, and circular queue wraparound logic.',
                "difficulty": 'Beginner',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Queue & Circular Buffer Interactive Simulation',
                "website_name": 'VisuAlgo',
                "url": 'https://visualgo.net/en/list',
                "description": 'Interactive animated tool for tracing queue insertions, head removals, and buffer indexing.',
                "difficulty": 'Beginner',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Recursion Fundamentals': [
            {
                "title": 'Understanding Recursion: Base Conditions & Call Stacks',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/introduction-to-recursion-data-structure-and-algorithm-tutorials/',
                "description": 'Conceptual guide explaining base cases, recursive reduction, stack frame allocation, and termination.',
                "difficulty": 'Intermediate',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Recursion in Programming: Full Tutorial',
                "website_name": 'FreeCodeCamp (YouTube)',
                "url": 'https://www.youtube.com/watch?v=IJDJ0kBx2LM',
                "description": 'Comprehensive video course on recursive thinking, call stacks, induction, and problem decomposition.',
                "difficulty": 'Intermediate',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Interactive Recursion Simulation & Call Tree',
                "website_name": 'VisuAlgo',
                "url": 'https://visualgo.net/en/recursion',
                "description": 'Visual simulation of recursive calls, activation records, and stack return value bubbling.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Tree Basics': [
            {
                "title": 'Binary Trees: Root, Leaf, Depth & Properties',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/binary-tree-data-structure/',
                "description": 'Hierarchical data structure guide: nodes, edges, height, level, full vs complete binary trees.',
                "difficulty": 'Intermediate',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Introduction to Trees in Computer Science',
                "website_name": 'FreeCodeCamp (YouTube)',
                "url": 'https://www.youtube.com/watch?v=qH6ClASRiIY',
                "description": 'Visual video lesson introducing tree terminologies, binary trees, properties, and applications.',
                "difficulty": 'Intermediate',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Interactive Binary Tree Visualizer',
                "website_name": 'VisuAlgo',
                "url": 'https://visualgo.net/en/bst',
                "description": 'Interactive canvas to build, insert, search, and visualize binary tree structures in real time.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Tree Traversal': [
            {
                "title": 'Tree Traversals: Inorder, Preorder, Postorder Walkthrough',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/tree-traversals-inorder-preorder-and-postorder/',
                "description": 'Comprehensive reference covering depth-first traversals with recursive and iterative implementations.',
                "difficulty": 'Intermediate',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Binary Tree Traversal: Preorder, Inorder, Postorder',
                "website_name": 'FreeCodeCamp (YouTube)',
                "url": 'https://www.youtube.com/watch?v=gm8DUJJhmY4',
                "description": 'Video explaining the mechanics and order of node visits in Preorder, Inorder, and Postorder traversals.',
                "difficulty": 'Intermediate',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Interactive Traversal Order Step-by-Step',
                "website_name": 'VisuAlgo',
                "url": 'https://visualgo.net/en/bst',
                "description": 'Step through tree traversals interactively node-by-node with highlighted current traversal state.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Recursive Practice': [
            {
                "title": 'Recursion Concepts and Algorithmic Patterns',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/recursion/',
                "description": 'Detailed compendium of recursive algorithms, divide-and-conquer strategies, and call stack analysis.',
                "difficulty": 'Intermediate',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Learn Recursion with Visual Code Trace',
                "website_name": 'FreeCodeCamp (YouTube)',
                "url": 'https://www.youtube.com/watch?v=ngCos392W4w',
                "description": 'Video tutorial walking through classic recursive challenges with animated stack frame traces.',
                "difficulty": 'Intermediate',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Tail Recursion and Call Stack Optimization Practice',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/tail-recursion/',
                "description": 'Hands-on guide and problems contrasting head vs tail recursion and compiler stack frame reuse.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Tree Problems & Applications': [
            {
                "title": 'Binary Search Tree Operations & Applications',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/binary-search-tree-data-structure/',
                "description": 'In-depth reference on BST search, insertion, deletion of nodes with zero, one, or two children.',
                "difficulty": 'Advanced',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Binary Search Trees Implementation & Applications',
                "website_name": 'FreeCodeCamp (YouTube)',
                "url": 'https://www.youtube.com/watch?v=fAAZixBzIAI',
                "description": 'Video covering BST property invariants, node deletion logic, finding predecessor/successor, and balancing.',
                "difficulty": 'Advanced',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Binary Search Tree Operations & Rebalancing',
                "website_name": 'VisuAlgo',
                "url": 'https://visualgo.net/en/bst',
                "description": 'Interactive simulator to practice search key queries, minimum/maximum extraction, and deletion cases.',
                "difficulty": 'Advanced',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Algorithm Complexity & Big-O': [
            {
                "title": 'Big-O Notation & Asymptotic Complexity Guide',
                "website_name": 'Big-O Cheat Sheet',
                "url": 'https://www.bigocheatsheet.com/',
                "description": 'Visual comparison of time and space complexity growth curves from O(1) to O(n!).',
                "difficulty": 'Beginner',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Computational Complexity and Big-O Notation',
                "website_name": 'CS50 (YouTube)',
                "url": 'https://www.youtube.com/watch?v=D6xkbGLQesk',
                "description": 'Harvard CS50 lecture explaining asymptotic bounds, upper/lower limits, and algorithm scaling.',
                "difficulty": 'Beginner',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Practice Questions on Time Complexity Analysis',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/practice-questions-time-complexity-analysis/',
                "description": 'Curated problems finding the tight Big-O bound of nested loops, divide-and-conquer recurrences, and recursion.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Statistical Learning & Feature Engineering': [
            {
                "title": 'Preprocessing & Feature Scaling',
                "website_name": 'Scikit-Learn Docs',
                "url": 'https://scikit-learn.org/stable/modules/preprocessing.html',
                "description": 'Official documentation covering StandardScaler, MinMaxScaler, imputation, one-hot encoding, and feature transformers.',
                "difficulty": 'Beginner',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'StatQuest: Machine Learning Fundamentals: Bias and Variance',
                "website_name": 'StatQuest (YouTube)',
                "url": 'https://www.youtube.com/watch?v=Gv9_4yMHFhI',
                "description": 'Clear visual lecture on underfitting, overfitting, model capacity, and balancing bias versus variance.',
                "difficulty": 'Beginner',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Feature Scaling Importance & Visualizer',
                "website_name": 'Scikit-Learn Examples',
                "url": 'https://scikit-learn.org/stable/auto_examples/preprocessing/plot_scaling_importance.html',
                "description": 'Interactive code example and visual demonstration of feature scaling impact on distance metrics.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Linear & Polynomial Regression': [
            {
                "title": 'Linear Models: Ordinary Least Squares & Polynomial Features',
                "website_name": 'Scikit-Learn Docs',
                "url": 'https://scikit-learn.org/stable/modules/linear_model.html',
                "description": 'Official guide on OLS mathematical formulations, coefficient estimation, and polynomial transformations.',
                "difficulty": 'Intermediate',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'StatQuest: Linear Regression, Clearly Explained',
                "website_name": 'StatQuest (YouTube)',
                "url": 'https://www.youtube.com/watch?v=nk2CQITm_eo',
                "description": 'Step-by-step graphical explanation of best-fit lines, residuals, sum of squared errors, and R-squared.',
                "difficulty": 'Intermediate',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Interactive Python Linear Regression Exercises',
                "website_name": 'W3Schools',
                "url": 'https://www.w3schools.com/python/python_ml_linear_regression.asp',
                "description": 'Interactive browser sandbox fitting linear regression models and calculating predictions.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Logistic Regression & Classification': [
            {
                "title": 'Logistic Regression for Binary & Multi-class',
                "website_name": 'Scikit-Learn Docs',
                "url": 'https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression',
                "description": 'Official documentation covering the sigmoid link function, log-loss optimization, and regularization.',
                "difficulty": 'Intermediate',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'StatQuest: Logistic Regression, Clearly Explained',
                "website_name": 'StatQuest (YouTube)',
                "url": 'https://www.youtube.com/watch?v=yIYKR4gTd5U',
                "description": 'Video explaining log-odds, probability thresholds, maximum likelihood estimation, and decision boundaries.',
                "difficulty": 'Intermediate',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Interactive Logistic Regression Sandbox',
                "website_name": 'W3Schools',
                "url": 'https://www.w3schools.com/python/python_ml_logistic_regression.asp',
                "description": 'Hands-on sandbox fitting logistic classification models and checking probability outputs.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Decision Trees & Random Forests': [
            {
                "title": 'Decision Trees & Ensembles Guide',
                "website_name": 'Scikit-Learn Docs',
                "url": 'https://scikit-learn.org/stable/modules/tree.html',
                "description": 'Official documentation on recursive splitting, Gini impurity, information gain, and bagging/forest ensembles.',
                "difficulty": 'Intermediate',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'StatQuest: Decision Trees Clearly Explained',
                "website_name": 'StatQuest (YouTube)',
                "url": 'https://www.youtube.com/watch?v=_L39rN6gz7Y',
                "description": 'Step-by-step visual demonstration of building decision trees from tabular data using Gini impurity.',
                "difficulty": 'Intermediate',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Interactive Decision Tree Classifier Sandbox',
                "website_name": 'W3Schools',
                "url": 'https://www.w3schools.com/python/python_ml_decision_tree.asp',
                "description": 'Interactive exercise building a decision tree, plotting branches, and classifying test samples.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Model Evaluation & Validation': [
            {
                "title": 'Model Evaluation: Cross-Validation & Metrics',
                "website_name": 'Scikit-Learn Docs',
                "url": 'https://scikit-learn.org/stable/modules/model_evaluation.html',
                "description": 'Official reference covering precision, recall, F1-score, ROC-AUC, k-fold cross-validation, and scoring parameters.',
                "difficulty": 'Intermediate',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'StatQuest: Cross Validation, Clearly Explained',
                "website_name": 'StatQuest (YouTube)',
                "url": 'https://www.youtube.com/watch?v=fSytzGwwBVw',
                "description": 'Video explaining why train/test splits can be lucky or unlucky, and how k-fold cross validation solves it.',
                "difficulty": 'Intermediate',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Confusion Matrix and Evaluation Metrics Exercises',
                "website_name": 'W3Schools',
                "url": 'https://www.w3schools.com/python/python_ml_confusion_matrix.asp',
                "description": 'Interactive browser exercises computing accuracy, precision, sensitivity, and specificity from confusion matrices.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Clustering & K-Means': [
            {
                "title": 'Clustering: K-Means Algorithm & Variants',
                "website_name": 'Scikit-Learn Docs',
                "url": 'https://scikit-learn.org/stable/modules/clustering.html#k-means',
                "description": "Official documentation covering unsupervised cluster centroid initialization, Lloyd's algorithm, and inertia.",
                "difficulty": 'Intermediate',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'StatQuest: K-Means Clustering, Clearly Explained',
                "website_name": 'StatQuest (YouTube)',
                "url": 'https://www.youtube.com/watch?v=4b5d3muPQmA',
                "description": 'Visual walkthrough of random centroid placement, distance assignment, centroid recalculation, and the elbow method.',
                "difficulty": 'Intermediate',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Interactive K-Means Clustering Sandbox',
                "website_name": 'W3Schools',
                "url": 'https://www.w3schools.com/python/python_ml_k-means.asp',
                "description": 'Interactive sandbox testing 2D point clustering, cluster inertia plotting, and elbow point detection.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Dimensionality Reduction & PCA': [
            {
                "title": 'Decomposition: Principal Component Analysis (PCA)',
                "website_name": 'Scikit-Learn Docs',
                "url": 'https://scikit-learn.org/stable/modules/decomposition.html#pca',
                "description": 'Official reference on covariance matrices, eigenvectors, singular value decomposition (SVD), and explained variance.',
                "difficulty": 'Advanced',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'StatQuest: Principal Component Analysis (PCA) Step-by-Step',
                "website_name": 'StatQuest (YouTube)',
                "url": 'https://www.youtube.com/watch?v=FgakZw6K1QQ',
                "description": 'Step-by-step visual demonstration of coordinate projection, principal axis fitting, and scree plots.',
                "difficulty": 'Advanced',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Principal Component Analysis Python Walkthrough',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/principal-component-analysis-pca/',
                "description": 'Worked practical exercises transforming high-dimensional datasets into 2D visualizations.',
                "difficulty": 'Advanced',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Neural Networks & Backpropagation': [
            {
                "title": 'Multi-layer Perceptron (Neural Networks) Guide',
                "website_name": 'Scikit-Learn Docs',
                "url": 'https://scikit-learn.org/stable/modules/neural_networks_supervised.html',
                "description": 'Official guide covering perceptrons, hidden layers, activation functions (ReLU, Sigmoid), and gradient descent.',
                "difficulty": 'Advanced',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": '3Blue1Brown: But what is a neural network? Deep learning',
                "website_name": '3Blue1Brown (YouTube)',
                "url": 'https://www.youtube.com/watch?v=aircAruvnKk',
                "description": 'World-renowned animated explanation of neurons, weights, biases, activations, and layered feature representations.',
                "difficulty": 'Advanced',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'TensorFlow Playground: Interactive Neural Network Simulator',
                "website_name": 'TensorFlow Playground',
                "url": 'https://playground.tensorflow.org/',
                "description": 'Interactive browser canvas training real-time neural networks with custom layers, learning rates, and dataset shapes.',
                "difficulty": 'Advanced',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Relational Data Model & Schemas': [
            {
                "title": 'Relational Model Concepts and Keys',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/relational-model-in-dbms/',
                "description": 'Foundational guide on tuples, attributes, primary keys, foreign keys, candidate keys, and relational schema constraints.',
                "difficulty": 'Beginner',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Relational Database Design and Modeling',
                "website_name": 'FreeCodeCamp (YouTube)',
                "url": 'https://www.youtube.com/watch?v=ztHopE5Wnpc',
                "description": 'Full video course covering ER diagrams, cardinalities, primary/foreign key relations, and schema normalization.',
                "difficulty": 'Beginner',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Interactive Relational Schema & SELECT Basics',
                "website_name": 'SQLZoo',
                "url": 'https://sqlzoo.net/wiki/SELECT_basics',
                "description": 'Hands-on browser SQL exercises querying tables, applying WHERE filters, and projecting attributes.',
                "difficulty": 'Beginner',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'SQL DDL & Integrity Constraints': [
            {
                "title": 'Data Definition and Table Constraints',
                "website_name": 'PostgreSQL Docs',
                "url": 'https://www.postgresql.org/docs/current/ddl.html',
                "description": 'Official manual covering CREATE TABLE, ALTER TABLE, DROP, NOT NULL, UNIQUE, and CHECK constraints.',
                "difficulty": 'Beginner',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'SQL Tutorial: Full Database Course for Beginners',
                "website_name": 'FreeCodeCamp (YouTube)',
                "url": 'https://www.youtube.com/watch?v=HXV3zeRR3h4',
                "description": 'Comprehensive video course demonstrating table creation, schema constraints, data types, and primary key setups.',
                "difficulty": 'Beginner',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Interactive SQL CREATE TABLE & Constraints',
                "website_name": 'W3Schools',
                "url": 'https://www.w3schools.com/sql/exercise.asp?filename=exercise_create_table1',
                "description": 'Interactive coding challenges practicing DDL statements, table definitions, and column rules.',
                "difficulty": 'Beginner',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'SQL DML & Aggregation Queries': [
            {
                "title": 'Data Manipulation: INSERT, UPDATE & DELETE',
                "website_name": 'PostgreSQL Docs',
                "url": 'https://www.postgresql.org/docs/current/dml.html',
                "description": 'Official database manual covering record insertion, safe updates with conditions, row deletions, and returning clauses.',
                "difficulty": 'Intermediate',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'SQL Tutorial: Aggregation, Group By & Filtering',
                "website_name": 'Programming with Mosh (YouTube)',
                "url": 'https://www.youtube.com/watch?v=7S_tz1z_5bA',
                "description": 'Video tutorial explaining aggregate functions (COUNT, SUM, AVG), GROUP BY partitions, and HAVING clause filters.',
                "difficulty": 'Intermediate',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Interactive Aggregate Functions Exercises',
                "website_name": 'SQLZoo',
                "url": 'https://sqlzoo.net/wiki/SUM_and_COUNT',
                "description": 'Browser-based SQL practice executing SUM, COUNT, MAX, and HAVING queries on live relational tables.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Complex SQL Joins & Subqueries': [
            {
                "title": 'Joined Tables, Cross Join, Inner & Outer Joins',
                "website_name": 'PostgreSQL Docs',
                "url": 'https://www.postgresql.org/docs/current/queries-table-expressions.html',
                "description": 'Official documentation covering INNER, LEFT, RIGHT, FULL OUTER joins, subqueries, and table aliases.',
                "difficulty": 'Intermediate',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'SQL Joins Tutorial: Inner, Left, Right & Full Joins',
                "website_name": 'Bro Code (YouTube)',
                "url": 'https://www.youtube.com/watch?v=0r1SlesupIE',
                "description": 'Video walkthrough with clear Venn diagrams illustrating join conditions, matching rows, and null padding.',
                "difficulty": 'Intermediate',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Interactive JOIN Operations Exercises',
                "website_name": 'SQLZoo',
                "url": 'https://sqlzoo.net/wiki/The_JOIN_operation',
                "description": 'Curated hands-on SQL problems joining multiple related tables to answer analytical questions.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Relational Algebra Operations': [
            {
                "title": 'Introduction to Relational Algebra in DBMS',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/introduction-of-relational-algebra-in-dbms/',
                "description": 'Theoretical guide explaining Selection (sigma), Projection (pi), Cartesian Product, Set Difference, and Joins.',
                "difficulty": 'Intermediate',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Relational Algebra in DBMS: Operators & Expressions',
                "website_name": 'Gate Smashers (YouTube)',
                "url": 'https://www.youtube.com/watch?v=4YilEjkNPrQ',
                "description": 'Lecture explaining procedural query language symbols, condition filtering, column projection, and union compatibility.',
                "difficulty": 'Intermediate',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Relational Algebra Operations and Solved Problems',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/gate-gate-cs-2012-question-43/',
                "description": 'Practice problems and step-by-step query equivalence evaluations for relational algebra expressions.',
                "difficulty": 'Intermediate',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Functional Dependencies & 1NF-3NF': [
            {
                "title": 'Database Normalization (1NF, 2NF, 3NF, BCNF)',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/database-normalization-introduction/',
                "description": 'Comprehensive reference explaining functional dependency closure, candidate keys, anomaly prevention, and normal forms.',
                "difficulty": 'Advanced',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'Database Design Tutorial: Normalization Explained',
                "website_name": 'Caleb Curry (YouTube)',
                "url": 'https://www.youtube.com/watch?v=UrYLYV7WSHM',
                "description": 'Video explaining why anomalies occur in unnormalized tables and how 1NF, 2NF, and 3NF decompose schemas losslessly.',
                "difficulty": 'Advanced',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'Practice Problems on Normalization and Candidate Keys',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/gate-gate-cs-2012-question-44/',
                "description": 'Worked practice problems finding attribute closures, minimal covers, and decomposing tables into 3NF/BCNF.',
                "difficulty": 'Advanced',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Indexing & B-Tree Storage': [
            {
                "title": 'PostgreSQL Index Types & B-Tree Storage',
                "website_name": 'PostgreSQL Docs',
                "url": 'https://www.postgresql.org/docs/current/indexes.html',
                "description": 'Official documentation covering B-Tree leaf pages, index selectivity, composite indexes, and sequential vs index scans.',
                "difficulty": 'Advanced',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'B-Trees and Database Indexing Architecture',
                "website_name": 'Hussein Nasser (YouTube)',
                "url": 'https://www.youtube.com/watch?v=aZjYr87r1b8',
                "description": 'Engineering-level breakdown of disk I/O, page splits, balanced tree search paths, and database execution plans.',
                "difficulty": 'Advanced',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'SQL Indexing Interactive Guide: Leaf Nodes & Range Scans',
                "website_name": 'Use The Index, Luke',
                "url": 'https://use-the-index-luke.com/sql/anatomy',
                "description": 'Interactive visual anatomy explaining index leaf node traversal, cluster ordering, and range scan costs.',
                "difficulty": 'Advanced',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ],
        'Transactions, ACID & Concurrency': [
            {
                "title": 'PostgreSQL Transaction Isolation & ACID Guarantees',
                "website_name": 'PostgreSQL Docs',
                "url": 'https://www.postgresql.org/docs/current/transaction-iso.html',
                "description": 'Official manual covering Atomicity, Consistency, Isolation, Durability, dirty reads, non-repeatable reads, and serializability.',
                "difficulty": 'Advanced',
                "type": 'Documentation',
                "resource_type": 'Documentation',
                "approved_by_faculty": False
            },
            {
                "title": 'ACID Properties in Databases Explained',
                "website_name": 'Hussein Nasser (YouTube)',
                "url": 'https://www.youtube.com/watch?v=pomx4vvpegg',
                "description": 'Video explaining transaction commit/rollback, write-ahead logging (WAL), two-phase locking, and isolation levels.',
                "difficulty": 'Advanced',
                "type": 'Video',
                "resource_type": 'Video',
                "approved_by_faculty": False
            },
            {
                "title": 'ACID Properties and Concurrency Exercises',
                "website_name": 'GeeksforGeeks',
                "url": 'https://www.geeksforgeeks.org/acid-properties-in-dbms/',
                "description": 'Practice questions analyzing transaction schedules, conflict serializability, and deadlock prevention.',
                "difficulty": 'Advanced',
                "type": 'Practice',
                "resource_type": 'Practice',
                "approved_by_faculty": False
            }
        ]
    }

    @classmethod
    def get_resources_for_topic(cls, topic_title: str) -> List[Dict[str, Any]]:
        clean_title = (topic_title or "").strip()
        if not clean_title:
            return []
        if clean_title in cls.RESOURCES_CATALOG:
            return cls.RESOURCES_CATALOG[clean_title]
        lower_title = clean_title.lower()
        for key, recs in cls.RESOURCES_CATALOG.items():
            if key.lower() == lower_title:
                return recs
        for key, recs in cls.RESOURCES_CATALOG.items():
            if key.lower() in lower_title or lower_title in key.lower():
                return recs
        encoded_query = urllib.parse.quote_plus(clean_title)
        return [
            {
                "title": f"Academic Reference & Study Guide: {clean_title}",
                "website_name": "Encyclopedic Reference",
                "url": f"https://en.wikipedia.org/wiki/Special:Search?search={encoded_query}",
                "description": f"Curated reference concepts and formal overview for {clean_title}.",
                "difficulty": "Intermediate",
                "type": "Documentation",
                "resource_type": "Documentation",
                "approved_by_faculty": False
            }
        ]
