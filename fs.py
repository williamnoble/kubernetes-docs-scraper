import os
import typing
from dataclasses import dataclass
from enum import Enum


class Filetype(Enum):
    MARKDOWN = ".md"
    PDF = ".pdf"


@dataclass
class FileWriter:
    output_dir: str

    def write(
            self,
            filename: str,
            content: str | list[str],
            mode: str = "w",
            header: str = None,
            suffix: Filetype = Filetype.MARKDOWN.value,
            multiple_documents: bool = False,
             overwrite: bool = False,
    ):

        file_name = f"{filename}{suffix}"
        file_path = os.path.join(self.output_dir, file_name)

        if not overwrite and os.path.exists(file_path):
            print(f"File {file_name} already exists. Skipping.")
            return

        with open(file_path, mode, encoding="utf-8") as f:
            if header:
                f.write(header)

            if isinstance(content, str):
                # Handle single
                f.write(content)
            else:
                # Handle iterable
                for i, item in enumerate(content):
                    if multiple_documents and i >0:
                        self.print_document_separator(f)
                    f.write(item)

    @staticmethod
    def print_document_separator(f: typing.IO):
        f.write("\n\n")
        f.write("+======================= NEW DOCUMENT =======================+\n")
        f.write("\n\n")