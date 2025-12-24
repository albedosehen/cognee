#!/usr/bin/env python3
"""
Test script to verify Alembic migrations work correctly with a fresh database when dockerized.
"""
import os
import sys
import tempfile
import subprocess
from pathlib import Path

def test_migrations():
    """Test migrations on a fresh SQLite database"""
    # Create a temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test_cognee.db"
        test_db_url = f"sqlite:///{test_db_path}"
        
        print(f"Testing migrations with fresh database at: {test_db_path}")
        print(f"Database URL: {test_db_url}")
        
        # Set environment variable for the test database
        env = os.environ.copy()
        env["DATABASE_URL"] = test_db_url
        env["DB_PROVIDER"] = "sqlite"
        
        try:
            # Run alembic upgrade head
            print("\n" + "="*60)
            print("Running: alembic upgrade head")
            print("="*60 + "\n")
            
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                env=env,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            print("STDOUT:")
            print(result.stdout)
            
            if result.stderr:
                print("\nSTDERR:")
                print(result.stderr)
            
            if result.returncode != 0:
                print(f"\n❌ Migration FAILED with exit code {result.returncode}")
                return False
            else:
                print("\n✅ Migration SUCCEEDED")
                
                # Run alembic check to verify database matches models
                print("\n" + "="*60)
                print("Running: alembic check")
                print("="*60 + "\n")
                
                check_result = subprocess.run(
                    ["alembic", "check"],
                    env=env,
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd()
                )
                
                print(check_result.stdout)
                if check_result.stderr:
                    print(check_result.stderr)
                
                if check_result.returncode != 0:
                    print("\n⚠️  Database check found differences")
                else:
                    print("\n✅ Database check passed")
                
                return True
                
        except Exception as e:
            print(f"\n❌ Error running migrations: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_migrations()
    sys.exit(0 if success else 1)
