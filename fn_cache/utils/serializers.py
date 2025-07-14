"""
序列化器模块

提供多种序列化格式支持，包括 JSON、Pickle、MessagePack 等。
借鉴 aiocache 的设计理念，提供统一的序列化接口。
"""

import json
import pickle
import base64
from abc import ABC, abstractmethod
from typing import Any, Optional
from loguru import logger

try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False
    logger.warning("MessagePack not available. Install with: pip install msgpack")


class Serializer(ABC):
    """序列化器抽象基类"""
    
    @abstractmethod
    def serialize(self, value: Any) -> str:
        """序列化值"""
        pass
    
    @abstractmethod
    def deserialize(self, value: str) -> Any:
        """反序列化值"""
        pass
    
    @property
    @abstractmethod
    def content_type(self) -> str:
        """内容类型"""
        pass


class JsonSerializer(Serializer):
    """JSON序列化器"""
    
    def __init__(self, ensure_ascii: bool = False, default: Optional[callable] = None):
        """
        初始化JSON序列化器
        
        Args:
            ensure_ascii: 是否确保ASCII编码
            default: 自定义序列化函数
        """
        self.ensure_ascii = ensure_ascii
        self.default = default
    
    def serialize(self, value: Any) -> str:
        """序列化值为JSON字符串"""
        try:
            return json.dumps(value, ensure_ascii=self.ensure_ascii, default=self.default)
        except (TypeError, ValueError) as e:
            logger.error(f"JSON serialization failed: {e}")
            raise
    
    def deserialize(self, value: str) -> Any:
        """从JSON字符串反序列化值"""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"JSON deserialization failed: {e}")
            raise
    
    @property
    def content_type(self) -> str:
        return "application/json"


class PickleSerializer(Serializer):
    """Pickle序列化器"""
    
    def __init__(self, protocol: int = pickle.HIGHEST_PROTOCOL):
        """
        初始化Pickle序列化器
        
        Args:
            protocol: Pickle协议版本
        """
        self.protocol = protocol
    
    def serialize(self, value: Any) -> str:
        """序列化值为Pickle字符串"""
        try:
            pickled = pickle.dumps(value, protocol=self.protocol)
            return base64.b64encode(pickled).decode('utf-8')
        except (pickle.PicklingError, TypeError) as e:
            logger.error(f"Pickle serialization failed: {e}")
            raise
    
    def deserialize(self, value: str) -> Any:
        """从Pickle字符串反序列化值"""
        try:
            pickled = base64.b64decode(value.encode('utf-8'))
            return pickle.loads(pickled)
        except (pickle.UnpicklingError, TypeError, ValueError) as e:
            logger.error(f"Pickle deserialization failed: {e}")
            raise
    
    @property
    def content_type(self) -> str:
        return "application/x-python-pickle"


class MessagePackSerializer(Serializer):
    """MessagePack序列化器"""
    
    def __init__(self, use_bin_type: bool = True):
        """
        初始化MessagePack序列化器
        
        Args:
            use_bin_type: 是否使用二进制类型
        """
        if not MSGPACK_AVAILABLE:
            raise ImportError("MessagePack not available. Install with: pip install msgpack")
        self.use_bin_type = use_bin_type
    
    def serialize(self, value: Any) -> str:
        """序列化值为MessagePack字符串"""
        try:
            packed = msgpack.packb(value, use_bin_type=self.use_bin_type)
            return base64.b64encode(packed).decode('utf-8')
        except (msgpack.PackException, TypeError) as e:
            logger.error(f"MessagePack serialization failed: {e}")
            raise
    
    def deserialize(self, value: str) -> Any:
        """从MessagePack字符串反序列化值"""
        try:
            packed = base64.b64decode(value.encode('utf-8'))
            return msgpack.unpackb(packed, raw=False)
        except (msgpack.UnpackException, TypeError, ValueError) as e:
            logger.error(f"MessagePack deserialization failed: {e}")
            raise
    
    @property
    def content_type(self) -> str:
        return "application/x-msgpack"


class StringSerializer(Serializer):
    """字符串序列化器"""
    
    def serialize(self, value: Any) -> str:
        """序列化值为字符串"""
        try:
            return str(value)
        except Exception as e:
            logger.error(f"String serialization failed: {e}")
            raise
    
    def deserialize(self, value: str) -> Any:
        """从字符串反序列化值（返回原字符串）"""
        return value
    
    @property
    def content_type(self) -> str:
        return "text/plain"


def get_serializer(serializer_type: str, **kwargs) -> Serializer:
    """
    根据类型获取序列化器
    
    Args:
        serializer_type: 序列化器类型
        **kwargs: 序列化器参数
        
    Returns:
        序列化器实例
    """
    serializer_map = {
        'json': JsonSerializer,
        'pickle': PickleSerializer,
        'msgpack': MessagePackSerializer,
        'string': StringSerializer,
    }
    
    if serializer_type not in serializer_map:
        raise ValueError(f"Unsupported serializer type: {serializer_type}")
    
    serializer_class = serializer_map[serializer_type]
    
    # 特殊处理MessagePack
    if serializer_type == 'msgpack' and not MSGPACK_AVAILABLE:
        logger.warning("MessagePack not available, falling back to JSON")
        serializer_class = JsonSerializer
    
    return serializer_class(**kwargs)
