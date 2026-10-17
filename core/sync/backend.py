from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime


# dataclass provides methods such as __init__ and __repr__.
@dataclass(frozen=True, kw_only=True)
class RemoteFile:
	remote_id		: str
	name			: str
	modified_time	: datetime

@dataclass(frozen=True, kw_only=True)
class RemoteFolder:
	remote_id		: str
	name			: str


# ABC uses ABCMeta to enforce implementation of abstract methods.
class CloudBackend(ABC):

	@abstractmethod
	def list_files(
		self,
		parent: RemoteFolder | None = None
	) -> list[RemoteFile]:
		"""
			If parent is None, returns the list of files in appData

			Raises:
				HttpError(status)
		"""
		pass

	@abstractmethod
	def list_folders(
		self,
		parent: RemoteFolder | None = None
	) -> list[RemoteFolder]:
		"""
			If parent is None, returns the list of folders in appData

			Raises:
				HttpError(status)
		"""
		pass

	@abstractmethod
	def find_file_by_name(
		self,
		name		: str,
		parent		: RemoteFolder | None = None
	) -> RemoteFile | None:
		"""
			Raises:
				HttpError(status)
		"""
		pass

	@abstractmethod
	def find_folder_by_name(
		self,
		name	: str,
		parent	: RemoteFolder | None = None
	) -> RemoteFolder | None:
		"""
			Raises:
				HttpError(status)
		"""
		pass

	@abstractmethod
	def create_folder(
		self,
		name	: str,
		parent	: RemoteFolder | None = None
	) -> RemoteFolder:
		"""
			Raises:
				HttpError(status)
		"""
		pass

	@abstractmethod
	def upload_file(
		self,
		remote_name	: str,
		source		: Path,
		parent		: RemoteFolder | None = None
	) -> RemoteFile:
		"""
			remote_name is the name the remote file will have

			Raises:
				HttpError(status)
		"""
		pass

	@abstractmethod
	def download_file(
		self,
		file		: RemoteFile,
		destination	: Path,
		parent		: RemoteFolder | None = None
	) -> None:
		"""
			Raises:
				HttpError(status)
				IOError
		"""
		pass

	@abstractmethod
	def download_folder(
		self,
		folder		: RemoteFolder,
		destination	: Path,
		parent		: RemoteFolder | None = None
	) -> None:
		"""
			Downloads the files in the folder and stores them in 'destination'/folder.name/
			Does not clean up upon failure

			Raises:
				HttpError(status)
				IOError
		"""

	@abstractmethod
	def update_file(
		self,
		file	: RemoteFile,
		source	: Path | None = None,
		name	: str | None = None,
		parent	: RemoteFolder | None = None
	) -> RemoteFile:
		"""
			- If source is not None, remote file is overwritten with file from source.
			- If name is not None, remote file is renamed to name.
			
			Raises:
				IllegalArgumentError: if both 'source' and 'name' are None
		"""
		pass

	@abstractmethod
	def delete_file(
		self,
		file	: RemoteFile,
		parent	: RemoteFolder | None = None
	) -> None:
		"""
			Raises:
				HttpError(status)
		"""
		pass

	@abstractmethod
	def delete_folder_recursive(
		self,
		folder	: RemoteFolder,
		parent	: RemoteFolder | None = None
	) -> None:
		"""
			Deletes the specified folder along with its content

			Raises:
				HttpError(status)
		"""
		pass

	@abstractmethod
	def wipe_appData(self) -> None:
		"""
			Deletes the contents of appData

			Raises:
				HttpError(status)
		"""
		pass