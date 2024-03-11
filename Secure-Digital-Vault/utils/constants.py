# All magic values have the size of 8 bytes in (UTF-8 and ASCII). UTF-8 is used during serialization

MAGIC_HEADER_START = "@bgnhdr@"
MAGIC_HEADER_END = "@endhdr@"

MAGIC_MAP_START = "#mapbgn#"
MAGIC_MAP_END = "#mapend#"

MAGIC_FOOTER_START = "@ftrbgn@"
MAGIC_FOOTER_END = "@endftr@"

MAGIC_ERROR_LOG_START = "!errbgn!"
MAGIC_ERROR_LOG_END = "!errend!"

MAGIC_NORMAL_LOG_START = "$bgnlog$"
MAGIC_NORMAL_LOG_END = "$endlog$"

# All keys representing the structure of the vault

VAULT_KEYS = ["vault_name", "vault_size", "header_size", "footer_size", "file_size", "trusted_timestamp", "amount_of_files", "is_vault_encrypted", "is_extension_valid"]
MAP_KEYS = ["file_ids", "directory_ids" , "voice_note_ids", "directories", "files", "voice_notes"]
