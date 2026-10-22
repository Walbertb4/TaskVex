"""Çalışma verisinin konumunu belirler; import sırasında dosya oluşturmaz.

Kaynak kodu ile kullanıcı verisi ayrıdır. Host bu fonksiyonu açılışta çağırır;
testler TASKVEX_HOME ile her seferinde ayrı geçici dizin seçer.
"""

import os
from pathlib import Path

from app.core.contracts import ContractError


def get_data_home() -> Path:
    """TASKVEX_HOME veya Windows LOCALAPPDATA/TaskVex yolunu ver.

    Açıkça verilmiş boş/göreli bir yol hatadır; yanlışlıkla çalışma dizinine
    veri yazmaya geri düşmeyiz. Dizin burada yaratılmaz, ilk yazmada yaratılır.
    Windows dışında bu ilk sürüm için TASKVEX_HOME açıkça ayarlanmalıdır.
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
