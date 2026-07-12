from __future__ import annotations
from urllib.parse import urlparse, parse_qs, unquote
from base64 import b32decode as decode



"""
	Example URI: otpauth://totp/ACME%20Co:john.doe@email.com?secret=HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ&issuer=ACME%20Co&algorithm=SHA1&digits=6&period=30

	@attributes:	- issuer: str		= "ACME"
			- account: str		= "john.doe@email.com"
			- algorithm: str	= "SHA1"
			- digits: int		= 6
			- period: int		= 30
"""
class TOTP_Config:
	def __init__(self: TOTP_Config, issuer="", account="", algorithm="SHA1", digits=6, period=30):
		self.issuer : str	= issuer
		self.account : str	= account
		self.algorithm : str	= algorithm
		self.digits : int	= digits
		self.period : int	= period


	def to_json(self: TOTP_Config) -> dict[str, str | int]:
		return {
			"issuer":	self.issuer,
			"account":	self.account,
			"algorithm":	self.algorithm,
			"digits":	f"{self.digits}",
			"period":	f"{self.period}"
		}

	@staticmethod
	def from_uri(uri: str) -> tuple[TOTP_Config, str] | None:
		# ParseResult(scheme='otpauth', netloc='totp', path='', params='', query='', fragment='')
		parsed = urlparse(uri)

		if parsed.scheme != "otpauth" or parsed.netloc != "totp":
			return None

		try:
			issuer, account = unquote(parsed.path.lstrip("/")).split(":", maxsplit=1)
			
			if len(issuer) == 0 or len(account) == 0:
				return None

		except ValueError:
			return None

		params = parse_qs(parsed.query)

		if "secret" not in params or len(params["secret"]) != 1 or not totp_secret_is_valid(params["secret"][0]):
			return None
		
		secret = params["secret"][0]

		if "issuer" in params and len(params["issuer"]) > 0:
			if issuer != params["issuer"][0]:
				return None
		
		# if algorithm is explicitly specified
		if "algorithm" in params and len(params["algorithm"]) > 0:
			# for now, we only support SHA1
			if params["algorithm"][0] != "SHA1":
				return None
		# otherwise, we assume algorithm is SHA1 implicitly
		
		try:
			# similarly, we assume (and only support) digits=6
			if "digits" in params and len(params["digits"]) > 0:
				if int(params["digits"][0]) != 6:
					return None

			if "period" in params and len(params["period"]) > 0:
				if int(params["period"][0]) != 30:
					return None

		except ValueError:
			return None

		totp = TOTP_Config(issuer=issuer, account=account)

		return totp, secret


def totp_secret_is_valid(secret: str) -> bool:
	try:
		padding = "=" * (-len(secret) % 8)			# padding neccessary padding to reach next length divisible by 8
		decoded = decode(secret + padding, casefold=True)

		return len(decoded) >= 16

	except Exception:
		return False