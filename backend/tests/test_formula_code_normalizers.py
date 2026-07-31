import pytest
from backend.app.services.content_extraction.normalizers import (
    FormulaNormalizer, FormulaOutput,
    CodeNormalizer, CodeOutput
)

def test_formula_normalization_clean_latex():
    raw_formula = "$$ L(\\theta) = \\frac{1}{N} \\sum_{i=1}^{N} (y_i - f(x_i))^2 $$"
    result = FormulaNormalizer.normalize_formula(
        raw_text=raw_formula,
        source_reference="Slide 28",
        surrounding_explanation="Cost of Error loss function"
    )

    assert isinstance(result, FormulaOutput)
    assert result.latex == "L(\\theta) = \\frac{1}{N} \\sum_{i=1}^{N} (y_i - f(x_i))^2"
    assert "\\theta" in result.variables
    assert result.confidence_score >= 0.9
    assert result.needs_review is False
    assert result.source_reference == "Slide 28"
    assert "Cost of Error" in result.surrounding_explanation

def test_formula_normalization_ambiguous_ocr():
    # Ambiguous formula needing review
    raw_ocr = "L(?theta) = \\sum UNKNOWN_SYMBOL"
    result = FormulaNormalizer.normalize_formula(
        raw_text=raw_ocr,
        source_reference="Page 12",
        is_ocr=True
    )

    assert result.confidence_score < 0.7
    assert result.needs_review is True
    # Verify raw formula not auto-altered when unconfident
    assert "UNKNOWN_SYMBOL" in result.original_representation

def test_python_code_ast_parsing_and_indentation():
    python_code = """# Compute Loss Function
import numpy as np
from math import sqrt

class LossEvaluator:
    def calculate_mse(self, y_true, y_pred):
        # Calculate mean squared error
        diff = y_true - y_pred
        return np.mean(diff ** 2)
"""
    result = CodeNormalizer.normalize_code(
        raw_code=python_code,
        hint_language="python",
        source_reference="Slide 30"
    )

    assert isinstance(result, CodeOutput)
    assert result.language == "python"
    assert result.parse_status == "SUCCESS"
    
    # Verify exact indentation & comments preserved intact
    assert "        diff = y_true - y_pred" in result.raw_code
    assert "# Compute Loss Function" in result.raw_code
    
    # Verify AST extracted symbols
    assert "LossEvaluator" in result.classes
    assert "calculate_mse" in result.functions
    assert "numpy" in result.imports or "np" in result.imports
    assert "math.sqrt" in result.imports

def test_python_code_syntax_error_fallback():
    broken_code = """class BrokenClass:
    def bad_function(self, x
        return x +
"""
    result = CodeNormalizer.normalize_code(
        raw_code=broken_code,
        hint_language="python"
    )

    # Must preserve raw code and set parse_status = ERROR
    assert result.parse_status == "ERROR"
    assert result.raw_code == broken_code
    assert "BrokenClass" in result.classes or "BrokenClass" in result.symbols

def test_javascript_code_parsing():
    js_code = """// JavaScript API Client
import axios from 'axios';

class ApiService {
    async fetchData(endpoint) {
        const response = await axios.get(endpoint);
        return response.data;
    }
}
"""
    result = CodeNormalizer.normalize_code(
        raw_code=js_code,
        hint_language="javascript"
    )

    assert result.language == "javascript"
    assert result.parse_status == "PARTIAL"
    assert "ApiService" in result.classes or "ApiService" in result.symbols
    assert "axios" in result.imports or "axios" in result.symbols
    assert "// JavaScript API Client" in result.raw_code
