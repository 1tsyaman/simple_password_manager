import traceback

class KeyLengthError(Exception):
	pass

class KeyDerivationError(Exception):
	pass

class VaultFormatError(Exception):
	pass

class CorruptedVaultError(Exception):
	pass

class PasswordError(Exception):
	pass

class PasswordRequirementsError(PasswordError):
	def __init__(
		self,
		*args: object,
		reason: str
	) -> None:
		super().__init__(*args)

		self.reason = reason

class EntryExistsError(Exception):
	pass

class NoSuchEntryError(Exception):
	pass

class EntryHasNoTotp(Exception):
	pass

class TotpUriError(Exception):
	pass

class TotpQRCodeError(Exception):
	pass

class InvalidEntryJSON(Exception):
	pass

class ImageOpenError(Exception):
	pass

class QRDecodeError(Exception):
	pass

class NoSettingsFileError(Exception):
	pass

class InvalidJSONError(Exception):
	pass

class InvalidSettingsFile(Exception):
	pass

class SettingsFileModifiedError(Exception):
	pass

class SettingsKeyNotSetError(Exception):
	pass

class SettingsLoadError(Exception):
	pass

"""
	Raised whenever some impossible incosistency occures.
	
	Should not be ignored, as reencrypting the vault in an inconsistent
		state could result in data loss
"""
class InconsistentVaultState(Exception):
	pass

def log(
	message: str,
	error: Exception | None = None
):
	print(message)

	if error is not None:
		print(f"Exception: {error}")

	print("Traceback:")
	traceback.print_exc()
