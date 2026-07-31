import json
from typing import Type, TypeVar, Tuple, Optional, Any
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

class OutputSchemaValidator:
    @staticmethod
    def validate_and_clean_json(json_str: str, schema_cls: Type[T]) -> Tuple[Optional[T], bool, str]:
        """
        Validates JSON string against Pydantic schema class.
        Strips unknown extra fields and verifies valid JSON structure.
        """
        if not json_str:
            return None, False, "Empty output"

        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                return None, False, "JSON output must be an object/dict"

            # Parse with Pydantic
            validated_obj = schema_cls.model_validate(data)
            return validated_obj, True, ""
        except json.JSONDecodeError as err:
            return None, False, f"Invalid JSON syntax: {err}"
        except ValidationError as err:
            return None, False, f"Schema validation error: {err}"
