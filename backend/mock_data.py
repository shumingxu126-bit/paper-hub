MOCK_PAPERS = {
    "ai": [
        {
            "id": "ai-1",
            "title": "A Survey of Multimodal Foundation Models",
            "score": 96,
            "tags": ["Multimodal", "Foundation Model", "Survey"],
            "year": 2026,
            "month": "03",
            "source": "arXiv",
            "link": "https://arxiv.org",
            "brief": "这篇论文梳理了多模态基础模型的主要技术路线、能力边界与未来演进方向。",
            "highlights": [
                "从文本到图像、视频、音频，多模态统一建模已成为主流趋势。",
                "训练成本与推理成本仍然是大规模落地的关键瓶颈。",
                "真正的工业价值不在模型更大，而在是否能进入具体工作流。"
            ],
            "bossQuestions": [
                "哪些多模态能力最适合接进我们的信息产品？",
                "这类模型落地时最大成本项是什么？",
                "是否适合先从摘要和标签生成切入？"
            ],
            "actions": [
                "先选 20 篇近期热门论文做摘要验证。",
                "搭一版标题、摘要、标签自动生成链路。",
                "评估多模态能力是否真的影响推荐点击。"
            ]
        },
        {
            "id": "ai-2",
            "title": "Agentic Workflows for Scientific Discovery",
            "score": 91,
            "tags": ["Agent", "Scientific Discovery", "Automation"],
            "year": 2026,
            "month": "03",
            "source": "arXiv",
            "link": "https://arxiv.org",
            "brief": "论文讨论了 agent 如何在科学研究流程中承担检索、整理、比较和总结任务。",
            "highlights": [
                "论文发现 agent 在文献筛选和初步总结上效率很高。",
                "但在事实校验与精细推理上仍需人工兜底。",
                "最合适的落地形态是半自动工作流，而不是全自动。"
            ],
            "bossQuestions": [
                "我们的论文站里哪些环节最适合 agent 化？",
                "自动总结是否需要人工审核开关？",
                "如何保证引用和原文一致？"
            ],
            "actions": [
                "把检索、筛选、总结拆成三个独立模块。",
                "给每篇论文保留原始摘要与 AI 摘要双版本。",
                "增加失败重试与人工修正入口。"
            ]
        }
    ],
    "recsys": [
        {
            "id": "rec-1",
            "title": "Large Language Models for Recommendation",
            "score": 94,
            "tags": ["LLM", "Recommendation", "Ranking"],
            "year": 2026,
            "month": "02",
            "source": "arXiv",
            "link": "https://arxiv.org",
            "brief": "这篇论文研究大模型在推荐系统中的角色，从特征理解延伸到排序与生成式推荐。",
            "highlights": [
                "LLM 更擅长补足语义理解，而不是直接替代整个推荐系统。",
                "推荐场景里，效率和成本通常比极致效果更重要。",
                "生成式推荐适合探索场景，不一定适合主排序链路。"
            ],
            "bossQuestions": [
                "LLM 在推荐链路里最适合放在哪一层？",
                "收益是否足以覆盖推理成本？",
                "是否可以只用于冷启动内容理解？"
            ],
            "actions": [
                "先做离线实验，不直接上线上链路。",
                "优先验证冷启动、标签生成、语义补全场景。",
                "把召回和排序分开看，不混着评估。"
            ]
        }
    ]
}