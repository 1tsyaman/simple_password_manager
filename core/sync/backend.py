from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


# dataclass provides methods such as __init__ and __repr__.
@dataclass(frozen=True, kw_only=True)
class RemoteFile:
	remote_id		: str
	name			: str
	modified_time	: str | None = None

@dataclass(frozen=True, kw_only=True)
class RemoteFolder:
	name			: str
	remote_id		: str


# ABC uses ABCMeta to enforce implementation of abstract methods.
class SyncBackend(ABC):

	@abstractmethod
	def list_files(
		self,
		parent: RemoteFolder | None = None
	) -> list[RemoteFile]:
		"""
			If parent is None, returns the list of files in appData
		"""
		pass

	@abstractmethod
	def list_folders(
		self,
		parent: RemoteFolder | None = None
	) -> list[RemoteFolder]:
		"""
			If parent is None, returns the list of folders in appData
		"""
		pass

	@abstractmethod
	def find_file_by_name(
		self,
		name		: str,
		parent		: RemoteFolder | None = None
	) -> RemoteFile | None:
		pass

	@abstractmethod
	def find_folder_by_name(
		self,
		name	: str,
		parent	: RemoteFolder | None = None
	) -> RemoteFolder | None:
		pass

	@abstractmethod
	def create_folder(
		self,
		name	: str,
		parent	: RemoteFolder | None = None
	) -> RemoteFolder:
		pass

	@abstractmethod
	def upload_file(
		self,
		remote_name	: str,
		path		: Path,
		parent		: RemoteFolder | None = None
	) -> RemoteFile:
		"""
			remote_name is the name the remote file will have
		"""
		pass

	@abstractmethod
	def download_file(
		self,
		file		: RemoteFile,
		destination	: Path,
		parent		: RemoteFolder | None = None
	) -> None:
		pass

	@abstractmethod
	def overwrite_file(
		self,
		file	: RemoteFile,
		path	: Path,
		parent	: RemoteFolder | None = None
	) -> RemoteFile:
		pass

	@abstractmethod
	def delete_file(
		self,
		file	: RemoteFile,
		parent	: RemoteFolder | None = None
	) -> None:
		pass

	@abstractmethod
	def delete_folder_recursive(
		self,
		folder	: RemoteFolder,
		parent	: RemoteFolder | None = None
	) -> None:
		"""
			Deletes the specified folder along with its content
		"""
		pass

	@abstractmethod
	def wipe_appData(self) -> None:
		"""
			Deletes the contents of appData
		"""
		pass