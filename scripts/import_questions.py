import argparse
import asyncio
import json
from pathlib import Path

from app.database import AsyncSessionLocal
from app.services.question_importer import QuestionFileError, import_questions


async def run(paths: list[Path]) -> int:
    exit_code = 0
    async with AsyncSessionLocal() as db:
        for path in paths:
            try:
                result = await import_questions(
                    db,
                    filename=path.name,
                    content=path.read_bytes(),
                )
                print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
                if result.failed_count:
                    exit_code = 1
            except (OSError, QuestionFileError) as exc:
                exit_code = 1
                print(
                    json.dumps(
                        {"filename": str(path), "status": "failed", "error": str(exc)},
                        ensure_ascii=False,
                        indent=2,
                    )
                )
    return exit_code


def main() -> None:
    parser = argparse.ArgumentParser(description="校验并批量导入 JSON 题库")
    parser.add_argument("files", nargs="+", type=Path, help="一个或多个 JSON 题库文件")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.files)))


if __name__ == "__main__":
    main()
