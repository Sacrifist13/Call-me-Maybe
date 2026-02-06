from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, model_validator


class PromptModel(BaseModel):
    prompt: List[str] = Field(min_length=1, description="Input prompts list")

    def __str__(self) -> str:
        s = ""
        for prompt in self.prompt:
            s += "\n{\n"
            s += f"      'prompt': {prompt}\n"
            s += "},\n"
        return s[:-2]


class FunctionModel(BaseModel):
    fn_name: str = Field(min_length=1, description="Function identifier")
    args_names: List[str] = Field(
        min_length=1, description="Arguments documentation"
    )
    args_types: Dict[str, str] = Field(description="Arguments type")
    return_type: str = Field(description="Output type")

    def __str__(self) -> str:
        s = "\n{\n"
        s += f"     'fn_name': {self.fn_name}\n"
        s += f"     'args_names': {self.args_names}\n"
        s += f"     'args_types': {self.args_types}\n"
        s += f"     'return_type': {self.return_type}\n"
        s += "},\n"
        return s[:-2]

    @model_validator(mode="after")
    def validate_model(self) -> "FunctionModel":
        valid_types = ["int", "bool", "str", "float"]

        errors: Dict[str, Any] = {
            "missing_types": [
                arg for arg in self.args_names if arg not in self.args_types
            ],
            "unknown_args": [
                key
                for key in self.args_types.keys()
                if key not in self.args_names
            ],
            "invalid_type": [
                (arg, self.args_types[arg])
                for arg in self.args_names
                if arg in self.args_types
                if self.args_types[arg] not in valid_types
            ],
            "return_type": (
                self.return_type
                if self.return_type not in valid_types
                else None
            ),
        }

        def report_failure() -> Optional[str]:
            report = ""

            if errors["missing_types"]:
                missing: List[str] = errors["missing_types"]
                names = ", ".join(missing)
                report += f"- Missing type definition for arguments: {names}\n"

            if errors["unknown_args"]:
                unknown: List[str] = errors["unknown_args"]
                names = ", ".join(unknown)
                report += (
                    f"- Type provided for undeclared arguments: {names}\n"
                )

            if errors["invalid_type"]:
                report += "- Argument with invalid type: "
                for arg, arg_type in errors["invalid_type"]:
                    report += f"'{arg}': {arg_type}, "
                report = report[:-2] + "\n"

            if errors["return_type"]:
                report += f"- Invalid return type: '{errors['return_type']}'."
                report += " Expected one of: int, bool, str, float\n"

            if report:
                return f"Function: {self.fn_name} error\n" + report

            return None

        report = report_failure()

        if report:
            raise ValueError(report)

        return self
