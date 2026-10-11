from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


# dataclass provides methods such as __init__ and __repr__.
@dataclass(frozen=True)
class RemoteVault:
	remote_id		: str
	vault_id		: str
	name			: str
	modified_time	: str | None = None


# ABC uses ABCMeta to enforce implementation of abstract methods.
class SyncBackend(ABC):

	@abstractmethod
	def list_vaults(self) -> list[RemoteVault]:
		pass

	@abstractmethod
	def find_vault_by_name(
		self,
		name: str,
	) -> RemoteVault | None:
		pass

	@abstractmethod
	def find_vault_by_id(
		self,
		id: str,
	) -> RemoteVault | None:
		pass

	@abstractmethod
	def upload_vault(self, path: Path) -> RemoteVault:
		pass

	@abstractmethod
	def download_vault(
		self,
		file_id: str,
		destination: Path,
	) -> None:
		pass

	@abstractmethod
	def update_vault(
		self,
		file_id: str,
		path: Path,
	) -> RemoteVault:
		pass
