import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def run_step(cmd):
    print(f"\n=== 正在执行: {' '.join(cmd)} ===")
    result = subprocess.run(cmd, cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"执行失败: {' '.join(cmd)}")
        sys.exit(result.returncode)

def main():
    run_step([sys.executable, "scripts/fetch_arxiv.py"])
    run_step([sys.executable, "scripts/build_processed_data.py"])
    run_step([sys.executable, "scripts/enrich_papers.py"])
    print("\n=== 全部流程执行完成 ===")

if __name__ == "__main__":
    main()