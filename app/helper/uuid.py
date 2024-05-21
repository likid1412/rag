"""uuid generator"""

import uuid


def get_uuid() -> str:
    """generate uuid

    Returns:
        str: uuid string
    """

    # FIXME: It's better to use distributed service to generate uuid, like Redis
    return str(uuid.uuid4())
