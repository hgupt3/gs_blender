import subprocess
import sys
import time
import os

def run_blender_once() -> int:
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    blend_path = os.path.join(repo_dir, "gelsight_sampler.blend")
    script_path = os.path.join(repo_dir, "scripting.py")

    cmd = [
        "blender",
        "-b",
        blend_path,
        "--python-exit-code",
        "1",
        "--python",
        script_path,
    ]

    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    max_retries = int(os.environ.get("BLENDER_MAX_RETRIES", "3"))
    for attempt in range(1, max_retries + 1):
        start_time = time.time()
        print(f"starting blender attempt {attempt}/{max_retries}")
        rc = run_blender_once()
        elapsed_time = time.time() - start_time
        print(f"ending blender attempt {attempt} with rc={rc} (elapsed {elapsed_time:.1f}s)")

        if rc == 0:
            sys.exit(0)

        if attempt < max_retries:
            time.sleep(2)
            continue

        sys.exit(rc)


