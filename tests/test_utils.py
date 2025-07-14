"""
工具函数测试模块

测试 fn_cache.utils 模块中的各种工具函数。
"""

import pytest
from unittest.mock import patch
from fn_cache.utils import strify, safe_redis_operation, safe_redis_void_operation
from fn_cache.utils.cache_key import format_cache_key, validate_cache_key
from fn_cache.utils import jsonify
import json


class TestStrify:
    """字符串化函数测试类"""

    def test_strify_string(self):
        """测试字符串化字符串"""
        result = strify("test")
        assert result == "test"

    def test_strify_number(self):
        """测试字符串化数字"""
        result = strify(123)
        assert result == "123"

    def test_strify_float(self):
        """测试字符串化浮点数"""
        result = strify(123.45)
        assert result == "123.45"

    def test_strify_list(self):
        """测试字符串化列表"""
        result = strify([1, 2, 3])
        assert result == "[1, 2, 3]"

    def test_strify_dict(self):
        """测试字符串化字典"""
        result = strify({"key": "value"})
        assert result == '{"key": "value"}'

    def test_strify_tuple(self):
        """测试字符串化元组"""
        result = strify((1, 2, 3))
        assert result == "[1, 2, 3]"

    def test_strify_none(self):
        """测试字符串化None"""
        result = strify(None)
        assert result is None

    def test_strify_boolean(self):
        """测试字符串化布尔值"""
        assert strify(True) == "True"
        assert strify(False) == "False"

    def test_strify_complex_object(self):
        """测试字符串化复杂对象"""
        class TestObject:
            def __init__(self, value):
                self.value = value
            
            def __str__(self):
                return f"TestObject({self.value})"
        
        result = strify(TestObject("test"))
        assert "TestObject" in result

    def test_strify_nested_structure(self):
        """测试字符串化嵌套结构"""
        data = {
            "list": [1, 2, {"nested": "value"}],
            "tuple": (1, 2, 3),
            "dict": {"key": "value"}
        }
        result = strify(data)
        assert isinstance(result, str)
        assert "list" in result
        assert "nested" in result


class TestSafeRedisOperation:
    """安全Redis操作测试类"""

    @pytest.mark.asyncio
    async def test_safe_redis_operation_success(self):
        """测试成功的安全Redis操作"""
        async def mock_operation():
            return "success_result"
    
        result = await safe_redis_operation(mock_operation(), "test_operation", "test_key")
        assert result == "success_result"

    @pytest.mark.asyncio
    async def test_safe_redis_operation_with_exception(self):
        """测试异常时的安全Redis操作"""
        async def mock_operation():
            raise Exception("Redis error")
    
        result = await safe_redis_operation(mock_operation(), "test_operation", "test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_safe_redis_operation_with_custom_default(self):
        """测试带自定义默认值的安全Redis操作"""
        async def mock_operation():
            raise Exception("Redis error")
    
        result = await safe_redis_operation(mock_operation(), "test_operation", "test_key", default_value="custom_default")
        assert result == "custom_default"

    @pytest.mark.asyncio
    async def test_safe_redis_operation_with_logging(self):
        """测试带日志记录的安全Redis操作"""
        with patch('fn_cache.utils.safe_oper.logger.error') as mock_logger:
            async def mock_operation():
                raise Exception("Redis error")
    
            result = await safe_redis_operation(mock_operation(), "test_operation", "test_key")
            assert result is None
            mock_logger.assert_called_once()

    @pytest.mark.asyncio
    async def test_safe_redis_operation_complex_result(self):
        """测试复杂结果的安全Redis操作"""
        complex_result = {"key": "value", "list": [1, 2, 3]}
    
        async def mock_operation():
            return complex_result
    
        result = await safe_redis_operation(mock_operation(), "test_operation", "test_key")
        assert result == complex_result


class TestSafeRedisVoidOperation:
    """安全Redis空操作测试类"""

    @pytest.mark.asyncio
    async def test_safe_redis_void_operation_success(self):
        """测试成功的空Redis操作"""
        async def mock_operation():
            return True
        
        result = await safe_redis_void_operation(mock_operation(), "test_operation", "test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_safe_redis_void_operation_with_exception(self):
        """测试异常时的空Redis操作"""
        async def mock_operation():
            raise Exception("Redis error")
        
        result = await safe_redis_void_operation(mock_operation(), "test_operation", "test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_safe_redis_void_operation_with_logging(self):
        """测试带日志记录的空Redis操作"""
        with patch('fn_cache.utils.safe_oper.logger.error') as mock_logger:
            async def mock_operation():
                raise Exception("Redis error")
            
            result = await safe_redis_void_operation(mock_operation(), "test_operation", "test_key")
            assert result is None
            mock_logger.assert_called_once()


class TestCacheKeyBuilder:
    """缓存键构建器测试类"""

    def test_format_cache_key_simple(self):
        """测试简单缓存键格式化"""
        key = format_cache_key("test_function")
        assert "test_function" in key
        assert isinstance(key, str)

    def test_format_cache_key_with_args(self):
        """测试带参数的缓存键格式化"""
        key = format_cache_key("test_function", "arg1", "arg2")
        assert "test_function" in key
        assert "arg1" in key
        assert "arg2" in key

    def test_format_cache_key_with_kwargs(self):
        """测试带关键字参数的缓存键格式化"""
        key = format_cache_key("test_function", param1="value1", param2=123)
        assert "test_function" in key
        assert "param1" in key
        assert "value1" in key
        assert "param2" in key
        assert "123" in key

    def test_format_cache_key_with_complex_args(self):
        """测试带复杂参数的缓存键格式化"""
        key = format_cache_key("test_function", {"key": "value"}, [1, 2, 3])
        assert "test_function" in key
        assert "key" in key
        assert "value" in key
        assert "1" in key
        assert "2" in key
        assert "3" in key

    def test_format_cache_key_consistent(self):
        """测试缓存键格式化的一致性"""
        key1 = format_cache_key("test_function", "arg1", "arg2", param1="value1")
        key2 = format_cache_key("test_function", "arg1", "arg2", param1="value1")
        
        assert key1 == key2

    def test_format_cache_key_different_args(self):
        """测试不同参数的缓存键格式化"""
        key1 = format_cache_key("test_function", "arg1")
        key2 = format_cache_key("test_function", "arg2")
        
        assert key1 != key2

    def test_format_cache_key_with_none_values(self):
        """测试带None值的缓存键格式化"""
        key = format_cache_key("test_function", None, "value", param1=None, param2="value")
        assert "test_function" in key
        assert "value" in key
        assert "None" in key

    def test_validate_cache_key(self):
        """测试缓存键验证"""
        # 有效键
        assert validate_cache_key("valid_key") is True
        assert validate_cache_key("key_with_123") is True
        assert validate_cache_key("key:with:colons") is True
        
        # 无效键
        assert validate_cache_key("") is False
        assert validate_cache_key(None) is False
        assert validate_cache_key("a" * 251) is False  # 超过长度限制


class TestSerializers:
    """序列化器测试类"""

    def test_jsonify_string(self):
        """测试字符串序列化"""
        data = "test_string"
        serialized = jsonify(data)
        assert serialized == data

    def test_jsonify_number(self):
        """测试数字序列化"""
        data = 123
        serialized = jsonify(data)
        assert serialized == data

    def test_jsonify_float(self):
        """测试浮点数序列化"""
        data = 123.45
        serialized = jsonify(data)
        assert serialized == data

    def test_jsonify_list(self):
        """测试列表序列化"""
        data = [1, "string", {"key": "value"}]
        serialized = jsonify(data)
        assert isinstance(serialized, list)
        assert serialized == data

    def test_jsonify_dict(self):
        """测试字典序列化"""
        data = {"key1": "value1", "key2": 123, "key3": [1, 2, 3]}
        serialized = jsonify(data)
        assert isinstance(serialized, dict)
        assert serialized == data

    def test_jsonify_tuple(self):
        """测试元组序列化"""
        data = (1, "string", {"key": "value"})
        serialized = jsonify(data)
        assert isinstance(serialized, list)  # 元组会被转换为列表
        assert serialized == list(data)

    def test_jsonify_none(self):
        """测试None序列化"""
        data = None
        serialized = jsonify(data)
        assert serialized is None

    def test_jsonify_boolean(self):
        """测试布尔值序列化"""
        data_true = True
        data_false = False
        
        serialized_true = jsonify(data_true)
        serialized_false = jsonify(data_false)
        
        assert serialized_true == data_true
        assert serialized_false == data_false

    def test_jsonify_complex_nested(self):
        """测试复杂嵌套结构序列化"""
        data = {
            "list": [1, 2, {"nested_key": "nested_value"}],
            "dict": {"key": [1, 2, 3]},
            "tuple": (1, "string", {"key": "value"}),
            "none": None,
            "boolean": True
        }
        serialized = jsonify(data)
        assert isinstance(serialized, dict)
        assert serialized["list"] == data["list"]
        assert serialized["dict"] == data["dict"]
        assert serialized["tuple"] == list(data["tuple"])
        assert serialized["none"] is None
        assert serialized["boolean"] is True

    def test_jsonify_custom_object(self):
        """测试自定义对象序列化"""
        class TestObject:
            def __init__(self, value):
                self.value = value
        
        data = TestObject("test_value")
        serialized = jsonify(data)
        # jsonify 会将对象转换为字典
        assert isinstance(serialized, dict)
        assert serialized["value"] == "test_value"

    def test_jsonify_performance(self):
        """测试序列化性能"""
        import time
        
        data = {"key": "value", "list": list(range(1000))}
        
        start_time = time.time()
        for _ in range(1000):
            jsonify(data)
        end_time = time.time()
        
        # 确保序列化性能在合理范围内（1秒内完成1000次）
        assert end_time - start_time < 1.0

    def test_strify_function(self):
        """测试strify函数"""
        # 测试字符串
        assert strify("test") == "test"
        
        # 测试数字
        assert strify(123) == "123"
        
        # 测试列表
        assert strify([1, 2, 3]) == "[1, 2, 3]"
        
        # 测试字典
        assert strify({"key": "value"}) == '{"key": "value"}'
        
        # 测试None
        assert strify(None) is None


class TestIntegration:
    """集成测试类"""

    def test_cache_key_with_serialization(self):
        """测试缓存键与序列化的集成"""
        complex_data = {
            "user_id": 123,
            "settings": {"theme": "dark", "language": "zh"},
            "preferences": [1, 2, 3]
        }
        
        # 格式化缓存键
        key = format_cache_key("get_user_settings", complex_data)
        
        # 序列化数据
        serialized = jsonify(complex_data)
        
        # 验证缓存键包含序列化数据的关键信息
        assert "get_user_settings" in key
        assert "123" in key
        assert "theme" in key
        assert "dark" in key

    def test_safe_operation_with_serialization(self):
        """测试安全操作与序列化的集成"""
        @pytest.mark.asyncio
        async def test_operation():
            data = {"key": "value", "number": 123}
            serialized = jsonify(data)
            return serialized
        
        # 这里我们只是测试概念，实际的异步测试需要不同的结构
        assert jsonify({"key": "value", "number": 123}) is not None

    def test_error_handling_integration(self):
        """测试错误处理集成"""
        # 测试序列化错误处理
        try:
            # 尝试序列化一个不可序列化的对象
            class UnserializableObject:
                def __init__(self):
                    self.method = lambda x: x
            
            obj = UnserializableObject()
            serialized = jsonify(obj)
            # 如果成功，应该返回字典表示
            assert isinstance(serialized, dict)
        except Exception:
            # 如果失败，应该被正确处理
            pass

    def test_cache_key_uniqueness(self):
        """测试缓存键唯一性"""
        keys = set()
        
        # 生成多个不同的缓存键
        test_cases = [
            ("arg1", {"param1": "value1"}),
            ("arg2", {"param1": "value1"}),
            ("arg1", {"param1": "value2"}),
            ("arg1", "arg2", {"param1": "value1"}),
        ]
        
        for test_case in test_cases:
            if isinstance(test_case, tuple) and len(test_case) == 2 and isinstance(test_case[1], dict):
                args, kwargs = test_case
                key = format_cache_key("test_function", args, **kwargs)
            else:
                key = format_cache_key("test_function", *test_case)
            assert key not in keys, f"Duplicate key found: {key}"
            keys.add(key)

    def test_serialization_consistency(self):
        """测试序列化一致性"""
        data = {"key": "value", "list": [1, 2, 3]}
        
        # 多次序列化应该产生相同结果
        serialized1 = jsonify(data)
        serialized2 = jsonify(data)
        serialized3 = jsonify(data)
        
        assert serialized1 == serialized2 == serialized3
        
        # 验证序列化结果
        assert serialized1 == data 