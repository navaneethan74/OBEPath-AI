import sys
sys.path.insert(0, 'backend')
from code_runner import CODING_CHALLENGES

for i, c in enumerate(CODING_CHALLENGES):
    print(f"{i+1}. [{c['id']}] Course {c['course_id']}, Topic {c['topic_id']}: {c['title']}")
    print("   Starter code:")
    for line in c['starter_code'].strip().split('\n')[:3]:
        print("     ", line)
