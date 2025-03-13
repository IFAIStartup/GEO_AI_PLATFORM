class EmptyNextcloudFolderException(Exception):
    """Folder in nextcloud cannot be empty."""


class NotFoundFileNextcloudException(Exception):
    """File(s) ".jpg" or ".jgw" or ".jpg.aux.xml" not found."""

    def __init__(self, filenames):
        self.filenames = filenames
        super().__init__(self.filenames)

    def __str__(self):
        return f"File(s) {self.filenames} not found."


class CRSConversionException(Exception):
    """Error when trying to convert CRS."""


class IncorrectFormatCsvOrJpgException(Exception):
    """Error in the mask format of a jpg file or csv content."""
