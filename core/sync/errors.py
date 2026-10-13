class ClientCredentialsNotFoundError(Exception):
	pass


class AuthDeniedError(Exception):
	pass


class AuthTimeoutError(Exception):
	pass


class SyncBackendError(Exception):
	pass

class HttpError(Exception):
	pass


class NoVaultSyncDataError(Exception):
	pass
