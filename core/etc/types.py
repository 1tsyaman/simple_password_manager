# Union type alias
type config_t			= str | int | bool
type vault_sync_data_t	= dict[str, str | None]
type sync_data_t		= dict[str, vault_sync_data_t]