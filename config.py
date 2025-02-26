import os

# Bot Configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN')  # Will be provided via secrets
ADMIN_IDS = [6459253633]  # Admin user ID

# Channel Configuration
REQUIRED_CHANNELS = ["@TMOG9"]  # Channel that users must join

# Fee Configuration
DEFAULT_FEE_PERCENTAGE = 3

# ID Prefixes
ESCROW_ID_PREFIX = "OGESC-"
REDEEM_CODE_PREFIX = "OGRDM-"

# Data file paths
USERS_FILE = "data/users.json"
DEALS_FILE = "data/deals.json"
REDEEM_CODES_FILE = "data/redeem_codes.json"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)