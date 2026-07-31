import ast
import re
import uuid
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class CodeOutput:
    code_block_id: str
    language: str
    raw_code: str
    symbols: List[str]
    imports: List[str]
    functions: List[str]
    classes: List[str]
    parse_status: str  # SUCCESS, PARTIAL, ERROR
    source_reference: str = ""

class CodeNormalizer:
    @staticmethod
    def detect_language(code_snippet: str, hint_lang: str = "") -> str:
        if hint_lang and hint_lang.lower() not in ["code", "text", ""]:
            return hint_lang.lower()

        clean = code_snippet.strip()
        if re.search(r"def\s+\w+\s*\(|class\s+\w+|import\s+\w+|from\s+\w+\s+import", clean):
            return "python"
        elif re.search(r"function\s+\w+|const\s+\w+\s*=|let\s+\w+\s*=|console\.log", clean):
            return "javascript"
        elif re.search(r"SELECT\s+.+FROM\s+|CREATE\s+TABLE|INSERT\s+INTO", clean, re.IGNORECASE):
            return "sql"
        elif re.search(r"#include\s+<.+>|std::cout|int\s+main\s*\(", clean):
            return "cpp"
        elif re.search(r"public\s+class\s+\w+|System\.out\.println", clean):
            return "java"
        
        return "python" if hint_lang == "python" else "text"

    @staticmethod
    def normalize_code(
        raw_code: str,
        hint_language: str = "",
        source_reference: str = ""
    ) -> CodeOutput:
        code_id = str(uuid.uuid4())
        preserved_code = raw_code

        language = CodeNormalizer.detect_language(preserved_code, hint_language)

        functions: List[str] = []
        classes: List[str] = []
        imports: List[str] = []
        symbols: List[str] = []
        parse_status = "SUCCESS"

        if language == "python":
            try:
                # AST Parsing (Static analysis only, NEVER execute code!)
                parsed_ast = ast.parse(preserved_code)

                for node in ast.walk(parsed_ast):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        functions.append(node.name)
                        symbols.append(node.name)
                    elif isinstance(node, ast.ClassDef):
                        classes.append(node.name)
                        symbols.append(node.name)
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                            symbols.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        mod = node.module or ""
                        for alias in node.names:
                            imp_str = f"{mod}.{alias.name}" if mod else alias.name
                            imports.append(imp_str)
                            symbols.append(imp_str)
                    elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                        symbols.append(node.id)

                functions = sorted(list(set(functions)))
                classes = sorted(list(set(classes)))
                imports = sorted(list(set(imports)))
                symbols = sorted(list(set(symbols)))

            except SyntaxError:
                parse_status = "ERROR"
                funcs_rx = re.findall(r"def\s+(\w+)\s*\(", preserved_code)
                cls_rx = re.findall(r"class\s+(\w+)", preserved_code)
                imp_rx = re.findall(r"(?:import|from)\s+([\w\.]+)", preserved_code)

                functions = sorted(list(set(funcs_rx)))
                classes = sorted(list(set(cls_rx)))
                imports = sorted(list(set(imp_rx)))
                symbols = sorted(list(set(functions + classes + imports)))
        else:
            parse_status = "PARTIAL"
            funcs_rx = re.findall(r"(?:function|def|fn|func)\s+(\w+)\s*\(", preserved_code)
            cls_rx = re.findall(r"(?:class|struct|interface)\s+(\w+)", preserved_code)
            
            # Non-python import regex (handles: import x from 'y', require('y'), #include <y>)
            imp_rx = re.findall(r"import\s+(?:\{?[\w\s,]+\}?)\s+from\s+['\"]([^'\"]+)['\"]", preserved_code)
            if not imp_rx:
                imp_rx = re.findall(r"(?:import|require|include)\s+['\"<]?([a-zA-Z0-9_\-\.\/]+)['\">]?", preserved_code)

            functions = sorted(list(set(funcs_rx)))
            classes = sorted(list(set(cls_rx)))
            imports = sorted(list(set(imp_rx)))
            symbols = sorted(list(set(functions + classes + imports)))

        return CodeOutput(
            code_block_id=code_id,
            language=language,
            raw_code=preserved_code,
            symbols=symbols,
            imports=imports,
            functions=functions,
            classes=classes,
            parse_status=parse_status,
            source_reference=source_reference
        )
