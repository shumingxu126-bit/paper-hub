import json
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent

RAW_AI_PATH = BASE_DIR / "data" / "raw" / "arxiv_ai.json"
RAW_RECSYS_PATH = BASE_DIR / "data" / "raw" / "arxiv_recsys.json"
PROCESSED_PATH = BASE_DIR / "data" / "processed" / "papers_base.json"


def load_json(path: Path):
    if not path.exists():
        return {"papers": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def safe_first_sentence(text: str) -> str:
    if not text:
        return "暂无摘要。"
    text = text.replace("\n", " ").strip()
    parts = text.split(". ")
    if parts:
        return parts[0].strip() + ("。" if not parts[0].endswith(("。", ".")) else "")
    return text[:120]


def extract_year_month(published: str):
    if not published:
        return 2026, "01"
    try:
        dt = datetime.fromisoformat(published)
        return dt.year, f"{dt.month:02d}"
    except Exception:
        return 2026, "01"


def build_tags(categories):
    if not categories:
        return ["arXiv"]
    return categories[:3]


def build_score(paper, category_name: str):
    title = (paper.get("title") or "").lower()
    summary = (paper.get("summary") or "").lower()

    score = 80

    if category_name == "ai":
        keywords = ["multimodal", "vision", "language model", "agent", "reasoning"]
    else:
        keywords = ["recommendation", "recommender", "ranking", "retrieval", "personalization"]

    for kw in keywords:
        if kw in title:
            score += 5
        elif kw in summary:
            score += 3

    return min(score, 99)


def build_highlights(paper, category_name: str):
    summary = (paper.get("summary") or "").strip()
    short_summary = safe_first_sentence(summary)

    if category_name == "ai":
        return [
            f"论文核心关注点是：{short_summary}",
            "从当前标题和摘要看，这篇论文更适合进入 AI 论文观察池做进一步筛选。",
            "后续可结合更细的标签体系判断其是否属于真正值得推荐的重点论文。"
        ]
    else:
        return [
            f"论文核心关注点是：{short_summary}",
            "从当前标题和摘要看，这篇论文与推荐系统、排序或个性化方向相关。",
            "后续可结合业务场景判断其更适合召回、排序还是用户理解方向。"
        ]


def build_boss_questions(category_name: str):
    if category_name == "ai":
        return [
            "这篇论文解决的是能力问题，还是工程落地问题？",
            "它是否适合进入我们的长期跟踪列表？",
            "这项能力能否迁移到内容理解或信息产品中？"
        ]
    else:
        return [
            "这篇论文更接近推荐策略优化，还是模型结构创新？",
            "它更适合用于召回、排序还是冷启动？",
            "这种方法在真实业务里是否有上线价值？"
        ]


def build_actions(category_name: str):
    if category_name == "ai":
        return [
            "先纳入 AI 论文池，后续再做人工复筛。",
            "补充更细粒度标签，如多模态、Agent、推理、生成。",
            "后续结合自动总结模块生成更完整解读。"
        ]
    else:
        return [
            "先纳入推荐系统论文池，后续再做人工复筛。",
            "补充更细粒度标签，如召回、排序、冷启动、用户建模。",
            "后续结合自动总结模块生成更完整解读。"
        ]


def transform_paper(paper, category_name: str, index: int):
    year, month = extract_year_month(paper.get("published", ""))
    return {
        "id": f"{category_name}-{index + 1}",
        "title": paper.get("title", "Untitled Paper"),
        "score": build_score(paper, category_name),
        "tags": build_tags(paper.get("categories", [])),
        "year": year,
        "month": month,
        "source": "arXiv",
        "link": paper.get("entry_id") or paper.get("pdf_url") or "https://arxiv.org",
        "brief": safe_first_sentence(paper.get("summary", "")),
        "highlights": build_highlights(paper, category_name),
        "bossQuestions": build_boss_questions(category_name),
        "actions": build_actions(category_name),
    }


def transform_category(raw_data, category_name: str):
    papers = raw_data.get("papers", [])
    return [transform_paper(p, category_name, idx) for idx, p in enumerate(papers)]


def main():
    raw_ai = load_json(RAW_AI_PATH)
    raw_recsys = load_json(RAW_RECSYS_PATH)

    processed_data = {
        "ai": transform_category(raw_ai, "ai"),
        "recsys": transform_category(raw_recsys, "recsys")
    }

    save_json(PROCESSED_PATH, processed_data)

    print(f"已生成处理后文件: {PROCESSED_PATH}")
    print(f"AI 论文数量: {len(processed_data['ai'])}")
    print(f"推荐系统论文数量: {len(processed_data['recsys'])}")


if __name__ == "__main__":
    main()