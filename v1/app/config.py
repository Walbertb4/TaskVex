"""Determines the location of study data; It does not create a file during import.

Source code and user data are separate. The host calls this function at startup;
The tests choose a separate temporary directory each time with TASKVEX_HOME.
"""

import os
from pathlib import Path

from app.core.contracts import ContractError


def get_data_home() -> Path:
    """Give the path TASKVEX_HOME or Windows LOCALAPPDATA/TaskVex.

    Clearly the given is a path error; mistakenly into working directory
    We don't fall back on writing data. The directory is not created here, it is created on the first write.
    For this first release outside of Windows, TASKVEX_HOME must be set explicitly.
    """
    configured = os.environ.get("TASKVEX_HOME")
    if configured is not None:
        path = Path(configured)
        if not configured.strip() or not path.is_absolute():
            raise ContractError("TASKVEX_HOME must be an absolute path")
        return path
    local = os.environ.get("LOCALAPPDATA")
    if os.name != "nt" or not local or not Path(local).is_absolute():
        raise ContractError("Set TASKVEX_HOME to an absolute data directory")
    return Path(local) / "TaskVex"
