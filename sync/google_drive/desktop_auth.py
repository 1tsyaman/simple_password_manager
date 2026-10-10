from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = [
	"https://www.googleapis.com/auth/drive.appdata"
]


def get_credentials(
	client_credentials_path	: Path,
	token_path				: Path,
) -> Credentials:

	credentials = None

	if token_path.exists():
		# Grab from file
		credentials = Credentials.from_authorized_user_file(
			filename=token_path,
			scopes=SCOPES,
		)

	if not credentials or not credentials.valid:

		# Refresh credentials if expired 
		if (
			credentials
			and credentials.expired
			and credentials.refresh_token
		):
			credentials.refresh(Request())

		else:
			# No credentials -> file doesn't exist or doesn't contain valid credentials
			# Authenticate user
			flow = InstalledAppFlow.from_client_secrets_file(
				client_secrets_file=client_credentials_path,
				scopes=SCOPES,
			)

			credentials = flow.run_local_server(port=0)

		# Create the file along with parent directories
		token_path.parent.mkdir(
			parents=True,
			exist_ok=True,
		)

		# Write credentials to token file
		token_path.write_text(
			credentials.to_json(),
			encoding="utf-8",
		)

	assert isinstance(credentials, Credentials)

	return credentials