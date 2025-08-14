from pydantic import BaseModel


class JoinRequestDTO(BaseModel):
    user_uuid: str
