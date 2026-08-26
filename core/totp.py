from __future__ import annotations

import math

from base64 import b32decode as decode
from time import time
from urllib.parse import (
	urlparse,
	parse_qs,
	unquote
)

from core.errors import TotpUriError

"""
	Example URI: otpauth://totp/ACME%20Co:john.doe@email.com?secret=HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ&issuer=ACME%20Co&algorithm=SHA1&digits=6&period=30

	@attributes:	- issuer: str		= "ACME"
			- account: str		= "john.doe@email.com"
			- algorithm: str	= "SHA1"
			- digits: int		= 6
			- period: int		= 30
"""
class TOTP_Config:
	def __init__(
		self: TOTP_Config,
		issuer="",
		account="",
		algorithm="SHA1",
		digits=6,
		period=30
	):
		self.issuer		: str	= issuer
		self.account	: str	= account
		self.algorithm	: str	= algorithm
		self.digits		: int	= digits
		self.period		: int	= period

	def seconds_remaining(self: TOTP_Config) -> int:
		return math.ceil(self.period - time() % self.period)	# calculate from unix time 


	def to_json(self: TOTP_Config) -> dict[str, str | int]:
		return {
			"issuer":		self.issuer,
			"account":		self.account,
			"algorithm":	self.algorithm,
			"digits":		f"{self.digits}",
			"period":		f"{self.period}"
		}

	"""
		@raises:
			- TotpUriError
	"""
	@staticmethod
	def from_uri(uri: str) -> tuple[TOTP_Config, str]:
		parsed = urlparse(uri)

		if parsed.scheme != "otpauth" or parsed.netloc != "totp":
			raise TotpUriError

		label = unquote(parsed.path.lstrip("/"))

		if len(label) == 0:
			raise TotpUriError

		# Labels may be either "issuer:account" or just "account"
		if ":" in label:
			label_issuer, account = label.split(":", maxsplit=1)

			if len(label_issuer) == 0 or len(account) == 0:
				raise TotpUriError
		else:
			label_issuer = None
			account = label

		params = parse_qs(parsed.query)

		if (
			"secret" not in params
			or len(params["secret"]) != 1
			or not totp_secret_is_valid(params["secret"][0])
		):
			raise TotpUriError

		secret = params["secret"][0]

		# The issuer may come from the label, the query parameter, or both
		query_issuer = None

		if "issuer" in params:
			if len(params["issuer"]) != 1 or len(params["issuer"][0]) == 0:
				raise TotpUriError

			query_issuer = params["issuer"][0]

			if label_issuer is not None and label_issuer != query_issuer:
				raise TotpUriError

		issuer = query_issuer if query_issuer is not None else label_issuer

		if issuer is None:
			raise TotpUriError

		# SHA1 is the default when algorithm is omitted
		if "algorithm" in params:
			if len(params["algorithm"]) != 1 or params["algorithm"][0].upper() != "SHA1":
				raise TotpUriError

		try:
			# Six digits and a 30-second period are the defaults
			if "digits" in params:
				if len(params["digits"]) != 1 or int(params["digits"][0]) != 6:
					raise TotpUriError

			if "period" in params:
				if len(params["period"]) != 1 or int(params["period"][0]) != 30:
					raise TotpUriError

		except ValueError:
			raise TotpUriError

		totp = TOTP_Config(
			issuer=issuer,
			account=account,
		)

		return totp, secret

def totp_secret_is_valid(secret: str) -> bool:
	try:
		padding = "=" * (-len(secret) % 8)			# padding neccessary padding to reach next length divisible by 8
		decoded = decode(
			s=secret + padding,
			casefold=True
		)

		return len(decoded) >= 10

	except:
		return False