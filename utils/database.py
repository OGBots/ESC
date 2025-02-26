import json
import os
from typing import Dict, List, Union
from config import USERS_FILE, DEALS_FILE, REDEEM_CODES_FILE

class Database:
    @staticmethod
    def load_data(file_path: str) -> dict:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}

    @staticmethod
    def save_data(file_path: str, data: dict):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    @classmethod
    def get_user(cls, user_id: int) -> dict:
        users = cls.load_data(USERS_FILE)
        return users.get(str(user_id), {})

    @classmethod
    def save_user(cls, user_id: int, user_data: dict):
        users = cls.load_data(USERS_FILE)
        users[str(user_id)] = user_data
        cls.save_data(USERS_FILE, users)

    @classmethod
    def get_deal(cls, deal_id: str) -> dict:
        deals = cls.load_data(DEALS_FILE)
        return deals.get(deal_id, {})

    @classmethod
    def save_deal(cls, deal_id: str, deal_data: dict):
        deals = cls.load_data(DEALS_FILE)
        deals[deal_id] = deal_data
        cls.save_data(DEALS_FILE, deals)

    @classmethod
    def get_redeem_code(cls, code: str) -> dict:
        codes = cls.load_data(REDEEM_CODES_FILE)
        return codes.get(code, {})

    @classmethod
    def save_redeem_code(cls, code: str, code_data: dict):
        codes = cls.load_data(REDEEM_CODES_FILE)
        codes[code] = code_data
        cls.save_data(REDEEM_CODES_FILE, codes)
