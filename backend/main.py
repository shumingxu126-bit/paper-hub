from fastapi import Query
import arxiv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from data_loader import load_papers
import subprocess
import sys
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


# 👇 挂载静态文件（css/js等）
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# 👇 首页返回 index.html（关键）
@app.get("/")
def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


# 👇 API：获取论文
@app.get("/api/papers")
def get_papers():
    return load_papers()


# 👇 API：刷新数据（可选，后面可以关掉）
@app.post("/api/refresh")
def refresh_papers():
    try:
        result = subprocess.run(
            [sys.executable, "scripts/run_pipeline.py"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        if result.returncode != 0:
            return {
                "success": False,
                "message": "Pipeline 执行失败",
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        return {
            "success": True,
            "message": "Pipeline 执行成功",
            "stdout": result.stdout,
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"执行 refresh 时发生异常: {str(e)}"
        }

# =========================
# 🔍 arXiv 搜索能力（新增）
# =========================

def paper_to_raw_dict(result):
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


def search_arxiv_online(keyword: str, max_results: int = 30):
    client = arxiv.Client(page_size=10, delay_seconds=2, num_retries=3)

    search = arxiv.Search(
        query=f'ti:"{keyword}" OR abs:"{keyword}"',
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )

    results = []
    for result in client.results(search):
        results.append(paper_to_raw_dict(result))
    return results
# =========================
# 🧠 打分逻辑
# =========================

def keyword_score(text, title, keywords, title_weight=8, summary_weight=4):
    score = 0
    for kw in keywords:
        if kw in title:
            score += title_weight
        elif kw in text:
            score += summary_weight
    return score


def penalty_score(text, title, keywords, title_weight=10, summary_weight=5):
    score = 0
    for kw in keywords:
        if kw in title:
            score += title_weight
        elif kw in text:
            score += summary_weight
    return score


def build_internet_score(paper):
    title = (paper.get("title") or "").lower()
    summary = (paper.get("summary") or "").lower()

    internet_keywords = [
        "recommendation", "ranking", "retrieval",
        "user", "content", "ads", "search",
        "feed", "ctr", "click", "conversion"
    ]

    penalties = [
        "disease", "clinical", "medical",
        "chemical", "molecule", "biology",
        "policy", "law"
    ]

    score = 30
    score += keyword_score(summary, title, internet_keywords)
    score -= penalty_score(summary, title, penalties)

    return max(0, min(score, 100))


def build_final_score(internet_score):
    return max(60, min(internet_score, 95))


# =========================
# 🔍 搜索接口（核心）
# =========================

@app.get("/api/search")
def search_papers(q: str = Query(..., min_length=1)):
    from datetime import datetime

    def extract_year_month(published: str):
        try:
            dt = datetime.fromisoformat(published)
            return dt.year, f"{dt.month:02d}"
        except Exception:
            return 2026, "01"

    def build_score(paper):
        title = (paper.get("title") or "").lower()
        summary = (paper.get("summary") or "").lower()
        text = f"{title} {summary}"

        # 核心关键词（互联网 + AI + 推荐）
        positive_keywords = [
            "recommendation", "recommender", "ranking", "retrieval",
            "user", "behavior", "personalization", "click",
            "feed", "ads", "advertising", "content", "platform",
            "search", "matching", "engagement",
            "llm", "agent", "multimodal", "generation"
        ]

        # 强过滤关键词（直接拉低）
        negative_keywords = [
            "disease", "medical", "clinical", "patient",
            "chemical", "molecule", "protein", "biology",
            "policy", "regulation", "law",
            "satellite", "geology", "material", "physics"
        ]

        score = 50

        # 正向加分
        for kw in positive_keywords:
            if kw in title:
                score += 8
            elif kw in summary:
                score += 4

        # 负向扣分
        for kw in negative_keywords:
            if kw in text:
                score -= 10

        return max(0, min(score, 100))

    def to_card(paper, idx):
        year, month = extract_year_month(paper.get("published", ""))

        score = build_score(paper)

        summary = paper.get("summary", "") or ""
        brief = summary[:180] + ("..." if len(summary) > 180 else "")

        return {
            "id": paper.get("arxiv_id") or paper.get("entry_id") or f"search-{idx+1}",
            "title": paper.get("title", "Untitled Paper"),
            "score": max(60, min(score, 95)),  # 保证在60-95区间
            "tags": paper.get("categories", [])[:3] or ["arXiv"],
            "year": year,
            "month": month,
            "source": "arXiv",
            "link": paper.get("entry_id") or paper.get("pdf_url") or "https://arxiv.org",
            "brief": brief,
            "highlights": [
                "该结果来自实时 arXiv 搜索。",
                "基于关键词匹配生成推荐指数。",
                "建议点击原文进一步查看。"
            ],
            "bossQuestions": [
                "这篇论文和当前搜索意图的贴合度如何？",
                "是否属于推荐系统或内容分发相关方向？",
                "是否值得进一步深入阅读？"
            ],
            "actions": [
                "先快速浏览摘要。",
                "若相关性高，再点击原文。",
                "可加入后续论文池跟踪。"
            ]
        }

    # 🔍 从 arXiv 抓取
    raw_results = search_arxiv_online(q, max_results=30)

    # 🧹 过滤明显不相关
    filtered = []
    for p in raw_results:
        text = ((p.get("title", "") or "") + " " + (p.get("summary", "") or "")).lower()

        penalties = [
            "medical", "disease", "chemical", "molecule",
            "policy", "regulation", "law", "biology"
        ]

        if sum(1 for x in penalties if x in text) >= 2:
            continue

        filtered.append(p)

    # 📊 排序 + Top10
    ranked = sorted(
        [to_card(p, idx) for idx, p in enumerate(filtered)],
        key=lambda x: x["score"],
        reverse=True
    )[:10]

    return {"results": ranked}