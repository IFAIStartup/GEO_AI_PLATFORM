class SaveImageException(Exception):
    """Failed to save image."""


class NotFound(Exception):
    """File not found."""


class NotFoundConfigFileException(Exception):
    """Not found config file '.pbtxt'."""


class PathNotFoundException(Exception):
    """Path not found."""


class NextcloudNotFoundFolders(Exception):
    """Nextcloud not found folders."""


class FolderIsEmptyException(Exception):
    """Folder is empty."""


class InvalidDirectoryStructure(Exception):
    """Invalid directory structure."""


class FolderWithMLIsNotExistsException(Exception):
    """Folder with ML model is not exists."""


class NotFoundJson(Exception):
    """Two json not found"""


class NotFoundTfw(Exception):
    """Two tfw not found"""


class MLServerIsNotRespond(Exception):
    """ ML server is not responding"""


class NextcloudIsNotResponding(Exception):
    """Nextcloud is not responding."""


class NotTrainingTypeModel(Exception):
    """This type of model is not available for training."""
