"""Save small JSON objects without leaving the old file unfinished.

The new content is written to a temporary file in the same directory as the target, with flush/fsync
is completed and replaced with the target with os.replace. Error before replacement
It does not replace the old file. Disk/write errors are not disguised as successes.

The file envelope contains version + data. Corrupt records are not automatically counted as empty data;
read gives an error, recover_corrupt, but if called explicitly, the original is preserved separately.
This class does not manage the grading scheme, authority, or secure storage of secrets.
"""

import json
import os
from pathlib import Path
import tempfile
from threading import RLock
from typing import Any, Callable
from uuid import uuid4

from app.core.contracts import ContractError, copy_json


class StoreError(ValueError):
    """It carries the error code; messages do not contain log content or system path."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Prevent the same JSON key from silently crushing the previous value."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    """The NaN/Infinity that the Python decoder accepts is not standard JSON."""
    raise ValueError("Non-finite JSON number")


class JsonStore:
    """It stores a version=1 JSON object in a single file chosen by the trusted host.

    path is an absolute file path; It should not be taken directly from the tool/model entry.
    read returns None in the missing file, {} in the current empty record. So 'yet
    'not created' and 'user cleared data' do not mix.

    Printers sharing the same instance can hold a lock during read-modify-write.
    Atomic replace alone does not rank two authors.
    shortcut: lock between processes or separate JsonStore instances
    does not provide protection; Switch to transaction-supported storage in multi-process writing.
    """

    def __init__(self, path: Path) -> None:
        """Check location; Creating an object does not read or create a file."""
        if not isinstance(path, Path) or not path.is_absolute() or not path.name:
            raise ContractError("Store path must be an absolute file path")
        self.path = path
        # Domain owners sharing the same instance hold this lock for read/modify/write.
        self.lock = RLock()

    def read(self) -> dict[str, Any] | None:
        """Read the record with verification; report error without modifying the file.

        Unsupported version is different error code: data of newer application
        Instead of thinking it's broken and resetting it, the upgrade/migration decision is left to the host.
        """
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except UnicodeError:
            raise StoreError("corrupt_data", "Stored data is not valid UTF-8") from None
        except OSError:
            raise StoreError("read_failed", "Stored data could not be read") from None
        try:
            document = json.loads(text, object_pairs_hook=_unique_object,
                                  parse_constant=_reject_constant)
            if (type(document) is not dict or type(document.get("version")) is not int
                    or document["version"] < 1):
                raise ValueError("Invalid version envelope")
            if document["version"] != 1:
                raise StoreError("unsupported_version", "Stored data version is not supported")
            if set(document) != {"version", "data"} or type(document["data"]) is not dict:
                raise ValueError("Invalid data envelope")
            return copy_json(document["data"])
        except (ValueError, RecursionError) as error:
            if isinstance(error, StoreError):
                raise
            raise StoreError("corrupt_data", "Stored data is invalid; original file preserved") from None

    def write(self, data: dict[str, Any]) -> None:
        """Replace full object atomic; The return occurs only if replace is successful.

        First we verify it in memory. Then we check the existing record: corrupt or
        We do not accidentally overwrite the new version file. Temporary before success
        the file is closed; This is also required for replace on Windows.
        """
        try:
            if type(data) is not dict:
                raise ContractError("Store data must be a JSON object")
            text = json.dumps({"version": 1, "data": copy_json(data)},
                              ensure_ascii=False, allow_nan=False, indent=2) + "\n"
            # Only surrogate characters that cannot be converted to UTF-8 can also be saved without touching the disk.
            # is rejected; It is not enough for json.dumps to produce text.
            content = text.encode("utf-8")
        except (ValueError, TypeError, RecursionError):
            raise StoreError("invalid_data", "Expected a JSON object with finite values") from None
        self.read()
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # The NamedTemporaryFile context closes the file before replace. same
            # Using indexes prevents loss of atomicity between different disks.
            with tempfile.NamedTemporaryFile(mode="wb", dir=self.path.parent,
                                             prefix=f".{self.path.name}.", suffix=".tmp",
                                             delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except OSError:
            raise StoreError("write_failed", "Stored data could not be saved") from None
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    # Don't let cleanliness mask the actual writing error. Now .tmp,
                    # It is never considered the main record during normal startup.
                    pass

    def recover_corrupt(self, *, validate: Callable[[dict], Any] | None = None) -> Path | None:
        """Just move the corrupted file to its unique .corrupt name; write a new record.

        The host must first notify the user of the error and explicitly choose this recovery.
        The returned path is the file that preserves the actual bytes. Healthy/incomplete None in registration;
        It grants read permission or denial in case of version error. If recovery fails, the original remains.
        If validate is given, the application schema in valid JSON is also checked;
        Only ContractError is considered a bad record, not an unexpected validator error.
        """
        try:
            data = self.read()
            if data is None:
                return None
            if validate is None:
                return None
            try:
                validate(data)
            except ContractError:
                pass
            else:
                return None
        except StoreError as error:
            if error.code != "corrupt_data":
                raise
        backup = self.path.with_name(f"{self.path.name}.{uuid4().hex}.corrupt")
        try:
            os.replace(self.path, backup)
        except OSError:
            raise StoreError("recovery_failed", "Corrupt data could not be preserved") from None
        return backup
