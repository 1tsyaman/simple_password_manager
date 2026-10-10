from uuid import uuid4

SYNC_SUBSECTIONS = [
	"remote_file_id",
	"version",
	"last_synced_version",
]


def get_default_sync_config() -> dict[str, str | None]:
	return {
		"remote_file_id": None,
		"version": str(uuid4()),
		"last_synced_version": None,
	}
