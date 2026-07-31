from typing import Dict, List

class GlossaryPromptFormatter:
    @staticmethod
    def format_glossary_instructions(glossary: Dict[str, str], max_terms: int = 50) -> str:
        if not glossary:
            return ""

        sorted_terms = sorted(list(glossary.keys()))[:max_terms]
        
        terms_bullet_list = "\n".join(
            f"  - **{term}**: {glossary[term]}" for term in sorted_terms
        )

        instruction = f"""
### QUY TẮC BẢO VỆ THUẬT NGỮ (GLOSSARY PROTECTION RULES):
1. GIỮ NGUYÊN VĂN BẰNG TIẾNG ANH (ENGLISH TERM) đối với tất cả các thuật ngữ kỹ thuật, tên thuật toán, tên mô hình, tên framework, thư viện, API, code identifier (hàm, biến, class) và ký hiệu toán học dưới đây.
2. KHÔNG DỊCH các thuật ngữ này sang tiếng Việt hoặc ngôn ngữ khác dưới mọi hình thức (ví dụ: GIỮ NGUYÊN "Gradient Descent", KHÔNG dịch thành "Giảm độ dốc"; GIỮ NGUYÊN "Overfitting", KHÔNG dịch thành "Quá khớp").
3. Phần giải thích hoặc nội dung mô tả đi kèm phải sử dụng ngôn ngữ chính của bài giảng.
4. Bảo toàn chính xác chữ hoa, chữ thường và dấu cách của các identifier code và tên công nghệ.

Danh sách thuật ngữ bắt buộc bảo vệ:
{terms_bullet_list}
"""
        return instruction.strip()
