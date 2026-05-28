import argparse
import json
import pickle
from pathlib import Path

from utils.result import Result


class ResultUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == "__main__" and name == "Result":
            return Result
        return super().find_class(module, name)


def load_result(path: Path) -> Result:
    with path.open("rb") as result_file:
        return ResultUnpickler(result_file).load()


def format_text(result: Result) -> str:
    data = result.to_dict()
    lines = [
        f"Covered line count: {data['covered_line_count']}",
        f"Crash count: {data['crash_count']}",
        f"Duration seconds: {data['duration_seconds']:.3f}",
        "",
        "Covered lines:",
    ]
    lines.extend(
        f"  - {location['function']}:{location['line']}"
        for location in data["covered_lines"]
    )

    lines.append("")
    lines.append("Crashes:")
    if data["crashes"]:
        lines.extend(f"  - {crash}" for crash in data["crashes"])
    else:
        lines.append("  - none")

    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="View a persisted fuzzing result file.")
    parser.add_argument("path", help="Path to a Sample-X.pkl result file")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    parser.add_argument("--output", help="Write the readable result to a file")
    return parser.parse_args()


def main():
    args = parse_args()
    result = load_result(Path(args.path))

    if args.json:
        content = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    else:
        content = format_text(result)

    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
    else:
        print(content)


if __name__ == "__main__":
    main()
