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

class SyncRollbackError(Exception):
	pass