"""
L-Cache 工具函数

提供一些常用的工具函数，用于缓存操作。
"""

import json
import enum
from datetime import datetime
from typing import Any, Optional, Iterable

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from .cache_key import *
from .safe_oper import *
from .serializers import *


def jsonify(var, date_fmt: Optional[str] = "%Y-%m-%d %H:%M:%S"):
    if var is None:
        return None

    return jsonable_encoder(
        var,
        custom_encoder={
            datetime: lambda v: v.strftime(date_fmt),
        },
    )


def strify(var: None | enum.Enum | Any) -> str | None:
    """
    将变量转换为字符串表示
    
    Args:
        var: 要转换的变量
        
    Returns:
        字符串表示，如果输入为None则返回None
    """
    if var is None:
        return var
    if isinstance(var, enum.Enum):
        return var.value
    if isinstance(var, str):
        return var
    if isinstance(var, (dict, BaseModel, list, tuple, set)):
        return json.dumps(jsonify(var), ensure_ascii=False, default=_json_default)
    return str(var)


def _json_default(obj):
    """JSON序列化的默认处理器"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)
