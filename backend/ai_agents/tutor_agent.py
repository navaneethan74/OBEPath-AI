from typing import Dict, Any, List

class TutorAgent:
    """
    Tutor Agent:
    Provides beginner-friendly, pedagogical learning explanations.
    For every topic across all 4 OBE courses, it delivers:
    1. A short, clear definition
    2. A familiar real-world example
    3. A small step-by-step example (Python code for Python, SQL tables & queries for DBMS,
       clear data structure state changes for DSA, and simple real-world examples for ML)
    4. A short summary
    """

    TOPIC_KNOWLEDGE: Dict[str, Dict[str, Any]] = {
        # =====================================================================
        # Course 1: CS101 Python Programming
        # =====================================================================
        "Variables, Data Types & Basic I/O": {
            "definition": "A variable is a named storage container in computer memory where you save values like numbers or text so your program can use them later.",
            "real_world": "Think of variables like labeled storage boxes in your room. If you write 'shoes' on a box, you know only shoes belong inside. In Python, writing `student_age = 19` puts the number 19 into a box labeled `student_age`.",
            "step_by_step": (
                "```python\n"
                "# Step 1: Store student name (text / string)\n"
                "student_name = 'Maya'\n\n"
                "# Step 2: Store number of courses (integer)\n"
                "course_count = 3\n\n"
                "# Step 3: Print a personalized welcome message\n"
                "print(f'Hello {student_name}! You are enrolled in {course_count} courses.')\n"
                "# Output: Hello Maya! You are enrolled in 3 courses.\n"
                "```"
            ),
            "summary": "Variables store values in memory, data types define what kind of value is stored, and `print()` displays messages on the screen.",
            "code": "name = 'Maya'\nage = 19\ngpa = 3.85\nis_enrolled = True\nprint(f'{name} is {age} years old with GPA {gpa}.')",
            "visual": "+-----------------------+----------------------+\n| Variable Name in Code | Stored Value in RAM  |\n+-----------------------+----------------------+\n| student_name          | 'Maya' (String)      |\n| course_count          | 3 (Integer)          |\n+-----------------------+----------------------+",
            "hint": "Variable names in Python cannot have spaces and cannot start with a number. Use underscores like `user_name`.",
            "test": "Which data type is `3.14` in Python? A) int, B) float, C) str, D) bool (Answer: B)"
        },
        "Conditional Statements & Branching": {
            "definition": "Conditional statements let your program make decisions and run different lines of code based on whether a question is True or False.",
            "real_world": "Checking the weather before going outside: IF it is raining, take an umbrella. ELSE IF it is sunny, wear sunglasses. ELSE, wear a normal jacket.",
            "step_by_step": (
                "```python\n"
                "# Step 1: Set the exam score\n"
                "score = 82\n\n"
                "# Step 2: Check conditions from top to bottom\n"
                "if score >= 90:\n"
                "    print('Grade: A')\n"
                "elif score >= 80:\n"
                "    print('Grade: B')  # Runs because 82 is >= 80!\n"
                "else:\n"
                "    print('Grade: C or below')\n"
                "# Output: Grade: B\n"
                "```"
            ),
            "summary": "Use `if`, `elif`, and `else` with a colon `:` and indented lines to guide your program down different decision paths.",
            "code": "temperature = 28\nif temperature > 30:\n    print('Turn on AC')\nelif temperature >= 20:\n    print('Pleasant weather')\nelse:\n    print('Turn on heater')",
            "visual": "     [ Check Condition: score >= 80? ]\n               /               \\\n       YES (True)             NO (False)\n          /                       \\\n[ Print 'Grade: B' ]      [ Check Next Condition ]",
            "hint": "Always indent lines inside an `if` block by 4 spaces. Forgetting indentation causes an `IndentationError`.",
            "test": "What will `if not False:` evaluate to? A) False, B) True, C) None, D) Error (Answer: B)"
        },
        "Loops & Iterative Control": {
            "definition": "A loop repeats a block of code multiple times automatically so you do not have to write the same line over and over by hand.",
            "real_world": "Doing 10 jumping jacks in gym class: you count from 1 to 10 and do the exact same exercise on each count until you reach 10.",
            "step_by_step": (
                "```python\n"
                "# Step 1: Tell Python to count through steps 1, 2, and 3\n"
                "for step_num in range(1, 4):\n"
                "    # Step 2: This indented line runs for each count\n"
                "    print(f'Completed step {step_num} of 3')\n\n"
                "# Output:\n"
                "# Completed step 1 of 3\n"
                "# Completed step 2 of 3\n"
                "# Completed step 3 of 3\n"
                "```"
            ),
            "summary": "`for` loops repeat for a fixed number of times; `while` loops repeat as long as a condition stays True.",
            "code": "# for loop over numbers\nfor i in range(1, 4):\n    print('Count:', i)\n\n# while loop\nfuel = 3\nwhile fuel > 0:\n    print('Driving... Fuel left:', fuel)\n    fuel -= 1",
            "visual": "Start -> [ Check: More items? ] -- YES --> [ Run Loop Code ] --+\n                 ^                                              |\n                 +----------------- Next Item ------------------+\n                 |-- NO --> [ Move to Next Part of Program ]",
            "hint": "In a `while` loop, always make sure the variable changes inside the loop, otherwise it will run forever (infinite loop)!",
            "test": "How many times does `for i in range(3):` run? A) 2, B) 3, C) 4, D) 0 (Answer: B, with values 0, 1, 2)"
        },
        "Python Lists & Tuples": {
            "definition": "A list is an ordered collection of items that you can edit anytime using square brackets `[]`. A tuple is an ordered collection in parentheses `()` that cannot be changed once created.",
            "real_world": "A list is like a grocery shopping list written in pencil: you can erase items or add snacks. A tuple is like your date of birth on your passport: once written, it is permanent and cannot be modified.",
            "step_by_step": (
                "```python\n"
                "# Step 1: Create a list of backpack items\n"
                "backpack = ['notebook', 'pencil']\n\n"
                "# Step 2: Add an item (lists can change!)\n"
                "backpack.append('calculator')\n"
                "print('Updated backpack:', backpack)\n"
                "# Output: ['notebook', 'pencil', 'calculator']\n\n"
                "# Step 3: Create a tuple for GPS coordinates (cannot change!)\n"
                "location = (12.97, 77.59)\n"
                "print('Latitude:', location[0])  # 12.97\n"
                "```"
            ),
            "summary": "Use lists `[]` when your collection needs to grow, shrink, or change; use tuples `()` when your data must stay protected from accidental changes.",
            "code": "fruits = ['apple', 'banana']\nfruits.append('orange')\nprint(fruits[0]) # 'apple' (first item is index 0)\n\nscreen_size = (1920, 1080) # Tuple: width, height",
            "visual": "List Index:      0            1             2\nItems:      ['notebook',   'pencil',   'calculator']\n(You can add, remove, and change items anytime)",
            "hint": "Python list indices start at 0, not 1! The first item is always `items[0]`.",
            "test": "Which symbol is used to create a Python list? A) (), B) {}, C) [], D) <> (Answer: C)"
        },
        "Dictionaries, Sets & Hash Collections": {
            "definition": "A dictionary stores data in key-value pairs (`{key: value}`) for instant lookup by name. A set stores unique items without duplicates.",
            "real_world": "Your phone contacts app: when you tap on 'Mom' (the key), her phone number appears instantly (the value) without searching through hundreds of other contacts.",
            "step_by_step": (
                "```python\n"
                "# Step 1: Create a student dictionary with key-value pairs\n"
                "student = {'name': 'Liam', 'major': 'Computer Science', 'gpa': 3.9}\n\n"
                "# Step 2: Look up values by key name\n"
                "print('Student Name:', student['name'])  # Liam\n\n"
                "# Step 3: Add a new key-value pair\n"
                "student['active'] = True\n"
                "print('Status:', student['active'])     # True\n"
                "```"
            ),
            "summary": "Dictionaries use `{key: value}` to look up data instantly without searching through everything; keys must be unique.",
            "code": "user = {'id': 101, 'email': 'liam@univ.edu', 'role': 'Student'}\nprint('Email:', user.get('email'))\n\nunique_tags = {'python', 'beginner', 'python'} # Set removes duplicates\nprint(unique_tags) # {'python', 'beginner'}",
            "visual": "+-------------------+-------------------------+\n| Key (Word/Lookup) | Value (Stored Answer)   |\n+-------------------+-------------------------+\n| 'name'            | 'Liam'                  |\n| 'major'           | 'Computer Science'      |\n| 'gpa'             | 3.9                     |\n+-------------------+-------------------------+",
            "hint": "Use `student.get('age', 0)` to look up values safely without crashing if a key does not exist.",
            "test": "Can a dictionary have two identical keys? A) Yes, B) No, later keys overwrite earlier ones, C) Only if numbers, D) Only in Python 2 (Answer: B)"
        },
        "Functions, Scope & Parameter Passing": {
            "definition": "A function is a reusable mini-program defined with `def` that takes input data, performs a specific task, and returns the result using `return`.",
            "real_world": "An automatic coffee machine: you put in water and coffee beans (parameters/inputs), press the brew button (function body), and pour out a hot cup of coffee (return value).",
            "step_by_step": (
                "```python\n"
                "# Step 1: Define the function recipe with input parameters\n"
                "def calculate_total(price, tax_rate=0.05):\n"
                "    # Step 2: Perform the calculation\n"
                "    tax = price * tax_rate\n"
                "    total = price + tax\n"
                "    # Step 3: Send the final answer back with return\n"
                "    return total\n\n"
                "# Step 4: Call the function with our lunch price\n"
                "my_bill = calculate_total(20.00)\n"
                "print(f'Total Bill: ${my_bill:.2f}')  # Total Bill: $21.00\n"
                "```"
            ),
            "summary": "Functions eliminate repetitive code; `print()` only displays text, while `return` gives the result back to your program to use.",
            "code": "def greet_user(first_name, course_name='Python'):\n    return f'Welcome {first_name} to {course_name}!'\n\nmessage = greet_user('Sara')\nprint(message)",
            "visual": "Input (price: 20) ---> [ Function: calculate_total ] ---> Output (21.00)\n                       | Do Math: 20 + (20 * 0.05) |\n                       +---------------------------+",
            "hint": "Variables created inside a function are local—they disappear once the function finishes running.",
            "test": "What keyword is used to send a value back from a function? A) send, B) exit, C) return, D) give (Answer: C)"
        },
        "File I/O & Exception Handling": {
            "definition": "File I/O lets your program save data to text files on your disk so it is not lost when the program closes. Exception handling (`try/except`) prevents your program from crashing when an error happens.",
            "real_world": "Writing homework notes in a diary so you can read them tomorrow (File I/O), and wearing a helmet while cycling so unexpected bumps do not hurt you (Exception Handling).",
            "step_by_step": (
                "```python\n"
                "# Step 1: Write text to a file using 'with'\n"
                "with open('student_notes.txt', 'w') as file:\n"
                "    file.write('Learning Python with OBEPath AI!\\n')\n\n"
                "# Step 2: Read it back safely with error protection\n"
                "try:\n"
                "    with open('student_notes.txt', 'r') as file:\n"
                "        content = file.read()\n"
                "        print('File content:', content.strip())\n"
                "except FileNotFoundError:\n"
                "    print('The file could not be found.')\n"
                "```"
            ),
            "summary": "Always use `with open(...)` to automatically close files, and use `try ... except` blocks to catch errors gently without crashing.",
            "code": "try:\n    number = int('not_a_number')\nexcept ValueError:\n    print('Please enter a valid number!')\nfinally:\n    print('Check complete.')",
            "visual": "[ Program ] ---> Writes data ---> [ student_notes.txt on Disk ]\n[ Program ] <--- Reads data  <--- [ student_notes.txt on Disk ]",
            "hint": "The `with` statement guarantees that the file is safely closed even if an unexpected error happens while reading.",
            "test": "Which mode is used to write and overwrite a file in Python? A) 'r', B) 'w', C) 'x', D) 'read' (Answer: B)"
        },
        "Object-Oriented Programming in Python": {
            "definition": "Object-Oriented Programming (OOP) is a way to organize code into reusable blueprints called **Classes**, which bundle together properties (attributes) and actions (methods).",
            "real_world": "A blueprint for a car: The blueprint defines that every car has wheels and a color, and can drive or brake. When the factory builds 5 cars from that blueprint, each individual car is an **Object** with its own color.",
            "step_by_step": (
                "```python\n"
                "# Step 1: Create the blueprint (Class)\n"
                "class Student:\n"
                "    def __init__(self, name, major):\n"
                "        self.name = name      # Attribute\n"
                "        self.major = major    # Attribute\n\n"
                "    def introduce(self):\n"
                "        return f'Hi, I am {self.name} studying {self.major}.'\n\n"
                "# Step 2: Build a real object from the blueprint\n"
                "alex = Student('Alex', 'Data Science')\n"
                "print(alex.introduce())\n"
                "# Output: Hi, I am Alex studying Data Science.\n"
                "```"
            ),
            "summary": "A Class is a reusable blueprint; an Object is a real instance created from that blueprint with its own unique data.",
            "code": "class BankAccount:\n    def __init__(self, owner, balance=0):\n        self.owner = owner\n        self.balance = balance\n    def deposit(self, amount):\n        self.balance += amount\n        return self.balance\n\nacc = BankAccount('Maya', 100)\nprint('New balance:', acc.deposit(50)) # 150",
            "visual": "Blueprint (Class Student) ----> Creates Object: alex (name: 'Alex', major: 'CS')\n                          ----> Creates Object: sara (name: 'Sara', major: 'AI')",
            "hint": "`__init__` is the special initialization function that runs automatically whenever you create a new object.",
            "test": "What is `self` inside a Python class method? A) A keyword to import math, B) A reference to the current object instance, C) A global variable, D) A loop counter (Answer: B)"
        },

        # Aliases for Course 1
        "Python Basics": {
            "definition": "Python is a clean, readable programming language that executes instructions line by line from top to bottom.",
            "real_world": "Talking to a smart assistant: you give clear instructions in plain English, and the assistant carries them out step by step.",
            "step_by_step": "```python\n# Step 1: Store a greeting\nmessage = 'Hello World!'\n# Step 2: Display it\nprint(message)\n```",
            "summary": "Python emphasizes readability, uses indentation instead of curly braces, and runs code sequentially.",
            "code": "print('Welcome to Python Programming!')",
            "visual": "Code File (.py) ---> Python Interpreter ---> Output on Screen",
            "hint": "Python is case-sensitive: `print` works, but `Print` or `PRINT` will cause an error.",
            "test": "Which function displays text on screen in Python? A) echo(), B) write(), C) print(), D) display() (Answer: C)"
        },
        "Variables and Data Types": {
            "definition": "Variables store values in computer memory with specific data types like integers, floating-point numbers, and text strings.",
            "real_world": "Labeled plastic containers in your pantry holding rice, sugar, or salt so you always know what is inside.",
            "step_by_step": "```python\nage = 20          # int\nprice = 9.99      # float\nproduct = 'Book'  # str\nprint(product, 'costs', price)\n```",
            "summary": "Python detects types automatically: whole numbers are integers, decimals are floats, and text in quotes is a string.",
            "code": "score = 95\nratio = 0.95\nstudent = 'Alex'\nprint(type(score)) # <class 'int'>",
            "visual": "Variable Name ---> Memory Location ---> Stored Value",
            "hint": "You do not need to declare types manually like in C++ or Java; Python infers them automatically.",
            "test": "What type is `'100'` (with quotes)? A) int, B) str, C) float, D) bool (Answer: B)"
        },
        "Conditional Statements": {
            "definition": "Decision-making code using `if`, `elif`, and `else` blocks that run when specific conditions are True.",
            "real_world": "Deciding whether to take an umbrella based on whether it is raining outside.",
            "step_by_step": "```python\nhas_ticket = True\nif has_ticket:\n    print('Welcome to the show!')\nelse:\n    print('Please purchase a ticket.')\n```",
            "summary": "Use comparison operators like `==`, `>`, `<`, and `>=` to create boolean questions for your code.",
            "code": "if 10 > 5:\n    print('Ten is greater than five')",
            "visual": "Condition -> True -> Run block\n          -> False -> Skip block",
            "hint": "Remember the colon `:` after `if`, `elif`, and `else`.",
            "test": "Which operator checks if two values are equal? A) =, B) ==, C) ===, D) != (Answer: B)"
        },
        "Loops": {
            "definition": "A programming construct that repeats a block of code multiple times automatically.",
            "real_world": "Repetitive exercises in a workout routine: doing 5 pushups one after another.",
            "step_by_step": "```python\nfor count in range(1, 4):\n    print('Repetition number', count)\n```",
            "summary": "Use `for` loops for sequences and ranges; use `while` loops when checking a boolean condition.",
            "code": "for x in [1, 2, 3]:\n    print(x * 2)",
            "visual": "Repeat block -> check count -> loop back or exit",
            "hint": "The `break` statement exits a loop early if needed.",
            "test": "What keyword immediately stops a loop? A) stop, B) halt, C) break, D) exit (Answer: C)"
        },
        "Lists and Tuples": {
            "definition": "Lists are editable ordered sequences `[]`; tuples are permanent read-only ordered sequences `()`.",
            "real_world": "A pencil-written grocery checklist vs a printed government certificate.",
            "step_by_step": "```python\ncolors = ['red', 'green']\ncolors.append('blue')\nprint(colors)\n```",
            "summary": "Choose lists when items will change; choose tuples when data must remain constant.",
            "code": "my_list = [10, 20, 30]\nmy_tuple = (10, 20, 30)",
            "visual": "List: [Item 0, Item 1, Item 2]",
            "hint": "Negative indices like `items[-1]` get the very last item in the list.",
            "test": "How do you get the last item of a list? A) items[last], B) items[-1], C) items[end], D) items[0] (Answer: B)"
        },
        "Dictionaries": {
            "definition": "Key-value pair mappings for fast lookups by name instead of by numerical index.",
            "real_world": "Looking up a word in an alphabetical dictionary to find its meaning.",
            "step_by_step": "```python\ncapitals = {'France': 'Paris', 'Japan': 'Tokyo'}\nprint(capitals['Japan'])  # Tokyo\n```",
            "summary": "Store data as `{key: value}` pairs for fast retrieval.",
            "code": "user = {'name': 'Sara', 'role': 'Admin'}\nprint(user['name'])",
            "visual": "Key -> Hash -> Value",
            "hint": "Dictionary keys must be unique and immutable (like strings or integers).",
            "test": "Which brackets create a dictionary? A) [], B) (), C) {}, D) <> (Answer: C)"
        },
        "Functions": {
            "definition": "A reusable block of code that takes inputs, performs logic, and returns a result.",
            "real_world": "A blender that takes ingredients and returns a smoothie.",
            "step_by_step": "```python\ndef double(number):\n    return number * 2\nprint(double(7))  # 14\n```",
            "summary": "Write functions once and reuse them anywhere in your code.",
            "code": "def add(a, b):\n    return a + b\nprint(add(3, 4))",
            "visual": "Input -> [ Function ] -> Output",
            "hint": "Use descriptive function names that start with a verb like `calculate_total`.",
            "test": "What keyword defines a function? A) func, B) def, C) function, D) define (Answer: B)"
        },
        "File Handling": {
            "definition": "Reading from and saving to files stored permanently on disk.",
            "real_world": "Saving your game progress to a memory card so you can resume tomorrow.",
            "step_by_step": "```python\nwith open('demo.txt', 'w') as f:\n    f.write('Saved!')\n```",
            "summary": "Use `with open()` for clean file operations that close files automatically.",
            "code": "with open('test.txt', 'w') as f:\n    f.write('Hello file')",
            "visual": "Program Memory <---> File on Disk",
            "hint": "Always use 'a' mode if you want to add lines without erasing existing text.",
            "test": "Which mode appends data to a file? A) 'w', B) 'r', C) 'a', D) 'append' (Answer: C)"
        },
        "Exception Handling": {
            "definition": "Safely catching and handling runtime errors so programs do not crash abruptly.",
            "real_world": "Catching a ball that drops from a desk before it hits the floor.",
            "step_by_step": "```python\ntry:\n    val = 10 / 0\nexcept ZeroDivisionError:\n    print('Cannot divide by zero!')\n```",
            "summary": "Use `try/except` blocks to handle errors and guide the user gently.",
            "code": "try:\n    x = int('abc')\nexcept ValueError:\n    print('Invalid integer')",
            "visual": "Code runs -> Error occurs -> Caught by except block -> Program continues",
            "hint": "Catch specific error types rather than using a bare `except:`.",
            "test": "Which block runs cleanup code regardless of errors? A) try, B) except, C) finally, D) else (Answer: C)"
        },
        "Mini Project": {
            "definition": "Bringing together variables, loops, functions, and files into one complete software project.",
            "real_world": "Building a full house using bricks, mortar, electrical wiring, and plumbing all together.",
            "step_by_step": "```python\ndef run_app():\n    print('Application running smoothly!')\nif __name__ == '__main__':\n    run_app()\n```",
            "summary": "Break down large real-world applications into modular, readable functions.",
            "code": "print('OBEPath AI Student Portfolio System Initialized.')",
            "visual": "UI / Input ---> Business Logic Functions ---> Data Storage",
            "hint": "Test each small function independently before connecting them together.",
            "test": "What does `if __name__ == '__main__':` do? A) Checks errors, B) Runs only when file is executed directly, C) Cleans memory, D) Compiles code (Answer: B)"
        },

        # =====================================================================
        # Course 2: CS201 Data Structures (DSA)
        # =====================================================================
        "Stack Basics & Operations": {
            "definition": "A Stack is a linear data structure that follows the Last-In, First-Out (LIFO) rule: the last item you place inside is the very first item that comes out.",
            "real_world": "A stack of clean dinner plates in a cafeteria. You add new plates to the top (Push), and people take plates from the top (Pop). The plate placed on top last is picked up first!",
            "step_by_step": (
                "```text\n"
                "Tracing Stack Operations:\n"
                "Step 1: Start with an empty stack:        []\n"
                "Step 2: push(10) -> Put 10 on the stack: [10]\n"
                "Step 3: push(20) -> Put 20 on top:      [10, 20] (Top is 20)\n"
                "Step 4: pop()    -> Remove top item:     Returns 20! Stack is now [10]\n"
                "```\n\n"
                "```python\n"
                "# Python Stack using a list\n"
                "stack = []\n"
                "stack.append(10)  # Push 10\n"
                "stack.append(20)  # Push 20\n"
                "top_val = stack.pop()  # Removes 20 (LIFO)\n"
                "print('Popped item:', top_val)   # 20\n"
                "print('Remaining stack:', stack) # [10]\n"
                "```"
            ),
            "summary": "Both push (insert) and pop (remove) occur only at one single end called the **Top**, operating in lightning-fast $O(1)$ constant time.",
            "code": "stack = []\nstack.append('Page 1') # Visit page 1\nstack.append('Page 2') # Visit page 2\nback_page = stack.pop() # Back button pops 'Page 2'\nprint('Back to:', stack[-1]) # Page 1",
            "visual": "+--- Top of Stack ---+\n|    Element [20]    | <- Pushed Last, Pops First (LIFO)\n+--------------------+\n|    Element [10]    | <- Pushed First, Pops Last\n+--------------------+",
            "hint": "Before popping an element, always verify the stack is not empty to avoid an `IndexError`.",
            "test": "After push(5), push(8), pop(), push(3), what is at the top of the stack? A) 5, B) 8, C) 3, D) Empty (Answer: C)"
        },
        "Queue Basics & Operations": {
            "definition": "A Queue is a linear data structure that follows the First-In, First-Out (FIFO) rule: the first item added to the queue is the first item removed.",
            "real_world": "A line of people waiting for concert tickets. The person who arrives first is served first and leaves first. People join at the back and exit from the front.",
            "step_by_step": (
                "```text\n"
                "Tracing Queue Operations:\n"
                "Step 1: Start with empty queue: Front -> [] <- Rear\n"
                "Step 2: enqueue('Maya') -> Front -> ['Maya'] <- Rear\n"
                "Step 3: enqueue('Alex') -> Front -> ['Maya', 'Alex'] <- Rear\n"
                "Step 4: dequeue()       -> 'Maya' leaves first! Remaining: ['Alex']\n"
                "```\n\n"
                "```python\n"
                "from collections import deque\n"
                "print_queue = deque()\n"
                "print_queue.append('Document1')  # Enqueue at rear\n"
                "print_queue.append('Document2')  # Enqueue at rear\n"
                "first_printed = print_queue.popleft()  # Dequeue from front\n"
                "print('Printed first:', first_printed) # Document1\n"
                "```"
            ),
            "summary": "Items enter at the **Rear** (enqueue) and exit from the **Front** (dequeue), providing fair, first-come, first-served processing.",
            "code": "from collections import deque\nq = deque()\nq.append('Customer 1')\nq.append('Customer 2')\nprint(q.popleft()) # 'Customer 1' (FIFO)",
            "visual": "Front (Exit)                                Rear (Entry)\n     |                                            |\n     v                                            v\n[ Maya ] <--- [ Alex ] <--- [ Liam ] <--- [ New Person Joins ]\n(Leaves first)",
            "hint": "Use Python's `collections.deque` instead of a plain list for queues to get fast $O(1)$ removals from the front.",
            "test": "Which end does an item exit from in a Queue? A) Rear, B) Top, C) Front, D) Middle (Answer: C)"
        },
        "Recursion Fundamentals": {
            "definition": "Recursion is a technique where a function solves a problem by calling itself with smaller input values until it reaches an easy stopping condition called the **base case**.",
            "real_world": "Russian Nesting Dolls (Matryoshka). You open a big doll to find a smaller doll inside. You keep opening smaller dolls until you hit the tiny solid doll at the center that cannot be opened (the base case). Then you close them all back up!",
            "step_by_step": (
                "```text\n"
                "Calculating countdown(3):\n"
                "Step 1: countdown(3) prints 3, calls countdown(2)\n"
                "Step 2: countdown(2) prints 2, calls countdown(1)\n"
                "Step 3: countdown(1) prints 1, calls countdown(0)\n"
                "Step 4: countdown(0) hits base case (n <= 0)! Prints 'Blastoff!' and stops.\n"
                "```\n\n"
                "```python\n"
                "def countdown(n):\n"
                "    # Step 1: Base Case (The STOP sign!)\n"
                "    if n <= 0:\n"
                "        print('Blastoff! 🚀')\n"
                "        return\n"
                "    # Step 2: Do work\n"
                "    print(n)\n"
                "    # Step 3: Recursive call with smaller number\n"
                "    countdown(n - 1)\n\n"
                "countdown(3)  # Prints 3, 2, 1, Blastoff!\n"
                "```"
            ),
            "summary": "Every recursive function must have two essentials: 1) A base case to stop, and 2) Progress toward the base case with each call.",
            "code": "def factorial(n):\n    if n <= 1: # Base case\n        return 1\n    return n * factorial(n - 1) # Recursive call\n\nprint(factorial(4)) # 4 * 3 * 2 * 1 = 24",
            "visual": "Call Stack Memory:\n| countdown(0) -> Base Case reached! Returns |\n| countdown(1) -> Waiting for countdown(0)   |\n| countdown(2) -> Waiting for countdown(1)   |\n| countdown(3) -> Initial call               |\n+--------------------------------------------+",
            "hint": "Without a base case, a recursive function will call itself forever and crash with a `RecursionError`.",
            "test": "What happens if a recursive function forgets its base case? A) Runs once, B) Crashes with maximum recursion depth exceeded, C) Returns 0, D) Skips execution (Answer: B)"
        },
        "Tree Basics": {
            "definition": "A Tree is a hierarchical data structure composed of nodes connected by branches, starting from one single **root node** at the top and branching downwards.",
            "real_world": "A company organizational chart: The CEO sits at the very top (Root). Underneath are Vice Presidents (branch nodes), and at the bottom are individual employees with no subordinates (leaf nodes).",
            "step_by_step": (
                "```text\n"
                "Tree Structure Diagram:\n"
                "              [1: Root]\n"
                "              /       \\\n"
                "         [2: Left]   [3: Right]\n"
                "\n"
                "Step 1: The Root is node 1 (has no parent).\n"
                "Step 2: Node 1 has two children: node 2 (left) and node 3 (right).\n"
                "Step 3: Nodes 2 and 3 have no children, so they are called Leaf Nodes.\n"
                "```\n\n"
                "```python\n"
                "class TreeNode:\n"
                "    def __init__(self, val):\n"
                "        self.val = val\n"
                "        self.left = None\n"
                "        self.right = None\n\n"
                "root = TreeNode('Root')\n"
                "root.left = TreeNode('Left Child')\n"
                "root.right = TreeNode('Right Child')\n"
                "print('Root has left child:', root.left.val)\n"
                "```"
            ),
            "summary": "Trees organize data into parent-child relationships; a Binary Tree limits each parent node to at most two children (left and right).",
            "code": "class Node:\n    def __init__(self, val):\n        self.val = val\n        self.left = None\n        self.right = None\n\nroot = Node(10)\nroot.left = Node(5)\nroot.right = Node(15)",
            "visual": "          [ 10: Root Node ]\n            /            \\\n    [ 5: Child ]      [ 15: Child ]\n    (Leaf Node)        (Leaf Node)",
            "hint": "A leaf node is any node whose left and right pointers are both `None`.",
            "test": "What is the maximum number of children in a Binary Tree node? A) 1, B) 2, C) 3, D) Unlimited (Answer: B)"
        },
        "Tree Traversal": {
            "definition": "Tree traversal means systematically visiting every single node in a tree exactly once in a specific, predictable order.",
            "real_world": "Touring an amusement park: You visit the main entrance gate first, then all rides in the left section, and finally all rides in the right section so you do not miss anything.",
            "step_by_step": (
                "```text\n"
                "Sample Binary Tree:\n"
                "        (1)\n"
                "       /   \\\n"
                "     (2)   (3)\n"
                "\n"
                "1. Preorder  (Root -> Left -> Right): Visits: 1 -> 2 -> 3\n"
                "2. Inorder   (Left -> Root -> Right): Visits: 2 -> 1 -> 3\n"
                "3. Postorder (Left -> Right -> Root): Visits: 2 -> 3 -> 1\n"
                "```\n\n"
                "```python\n"
                "def inorder(node):\n"
                "    if node is None:\n"
                "        return\n"
                "    inorder(node.left)       # 1. Visit left branch\n"
                "    print(node.val, end=' ') # 2. Visit node itself\n"
                "    inorder(node.right)      # 3. Visit right branch\n"
                "```"
            ),
            "summary": "Inorder traversal visits Left $\\rightarrow$ Root $\\rightarrow$ Right; for a Binary Search Tree (BST), Inorder traversal prints all numbers in ascending order!",
            "code": "def preorder(node):\n    if node:\n        print(node.val, end=' ')\n        preorder(node.left)\n        preorder(node.right)",
            "visual": "Binary Tree:\n      1\n     / \\\n    2   3\nTraversals:\nPreorder:  1, 2, 3\nInorder:   2, 1, 3\nPostorder: 2, 3, 1",
            "hint": "Remember the word 'In' means Root is IN the middle: Left $\\rightarrow$ Root $\\rightarrow$ Right.",
            "test": "In Inorder traversal, which order is followed? A) Root-Left-Right, B) Left-Root-Right, C) Left-Right-Root, D) Right-Root-Left (Answer: B)"
        },
        "Recursive Practice": {
            "definition": "Recursive practice means applying recursive base cases and self-calling steps to solve real problems like summing numbers, counting leaves, or searching trees.",
            "real_world": "Counting the total number of books across all shelves in a library: Count the books on shelf 1, then ask your assistant to count the remaining shelves.",
            "step_by_step": (
                "```text\n"
                "Counting total leaves in a tree:\n"
                "Step 1: If current node is None -> Return 0 (Base Case 1)\n"
                "Step 2: If node has no children -> Return 1 (Base Case 2: It is a leaf!)\n"
                "Step 3: Otherwise -> Return count_leaves(left) + count_leaves(right)\n"
                "```\n\n"
                "```python\n"
                "def count_leaves(node):\n"
                "    if node is None:\n"
                "        return 0\n"
                "    if node.left is None and node.right is None:\n"
                "        return 1  # Leaf found!\n"
                "    return count_leaves(node.left) + count_leaves(node.right)\n"
                "```"
            ),
            "summary": "Break complex tree problems into subproblems: solve for the left child and right child, then combine their results.",
            "code": "def tree_sum(node):\n    if not node: return 0\n    return node.val + tree_sum(node.left) + tree_sum(node.right)",
            "visual": "Node(5) -> Sum = 5 + (Sum of Left Subtree) + (Sum of Right Subtree)",
            "hint": "Trust the recursive leap of faith: solve the base case, and assume your recursive call works for smaller branches.",
            "test": "What does `count_leaves` return for an empty tree (None)? A) 1, B) 0, C) -1, D) Error (Answer: B)"
        },
        "Tree Problems & Applications": {
            "definition": "A Binary Search Tree (BST) is a tree where for every node, all values on its left are smaller and all values on its right are larger, making searches extremely fast.",
            "real_world": "The number guessing game: 'Guess a secret number between 1 and 100.' If you guess 50 and I say 'Higher', you immediately eliminate numbers 1 through 50 in one step!",
            "step_by_step": (
                "```text\n"
                "Searching for number 7 in a Binary Search Tree:\n"
                "              [5]\n"
                "             /   \\\n"
                "           [3]   [8]\n"
                "                 /\n"
                "               [7]\n"
                "\n"
                "Step 1: Start at root (5). 7 is greater than 5 -> Go RIGHT to node 8.\n"
                "Step 2: At node 8. 7 is smaller than 8 -> Go LEFT to node 7.\n"
                "Step 3: Found 7! It only took 2 comparisons instead of checking all 4 nodes.\n"
                "```\n\n"
                "```python\n"
                "def search_bst(node, target):\n"
                "    if node is None or node.val == target:\n"
                "        return node is not None\n"
                "    if target < node.val:\n"
                "        return search_bst(node.left, target)  # Search left\n"
                "    return search_bst(node.right, target)     # Search right\n"
                "```"
            ),
            "summary": "BSTs cut the remaining search space in half at each step, achieving fast $O(\\log n)$ search, insert, and delete operations.",
            "code": "def insert_bst(node, val):\n    if not node: return Node(val)\n    if val < node.val:\n        node.left = insert_bst(node.left, val)\n    else:\n        node.right = insert_bst(node.right, val)\n    return node",
            "visual": "Rule: (All values on Left < Node < All values on Right)\nExample:       [ 10 ]\n              /      \\\n           [ 4 ]    [ 18 ]",
            "hint": "If a BST becomes completely unbalanced (like a straight line 1 -> 2 -> 3), search slows down to $O(n)$.",
            "test": "In a BST, where do values smaller than the root go? A) Right, B) Left, C) Leaves only, D) Root (Answer: B)"
        },
        "Algorithm Complexity & Big-O": {
            "definition": "Big-O notation is a simple yardstick that measures how the execution time or memory of an algorithm grows as the input data size ($n$) becomes larger.",
            "real_world": "Looking up a contact in your phone takes the exact same fraction of a second whether you have 10 contacts or 1,000 contacts ($O(1)$). But reading a physical book line by line takes 10 times longer if the book has 10 times more pages ($O(n)$).",
            "step_by_step": (
                "```text\n"
                "Big-O Efficiency Ranking (Fastest to Slowest):\n"
                "1. O(1)      - Constant Time: Instant! (e.g., getting list[0])\n"
                "2. O(log n)  - Logarithmic: Cuts problem in half each step (Binary Search)\n"
                "3. O(n)      - Linear: Checks every single item once (for-loop over list)\n"
                "4. O(n^2)    - Quadratic: Nested loops (Comparing every item to every other item)\n"
                "```\n\n"
                "```python\n"
                "# O(1) Constant Time - Instant!\n"
                "def get_first_item(items):\n"
                "    return items[0]\n\n"
                "# O(n) Linear Time - Takes longer as items list grows\n"
                "def find_item(items, target):\n"
                "    for x in items:\n"
                "        if x == target:\n"
                "            return True\n"
                "    return False\n"
                "```"
            ),
            "summary": "Aim for $O(1)$ and $O(\\log n)$ algorithms; avoid $O(n^2)$ when working with large datasets.",
            "code": "# O(1) Constant\nx = arr[0]\n\n# O(n) Linear\nfor item in arr: print(item)\n\n# O(n^2) Quadratic\nfor a in arr:\n    for b in arr: print(a, b)",
            "visual": "Time Needed\n   ^\n   |         / O(n^2) - Avoid for big data!\n   |        / \n   |       /   O(n) - Linear\n   |      /--_ O(log n) - Fast\n   |  ---'---- O(1) - Instant\n   +-----------------------------> Input Size (n)",
            "hint": "When counting Big-O, drop constant numbers: $O(2n)$ simply becomes $O(n)$.",
            "test": "What is the time complexity of Binary Search? A) O(1), B) O(n), C) O(log n), D) O(n^2) (Answer: C)"
        },

        # =====================================================================
        # Course 3: AI301 Machine Learning Fundamentals
        # =====================================================================
        "Statistical Learning & Feature Engineering": {
            "definition": "Feature engineering is the process of cleaning, transforming, and converting raw information into clean numeric measurements (features) that machine learning algorithms can learn from.",
            "real_world": "Making fruit salad: You do not toss whole unpeeled pineapples with leaves into a bowl. You wash, peel, and chop them into bite-sized pieces first. Feature engineering is peeling and preparing data for the AI model!",
            "step_by_step": (
                "```text\n"
                "Transforming House Data into Machine Learning Features:\n"
                "Step 1 (Raw Input): '3 bedrooms, large garden, built in 2014'\n"
                "Step 2 (Feature Engineering Transformations):\n"
                "       - num_bedrooms = 3 (Numeric)\n"
                "       - has_garden   = 1 (Binary Yes=1, No=0)\n"
                "       - house_age    = 2026 - 2014 = 12 years\n"
                "Step 3 (Clean Table): The model now receives [3, 1, 12] as clean numeric inputs!\n"
                "```"
            ),
            "summary": "High-quality features allow simple machine learning models to make great predictions; always scale numbers and convert text into numbers.",
            "code": "# Converting text categories to numbers (One-Hot / Binary)\nhas_pool = 1 if user_input == 'yes' else 0\nscaled_income = (income - min_inc) / (max_inc - min_inc)",
            "visual": "Raw Text / Dirty Data ---> [ Feature Engineering ] ---> Clean Numeric Features [x1, x2, x3]",
            "hint": "Features should be scaled to a similar range (like 0 to 1) so large numbers do not overpower small numbers.",
            "test": "Why do we convert text categories into numbers in Machine Learning? A) To save disk space, B) Computers and math algorithms calculate with numbers, C) Text is illegal in Python, D) To encrypt data (Answer: B)"
        },
        "Linear & Polynomial Regression": {
            "definition": "Linear regression finds the best-fitting straight line through data points to predict a continuous numeric number (like house price, salary, or temperature).",
            "real_world": "Predicting your electricity bill based on air conditioning usage. The more hours you run the AC, the higher your bill climbs in a straight, steady upward trend line.",
            "step_by_step": (
                "```text\n"
                "Predicting Lemonade Sales based on Temperature:\n"
                "Step 1 (Observed Data):\n"
                "       - At 20°C: Sold 40 cups\n"
                "       - At 25°C: Sold 50 cups\n"
                "       - At 30°C: Sold 60 cups\n"
                "Step 2 (Discovered Linear Trend): Cups Sold = 2 * Temperature\n"
                "Step 3 (Prediction for Tomorrow at 35°C):\n"
                "       Predicted Sales = 2 * 35 = 70 cups!\n"
                "```"
            ),
            "summary": "Linear regression fits a straight trend line ($y = mx + b$); polynomial regression bends the line to fit curves when data changes non-linearly.",
            "code": "# Simple Linear Formula: y = slope * x + intercept\ndef predict_sales(temp):\n    slope = 2.0\n    intercept = 0.0\n    return (slope * temp) + intercept\n\nprint('Expected sales at 35C:', predict_sales(35)) # 70",
            "visual": "Cups Sold\n   ^\n70 |               * (35°C, 70)\n60 |           * (30°C, 60)   / Best Fit Line\n50 |       * (25°C, 50)     /\n40 |   * (20°C, 40)       /\n   +--------------------------> Temperature (°C)",
            "hint": "Linear regression predicts continuous numeric values (like dollar amounts or temperatures), not categories.",
            "test": "What type of line does simple linear regression fit? A) Circle, B) Straight line, C) Step function, D) Sine wave (Answer: B)"
        },
        "Logistic Regression & Classification": {
            "definition": "Logistic regression predicts the probability (between 0% and 100%) that an item belongs to a specific category (such as 'Spam' vs 'Not Spam' or 'Pass' vs 'Fail').",
            "real_world": "A medical test checking for strep throat: the doctor takes measurements and calculates an 85% probability of infection ($Yes$), deciding to prescribe medicine.",
            "step_by_step": (
                "```text\n"
                "Email Spam Filter Classification:\n"
                "Step 1 (Input Email): 'Congratulations! You won $1,000,000 cash prize!'\n"
                "Step 2 (Calculate Probability): Model scores keywords -> Probability of Spam = 92%\n"
                "Step 3 (Threshold Decision at 50%):\n"
                "       Because 92% >= 50%, the email is classified as SPAM and moved to Junk!\n"
                "```"
            ),
            "summary": "Despite having 'regression' in its name, logistic regression is used for **classification** by mapping scores through an S-shaped curve (sigmoid) between 0 and 1.",
            "code": "import math\ndef sigmoid(z):\n    return 1 / (1 + math.exp(-z))\n\nprob = sigmoid(2.5)\nprint(f'Spam probability: {prob:.1%}') # ~92.4%\nis_spam = prob >= 0.5",
            "visual": "Probability\n 1.0 |           _---\"\"\"\"\"\" (Class: 1 / Yes)\n     |         / \n 0.5 | -------/------- (Threshold: 50%)\n     |       / \n 0.0 | \"\"\"\"--         (Class: 0 / No)\n     +-------------------------> Score",
            "hint": "The decision threshold is usually 0.5 (50%), but can be adjusted higher or lower depending on how cautious you need to be.",
            "test": "What range of values does the logistic sigmoid function output? A) -1 to +1, B) 0 to 1, C) 0 to infinity, D) Any integer (Answer: B)"
        },
        "Decision Trees & Random Forests": {
            "definition": "A Decision Tree is a flowchart of yes/no questions that leads to an answer. A Random Forest combines the votes of many different decision trees to reach a reliable group decision.",
            "real_world": "Playing the game '20 Questions': 'Is it an animal? Yes. Does it fly? No. Does it bark? Yes. -> It is a dog!' A Random Forest is like asking 10 of your friends to play too and taking the majority vote.",
            "step_by_step": (
                "```text\n"
                "Deciding Whether to Play Outdoor Sports:\n"
                "Step 1: Question 1: Is it raining?\n"
                "        - YES -> Stay inside.\n"
                "        - NO  -> Go to Question 2.\n"
                "Step 2: Question 2: Is temperature > 38°C (too hot)?\n"
                "        - YES -> Stay inside in the AC.\n"
                "        - NO  -> Go outside and play soccer!\n"
                "```"
            ),
            "summary": "Decision trees are easy for humans to understand because they read like simple rules; Random Forests prevent mistakes by averaging many trees together.",
            "code": "# Conceptual rule matching a decision tree leaf\ndef should_play(is_raining, temp):\n    if is_raining:\n        return 'Stay Inside'\n    elif temp > 38:\n        return 'Stay Inside'\n    return 'Play Soccer!'",
            "visual": "                [ Is it raining? ]\n                 /              \\\n             YES                 NO\n             /                     \\\n     [ Stay Inside ]       [ Temperature > 38°C? ]\n                             /               \\\n                           YES                NO\n                           /                    \\\n                   [ Stay Inside ]       [ Play Soccer! ]",
            "hint": "Single decision trees can memorize training data too closely (overfitting); Random Forests solve this by training on random subsets.",
            "test": "What is a Random Forest? A) A single tree with many leaves, B) An ensemble of multiple decision trees voting together, C) An unorganized dataset, D) A database index (Answer: B)"
        },
        "Model Evaluation & Validation": {
            "definition": "Model evaluation is testing how accurately your AI model performs on fresh, unseen test questions that it was never allowed to see during training.",
            "real_world": "Studying for a school final exam: If you only memorize the exact practice quiz questions, you will struggle when the real exam has new questions. You need a mock test with new questions to measure real understanding!",
            "step_by_step": (
                "```text\n"
                "Evaluating an AI Medical Diagnostic Model on 100 New Patients:\n"
                "Step 1: Model diagnosed 45 sick patients correctly (True Positives).\n"
                "Step 2: Model diagnosed 50 healthy patients correctly (True Negatives).\n"
                "Step 3: Model made 5 mistakes (False Alarms).\n"
                "Step 4: Accuracy = (45 + 50) / 100 = 95% Correct!\n"
                "```"
            ),
            "summary": "Never test your model on the same data it learned from; always split data into a training set (to learn) and a test set (to evaluate).",
            "code": "# Train-Test Evaluation Metric Calculation\ncorrect_predictions = 95\ntotal_test_samples = 100\naccuracy = correct_predictions / total_test_samples\nprint(f'Model Test Accuracy: {accuracy:.1%}') # 95.0%",
            "visual": "All Data (100%)\n[ ======= Training Set (80%): Model Learns ======= ] [ === Test Set (20%): Evaluated === ]",
            "hint": "If a model scores 100% on training data but only 50% on test data, it has suffered from **overfitting** (memorization without understanding).",
            "test": "Why must we evaluate models on a separate test set? A) To make code run faster, B) To test generalization on unseen data, C) Because Python requires it, D) To compress data (Answer: B)"
        },
        "Clustering & K-Means": {
            "definition": "Clustering is an unsupervised learning method that automatically groups similar items together into clusters without needing any pre-existing labels.",
            "real_world": "Sorting clothes from a laundry basket: without checking any brand tags, you naturally group t-shirts into one pile, socks into another pile, and towels into a third pile based on size and texture.",
            "step_by_step": (
                "```text\n"
                "Grouping Online Shoppers into 3 Customer Types (K=3):\n"
                "Step 1: Pick 3 starting center points in the customer spending data.\n"
                "Step 2: Assign each customer to their closest center:\n"
                "       - Group 1: Deal hunters (low spending, frequent visits)\n"
                "       - Group 2: Regular shoppers (medium spending, weekly visits)\n"
                "       - Group 3: Luxury buyers (high spending, seasonal visits)\n"
                "Step 3: Move center points to the middle of each group and repeat until stable!\n"
                "```"
            ),
            "summary": "K-Means finds $K$ center points and groups nearby data points around them automatically without human labeling.",
            "code": "# Conceptual K-Means cluster assignment\ndef find_closest_cluster(point, centroids):\n    distances = [abs(point - c) for c in centroids]\n    return distances.index(min(distances)) # Return index of closest center",
            "visual": "Cluster A: ( * * * )       Cluster B: ( # # # )\n         Center A                     Center B\n                     Cluster C: ( @ @ @ )\n                              Center C",
            "hint": "You must choose the number of clusters ($K$) beforehand, often by using the 'Elbow Method' to find the sweet spot.",
            "test": "Is K-Means supervised or unsupervised learning? A) Supervised, B) Unsupervised (no labels needed), C) Semi-supervised, D) Reinforcement (Answer: B)"
        },
        "Dimensionality Reduction & PCA": {
            "definition": "Principal Component Analysis (PCA) simplifies large datasets with dozens of variables down into 2 or 3 essential summary variables while keeping the most important information.",
            "real_world": "A 2D shadow of your 3D hand on a wall. Your hand has depth, width, and height (3 dimensions), but its flat 2D shadow still clearly shows all 5 fingers and hand gestures!",
            "step_by_step": (
                "```text\n"
                "Simplifying Car Specifications:\n"
                "Step 1: You have 10 measurements for each car: horsepower, engine volume, weight, top speed, etc.\n"
                "Step 2: PCA discovers that horsepower and weight change together closely.\n"
                "Step 3: Combines the 10 measurements into 2 summary axes: 'Engine Power' and 'Fuel Efficiency'.\n"
                "Step 4: Now you can easily plot all cars on a simple 2D screen chart!\n"
                "```"
            ),
            "summary": "PCA removes duplicate and redundant information, making big datasets easy to visualize and faster to process.",
            "code": "# PCA compresses many correlated variables into primary directions of variation\n# Preserves maximum variance with fewer dimensions",
            "visual": "3D Data Cloud (x, y, z) ===[ PCA Compression ]===> 2D Plot (Component 1, Component 2)\n(Easy to view on any computer screen!)",
            "hint": "PCA is fantastic for visualizing complex datasets that have more than 3 variables on a 2D screen.",
            "test": "What is the primary benefit of PCA? A) Increases file size, B) Reduces the number of variables while preserving key variance, C) Adds labels, D) Encrypts data (Answer: B)"
        },
        "Neural Networks & Backpropagation": {
            "definition": "A Neural Network is a computer program inspired by brain cells that processes signals through layers of connected math nodes. Backpropagation is how it learns from mistakes by tuning connection weights backwards.",
            "real_world": "Practicing basketball free throws: You shoot the ball and miss 2 inches to the left (error). Your brain analyzes the miss and adjusts your wrist angle backwards before the next shot. Over 50 practice shots, you adjust until you swish consistently!",
            "step_by_step": (
                "```text\n"
                "Recognizing a Handwritten Digit '7':\n"
                "Step 1 (Forward Pass): The 28x28 image pixels enter the input layer.\n"
                "Step 2 (Hidden Layers): Multiplies signals by connection weights and sums them up.\n"
                "Step 3 (Guess & Error): Network guesses '1' with high error (it was actually a 7!).\n"
                "Step 4 (Backpropagation): Calculates the error and adjusts weights backwards\n"
                "       so next time the guess moves closer to '7'.\n"
                "```"
            ),
            "summary": "The forward pass makes a prediction; backpropagation calculates the mistake and updates connection weights backwards so the network gets smarter.",
            "code": "# Forward pass: output = activation(weight * input + bias)\n# Backward pass (Backprop): adjust weight based on (output - target) error",
            "visual": "[ Input Pixels ] ---> [ Hidden Layer Nodes ] ---> [ Output Guess: '7' ]\n       ^                        ^                        |\n       |-- Adjusted Backwards --|-- Error Calculated <---+\n           (Backpropagation)",
            "hint": "Neural networks need many training examples and small adjustment steps (learning rate) to learn smoothly without overshooting.",
            "test": "What is the purpose of backpropagation? A) To generate random numbers, B) To adjust weights backwards based on prediction error, C) To shut down the network, D) To print the output (Answer: B)"
        },

        # =====================================================================
        # Course 4: CS302 Database Management Systems (DBMS)
        # =====================================================================
        "Relational Data Model & Schemas": {
            "definition": "The relational data model organizes information into two-dimensional tables made of rows (individual records) and columns (attributes), connected by unique ID keys.",
            "real_world": "A digital spreadsheet for a school. One sheet is 'Students' with student ID, name, and major. Each student has a unique ID number that links them to their course grades.",
            "step_by_step": (
                "```sql\n"
                "-- Step 1: Create the students table schema\n"
                "CREATE TABLE students (\n"
                "    student_id INT PRIMARY KEY,\n"
                "    full_name VARCHAR(50),\n"
                "    major VARCHAR(30)\n"
                ");\n\n"
                "-- Step 2: Insert two sample student rows\n"
                "INSERT INTO students VALUES (101, 'Maya Lin', 'Computer Science');\n"
                "INSERT INTO students VALUES (102, 'Alex Roy', 'Data Science');\n\n"
                "-- Step 3: View the records\n"
                "SELECT * FROM students;\n"
                "```\n\n"
                "*Result Table:*\n"
                "| student_id | full_name | major            |\n"
                "| :--------- | :-------- | :--------------- |\n"
                "| 101        | Maya Lin  | Computer Science |\n"
                "| 102        | Alex Roy  | Data Science     |"
            ),
            "summary": "A schema defines table columns and rules; each row represents one distinct item identified by a unique Primary Key.",
            "code": "CREATE TABLE courses (\n    course_id INT PRIMARY KEY,\n    title VARCHAR(100),\n    credits INT\n);\nINSERT INTO courses VALUES (1, 'Python Basics', 3);",
            "visual": "Table: students\n+------------+-----------+------------------+\n| student_id | full_name | major            | <- Columns (Attributes)\n+------------+-----------+------------------+\n| 101        | Maya Lin  | Computer Science | <- Row 1 (Record)\n| 102        | Alex Roy  | Data Science     | <- Row 2 (Record)\n+------------+-----------+------------------+",
            "hint": "Every table should have a Primary Key column (like `student_id`) so that every row can be uniquely identified.",
            "test": "What is a row in a relational database table called? A) Attribute, B) Record or Tuple, C) Schema, D) Column (Answer: B)"
        },
        "SQL DDL & Integrity Constraints": {
            "definition": "Data Definition Language (DDL) commands (`CREATE`, `ALTER`, `DROP`) build and modify table structures, while Integrity Constraints enforce data quality rules (like forbidding empty values or negative numbers).",
            "real_world": "Filling out an online registration form: If you try to submit without entering your email address, or enter a negative age like -5, the form blocks you (`NOT NULL` and `CHECK` constraints).",
            "step_by_step": (
                "```sql\n"
                "-- Step 1: Build table with safety constraints\n"
                "CREATE TABLE user_accounts (\n"
                "    user_id INT PRIMARY KEY,\n"
                "    username VARCHAR(50) NOT NULL,        -- Cannot be blank!\n"
                "    email VARCHAR(100) UNIQUE,            -- No duplicates allowed!\n"
                "    balance DECIMAL(10,2) CHECK (balance >= 0) -- Cannot be negative!\n"
                ");\n\n"
                "-- Step 2: Valid insertion works!\n"
                "INSERT INTO user_accounts VALUES (1, 'maya99', 'maya@univ.edu', 50.00);\n\n"
                "-- Step 3: An invalid negative balance is BLOCKED automatically by the database!\n"
                "-- INSERT INTO user_accounts VALUES (2, 'bad_row', 'bad@univ.edu', -10.00);\n"
                "-- Error: CHECK constraint failed!\n"
                "```"
            ),
            "summary": "Constraints (`NOT NULL`, `UNIQUE`, `CHECK`, `FOREIGN KEY`) act as automated guardrails to keep database data clean and reliable.",
            "code": "CREATE TABLE enrollments (\n    enrollment_id INT PRIMARY KEY,\n    student_id INT NOT NULL,\n    course_id INT NOT NULL,\n    grade CHAR(1) DEFAULT 'I'\n);",
            "visual": "+-------------------+------------------------------------------+\n| Constraint Name   | Rule Enforced                            |\n+-------------------+------------------------------------------+\n| PRIMARY KEY       | Unique identifier; cannot be empty (NULL)|\n| NOT NULL          | Field must have a value                  |\n| UNIQUE            | No two rows can have the same value      |\n| CHECK             | Value must satisfy a custom math rule    |\n+-------------------+------------------------------------------+",
            "hint": "A Foreign Key links a column in one table to the Primary Key of another table, ensuring references are always valid.",
            "test": "Which constraint ensures that no two rows have the same value in a column? A) NOT NULL, B) UNIQUE, C) CHECK, D) DEFAULT (Answer: B)"
        },
        "SQL DML & Aggregation Queries": {
            "definition": "Data Manipulation Language (DML) lets you query (`SELECT`), add (`INSERT`), update (`UPDATE`), and delete (`DELETE`) records. Aggregations summarize groups of rows using functions like `COUNT`, `SUM`, and `AVG`.",
            "real_world": "Checking the class test statistics: Rather than manually reading through all 100 student exam scores, the teacher queries the system: 'What is the average score and highest score in Class A?'",
            "step_by_step": (
                "```sql\n"
                "-- Step 1: Look at the student grades table\n"
                "-- Alice: 85, Bob: 90, Charlie: 95\n\n"
                "-- Step 2: Write an aggregation query\n"
                "SELECT \n"
                "    COUNT(*) AS total_students,\n"
                "    AVG(score) AS average_score,\n"
                "    MAX(score) AS highest_score\n"
                "FROM student_scores;\n"
                "```\n\n"
                "*Result Table:*\n"
                "| total_students | average_score | highest_score |\n"
                "| :------------- | :------------ | :------------ |\n"
                "| 3              | 90.0          | 95            |"
            ),
            "summary": "Use `SELECT ... FROM ... WHERE` to filter rows, and combine with `GROUP BY` and `AVG()` / `COUNT()` to calculate summaries.",
            "code": "-- Filter and group by department\nSELECT department, COUNT(*) AS student_count\nFROM students\nGROUP BY department\nHAVING COUNT(*) >= 5;",
            "visual": "Raw Rows: [85], [90], [95] ===[ AVG() Function ]===> Single Summary: [90.0]",
            "hint": "Use `WHERE` to filter individual rows before grouping; use `HAVING` to filter groups after aggregating.",
            "test": "Which SQL function counts the total number of rows? A) SUM(), B) COUNT(), C) TOTAL(), D) ROWS() (Answer: B)"
        },
        "Complex SQL Joins & Subqueries": {
            "definition": "A JOIN combines columns from two separate tables into one unified view by matching a shared key. A subquery is a query nested inside another query.",
            "real_world": "Your online shopping order receipt: The receipt combines your name from the 'Customers' table with the items you bought from the 'Order Items' table by matching your Order Number.",
            "step_by_step": (
                "```sql\n"
                "-- Table 1: students (id, name)\n"
                "-- Table 2: grades (student_id, course, grade)\n\n"
                "-- Step 1: Combine both tables using INNER JOIN\n"
                "SELECT \n"
                "    students.name,\n"
                "    grades.course,\n"
                "    grades.grade\n"
                "FROM students\n"
                "INNER JOIN grades ON students.id = grades.student_id;\n"
                "```\n\n"
                "*Result Table:*\n"
                "| name     | course          | grade |\n"
                "| :------- | :-------------- | :---- |\n"
                "| Maya Lin | Data Structures | A     |\n"
                "| Alex Roy | Python Basics   | B     |"
            ),
            "summary": "`INNER JOIN` only shows rows that have matches in both tables; `LEFT JOIN` keeps all rows from the left table even if the right table has no match.",
            "code": "SELECT s.name, c.title\nFROM students s\nLEFT JOIN enrollments e ON s.id = e.student_id\nLEFT JOIN courses c ON e.course_id = c.id;",
            "visual": "Table A (Students)       Table B (Grades)\n[ ID: 101 | Maya ]  +---> [ StudentID: 101 | Grade: 'A' ]\n                    |\nCombined Result:   [ Maya | Grade: 'A' ]",
            "hint": "Always check that your `ON` condition matches the foreign key to the primary key (`ON students.id = grades.student_id`).",
            "test": "Which join returns all rows from Table A, plus matching rows from Table B? A) INNER JOIN, B) LEFT JOIN, C) RIGHT JOIN, D) CROSS JOIN (Answer: B)"
        },
        "Relational Algebra Operations": {
            "definition": "Relational Algebra is the formal mathematical foundation behind SQL. It defines core operations like Selection (filter rows $\\sigma$), Projection (pick columns $\\pi$), and Join ($\\bowtie$).",
            "real_world": "Ordering at a coffee shop: Selection is choosing only hot drinks (filtering rows). Projection is printing only the drink name and price on the receipt (selecting specific columns).",
            "step_by_step": (
                "```text\n"
                "Task: Find names of students majoring in 'Computer Science'.\n"
                "Step 1: Selection (sigma) - Filter rows where major = 'CS':\n"
                "       sigma_{major = 'CS'}(students)\n"
                "Step 2: Projection (pi) - Pick only the student_name column:\n"
                "       pi_{student_name}(filtered_result)\n"
                "Step 3: Equivalent SQL Query:\n"
                "```\n\n"
                "```sql\n"
                "SELECT student_name \n"
                "FROM students \n"
                "WHERE major = 'Computer Science';\n"
                "```"
            ),
            "summary": "Selection ($\\sigma$) chooses rows; Projection ($\\pi$) chooses columns; SQL translates your queries into these relational algebra steps.",
            "code": "-- Projection (pi) and Selection (sigma) in SQL\nSELECT name, major           -- Projection: pi_{name, major}\nFROM students\nWHERE student_id = 101;     -- Selection: sigma_{student_id=101}",
            "visual": "Table Rows (Vertical)   ---[ Selection (sigma) ]---> Keeps matching rows\nTable Columns (Horizontal) ---[ Projection (pi)  ]---> Keeps matching columns",
            "hint": "Sigma ($\sigma$) starts with 'S' for **Select rows**; Pi ($\pi$) starts with 'P' for **Project columns**.",
            "test": "In Relational Algebra, what does Projection (pi) do? A) Filters rows, B) Chooses specific columns, C) Deletes tables, D) Sorts data (Answer: B)"
        },
        "Functional Dependencies & 1NF-3NF": {
            "definition": "Database Normalization is the process of splitting tables into clean normal forms (1NF, 2NF, 3NF) to eliminate repeated duplicate data and prevent accidental deletion errors.",
            "real_world": "Storing department office addresses: If you repeat 'Sales Department: Room 402' on 200 employee records, moving the office requires updating 200 rows! Normalization splits this into two clean tables: Employees and Departments.",
            "step_by_step": (
                "```text\n"
                "Before Normalization (Duplicate department data repeated):\n"
                "| emp_id | emp_name | dept_id | dept_name |\n"
                "| 1      | Maya     | D1      | Marketing |\n"
                "| 2      | Alex     | D1      | Marketing | <- Duplicate!\n\n"
                "After 3NF Normalization (Clean split connected by dept_id):\n"
                "Table 1: employees (emp_id, emp_name, dept_id)\n"
                "Table 2: departments (dept_id, dept_name)\n"
                "Now changing a department name only updates ONE row in Table 2!\n"
                "```"
            ),
            "summary": "1NF eliminates lists inside cells; 2NF removes partial key dependencies; 3NF ensures columns depend *only* on the primary key.",
            "code": "-- Table in 3NF: department details live in their own dedicated table\nCREATE TABLE departments (\n    dept_id VARCHAR(5) PRIMARY KEY,\n    dept_name VARCHAR(50)\n);\nCREATE TABLE employees (\n    emp_id INT PRIMARY KEY,\n    name VARCHAR(50),\n    dept_id VARCHAR(5) REFERENCES departments(dept_id)\n);",
            "visual": "Messy Table with Duplicates ---> [ Normalization ] ---> Table A (Employees) + Table B (Departments)\n                                                            \\__________________________/",
            "hint": "Remember the 3NF mantra: Every column must depend on the key, the whole key, and nothing but the key!",
            "test": "What problem does normalization solve? A) Makes database files larger, B) Eliminates duplicate data and update anomalies, C) Encrypts passwords, D) Removes primary keys (Answer: B)"
        },
        "Indexing & B-Tree Storage": {
            "definition": "An Index is a fast lookup guide (usually structured as a balanced B-Tree) that allows the database to find matching rows in milliseconds without reading the entire table.",
            "real_world": "The alphabetical index at the back of a 1,000-page textbook. If you want to find 'Database Index', you flip to letter 'D' in the back and jump directly to page 340, rather than reading all 1,000 pages from start to finish!",
            "step_by_step": (
                "```sql\n"
                "-- Step 1: Without an index, searching 1,000,000 users checks all 1,000,000 rows!\n"
                "-- SELECT * FROM users WHERE email = 'maya@univ.edu'; (Slow!)\n\n"
                "-- Step 2: Create a B-Tree index on the email column\n"
                "CREATE INDEX idx_users_email ON users(email);\n\n"
                "-- Step 3: Now the database traverses a small B-Tree in only 3 to 4 fast steps!\n"
                "SELECT * FROM users WHERE email = 'maya@univ.edu'; -- Fast!\n"
                "```\n\n"
                "*B-Tree Traversal:*\n"
                "Root node checks first letter -> branches to 'M' node -> finds exact row pointer immediately!"
            ),
            "summary": "Indexes make searches and queries lightning-fast, but slightly slow down inserts and updates because the index must be kept up to date.",
            "code": "-- Create index to speed up student lookups by email\nCREATE INDEX idx_student_email ON students(email);",
            "visual": "B-Tree Index Structure:\n                  [ 'M' ]\n                 /       \\\n         [ 'F' ]           [ 'S' ]\n        /       \\         /       \\\n     ['A'-'E'] ['G'-'L'] ['N'-'R'] ['T'-'Z']",
            "hint": "Add indexes to columns you search often (like `email` or `user_id`), but do not index every single column unnecessarily.",
            "test": "Why does an index make searches faster? A) Compresses table text, B) Avoids scanning every row using a balanced search tree, C) Deletes unused rows, D) Removes duplicate data (Answer: B)"
        },
        "Transactions, ACID & Concurrency": {
            "definition": "A transaction is a group of database actions executed as one single all-or-nothing unit. It follows ACID rules to ensure data is never lost or corrupted.",
            "real_world": "Transferring $50 from your bank account to a friend's account. Step 1: Deduct $50 from you. Step 2: Add $50 to your friend. If the bank power cuts out after Step 1, the transaction rolls back so your $50 does not disappear into thin air!",
            "step_by_step": (
                "```sql\n"
                "-- Step 1: Start the protected transaction\n"
                "BEGIN TRANSACTION;\n\n"
                "-- Step 2: Deduct $50 from Maya's account\n"
                "UPDATE accounts SET balance = balance - 50.00 WHERE account_id = 101;\n\n"
                "-- Step 3: Add $50 to Alex's account\n"
                "UPDATE accounts SET balance = balance + 50.00 WHERE account_id = 102;\n\n"
                "-- Step 4: If both steps succeeded, save permanently\n"
                "COMMIT;\n"
                "-- (If an error occurs, ROLLBACK undoes both steps back to the start!)\n"
                "```"
            ),
            "summary": "ACID stands for **Atomicity** (all or nothing), **Consistency** (rules upheld), **Isolation** (transactions do not interfere), and **Durability** (saved permanently).",
            "code": "BEGIN TRANSACTION;\nUPDATE inventory SET stock = stock - 1 WHERE item_id = 55;\nINSERT INTO orders (item_id, user_id) VALUES (55, 99);\nCOMMIT;",
            "visual": "Transaction: [ Deduct $50 ] + [ Credit $50 ]\n      |                               |\n   SUCCESS? ----------------------> COMMIT (Saved!)\n   FAILURE? ----------------------> ROLLBACK (Undone completely!)",
            "hint": "Atomicity means either 100% of the steps succeed, or 0% are saved. There is never a half-completed transaction.",
            "test": "What does the 'A' in ACID stand for? A) Accuracy, B) Atomicity (All or nothing), C) Automatic, D) Authorization (Answer: B)"
        }
    }

    @classmethod
    def get_topic_info(cls, topic_title: str) -> Dict[str, Any]:
        """
        Retrieves comprehensive topic knowledge with case-insensitive and partial matching.
        """
        clean_title = (topic_title or "").strip()
        if not clean_title:
            return cls.TOPIC_KNOWLEDGE["Variables, Data Types & Basic I/O"]

        # Exact match
        if clean_title in cls.TOPIC_KNOWLEDGE:
            return cls.TOPIC_KNOWLEDGE[clean_title]

        # Case-insensitive match
        lower_title = clean_title.lower()
        for k, v in cls.TOPIC_KNOWLEDGE.items():
            if k.lower() == lower_title:
                return v

        # Partial match
        for k, v in cls.TOPIC_KNOWLEDGE.items():
            if k.lower() in lower_title or lower_title in k.lower():
                return v

        # Fallback default
        return cls.TOPIC_KNOWLEDGE["Variables, Data Types & Basic I/O"]

    @classmethod
    def respond(
        cls,
        topic_title: str,
        user_message: str = "",
        mastery_score: float = 50.0,
        action: str = "",
        quick_action: str = "",
        modality: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generates beginner-friendly pedagogical responses for chat inquiries and quick actions.
        """
        action = quick_action or action or modality or ""
        info = cls.get_topic_info(topic_title)
        level_label = "Beginner (Scaffolded)" if mastery_score < 40 else ("Intermediate" if mastery_score < 80 else "Advanced")

        if action in ["explain_simply", "explain"]:
            reply = (
                f"### 💡 Simple Explanation: {topic_title}\n\n"
                f"**1. What is it?**\n{info['definition']}\n\n"
                f"**2. Real-World Example:**\n{info['real_world']}\n\n"
                f"**3. Quick Summary:**\n{info['summary']}"
            )
            followups = ["Give an example", "Give a hint", "Test me", "Summarize"]

        elif action in ["give_example", "example"]:
            reply = (
                f"### 💻 Step-by-Step Example: {topic_title}\n\n"
                f"{info['step_by_step']}\n\n"
                f"**Key Rule to Remember:**\n{info['hint']}"
            )
            followups = ["Explain simply", "Give another example", "Test me", "Summarize"]

        elif action in ["give_hint", "hint"]:
            reply = (
                f"### 🔍 Helpful Beginner Hint: {topic_title}\n\n"
                f"💡 **Pro-Tip:** {info['hint']}\n\n"
                f"**Remember:** {info['summary']}"
            )
            followups = ["Give an example", "Explain simply", "Test me"]

        elif action in ["test_me", "test"]:
            reply = (
                f"### 🎯 Quick Practice Check: {topic_title}\n\n"
                f"{info['test']}\n\n"
                f"Think through your answer, and try typing your response below to check your understanding!"
            )
            followups = ["Explain simply", "Give a hint", "Give an example"]

        elif action == "summarize":
            reply = (
                f"### 📋 Key Takeaways: {topic_title}\n\n"
                f"1. **Core Concept:** {info['definition']}\n"
                f"2. **Real-World Analogy:** {info['real_world']}\n"
                f"3. **Summary:** {info['summary']}"
            )
            followups = ["Give an example", "Test me", "Explain simply"]

        else:
            # Full beginner-friendly structured explanation
            reply = (
                f"### 📖 {topic_title} — Beginner's Learning Guide\n\n"
                f"#### 1. What Is It? (Short Definition)\n"
                f"{info['definition']}\n\n"
                f"#### 2. Familiar Real-World Example\n"
                f"{info['real_world']}\n\n"
                f"#### 3. Small Step-by-Step Example\n"
                f"{info['step_by_step']}\n\n"
                f"#### 4. Summary & Key Takeaway\n"
                f"{info['summary']}"
            )
            followups = ["Explain simply", "Give an example", "Give a hint", "Test me", "Summarize"]

        return {
            "reply": reply,
            "action_taken": action or "beginner_tutor_explanation",
            "adapted_for_level": level_label,
            "suggested_followups": followups
        }

    @classmethod
    def generate_modality_content(
        cls,
        topic_title: str,
        modality: str,
        mastery_score: float = 50.0,
        user_prompt: str = "",
        pedagogical_style: str = ""
    ) -> Dict[str, Any]:
        """
        Synthesizes structured beginner-friendly learning content across 6 educational modalities:
        - explanation (Definition, Real-World Example, Step-by-Step Example, Summary)
        - analogy (Detailed Real-World Everyday Model)
        - worked_example (Step-by-Step Code / Table walkthrough)
        - code (Clean, commented implementation or query)
        - visual (ASCII memory diagram or table layout)
        - practice (Interactive diagnostic question)
        """
        info = cls.get_topic_info(topic_title)
        level = "Beginner (Scaffolded)" if mastery_score < 40 else ("Intermediate" if mastery_score < 80 else "Advanced Mastery")
        style = pedagogical_style or "Adaptive Beginner-Friendly"

        code_snippet = info.get("code")
        visual_ascii = info.get("visual")
        practice_question = None

        if modality in ["explanation", "simple"]:
            content_markdown = (
                f"### 📖 {topic_title} — Beginner's Guide\n\n"
                f"#### 1. What Is It? (Short Definition)\n"
                f"{info['definition']}\n\n"
                f"#### 2. Familiar Real-World Example\n"
                f"{info['real_world']}\n\n"
                f"#### 3. Small Step-by-Step Example\n"
                f"{info['step_by_step']}\n\n"
                f"#### 4. Summary & Key Takeaway\n"
                f"{info['summary']}"
            )
            key_takeaways = [
                f"Definition: {info['definition'][:85]}...",
                f"Real-World: {info['real_world'][:85]}...",
                f"Golden Rule: {info['hint']}"
            ]
            suggested_prompts = [
                "Give me another real-world analogy",
                "Show me the step-by-step example again",
                "Test my knowledge with a quick challenge"
            ]

        elif modality in ["analogy", "real_world"]:
            content_markdown = (
                f"### 🌐 Everyday Real-World Analogy: {topic_title}\n\n"
                f"#### The Everyday Picture:\n"
                f"> {info['real_world']}\n\n"
                f"#### Why This Helps You Understand {topic_title}:\n"
                f"- **In Real Life:** You interact with concrete physical things that have clear rules and boundaries.\n"
                f"- **In the Computer:** The exact same rules apply! Memory boxes, queues, tables, and models mirror everyday systems.\n\n"
                f"#### Quick Definition Connection:\n"
                f"{info['definition']}\n\n"
                f"#### Key Rule to Keep in Mind:\n"
                f"{info['hint']}"
            )
            key_takeaways = [
                f"Mental Model: {info['real_world'][:90]}...",
                "Physical intuition maps directly to computer operations.",
                f"Core Takeaway: {info['summary']}"
            ]
            suggested_prompts = [
                "Show how this analogy connects to code",
                "Give me a step-by-step example",
                "Test me on this analogy"
            ]

        elif modality in ["worked_example", "step_by_step"]:
            content_markdown = (
                f"### 📝 Step-by-Step Example: {topic_title}\n\n"
                f"Here is a concrete, small example walking through the concept step-by-step:\n\n"
                f"{info['step_by_step']}\n\n"
                f"#### What Just Happened?\n"
                f"1. We defined our starting data and inputs.\n"
                f"2. We carried out the operation according to the core rule: *{info['definition']}*\n"
                f"3. We verified the final result without errors.\n\n"
                f"#### Beginner Pro-Tip:\n"
                f"💡 {info['hint']}"
            )
            key_takeaways = [
                "Follow steps in sequence from input to result.",
                f"Key Takeaway: {info['summary']}",
                f"Pro-Tip: {info['hint']}"
            ]
            suggested_prompts = [
                "Give me another step-by-step example",
                "What happens on edge cases or empty input?",
                "Test my understanding with a quiz"
            ]

        elif modality in ["code", "implementation"]:
            content_markdown = (
                f"### 💻 Code & Implementation: {topic_title}\n\n"
                f"Below is clean, beginner-friendly code with comments:\n\n"
                f"```text\n"
                f"{code_snippet}\n"
                f"```\n\n"
                f"#### Step-by-Step Breakdown:\n"
                f"{info['step_by_step']}\n\n"
                f"#### Best Practice Rule:\n"
                f"💡 {info['hint']}"
            )
            key_takeaways = [
                "Small, readable code example with clear comments.",
                "Avoids complex, unnecessary technical jargon.",
                f"Core Summary: {info['summary']}"
            ]
            suggested_prompts = [
                "Explain what each line of code does",
                "Show how to test this code with different values",
                "Show the visual diagram of this code"
            ]

        elif modality in ["visual", "diagram"]:
            content_markdown = (
                f"### 📊 Visual Layout & Memory Representation: {topic_title}\n\n"
                f"```text\n"
                f"{visual_ascii}\n"
                f"```\n\n"
                f"#### How to Read This Diagram:\n"
                f"1. **Input / Start:** Data enters the system.\n"
                f"2. **State / Structure:** Shows how values or nodes are organized in memory.\n"
                f"3. **Result:** Produces the expected, verified outcome.\n\n"
                f"#### Conceptual Meaning:\n"
                f"{info['definition']}"
            )
            key_takeaways = [
                "Visual diagram anchors memory states into an intuitive picture.",
                f"Concept: {info['definition'][:80]}...",
                f"Summary: {info['summary']}"
            ]
            suggested_prompts = [
                "Explain the diagram step-by-step",
                "Show the code for this diagram",
                "Test me on this structure"
            ]

        elif modality in ["practice", "questions"]:
            practice_question = {
                "question": info["test"],
                "options": [
                    "Option A",
                    "Option B",
                    "Option C",
                    "Option D"
                ],
                "correct": "Option B",
                "explanation": f"Key takeaway: {info['summary']} Remember: {info['hint']}"
            }
            content_markdown = (
                f"### 🎯 Beginner Practice Challenge: {topic_title}\n\n"
                f"**Question:**\n"
                f"> {info['test']}\n\n"
                f"#### Helpful Hint to Guide You:\n"
                f"💡 {info['hint']}\n\n"
                f"#### Summary Reference:\n"
                f"{info['summary']}"
            )
            key_takeaways = [
                "Practice questions reinforce active recall.",
                f"Key Rule: {info['hint']}",
                f"Summary: {info['summary']}"
            ]
            suggested_prompts = [
                "Give me another practice question",
                "Explain the answer simply",
                "Show a real-world example"
            ]

        return {
            "topic_id": 0,
            "topic_title": topic_title,
            "modality": modality,
            "pedagogical_style": style,
            "content_markdown": content_markdown,
            "key_takeaways": key_takeaways,
            "code_snippet": code_snippet,
            "visual_ascii": visual_ascii,
            "practice_question": practice_question,
            "suggested_prompts": suggested_prompts
        }
