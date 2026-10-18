from dataclasses import dataclass
from collections.abc import Callable

from core.etc.types import sync_data_t
@dataclass
class SyncCallbacks:
	sync_data_writeback		: Callable[[sync_data_t], None]
	local_version_getter	: Callable[[str], str]
	vault_auth_checker		: Callable[[str], bool]