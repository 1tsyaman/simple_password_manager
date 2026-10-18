from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

from core.etc.errors import IllegalArgumentError

# Union type alias
type config_t			= str | int | bool


# Sync types

type vault_sync_data_t	= dict[str, str | None]
type sync_data_t		= dict[str, vault_sync_data_t]

@dataclass
class VaultSyncData:
	remote_folder_id	: str
	last_synced_version	: str | None

	def to_dict(self) -> vault_sync_data_t:
		return {
			"remote_folder_id"		: self.remote_folder_id,
			"last_synced_version"	: self.last_synced_version
		}

	@staticmethod
	def from_dict(data: dict[str, str | None]) -> VaultSyncData:
		"""
			Raises:
				IllegalArgumentError: If data is not of the shape
					{
						"remote_folder_id"		: str
						"last_synced_version"	: str | None
					}
		"""
		if not isinstance(data, dict):
			raise IllegalArgumentError

		try:
			remote_folder_id	= data["remote_folder_id"]
			last_synced_version	= data["last_synced_version"]
		except KeyError:
			raise IllegalArgumentError

		if not (
			isinstance(remote_folder_id, str)
			and (
				isinstance(last_synced_version, str) or last_synced_version is None
			)
		):
			raise IllegalArgumentError

		return VaultSyncData(
			remote_folder_id=remote_folder_id,
			last_synced_version=last_synced_version
		)

class SyncActions(Enum):
	PULL 		= 1
	PUSH 		= 2
	CONFLICT	= 3
	NO_OP		= 4