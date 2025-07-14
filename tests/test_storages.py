"""
存储层测试模块

测试 fn_cache.storages 模块中的各种存储实现。
"""

import pytest
import json
import time
from unittest.mock import patch, AsyncMock, Mock
from collections import OrderedDict

from fn_cache.storages import MemoryCacheStorage
from fn_cache.config import CacheConfig, CacheType


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
        
        # 创建一个抛出异常的假缓存对象
        mock_cache = Mock()
        mock_cache.__contains__ = Mock(side_effect=Exception("Test error"))
        
        # 替换缓存对象
        storage._cache = mock_cache
        
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


 