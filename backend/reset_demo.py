import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, Base
import seed_data

def reset():
    print("Dropping and reseeding database...")
    Base.metadata.drop_all(bind=engine)
    seed_data.seed_database()
    print("Demo state reset to initial specifications!")

if __name__ == "__main__":
    reset()
