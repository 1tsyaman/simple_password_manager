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


class NoVaultSyncDataError(Exception):
	pass
