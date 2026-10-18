class ClientCredentialsNotFoundError(Exception):
	pass


class AuthDeniedError(Exception):
	pass


class AuthTimeoutError(Exception):
	pass


class CloudBackendError(Exception):
	pass

class HttpError(Exception):
	pass

class RemoteVaultNotFoundError(Exception):
	pass

class NoVaultSyncDataError(Exception):
	pass

class VaultSyncDataExistsError(Exception):
	pass

class CloudConnectionError(Exception):
	pass

class SyncConflictError(Exception):
	"""Raised if both remote and local have changed"""

class CloudVaultAuthenticityError(Exception):
	"""Raised if latest cloud version fails the authenticity check"""

class SyncRollbackError(Exception):
	pass