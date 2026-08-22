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
	def __init__(self, *args: object, reason: str) -> None:
		super().__init__(*args)

		self.reason = reason

class EntryExistsError(Exception):
	pass

def log(message: str, error: Exception | None = None):
	print(message)

	if error is not None:
		print(f"Exception: {error}")

	print("Traceback:")
	traceback.print_exc()
