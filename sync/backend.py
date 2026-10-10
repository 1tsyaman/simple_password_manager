from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


# dataclass decorator gives us useful methods, such as
# 	__init__ and __repr__
@dataclass(frozen=True)
class RemoteFile:
	id: str
	name: str
	modified_time: str | None = None

"""
	ABC = Abstract Base Class
	-> 	Inherits from Python's meta class ABCmeta, which
		enforces implementation of abstract methods
"""
class SyncBackend(ABC):

	@abstractmethod
	def list_files(self) -> list[RemoteFile]:
		pass

	@abstractmethod
	def find_file(
		self,
		name: str,
	) -> RemoteFile | None:
		pass

	@abstractmethod
	def upload_file(self, path: Path) -> RemoteFile:
		pass

	@abstractmethod
	def download_file(
		self,
		file_id: str,
		destination: Path,
	) -> None:
		pass

	@abstractmethod
	def update_file(
		self,
		file_id: str,
		path: Path,
	) -> RemoteFile:
		pass