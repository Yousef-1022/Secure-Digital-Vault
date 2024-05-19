# All magic values have the size of 8 bytes in (UTF-8 and ASCII). UTF-8 is used during serialization

MAGIC_HEADER_START = "@bgnhdr@"
MAGIC_HEADER_END = "@endhdr@"
MAGIC_HEADER_PAD = "@padhdr@"

MAGIC_LOG_START = "$bgnlog$"
MAGIC_LOG_END = "$endlog$"

# All keys representing the structure of the vault

VAULT_CREATION_KEYS = ["Vault Name" , "Vault Extension", "Vault Location", "Password Hint"]
VAULT_KEYS = ["vault_name", "vault_extension", "header_size", "file_size", "trusted_timestamp", "amount_of_files", "is_vault_encrypted"]
MAP_KEYS = ["file_ids", "directory_ids" , "note_ids", "directories", "files", "notes"]
FOOTER_KEYS = ["error_log", "session_log"]

# Utils
TREE_COLUMNS = ["Name", "Type", "Size", "Data Created", "Data Modified"]
DEFAULT_ICON_SIZE = 16      # 16x16
NOTE_LIMIT = 7_340_032      # 7MB
CHUNK_LIMIT = 52_428_800    # 50MB
VAULT_BUFFER_LIMIT = 4096   # 4KB
MINIMUM_WINDOW_WIDTH = 640  # 640x480
MINIMUM_WINDOW_HEIGHT = 480 # 640x480

# All icons
from config import ASSETS_DIR
ICON_1 = f'{ASSETS_DIR}\\icon1.png'
ICON_2 = f'{ASSETS_DIR}\\icon2.png'
ICON_3 = f'{ASSETS_DIR}\\icon3.png'
ICON_4 = f'{ASSETS_DIR}\\icon4.png'
ICON_5 = f'{ASSETS_DIR}\\icon5.png'
ICON_6 = f'{ASSETS_DIR}\\icon6.png'
ICON_7 = f'{ASSETS_DIR}\\icon7.png'