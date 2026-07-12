from __future__ import annotations
from urllib.parse import urlparse, parse_qs, unquote

"""
	Example URI: otpauth://totp/ACME%20Co:john.doe@email.com?secret=HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ&issuer=ACME%20Co&algorithm=SHA1&digits=6&period=30

	@attributes:	- secret: str		= "HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ"
			- issuer: str		= "ACME"
			- account: str		= "john.doe@email.com"
			- algorithm: str	= "SHA1"
			- digits: int		= 6
			- period: int		= 30
"""
class TOTP:
	def __init__(self: TOTP, secret="", issuer="", account="", algorithm="SHA1", digits=6, period=30):
		self.secret	= secret
		self.issuer	= issuer
		self.account	= account
		self.algorithm	= algorithm
		self.digits	= digits
		self.period	= period

	def to_json(self: TOTP) -> dict[str, str | int]:
		return {
			"secret":	self.secret,
			"issuer":	self.issuer,
			"account":	self.account,
			"algorithm":	self.algorithm,
			"digits":	self.digits,
			"period":	self.period
		}

	@staticmethod
	def from_uri(uri: str) -> TOTP | None:
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

		if "secret" not in params or len(params["secret"]) != 1 or len(params["secret"][0]) == 0:
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

		return TOTP(secret=secret, issuer=issuer, account=account)

