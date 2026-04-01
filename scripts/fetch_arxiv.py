import json
from pathlib import Path
from datetime import datetime
import arxiv
import time

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

AI_OUTPUT_PATH = RAW_DIR / "arxiv_ai.json"
RECSYS_OUTPUT_PATH = RAW_DIR / "arxiv_recsys.json"


def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def paper_to_dict(result):
    return {
        "arxiv_id": result.get_short_id(),
        "title": result.title.strip() if result.title else "",
        "summary": result.summary.strip().replace("\n", " ") if result.summary else "",
        "authors": [author.name for author in result.authors] if result.authors else [],
        "published": result.published.isoformat() if result.published else "",
        "updated": result.updated.isoformat() if result.updated else "",
        "categories": result.categories if result.categories else [],
        "primary_category": result.primary_category if hasattr(result, "primary_category") else "",
        "pdf_url": result.pdf_url if hasattr(result, "pdf_url") else "",
        "entry_id": result.entry_id if hasattr(result, "entry_id") else "",
    }


def fetch_papers(query: str, max_results: int = 5):
    print(f"正在执行 query: {query}")

    client = arxiv.Client(
        page_size=5,
        delay_seconds=3,
        num_retries=5
    )

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )

    retry_count = 0

    while retry_count < 3:
        try:
            papers = []
            for idx, result in enumerate(client.results(search), start=1):
                paper = paper_to_dict(result)
                papers.append(paper)
                print(f"已抓取第 {idx} 篇: {paper['title'][:60]}")

            print(f"本次抓取完成，共 {len(papers)} 篇")
            return papers

        except Exception as e:
            retry_count += 1
            print(f"抓取失败（第{retry_count}次），等待重试...")
            print(e)
            time.sleep(5)

    print("连续重试 3 次后仍然失败，返回空列表。")
    return []

def save_json(path: Path, data):
    payload = {
        "generated_at": datetime.now().isoformat(),
        "count": len(data),
        "papers": data
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    ensure_dirs()

    ai_query = 'ti:"multimodal"'
    recsys_query = 'ti:"recommendation"'

    print(f"AI 输出文件: {AI_OUTPUT_PATH}")
    print(f"推荐系统输出文件: {RECSYS_OUTPUT_PATH}")

    print("开始抓取 AI 论文...")
    ai_papers = fetch_papers(ai_query, max_results=5)
    save_json(AI_OUTPUT_PATH, ai_papers)

    print("开始抓取推荐系统论文...")
    recsys_papers = fetch_papers(recsys_query, max_results=5)
    save_json(RECSYS_OUTPUT_PATH, recsys_papers)
if __name__ == "__main__":
    main()