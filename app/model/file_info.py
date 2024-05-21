"""file info models"""

from pydantic import BaseModel


class FileInfo(BaseModel):
    """file info model"""

    file_id: str
    file_name: str
    file_unique_name: str

    def is_valid(self) -> bool:
        """check FileInfo instance is valid

        Returns:
            bool: True if all variables have value, otherwise False
        """

        if (
            len(self.file_id) == 0
            or len(self.file_name) == 0
            or len(self.file_unique_name) == 0
        ):
            return False

        return True
