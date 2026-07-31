class SecurityPermissionException(Exception):
    pass

class ToolPermissionPolicy:
    ALLOWED_TOOLS_STUDENT = {
        "search_course_rag",
        "get_mindmap_node",
        "get_flashcard_progress"
    }

    FORBIDDEN_TOOLS = {
        "execute_code",
        "run_shell_command",
        "fetch_external_url",
        "access_other_course"
    }

    @classmethod
    def validate_tool_execution(cls, tool_name: str, user_role: str = "student"):
        if tool_name in cls.FORBIDDEN_TOOLS:
            raise SecurityPermissionException(f"Execution of tool '{tool_name}' is strictly forbidden by guardrails policy.")
        if tool_name not in cls.ALLOWED_TOOLS_STUDENT:
            raise SecurityPermissionException(f"Tool '{tool_name}' is not permitted for student context.")
