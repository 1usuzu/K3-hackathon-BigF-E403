from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from providers import ModelResponse, OpenRouterProvider, ToolCall, get_llm_provider


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------

@dataclass
class AgentRun:
    """Normalized result of a single agent invocation — used by eval."""
    text: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helper: load YAML tools once
# ---------------------------------------------------------------------------

def _load_tools(path: str) -> list[dict[str, Any]]:
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_args(raw: str) -> dict[str, Any]:
    try:
        return json.loads(raw)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Base directory resolution (works when imported from any cwd)
# ---------------------------------------------------------------------------

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ARTIFACTS = os.path.join(_BASE_DIR, "artifacts")


# ---------------------------------------------------------------------------
# Eval-compatible single-turn agent
# ---------------------------------------------------------------------------

class EvalAgent:
    """
    Thin eval wrapper that mirrors DAY04 ResearchAgent.
    Used by run_eval.py — one LLM call per case, typed ToolCall output.
    """

    def __init__(
        self,
        provider: OpenRouterProvider,
        *,
        system_prompt: str,
        tools: list[dict[str, Any]],
        model: str | None = None,
    ) -> None:
        self.provider = provider
        self.system_prompt = system_prompt
        self.tools = tools
        self.model = model

    def run(
        self,
        user_messages: list[dict[str, str]],
        *,
        tool_choice: Any | None = None,
    ) -> AgentRun:
        messages = [{"role": "system", "content": self.system_prompt}, *user_messages]
        response: ModelResponse = self.provider.complete(
            messages,
            self.tools,
            model=self.model,
            temperature=0.0,
            tool_choice=tool_choice,
        )
        return AgentRun(
            text=response.text,
            tool_calls=response.tool_calls,
            tool_results=[],
        )


# ---------------------------------------------------------------------------
# Full VLearn agent (used by Flask app) — now with better error handling
# ---------------------------------------------------------------------------

class VLearnAgent:
    """
    Multi-step agent: Mindmap → Flashcard → Quiz.
    Delegates LLM calls to the provider; parses typed ToolCall results.
    """

    def __init__(self) -> None:
        self.provider = get_llm_provider()
        self.tools: list[dict[str, Any]] = _load_tools(
            os.path.join(_ARTIFACTS, "tools.yaml")
        )
        self.mindmap_prompt: str = _load_text(
            os.path.join(_ARTIFACTS, "mindmap_prompt.md")
        )
        self.flashcard_prompt: str = _load_text(
            os.path.join(_ARTIFACTS, "flashcard_prompt.md")
        )
        self.quiz_prompt: str = _load_text(
            os.path.join(_ARTIFACTS, "quiz_prompt.md")
        )

    # ------------------------------------------------------------------
    # Internal: call provider and extract the first tool call result
    # ------------------------------------------------------------------

    def _call(
        self,
        system: str,
        user: str,
        allowed_tools: list[str],
    ) -> tuple[str | None, dict[str, Any] | None]:
        """
        Returns (tool_name, tool_args) or (None, None) if no tool was called.
        Priority: primary tool (generate_*) beats report_error if both appear.
        Raises on provider errors.
        """
        subset = [t for t in self.tools if t.get("function", {}).get("name") in allowed_tools]
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        response: ModelResponse = self.provider.complete(
            messages, subset, temperature=0.0
        )
        if not response.tool_calls:
            return None, None

        # Prefer primary tools over report_error when both are returned
        primary_tools = [tc for tc in response.tool_calls if tc.name != "report_error"]
        chosen = primary_tools[0] if primary_tools else response.tool_calls[0]
        return chosen.name, chosen.args

    # ------------------------------------------------------------------
    # Mindmap → Flashcard combined flow
    # ------------------------------------------------------------------

    def generate_study_material(
        self, slide_text: str, student_history: list
    ) -> dict[str, Any]:
        history_str = (
            json.dumps(student_history, ensure_ascii=False)
            if student_history
            else "Chưa có lịch sử làm sai."
        )

        # ── Step 1: Mindmap ─────────────────────────────────────────────
        try:
            name, args = self._call(
                self.mindmap_prompt,
                slide_text,
                ["generate_mindmap", "report_error"],
            )
        except Exception as e:
            return {"status": "error", "message": f"Lỗi gọi API Mindmap: {e}"}

        if name is None:
            return {"status": "error", "message": "AI không gọi tool Mindmap."}
        if name == "report_error":
            return {"status": "error", "message": (args or {}).get("reason", "Lỗi nội dung slide")}

        mindmap_data: list[dict[str, Any]] = (args or {}).get("nodes", [])
        if not mindmap_data:
            return {"status": "error", "message": "Không sinh được Mindmap."}

        # ── Step 2: Flashcard ────────────────────────────────────────────
        user_content = (
            f"Lịch sử sai:\n{history_str}\n\n"
            f"Nội dung Slide:\n{slide_text}\n\n"
            f"Dàn ý Mindmap:\n{json.dumps(mindmap_data, ensure_ascii=False)}"
        )
        try:
            name, args = self._call(
                self.flashcard_prompt,
                user_content,
                ["generate_flashcards", "report_error"],
            )
        except Exception as e:
            return {"status": "error", "message": f"Lỗi gọi API Flashcard: {e}"}

        flashcards_data: list[dict[str, Any]] = []
        if name == "report_error":
            return {"status": "error", "message": (args or {}).get("reason", "Lỗi nội dung slide")}
        elif name == "generate_flashcards":
            flashcards_data = (args or {}).get("cards", [])
            for c in flashcards_data:
                c["topic"] = "Toàn bộ bài giảng"

        tree = self._build_tree(mindmap_data)
        return {
            "status": "success",
            "message": "Tổng hợp thành công",
            "mindmap": tree,
            "flashcards": flashcards_data,
        }

    # ------------------------------------------------------------------
    # Section-level flashcard generation (for a single mindmap branch)
    # ------------------------------------------------------------------

    def generate_section_flashcards(self, slide_text: str, topic: str = "") -> dict[str, Any]:
        topic_instruction = f"\nQUAN TRỌNG: Hãy tập trung sinh 5 flashcards cho chủ đề/khái niệm '{topic}' trong phần nội dung này." if topic else "\nQUAN TRỌNG: Hãy tập trung sinh 5 flashcards cho phần nội dung này."
        system = (
            self.flashcard_prompt
            + topic_instruction
        )
        try:
            name, args = self._call(
                system,
                slide_text,
                ["generate_flashcards", "report_error"],
            )
        except Exception as e:
            return {"status": "error", "message": f"Lỗi gọi API Flashcard: {e}"}

        if name == "report_error":
            return {"status": "error", "message": (args or {}).get("reason", "Lỗi nội dung")}
        if name == "generate_flashcards":
            flashcards_data = (args or {}).get("cards", [])
            for c in flashcards_data:
                c["topic"] = topic or "Toàn bộ bài giảng"
            return {"status": "success", "flashcards": flashcards_data}
        return {"status": "success", "flashcards": []}

    # ------------------------------------------------------------------
    # Quiz generation from weak flashcards
    # ------------------------------------------------------------------

    def generate_quiz(
        self, history: list, slide_text: str = ""
    ) -> dict[str, Any]:
        if not history:
            return {"status": "error", "message": "Không có thẻ yếu nào để tạo Quiz."}

        history_str = json.dumps(history, ensure_ascii=False)
        user_content = f"Nội dung slide: {slide_text}\nCác thẻ chưa hiểu: \n{history_str}"

        try:
            name, args = self._call(
                self.quiz_prompt,
                user_content,
                ["generate_quiz", "report_error"],
            )
        except Exception as e:
            return {"status": "error", "message": f"Lỗi gọi API Quiz: {e}"}

        if name is None:
            return {"status": "error", "message": "AI không thể tạo Quiz từ các thẻ này."}
        if name == "report_error":
            return {"status": "error", "message": (args or {}).get("reason", "Lỗi nội dung")}
        if name == "generate_quiz":
            return {"status": "success", "questions": (args or {}).get("questions", [])}
        return {"status": "error", "message": "Unexpected tool call."}

    # ------------------------------------------------------------------
    # Internal: flat-node list → nested tree for UI
    # ------------------------------------------------------------------

    def _build_tree(self, nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not nodes:
            return None

        node_map: dict[str, dict[str, Any]] = {
            n["id"]: {"label": n["text"], "slide": n.get("slide") or "Trích xuất", "children": []}
            for n in nodes
        }
        root: dict[str, Any] | None = None

        for n in nodes:
            pid = n.get("parent_id")
            if not pid or pid not in node_map:
                root = node_map[n["id"]]
                root["slide"] = "Toàn bộ bài"
            else:
                node_map[pid]["children"].append(node_map[n["id"]])

        if root is None and node_map:
            root = list(node_map.values())[0]
            root["slide"] = "Toàn bộ bài"

        return root
