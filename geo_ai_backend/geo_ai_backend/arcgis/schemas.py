from pydantic import BaseModel


class TokenArcgisSchemas(BaseModel):
    token: str
    expires: str
    ssl: str