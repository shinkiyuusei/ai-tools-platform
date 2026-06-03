import re

_DEFAULT_SENSITIVE_WORDS = [
    "fuck", "shit", "ass", "bitch", "damn", "bastard", "motherfucker", "dick",
    "porn", "sex", "nude", "naked", "xxx",
    "gambling", "casino", "bet",
    "hack", "crack", "keygen",
    "暴力", "恐怖主义", "毒品", "枪支", "炸弹",
    "赌博", "色情", "裸体",
]


class ContentAuditor:
    def __init__(self, sensitive_words=None):
        self._words = sensitive_words or _DEFAULT_SENSITIVE_WORDS
        self._pattern = re.compile(
            "|".join(re.escape(w) for w in self._words),
            re.IGNORECASE,
        )

    def check(self, text: str) -> dict:
        if not text:
            return {"passed": True, "message": "ok"}

        matches = self._pattern.findall(text)
        if matches:
            unique_matches = list(set(m.lower() for m in matches))
            return {
                "passed": False,
                "message": f"内容包含敏感词：{', '.join(unique_matches[:5])}",
                "keywords": unique_matches[:5],
            }

        return {"passed": True, "message": "ok"}

_auditor = ContentAuditor()


def audit_content(text: str) -> dict:
    return _auditor.check(text)



