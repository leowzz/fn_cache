import enum
import json
from datetime import datetime
from typing import Optional, Iterable

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel


def jsonify(var, date_fmt: Optional[str] = '%Y-%m-%d %H:%M:%S'):
    if var is None:
        return None

    return jsonable_encoder(var, custom_encoder={
        datetime: lambda v: v.strftime(date_fmt),
    })


def strify(var: None | enum.Enum | dict | BaseModel | str | list | Iterable) -> str | None:
    if var is None:
        return var
    if isinstance(var, enum.Enum):
        return var.value
    if isinstance(var, str):
        return var
    if isinstance(var, (dict, BaseModel, list, Iterable)):
        return json.dumps(jsonify(var))
    return str(var)
