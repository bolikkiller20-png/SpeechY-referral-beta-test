import base64
import hashlib
import random
import string

from config import settings


class ReferralUtils:
    @staticmethod
    def generate_referral_code(
            user_id: int,
            length: int = settings.get_REFERRAL_CODE_LENGTH(),
            salt: str = settings.get_SPEECHY_SALT()
    ) -> str:
        """
        Gen unique hashed referral code based on special salt
        :param user_id:
        :param length:
        :param salt:
        :return: code
        """
        unique_string = f"{user_id}_{salt}"

        hash_obj = hashlib.blake2s(
            unique_string.encode(),
            digest_size=5
        )

        code = base64.b32encode(hash_obj.digest()).decode().replace('=', '').upper()

        return code[:length]

    
