import logging
import os
import shutil
from argparse import ArgumentParser
from enum import Enum
from functools import reduce
from glob import glob
from pathlib import Path
from typing import Dict, List, Tuple
from zipfile import ZipFile


class BColor(str, Enum):
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class MultiToSingleTestCase:
    TEMP_DIR_SUFFIX = "_temp"
    RESULT_DIR = "result"
    SOURCE_DIR = "source"
    ANSWER_SUFFIX = "ans"
    INPUT_SUFFIX = "in"
    DATA_DIR = "data"
    SECRET_DIR = "secret"
    SAMPLE_DIR = "sample"

    @classmethod
    def from_folder(
        cls,
        path: Path,
        output_path: Path,
        logger: logging.Logger,
        ignore: int = 0,
    ) -> "MultiToSingleTestCase":
        logger.debug(f"Archive problem folder {path.absolute()}.")
        folder_path = os.path.split(path.absolute())[0]
        out = shutil.make_archive(
            path.absolute(),
            "zip",
            root_dir=path,
            verbose=True,
            logger=logger,
        )
        path = Path(folder_path).joinpath(out)
        logger.info(f"{path}")
        return MultiToSingleTestCase(path, output_path, logger, ignore)

    def __init__(
        self,
        file_path: Path,
        output_path: Path,
        logger: logging.Logger,
        ignore: int = 0,
    ) -> None:
        if not file_path.exists():
            raise FileNotFoundError(
                f"[Errno 2] No such file or directory: {file_path.absolute()}",
            )

        self.logger = logger
        self.logs: List[Path] = []

        if not output_path.exists():
            os.makedirs(output_path.absolute())
            self.logs.append(output_path)

        self.output_path = output_path
        self.source_dir = self.output_path.joinpath(self.SOURCE_DIR)
        self.ignore = ignore
        if not self.source_dir.exists():
            logger.debug(f"Make folder: {self.source_dir.absolute()}")
            os.mkdir(self.source_dir)
            self.logs.append(self.source_dir)

        self.file = file_path
        self.dir = self.unzip_to_temp_dir()

    def print(self, message: str, color: BColor = BColor.OKBLUE) -> None:
        print()
        print(f"{color}{message}{color}")
        print()

    def archive_result(self) -> None:
        self.logger.debug("Archive convert result to zip file.")
        folder_name = os.path.split(self.dir.absolute())[-1]
        file_name = str(folder_name).replace(self.TEMP_DIR_SUFFIX, "")
        self.logger.debug(f"file name: {file_name}")

        result_dir = self.output_path.joinpath(self.RESULT_DIR)
        if not result_dir.exists():
            self.logger.debug(f"Make folder: {result_dir.absolute()}")
            os.mkdir(result_dir)
            self.logs.append(result_dir)

        out = shutil.make_archive(
            result_dir.joinpath(file_name).absolute(),
            "zip",
            root_dir=self.dir,
            verbose=True,
            logger=self.logger,
        )
        path = result_dir.joinpath(out)
        self.print(f"Delete {self.dir.absolute()}")
        shutil.rmtree(self.dir)
        self.print(f"Success covert format. {path}", BColor.OKGREEN)

    def unzip_to_temp_dir(self) -> Path:
        file_path, file_name = os.path.split(self.file)
        file_name, _ = os.path.splitext(file_name)
        temp_dir = self.output_path.joinpath(file_path).joinpath(
            f"{file_name}{self.TEMP_DIR_SUFFIX}"
        )

        with ZipFile(self.file, "r") as zipfile:
            if temp_dir.exists():
                self.logger.debug(f"Remove folder {temp_dir.absolute()}")
                shutil.rmtree(temp_dir)

            zipfile.extractall(temp_dir)
            self.logs.append(temp_dir)

        return temp_dir

    def move_zip_source_dir(self) -> None:
        self.logger.debug("Move zip file to source folder.")
        new_path = self.source_dir.joinpath(self.file.name)
        shutil.move(self.file, new_path)
        self.print(f"Move {self.file.name} to {new_path.absolute()}")

    def recover_zip_path(self) -> None:
        self.logger.debug("Recover zip file to original path.")
        new_path = self.source_dir.joinpath(self.file.name)
        shutil.move(new_path, self.file)
        self.print(f"Move {self.file.name} to {self.file.absolute()}")

    def recover_folders(self) -> None:
        self.logger.debug("Remove all new created folders.")
        for path in self.logs:
            if not path.exists():
                continue

            self.logger.warning(f"Remove {path.absolute()}.")
            shutil.rmtree(path)

    def match_testcase(self, paths: List[str]) -> Dict[str, Tuple[str, str]]:
        self.logger.debug("Match testcase, input and answer.")
        inputs = []
        answers = []
        for path in paths:
            file_name = os.path.split(path)[-1]
            name, extension = os.path.splitext(file_name)
            if self.INPUT_SUFFIX in extension:
                inputs.append((name, path))

            if self.ANSWER_SUFFIX in extension:
                answers.append((name, path))

        ret = {}
        for in_temp, ans_temp in zip(sorted(inputs), sorted(answers)):
            in_name, in_path = in_temp
            ans_name, ans_path = ans_temp

            if in_name == ans_name:
                self.logger.debug(f"Input: {in_path}, Answer: {ans_path} .")
                ret[in_name] = (in_path, ans_path)
            else:
                self.logger.warning(f"Input: {in_path} not match Answer: {ans_path} .")

        return ret

    def collect_testcase(
        self,
    ) -> Tuple[
        Dict[str, Tuple[str, str]],
        Dict[str, Tuple[str, str]],
        Dict[str, Tuple[str, str]],
    ]:
        self.logger.debug("Collect testcase info from folder.")
        pattern_path = os.path.join(self.dir.joinpath(self.DATA_DIR), "**")
        secret_paths = []
        sample_paths = []
        paths = []

        for path in glob(pattern_path, recursive=True):
            if self.SAMPLE_DIR in path:
                sample_paths.append(path)
            elif self.SECRET_DIR in path:
                secret_paths.append(path)
            else:
                paths.append(path)

        return (
            self.match_testcase(sample_paths),
            self.match_testcase(secret_paths),
            self.match_testcase(path),
        )

    def write_file(self, path: str, file_name: str, content: str) -> Path:
        dir_path = os.path.split(path)[0]
        file_path = Path(dir_path).joinpath(file_name)
        with open(file_path, "w") as file:
            file.write(content)
        self.logger.info(f"{file_path}")
        return Path(dir_path).joinpath(file_name)

    def convert_input(self, key: str, input_path: str) -> List[Path]:
        convert_result = []
        with open(input_path, "r") as content:
            count = 0
            for index, line in enumerate(content.read().splitlines()):
                text = line.strip()
                if index < self.ignore:
                    line_msg = "lines" if index > 0 else "line"
                    self.logger.debug(f"Ignore {index + 1} {line_msg} .")
                    continue

                if text:
                    count += 1
                    file_name = "{}{}.{}".format(
                        key,
                        str(count).zfill(2),
                        self.INPUT_SUFFIX,
                    )
                    convert_result.append(self.write_file(input_path, file_name, text))

        os.remove(input_path)
        return convert_result

    def convert_answer(self, key: str, answer_path: str) -> List[Path]:
        convert_result = []
        with open(answer_path, "r") as content:
            count = 0
            for line in content.read().splitlines():
                text = line.strip()

                if text:
                    count += 1
                    file_name = "{}{}.{}".format(
                        key,
                        str(count).zfill(2),
                        self.ANSWER_SUFFIX,
                    )
                    self.write_file(answer_path, file_name, text)
                    convert_result.append(self.write_file(answer_path, file_name, text))

        os.remove(answer_path)
        return convert_result

    def covert_testcase(self, data: Dict[str, Tuple[str, str]]) -> None:
        self.logger.debug("Covert testcase format.")
        for key, paths in data.items():
            in_path, ans_path = paths
            input_result = self.convert_input(key, in_path)
            answer_result = self.convert_answer(key, ans_path)
            full_result = set(input_result + answer_result)
            zip_result = set(
                reduce(
                    list.__add__,
                    map(
                        list,
                        zip(
                            input_result,
                            answer_result,
                        ),
                    ),
                )
            )
            diff_result = full_result - zip_result

            for path in diff_result:
                self.logger.warning(
                    f"{path.name} Can't match a input or answer, remove {path.absolute()} .",
                )
                os.remove(path.absolute())


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("problem", help="A problem folder or zip file path.")
    parser.add_argument(
        "-o",
        "--output",
        help="Output base folder path.",
    )
    parser.add_argument(
        "-l",
        "--lines",
        action="count",
        help="ignore input testcase lines, -l: one line, -ll: two lines.",
        default=0,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        help="-v: INFO, -vv: DEBUG, default: WARNING.",
        default=0,
    )

    args = parser.parse_args()

    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    level = levels[min(args.verbose, len(levels) - 1)]
    logger = logging.getLogger()
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter(
        f"{BColor.ENDC}%(name)s:%(levelname)s:\t%(message)s{BColor.ENDC}",
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    file_path = Path(args.problem)
    base_path = Path(args.output) if args.output else Path()
    lines = args.lines

    try:
        if file_path.is_file and "zip" in file_path.name:
            logger.debug(f"Open a problem zip file, {file_path.name}")
            handler = MultiToSingleTestCase(file_path, base_path, logger, lines)
        else:
            logger.debug(f"Open a problem folder, {file_path.name}")
            handler = MultiToSingleTestCase.from_folder(
                file_path,
                base_path,
                logger,
                lines,
            )

    except Exception as e:
        logger.error(f"{e}")
        exit(0)

    try:
        handler.move_zip_source_dir()
        testcase_collection = handler.collect_testcase()
        for testcase in testcase_collection:
            handler.covert_testcase(testcase)

        handler.archive_result()
    except Exception as e:
        logger.error(f"{e}")
        handler.recover_zip_path()
        handler.recover_folders()
