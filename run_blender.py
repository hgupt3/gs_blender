import multiprocessing
import subprocess
import time
import os


def run_blender():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    blend_path = os.path.join(repo_dir, "gelsight_sampler.blend")
    script_path = os.path.join(repo_dir, "scripting.py")
    subprocess.call(["blender", blend_path, "--python", script_path])


if __name__ == "__main__":
    while True:
        start_time = time.time()
        print("starting process")
        p = multiprocessing.Process(target=run_blender)
        p.start()
        p.join()
        print("ending process")
        elasped_time = time.time() - start_time

        if elasped_time < 60:
            break


