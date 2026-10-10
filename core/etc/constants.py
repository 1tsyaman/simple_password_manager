##			encrypt.py			##
NONCE			= "nonce"
CIPHERTEXT		= "ciphertext"
ASSOCIATED_DATA	= "associated_data"
SALT			= "salt"

RECORD_KEYS = [
	NONCE,
	CIPHERTEXT,
	ASSOCIATED_DATA,
	SALT
]

##			keys.py				##
KEY_LEN				= 32		# 32 bytes = 256-bit AES key
SALT_LEN			= 16		# 16 random bytes is a good salt size

ARGON2_TIME_COST	= 3
ARGON2_MEMORY_COST	= 64 * 1024	# 64 MiB, value is in KiB
ARGON2_PARALLELISM	= 1

##			passwords.py		##
LETTERS_LOWER	= [l for l in "abcdefghijklmnopqrstuvwxyz"]
LETTERS_UPPER	= [l.upper() for l in LETTERS_LOWER]
DIGITS			= [d for d in "1234567890"]
SPECIAL_CHARS	= [s for s in "!\"#$%&'()*+,-./:<=>?@[\\]^_`{|}~"]
MIN_PWD_LENGTH	= 8
PWD_LENGTH		= 24

##			pwd_manager.py		##
PWD			= "pwd"
TOTP_SECRET	= "totp_secret"
TOTP_URI	= "totp_uri"

##			settings.py			##
RELATIVE_CONFIG_PATH = "config/settings.json"

SETTINGS_DICT_SECTIONS	= [
	"Password Generation",
	"Security",
	"Others",
	"HMAC"
]

PWD_GEN_SUBSECTIONS		= [
	"special_chars",
	"password_length",
	"use_uppercase",
	"use_digits",
	"use_special",
]
SECURITY_SUBSECTIONS	= [
	"timeout_duration",
	"lock_on_minimize",
]
OTHERS_SUBSECTIONS		= [
	"theme"
]
HMAC_SUBSECTIONS		= [
	"Salt",
	"Hash"
]

DEFAULT_SETTINGS = {
	"Password Generation": {
		"special_chars":		"!\"#$%&'()*+,-./:<=>?@[\\]^_`{|}~",
		"password_length":		24,
		"use_uppercase":		True,
		"use_digits":			True,
		"use_special":			True
	},

	"Security":	{
		"timeout_duration":		60,
		"lock_on_minimize":		True,
	},

	"Others": {
		"theme":				"Light"
	}
}