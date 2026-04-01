import json
import re
import time
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
BASE_PAPERS_PATH = BASE_DIR / "data" / "processed" / "papers_base.json"
FINAL_PAPERS_PATH = BASE_DIR / "data" / "processed" / "papers.json"
PROMPT_PATH = BASE_DIR / "prompts" / "paper_summary_prompt.txt"
ENV_PATH = BASE_DIR / "backend" / ".env"

load_dotenv(ENV_PATH)

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "").strip()
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1").strip()
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7").strip()

MINIMAX_CHAT_URL = f"{MINIMAX_BASE_URL.rstrip('/')}/chat/completions"


def load_json(path: Path):
    if not path.exists():
        return {"ai": [], "recsys": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_prompt():
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt 文件不存在: {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def extract_json_block(text: str):
    text = text.strip()

    code_block_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1)

    brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if brace_match:
        return brace_match.group(1)

    raise ValueError("模型返回中未找到 JSON 结构。")


def normalize_list(value, fallback):
    if isinstance(value, list) and value:
        cleaned = [str(x).strip() for x in value if str(x).strip()]
        if cleaned:
            return cleaned[:3]
    return fallback


def build_user_input(paper: dict):
    return f"""
论文标题：
{paper.get("title", "")}

论文摘要：
{paper.get("brief", "")}

论文链接：
{paper.get("link", "")}

已有标签：
{paper.get("tags", [])}
""".strip()


def call_minimax(paper: dict, system_prompt: str):
    if not MINIMAX_API_KEY:
        raise ValueError("MINIMAX_API_KEY 未配置，请检查 backend/.env")

    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MINIMAX_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": build_user_input(paper)},
        ],
        "temperature": 0.3,
    }

    response = requests.post(
        MINIMAX_CHAT_URL,
        headers=headers,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    data = response.json()

    if "choices" not in data or not data["choices"]:
        raise ValueError(f"模型返回异常，缺少 choices：{data}")

    message = data["choices"][0].get("message", {})
    content = message.get("content", "")

    if not content:
        raise ValueError(f"模型返回异常，content 为空：{data}")

    json_text = extract_json_block(content)
    return json.loads(json_text)


def safe_enrich_paper(paper: dict, system_prompt: str, max_retries: int = 2):
    fallback_highlights = [
        f"论文《{paper.get('title', '')}》暂未成功生成自动总结。",
        "当前展示的是兜底内容。",
        "请检查 API Key、模型返回格式或网络状态。"
    ]
    fallback_questions = [
        "这篇论文的核心创新点是什么？",
        "它更偏方法创新还是工程优化？",
        "它和当前关注方向的关系有多强？"
    ]
    fallback_actions = [
        "先保留在论文池中。",
        "稍后重试自动总结。",
        "必要时人工阅读原文补充判断。"
    ]

    for attempt in range(1, max_retries + 2):
        try:
            result = call_minimax(paper, system_prompt)

            paper["brief"] = str(result.get("brief") or paper.get("brief") or "暂无摘要。").strip()
            paper["highlights"] = normalize_list(result.get("highlights"), fallback_highlights)
            paper["bossQuestions"] = normalize_list(result.get("bossQuestions"), fallback_questions)
            paper["actions"] = normalize_list(result.get("actions"), fallback_actions)

            if result.get("tags"):
                paper["tags"] = normalize_list(result.get("tags"), paper.get("tags", ["arXiv"]))

            return paper

        except Exception as e:
            print(f"处理论文失败（第 {attempt} 次）：{paper.get('title', '')}")
            print(e)

            if attempt <= max_retries:
                time.sleep(3)
            else:
                paper["highlights"] = fallback_highlights
                paper["bossQuestions"] = fallback_questions
                paper["actions"] = fallback_actions
                return paper


def enrich_category(papers: list, system_prompt: str):
    enriched = []
    for idx, paper in enumerate(papers, start=1):
        print(f"正在处理第 {idx} 篇: {paper.get('title', '')}")
        enriched.append(safe_enrich_paper(paper.copy(), system_prompt))
    return enriched


def main():
    print(f"读取基础数据: {BASE_PAPERS_PATH}")
    print(f"输出最终数据: {FINAL_PAPERS_PATH}")
    print(f"模型: {MINIMAX_MODEL}")
    print(f"接口地址: {MINIMAX_CHAT_URL}")

    system_prompt = load_prompt()
    data = load_json(BASE_PAPERS_PATH)

    final_data = {
        "ai": enrich_category(data.get("ai", []), system_prompt),
        "recsys": enrich_category(data.get("recsys", []), system_prompt),
    }

    save_json(FINAL_PAPERS_PATH, final_data)

    print(f"已生成最终展示文件: {FINAL_PAPERS_PATH}")
    print(f"AI 数量: {len(final_data['ai'])}")
    print(f"推荐系统数量: {len(final_data['recsys'])}")


if __name__ == "__main__":
    main()