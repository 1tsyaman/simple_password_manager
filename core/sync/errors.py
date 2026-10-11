class ClientCredentialsNotFoundError(Exception):
	pass


class AuthDeniedError(Exception):
	pass


class AuthTimeoutError(Exception):
	pass


class SyncBackendError(Exception):
	"""Base error for backend operations, independent of the cloud provider."""


class NoVaultSyncDataError(Exception):
	pass
