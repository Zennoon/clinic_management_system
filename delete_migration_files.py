import glob
import os

def delete_migration_files():
    files = glob.glob("**/migrations/**.py", recursive=True)
    for file in files:
        if not file.endswith("__init__.py"):
            print(file)
            os.remove(file)
            print("*"*50 + "deleted")


if __name__ == "__main__":
    delete_migration_files()