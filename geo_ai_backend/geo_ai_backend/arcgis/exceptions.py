class NotFoundFileException(Exception):
    """File is not found."""


class TypeFileCSVException(Exception):
    """Type file is not '.csv'."""


class FileCSVAlreadyExistsException(Exception):
    """File '.csv' already exists."""


class TypeFileZipException(Exception):
    """Type file is not '.zip'."""


class ShapefileAlreadyExistsException(Exception):
    """Shapefile already exists."""


class BadRequestTokenException(Exception):
    """Bad request token."""