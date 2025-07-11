"""
存储层测试模块

测试 l_cache.storages 模块中的各种存储实现。
"""

import pytest
import json
import time
from unittest.mock import patch, AsyncMock
from collections import OrderedDict

from l_cache.storages import MemoryCacheStorage, RedisCacheStorage
from l_cache.config import CacheConfig, CacheType


class TestMemoryCacheStorage:
    """内存缓存存储测试类"""

    def test_init_with_ttl_config(self):
        """测试TTL配置初始化"""
        config = CacheConfig(cache_type=CacheType.TTL)
        storage = MemoryCacheStorage(config)
        assert storage.config.cache_type == CacheType.TTL
        assert storage.is_enabled is True

    def test_init_with_lru_config(self):
        """测试LRU配置初始化"""
        config = CacheConfig(cache_type=CacheType.LRU, max_size=100)
        storage = MemoryCacheStorage(config)
        assert storage.config.cache_type == CacheType.LRU
        assert storage.config.max_size == 100
        assert storage.is_enabled is True

    def test_set_sync_ttl_success(self):
        """测试TTL缓存同步设置成功"""
        storage = MemoryCacheStorage(CacheConfig(cache_type=CacheType.TTL))
        result = storage.set_sync("test_key", "test_value", ttl_seconds=60)
        assert result is True

    def test_set_sync_lru_success(self):
        """测试LRU缓存同步设置成功"""
        storage = MemoryCacheStorage(CacheConfig(cache_type=CacheType.LRU))
        result = storage.set_sync("test_key", "test_value", ttl_seconds=60)
        assert result is True

    def test_set_sync_disabled(self):
        """测试禁用状态下的设置"""
        storage = MemoryCacheStorage(CacheConfig())
        storage.is_enabled = False
        result = storage.set_sync("test_key", "test_value", ttl_seconds=60)
        assert result is False

    def test_set_sync_with_exception(self):
        """测试设置时异常处理"""
        storage = MemoryCacheStorage(CacheConfig())
        
        # 模拟异常情况
        with patch.object(storage, '_set_ttl', side_effect=Exception("Test error")):
            result = storage.set_sync("test_key", "test_value", ttl_seconds=60)
            assert result is False

    def test_get_sync_ttl_success(self):
        """测试TTL缓存同步获取成功"""
        storage = MemoryCacheStorage(CacheConfig(cache_type=CacheType.TTL))
        storage.set_sync("test_key", "test_value", ttl_seconds=60)
        value = storage.get_sync("test_key")
        assert value == "test_value"

    def test_get_sync_ttl_expired(self):
        """测试TTL缓存过期"""
        storage = MemoryCacheStorage(CacheConfig(cache_type=CacheType.TTL))
        storage.set_sync("test_key", "test_value", ttl_seconds=1)
        
        # 等待过期
        time.sleep(1.1)
        
        value = storage.get_sync("test_key")
        assert value is None

    def test_get_sync_ttl_not_found(self):
        """测试TTL缓存获取不存在的键"""
        storage = MemoryCacheStorage(CacheConfig(cache_type=CacheType.TTL))
        value = storage.get_sync("nonexistent_key")
        assert value is None

    def test_get_sync_lru_success(self):
        """测试LRU缓存同步获取成功"""
        storage = MemoryCacheStorage(CacheConfig(cache_type=CacheType.LRU))
        storage.set_sync("test_key", "test_value", ttl_seconds=60)
        value = storage.get_sync("test_key")
        assert value == "test_value"

    def test_get_sync_lru_not_found(self):
        """测试LRU缓存获取不存在的键"""
        storage = MemoryCacheStorage(CacheConfig(cache_type=CacheType.LRU))
        value = storage.get_sync("nonexistent_key")
        assert value is None

    def test_get_sync_disabled(self):
        """测试禁用状态下的获取"""
        storage = MemoryCacheStorage(CacheConfig())
        storage.is_enabled = False
        value = storage.get_sync("test_key")
        assert value is None

    def test_delete_sync_success(self):
        """测试同步删除成功"""
        storage = MemoryCacheStorage(CacheConfig())
        storage.set_sync("test_key", "test_value", ttl_seconds=60)
        result = storage.delete_sync("test_key")
        assert result is True
        
        # 验证已删除
        value = storage.get_sync("test_key")
        assert value is None

    def test_delete_sync_not_found(self):
        """测试删除不存在的键"""
        storage = MemoryCacheStorage(CacheConfig())
        result = storage.delete_sync("nonexistent_key")
        assert result is True  # 删除操作总是成功，无论键是否存在

    def test_delete_sync_disabled(self):
        """测试禁用状态下的删除"""
        storage = MemoryCacheStorage(CacheConfig())
        storage.is_enabled = False
        result = storage.delete_sync("test_key")
        assert result is False

    def test_delete_sync_with_exception(self):
        """测试删除时异常处理"""
        storage = MemoryCacheStorage(CacheConfig())
        
        # 模拟异常情况
        with patch.object(storage, '_cache', side_effect=Exception("Test error")):
            result = storage.delete_sync("test_key")
            assert result is False

    def test_lru_eviction(self):
        """测试LRU缓存淘汰"""
        config = CacheConfig(cache_type=CacheType.LRU, max_size=2)
        storage = MemoryCacheStorage(config)
        
        # 添加两个项目
        storage.set_sync("key1", "value1", ttl_seconds=60)
        storage.set_sync("key2", "value2", ttl_seconds=60)
        
        # 添加第三个项目，应该淘汰第一个
        storage.set_sync("key3", "value3", ttl_seconds=60)
        
        # 验证key1被淘汰
        assert storage.get_sync("key1") is None
        assert storage.get_sync("key2") == "value2"
        assert storage.get_sync("key3") == "value3"

    def test_lru_access_order(self):
        """测试LRU访问顺序"""
        config = CacheConfig(cache_type=CacheType.LRU, max_size=2)
        storage = MemoryCacheStorage(config)
        
        # 添加两个项目
        storage.set_sync("key1", "value1", ttl_seconds=60)
        storage.set_sync("key2", "value2", ttl_seconds=60)
        
        # 访问key1，使其成为最近使用的
        storage.get_sync("key1")
        
        # 添加第三个项目，应该淘汰key2
        storage.set_sync("key3", "value3", ttl_seconds=60)
        
        # 验证key2被淘汰，key1保留
        assert storage.get_sync("key1") == "value1"
        assert storage.get_sync("key2") is None
        assert storage.get_sync("key3") == "value3"

    def test_ttl_precision(self):
        """测试TTL精度"""
        storage = MemoryCacheStorage(CacheConfig(cache_type=CacheType.TTL))
        
        # 设置1秒TTL
        storage.set_sync("test_key", "test_value", ttl_seconds=1)
        
        # 立即获取应该成功
        value = storage.get_sync("test_key")
        assert value == "test_value"
        
        # 等待过期
        time.sleep(1.1)
        
        # 过期后应该返回None
        value = storage.get_sync("test_key")
        assert value is None

    def test_complex_data_types(self):
        """测试复杂数据类型"""
        storage = MemoryCacheStorage(CacheConfig())
        
        # 测试字典
        test_dict = {"key": "value", "list": [1, 2, 3]}
        storage.set_sync("dict_key", test_dict, ttl_seconds=60)
        assert storage.get_sync("dict_key") == test_dict
        
        # 测试列表
        test_list = [1, "string", {"nested": "value"}]
        storage.set_sync("list_key", test_list, ttl_seconds=60)
        assert storage.get_sync("list_key") == test_list
        
        # 测试元组
        test_tuple = (1, 2, 3)
        storage.set_sync("tuple_key", test_tuple, ttl_seconds=60)
        assert storage.get_sync("tuple_key") == test_tuple

    @pytest.mark.asyncio
    async def test_async_operations(self):
        """测试异步操作"""
        storage = MemoryCacheStorage(CacheConfig())
        
        # 异步设置
        result = await storage.set("async_key", "async_value", ttl_seconds=60)
        assert result is True
        
        # 异步获取
        value = await storage.get("async_key")
        assert value == "async_value"
        
        # 异步删除
        result = await storage.delete("async_key")
        assert result is True
        
        # 验证已删除
        value = await storage.get("async_key")
        assert value is None

    def test_storage_cleanup(self):
        """测试存储清理"""
        storage = MemoryCacheStorage(CacheConfig(cache_type=CacheType.TTL))
        
        # 添加一些数据
        storage.set_sync("key1", "value1", ttl_seconds=1)
        storage.set_sync("key2", "value2", ttl_seconds=60)
        
        # 等待key1过期
        time.sleep(1.1)
        
        # 获取key1应该触发清理
        value = storage.get_sync("key1")
        assert value is None
        
        # key2应该仍然存在
        value = storage.get_sync("key2")
        assert value == "value2"


class TestRedisCacheStorage:
    """Redis缓存存储测试类"""

    def test_init(self):
        """测试初始化"""
        config = CacheConfig(prefix="test:")
        storage = RedisCacheStorage(config)
        assert storage.config == config
        assert storage._prefix == "test:"
        assert storage._redis is None

    @pytest.mark.asyncio
    async def test_get_redis_connection_success(self):
        """测试成功获取Redis连接"""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis_class.return_value = mock_redis
            
            storage = RedisCacheStorage(CacheConfig())
            redis_client = await storage._get_redis()
            
            assert redis_client == mock_redis
            mock_redis_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_redis_connection_import_error(self):
        """测试Redis导入错误"""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'redis'")):
            storage = RedisCacheStorage(CacheConfig())
            
            with pytest.raises(ImportError, match="Redis is required"):
                await storage._get_redis()

    @pytest.mark.asyncio
    async def test_get_redis_connection_error(self):
        """测试Redis连接错误"""
        with patch('redis.asyncio.Redis', side_effect=Exception("Connection failed")):
            storage = RedisCacheStorage(CacheConfig())
            
            with pytest.raises(Exception, match="Connection failed"):
                await storage._get_redis()

    @pytest.mark.asyncio
    async def test_get_success(self):
        """测试成功获取缓存"""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = json.dumps("test_value")
            mock_redis_class.return_value = mock_redis
            
            storage = RedisCacheStorage(CacheConfig(prefix="test:"))
            storage._redis = mock_redis
            
            value = await storage.get("test_key")
            assert value == "test_value"
            mock_redis.get.assert_called_once_with("test:test_key")

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """测试获取不存在的缓存"""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_redis_class.return_value = mock_redis
            
            storage = RedisCacheStorage(CacheConfig())
            storage._redis = mock_redis
            
            value = await storage.get("test_key")
            assert value is None

    @pytest.mark.asyncio
    async def test_get_with_json_error(self):
        """测试获取时JSON解析错误"""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = "invalid_json"
            mock_redis_class.return_value = mock_redis
            
            storage = RedisCacheStorage(CacheConfig())
            storage._redis = mock_redis
            
            value = await storage.get("test_key")
            assert value == "invalid_json"  # 返回原始值

    @pytest.mark.asyncio
    async def test_get_with_redis_error(self):
        """测试Redis错误时的获取"""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.get.side_effect = Exception("Redis error")
            mock_redis_class.return_value = mock_redis
            
            storage = RedisCacheStorage(CacheConfig())
            storage._redis = mock_redis
            
            value = await storage.get("test_key")
            assert value is None

    @pytest.mark.asyncio
    async def test_set_success(self):
        """测试成功设置缓存"""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.setex.return_value = True
            mock_redis_class.return_value = mock_redis
    
            storage = RedisCacheStorage(CacheConfig(prefix="test:"))
            storage._redis = mock_redis
    
            result = await storage.set("test_key", "test_value", ttl_seconds=60)
            assert result is True
            mock_redis.setex.assert_called_once_with("test:test_key", 60, "test_value")

    @pytest.mark.asyncio
    async def test_set_complex_data(self):
        """测试设置复杂数据"""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.setex.return_value = True
            mock_redis_class.return_value = mock_redis

            storage = RedisCacheStorage(CacheConfig())
            storage._redis = mock_redis

            test_data = {"key": "value", "list": [1, 2, 3]}
            result = await storage.set("test_key", test_data, ttl_seconds=60)
            assert result is True
            mock_redis.setex.assert_called_once_with("test_key", 60, json.dumps(test_data))

    @pytest.mark.asyncio
    async def test_set_with_redis_error(self):
        """测试Redis错误时的设置"""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.setex.side_effect = Exception("Redis error")
            mock_redis_class.return_value = mock_redis

            storage = RedisCacheStorage(CacheConfig())
            storage._redis = mock_redis

            result = await storage.set("test_key", "test_value", ttl_seconds=60)
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_success(self):
        """测试成功删除缓存"""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.delete.return_value = 1
            mock_redis_class.return_value = mock_redis
            
            storage = RedisCacheStorage(CacheConfig(prefix="test:"))
            storage._redis = mock_redis
            
            result = await storage.delete("test_key")
            assert result is True
            mock_redis.delete.assert_called_once_with("test:test_key")

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        """测试删除不存在的键"""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.delete.return_value = 0
            mock_redis_class.return_value = mock_redis
            
            storage = RedisCacheStorage(CacheConfig())
            storage._redis = mock_redis
            
            result = await storage.delete("test_key")
            assert result is True  # Redis删除不存在的键返回0，但我们返回True

    @pytest.mark.asyncio
    async def test_delete_with_redis_error(self):
        """测试Redis错误时的删除"""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.delete.side_effect = Exception("Redis error")
            mock_redis_class.return_value = mock_redis
            
            storage = RedisCacheStorage(CacheConfig())
            storage._redis = mock_redis
            
            result = await storage.delete("test_key")
            assert result is False

    def test_sync_operations_not_supported(self):
        """测试同步操作不支持"""
        storage = RedisCacheStorage(CacheConfig())
        
        with pytest.raises(NotImplementedError):
            storage.get_sync("test_key")
        
        with pytest.raises(NotImplementedError):
            storage.set_sync("test_key", "test_value", ttl_seconds=60)
        
        with pytest.raises(NotImplementedError):
            storage.delete_sync("test_key")

    @pytest.mark.asyncio
    async def test_connection_reuse(self):
        """测试连接复用"""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis_class.return_value = mock_redis
            
            storage = RedisCacheStorage(CacheConfig())
            
            # 第一次获取连接
            redis1 = await storage._get_redis()
            
            # 第二次获取连接
            redis2 = await storage._get_redis()
            
            # 应该是同一个连接
            assert redis1 is redis2
            assert mock_redis_class.call_count == 1

    @pytest.mark.asyncio
    async def test_prefix_handling(self):
        """测试前缀处理"""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = json.dumps("test_value")
            mock_redis.setex.return_value = True
            mock_redis.delete.return_value = 1
            mock_redis_class.return_value = mock_redis
    
            storage = RedisCacheStorage(CacheConfig(prefix="custom:"))
            storage._redis = mock_redis
    
            # 测试设置
            await storage.set("test_key", "test_value", ttl_seconds=60)
            mock_redis.setex.assert_called_with("custom:test_key", 60, "test_value")
            
            # 测试获取
            await storage.get("test_key")
            mock_redis.get.assert_called_with("custom:test_key")
            
            # 测试删除
            await storage.delete("test_key")
            mock_redis.delete.assert_called_with("custom:test_key") 