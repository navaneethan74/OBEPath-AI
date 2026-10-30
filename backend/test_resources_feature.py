import sys
import os
import urllib.parse
from sqlalchemy.orm import Session

# Add backend to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Course, Topic, Resource
from ai_agents.resource_agent import ResourceAgent
from routes.courses import get_course

def run_tests():
    print("=" * 60)
    print("RUNNING OBEPATH AI TOPIC RESOURCES TESTS")
    print("=" * 60)

    db: Session = SessionLocal()
    passed = 0
    total = 0

    def assert_test(condition: bool, msg: str):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {msg}")
        else:
            print(f"  [FAIL] {msg}")
            raise AssertionError(msg)

    try:
        # Test 1: Direct ResourceAgent catalog coverage across all 4 courses
        print("\n--- Test Suite 1: ResourceAgent Catalog Coverage Across 4 Courses ---")
        sample_topics = [
            ("Variables, Data Types & Basic I/O", "CS101 Python"),
            ("Conditional Statements & Branching", "CS101 Python"),
            ("Stack Basics & Operations", "CS201 Data Structures"),
            ("Recursion Fundamentals", "CS201 Data Structures"),
            ("Statistical Learning & Feature Engineering", "AI301 ML"),
            ("Neural Networks & Backpropagation", "AI301 ML"),
            ("Relational Data Model & Schemas", "CS302 DBMS"),
            ("Transactions, ACID & Concurrency", "CS302 DBMS"),
        ]

        for topic_title, course_label in sample_topics:
            recs = ResourceAgent.get_resources_for_topic(topic_title)
            assert_test(len(recs) >= 1, f"ResourceAgent has resources for {course_label}: '{topic_title}'")
            first = recs[0]
            assert_test(bool(first.get("title")), f"Resource has title: {first.get('title')[:35]}...")
            assert_test(bool(first.get("website_name")), f"Resource has website_name: {first.get('website_name')}")
            assert_test(bool(first.get("description")), f"Resource has description")
            assert_test(first.get("difficulty") in ["Beginner", "Intermediate", "Advanced"], f"Resource has valid difficulty: {first.get('difficulty')}")
            assert_test(first.get("approved_by_faculty") is False, f"Unapproved recommendation has approved_by_faculty=False")
            url = first.get("url", "")
            assert_test(url.startswith("https://") or url.startswith("http://"), f"Valid URL format: {url[:40]}...")

        # Test 2: Fallback for uncataloged topic uses safe encyclopedic reference
        print("\n--- Test Suite 2: Fallback for Unknown Topic ---")
        unknown_recs = ResourceAgent.get_resources_for_topic("Quantum Distributed Consensus 999")
        assert_test(len(unknown_recs) == 1, "Fallback returns exactly 1 encyclopedic study guide")
        assert_test("wikipedia.org" in unknown_recs[0]["url"], "Fallback URL points to Wikipedia search")
        assert_test(unknown_recs[0]["approved_by_faculty"] is False, "Fallback is marked approved_by_faculty=False")

        # Test 3: API get_course() behavior across all 4 courses
        print("\n--- Test Suite 3: API get_course() Resources for All 4 Courses ---")
        for cid in [1, 2, 3, 4]:
            course_data = get_course(course_id=cid, db=db)
            code = course_data["code"]
            title = course_data["title"]
            topics = course_data["topics"]
            print(f"\nEvaluating Course {cid}: [{code}] {title} ({len(topics)} topics)")

            assert_test(len(topics) > 0, f"Course {code} contains topics")

            for t in topics:
                res_list = t["resources"]
                assert_test(len(res_list) > 0, f"Topic '{t['title']}' has non-empty resources (count={len(res_list)})")

                for r in res_list:
                    # Check required fields
                    assert_test("title" in r and bool(r["title"]), f"  Topic {t['id']} resource has title")
                    assert_test("website_name" in r and bool(r["website_name"]), f"  Topic {t['id']} resource has website_name: {r.get('website_name')}")
                    assert_test("description" in r and bool(r["description"]), f"  Topic {t['id']} resource has description")
                    assert_test("difficulty" in r and bool(r["difficulty"]), f"  Topic {t['id']} resource has difficulty: {r.get('difficulty')}")
                    assert_test("approved_by_faculty" in r, f"  Topic {t['id']} resource has approved_by_faculty")
                    
                    # URL validation
                    url = r.get("url", "")
                    assert_test(url.startswith("http://") or url.startswith("https://"), f"  Valid HTTP URL: {url[:35]}...")

                    # Check faculty approval labeling rules:
                    # All 4 courses (CS101, CS201, AI301, CS302) now have verified topic resources seeded in DB
                    assert_test(r["approved_by_faculty"] is True, f"  Course {cid} ({code}) DB resource has approved_by_faculty=True")

        # Test 4: Database coverage check
        print("\n--- Test Suite 4: Database Resource Coverage Check ---")
        db_resource_count = db.query(Resource).count()
        assert_test(db_resource_count >= 96, f"DB resources count covers all 32 topics (count={db_resource_count} >= 96)")

        print("\n" + "=" * 60)
        print(f"ALL TESTS PASSED! ({passed}/{total} assertions)")
        print("=" * 60)

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
