"""Build script to bundle frontend Next.js application into FastAPI backend static files directory (M46)."""

import os
import shutil
import subprocess
import sys


def main():
    # Root path
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")
    backend_static_dir = os.path.join(root_dir, "backend", "app", "static")

    print("=== Step 1: Building Frontend using Bun ===")
    try:
        # Check if bun is installed
        subprocess.run(["bun", "--version"], check=True, capture_output=True)
    except Exception:
        print("Error: 'bun' package manager is not installed or not in PATH.")
        sys.exit(1)

    print("Running 'bun run build' inside frontend directory...")
    # Execute bun run build
    res = subprocess.run(
        ["bun", "run", "build"],
        cwd=frontend_dir,
        shell=True,
    )
    if res.returncode != 0:
        print("Error: Frontend build failed.")
        sys.exit(1)

    print("\n=== Step 2: Preparing static directory in backend ===")
    # Clear static folder inside backend/app/static
    if os.path.exists(backend_static_dir):
        print(f"Cleaning existing directory: {backend_static_dir}")
        shutil.rmtree(backend_static_dir)

    print(f"Creating new directory: {backend_static_dir}")
    os.makedirs(backend_static_dir, exist_ok=True)

    # Copy build output (frontend/out) to backend/app/static
    frontend_out_dir = os.path.join(frontend_dir, "out")
    if not os.path.exists(frontend_out_dir):
        print(f"Error: Build output directory not found at {frontend_out_dir}")
        sys.exit(1)

    print(f"Copying files from {frontend_out_dir} to {backend_static_dir}...")
    for item in os.listdir(frontend_out_dir):
        s = os.path.join(frontend_out_dir, item)
        d = os.path.join(backend_static_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    print("\n=== Success: Single-Deploy Bundle Built! ===")
    print("Run the backend now: uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
