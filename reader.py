import json
import collections
from typing import Dict, List, Optional
from argparse import ArgumentParser, ArgumentError
from pathlib import Path
from pydantic import ValidationError
from .models import PromptModel, FunctionModel
from .tools import print_err


class Reader:
    def __init__(self, output_errors: bool) -> None:
        self.path: Dict[str, Path] = {}
        self.valid_input_files: Dict[str, List[Path]] = {
            "calling": [],
            "definitions": [],
        }
        self.output_errors = output_errors

    def validate_arguments(self) -> bool:
        usage = "uv run python -m src "
        usage += "[--input <input_file>] [--output <output_file>]"

        parser = ArgumentParser(
            prog="Call me Maybe",
            exit_on_error=False,
            usage=usage,
        )
        parser.add_argument(
            "--input", default="data/input/", help="input directory path"
        )
        parser.add_argument(
            "--output",
            default="data/output/function_calling_results.json",
            help="output file path",
        )
        try:
            args = vars(parser.parse_args())
            self.path["input_dir"] = Path(args["input"])
            self.path["output_file"] = Path(args["output"])

            path = self.path["input_dir"].resolve()

            if not self.path["input_dir"].exists():
                print_err(f"Error: Input directory not found at: '{path}'")
                return False

            if not self.path["input_dir"].is_dir():
                print_err(
                    f"Error: The path provided is not a directory: '{path}'"
                )
                return False

            if not self.path["output_file"].suffix == ".json":
                name = self.path["output_file"].name
                err = "Invalid output format. File must have a '.json'"
                err += f" extension (Received: '{name}')"
                print_err(err)
                return False
            return True

        except ArgumentError as e:
            print_err(f"Error: {e}")
            return False

        except Exception as e:
            print_err(f"Unexpected error: {type(e).__name__} -> {e}")
            return False

    def scan_input_directory(self) -> bool:
        errors: Dict[str, List[str]] = collections.defaultdict(list)

        def report_failures() -> None:
            if not self.output_errors:
                return

            for key, value in errors.items():
                count = len(value)
                files = (", ").join(value)

                if key == "syntax":
                    print_err(f"Syntax error -> {count} rejected ({files})")

                elif key == "json_format":
                    print_err(f"Format error -> {count} rejected ({files})")

                elif key == "permission":
                    print_err(
                        f"Permission error -> {count} rejected ({files})"
                    )

        if not self.validate_arguments():
            return False

        for file in self.path["input_dir"].glob("*.json"):
            try:
                f = json.loads(file.read_text(encoding="utf-8"))

                if not isinstance(f, list) or not f:
                    errors["json_format"].append(file.name)
                    continue

                definitions: bool = False
                calling: bool = False

                for el in f:
                    file_error: bool = False
                    match el:
                        case {"prompt": _}:
                            if definitions:
                                errors["syntax"].append(file.name)
                                file_error = True
                                break
                            calling = True

                        case {
                            "fn_name": _,
                            "args_names": _,
                            "args_types": _,
                            "return_type": _,
                        }:
                            if calling:
                                errors["syntax"].append(file.name)
                                file_error = True
                                break
                            definitions = True

                        case _:
                            errors["syntax"].append(file.name)
                            file_error = True
                            break

                if not file_error:
                    if definitions:
                        self.valid_input_files["definitions"].append(file)
                    else:
                        self.valid_input_files["calling"].append(file)

            except PermissionError:
                errors["permission"].append(file.name)

            except json.JSONDecodeError:
                errors["syntax"].append(file.name)

            except Exception as e:
                print("test")
                errors["unexpected"].append(f"{type(e).__name__} -> {e}")

        report_failures()

        if (
            self.valid_input_files["calling"]
            and self.valid_input_files["definitions"]
        ):
            return True
        err = "Missing required input: Ensure the input directory contains "
        err += "at least one file of each type ('calling' and 'definitions')."
        print_err(err)
        return False

    def load_validated_data(
        self,
    ) -> Optional[Dict[str, List[PromptModel | FunctionModel]]]:
        validated_data: Dict[str, List[PromptModel | FunctionModel]] = {
            "prompt": [],
            "function": [],
        }

        if not self.validate_arguments():
            return None

        if not self.scan_input_directory():
            return None

        for calling_file in self.valid_input_files["calling"]:
            f = json.loads(calling_file.read_text(encoding="utf-8"))

            user_input = [prompt["prompt"] for prompt in f]
            try:
                validated_data["prompt"].append(PromptModel(prompt=user_input))
            except ValidationError as e:
                print(e)

        for definition_file in self.valid_input_files["definitions"]:
            f = json.loads(definition_file.read_text(encoding="utf-8"))

            for function in f:
                try:
                    validated_data["function"].append(
                        FunctionModel(
                            fn_name=function["fn_name"],
                            args_names=function["args_names"],
                            args_types=function["args_types"],
                            return_type=function["return_type"],
                        )
                    )
                except ValidationError as e:
                    errors = e.errors()[0]
                    msg = (
                        errors["msg"].replace("Value error, ", "")
                        if not errors["loc"]
                        else errors["loc"][0]
                        + f" {errors['msg'].lower()} "
                        + f"(input {errors['input']})"
                    )
                    print_err(msg)

        return validated_data
