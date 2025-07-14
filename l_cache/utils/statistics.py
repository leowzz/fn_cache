"""
缓存统计模块

提供缓存性能监控和统计功能，包括命中率、访问次数、响应时间等指标。
借鉴 aiocache 的设计理念，提供详细的缓存性能分析。
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from collections import defaultdict
from loguru import logger


@dataclass
class CacheStatistics:
    """缓存统计信息"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    total_requests: int = 0
    total_response_time: float = 0.0
    min_r_t: float = float('inf')
    max_r_t: float = 0.0
    # 新增命中/未命中耗时统计
    hit_total_time: float = 0.0
    hit_count: int = 0
    miss_total_time: float = 0.0
    miss_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        """命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    @property
    def miss_rate(self) -> float:
        """未命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.misses / self.total_requests
    
    @property
    def avg_r_t(self) -> float:
        """平均响应时间"""
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time / self.total_requests

    @property
    def avg_hit_time(self) -> float:
        """命中缓存平均耗时"""
        if self.hit_count == 0:
            return 0.0
        return self.hit_total_time / self.hit_count

    @property
    def avg_miss_time(self) -> float:
        """未命中缓存平均耗时"""
        if self.miss_count == 0:
            return 0.0
        return self.miss_total_time / self.miss_count

    def reset(self):
        """重置统计信息"""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0
        self.total_requests = 0
        self.total_response_time = 0.0
        self.min_r_t = float('inf')
        self.max_r_t = 0.0
        self.hit_total_time = 0.0
        self.hit_count = 0
        self.miss_total_time = 0.0
        self.miss_count = 0


class CacheStatisticsManager:
    """缓存统计管理器"""
    
    def __init__(self):
        self._statistics: Dict[str, CacheStatistics] = defaultdict(CacheStatistics)
        self._lock = threading.RLock()
        self._enabled = True
    
    def _update_response_time_stats(self, stats: CacheStatistics, response_time: float):
        """统一更新响应时间相关统计"""
        stats.total_response_time += response_time
        stats.min_r_t = min(stats.min_r_t, response_time)
        stats.max_r_t = max(stats.max_r_t, response_time)

    def record_hit(self, cache_id: str, response_time: float = 0.0):
        """记录缓存命中"""
        if not self._enabled:
            return
        with self._lock:
            stats = self._statistics[cache_id]
            stats.hits += 1
            stats.total_requests += 1
            self._update_response_time_stats(stats, response_time)
            # 新增命中耗时统计
            stats.hit_total_time += response_time
            stats.hit_count += 1

    def record_miss(self, cache_id: str, response_time: float = 0.0):
        """记录缓存未命中"""
        if not self._enabled:
            return
        with self._lock:
            stats = self._statistics[cache_id]
            stats.misses += 1
            stats.total_requests += 1
            self._update_response_time_stats(stats, response_time)
            # 新增未命中耗时统计
            stats.miss_total_time += response_time
            stats.miss_count += 1

    def record_set(self, cache_id: str, response_time: float = 0.0):
        """记录缓存设置"""
        if not self._enabled:
            return
        with self._lock:
            stats = self._statistics[cache_id]
            stats.sets += 1
            self._update_response_time_stats(stats, response_time)

    def record_delete(self, cache_id: str, response_time: float = 0.0):
        """记录缓存删除"""
        if not self._enabled:
            return
        with self._lock:
            stats = self._statistics[cache_id]
            stats.deletes += 1
            self._update_response_time_stats(stats, response_time)
    
    def record_error(self, cache_id: str, error: Exception):
        """记录缓存错误"""
        if not self._enabled:
            return
        
        with self._lock:
            stats = self._statistics[cache_id]
            stats.errors += 1
            logger.error(f"Cache error for {cache_id}: {error}")
    
    def get_statistics(self, cache_id: Optional[str] = None) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            if cache_id:
                if cache_id not in self._statistics:
                    return {}
                stats = self._statistics[cache_id]
                def _f6(val):
                    # 保证小数点后6位，非数字类型直接返回，且不使用科学计数法
                    if isinstance(val, float):
                        return round(val, 6)
                    return val

                return {
                    "cache_id": cache_id,
                    "hits": stats.hits,
                    "misses": stats.misses,
                    "sets": stats.sets,
                    "deletes": stats.deletes,
                    "errors": stats.errors,
                    "total_requests": stats.total_requests,
                    "hit_rate": _f6(stats.hit_rate),
                    "miss_rate": _f6(stats.miss_rate),
                    "avg_r_t": _f6(stats.avg_r_t),
                    "min_r_t": _f6(stats.min_r_t if stats.min_r_t != float('inf') else 0.0),
                    "max_r_t": _f6(stats.max_r_t),
                    # 新增命中/未命中平均耗时
                    "avg_hit_time": _f6(stats.avg_hit_time),
                    "avg_miss_time": _f6(stats.avg_miss_time),
                }
            else:
                return {
                    cache_id: self.get_statistics(cache_id)
                    for cache_id in self._statistics.keys()
                }
    
    def reset_statistics(self, cache_id: Optional[str] = None):
        """重置统计信息"""
        with self._lock:
            if cache_id:
                if cache_id in self._statistics:
                    self._statistics[cache_id].reset()
            else:
                for stats in self._statistics.values():
                    stats.reset()
    
    def enable(self):
        """启用统计"""
        self._enabled = True
    
    def disable(self):
        """禁用统计"""
        self._enabled = False
    
    @property
    def is_enabled(self) -> bool:
        """是否启用统计"""
        return self._enabled


# 全局统计管理器实例
_statistics_manager = CacheStatisticsManager()


def get_cache_statistics(cache_id: Optional[str] = None) -> Dict[str, Any]:
    """获取缓存统计信息"""
    return _statistics_manager.get_statistics(cache_id)


def reset_cache_statistics(cache_id: Optional[str] = None):
    """重置缓存统计信息"""
    _statistics_manager.reset_statistics(cache_id)


def enable_cache_statistics():
    """启用缓存统计"""
    _statistics_manager.enable()


def disable_cache_statistics():
    """禁用缓存统计"""
    _statistics_manager.disable()


def record_cache_hit(cache_id: str, response_time: float = 0.0):
    """记录缓存命中"""
    _statistics_manager.record_hit(cache_id, response_time)


def record_cache_miss(cache_id: str, response_time: float = 0.0):
    """记录缓存未命中"""
    _statistics_manager.record_miss(cache_id, response_time)


def record_cache_set(cache_id: str, response_time: float = 0.0):
    """记录缓存设置"""
    _statistics_manager.record_set(cache_id, response_time)


def record_cache_delete(cache_id: str, response_time: float = 0.0):
    """记录缓存删除"""
    _statistics_manager.record_delete(cache_id, response_time)


def record_cache_error(cache_id: str, error: Exception):
    """记录缓存错误"""
    _statistics_manager.record_error(cache_id, error) 