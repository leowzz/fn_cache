fn_cache 文档
=============

欢迎使用 fn_cache - 轻量级通用缓存库！

.. toctree::
   :maxdepth: 2
   :caption: 快速开始

   installation
   quickstart
   examples/basic

.. toctree::
   :maxdepth: 2
   :caption: 核心概念

   concepts/decorators
   concepts/manager
   concepts/storages
   concepts/config
   concepts/versioning

.. toctree::
   :maxdepth: 2
   :caption: 进阶用法

   advanced/keys_serialization
   advanced/memory_monitoring
   advanced/async_support
   advanced/custom_storage
   advanced/preloading

.. toctree::
   :maxdepth: 2
   :caption: 工具与CLI

   tools/cli
   tools/monitoring

.. toctree::
   :maxdepth: 2
   :caption: API参考

   api/decorators
   api/manager
   api/storages
   api/config
   api/enums
   api/utils

.. toctree::
   :maxdepth: 2
   :caption: 示例教程

   examples/basic
   examples/advanced
   examples/global_switch
   examples/memory_monitoring
   examples/comprehensive

.. toctree::
   :maxdepth: 2
   :caption: 帮助

   faq
   troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: 开发

   contributing
   development
   testing

索引和表格
==========

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

项目特性
========

fn_cache 是一个专为现代 Python 应用设计的轻量级缓存库，具有以下核心特性：

* **多种缓存策略**: TTL 和 LRU 缓存淘汰策略
* **灵活的存储后端**: 内存和 Redis 存储支持
* **多种序列化格式**: JSON、Pickle、MessagePack、字符串
* **版本控制机制**: 全局和用户级缓存失效
* **强大的装饰器**: 支持同步/异步函数
* **缓存预热**: 服务启动时预加载数据
* **内存监控**: 实时内存占用监控
* **缓存统计**: 详细的性能指标

快速安装
========

.. code-block:: bash

   pip install fn-cache

快速示例
========

.. code-block:: python

   from fn_cache import cached

   @cached(ttl_seconds=300)
   def get_user_data(user_id: int):
       # 模拟数据库查询
       return {"user_id": user_id, "name": f"用户_{user_id}"}

   # 第一次调用会执行函数
   result1 = get_user_data(123)

   # 第二次调用直接从缓存返回
   result2 = get_user_data(123)  # 命中缓存

许可证
======

本项目采用 MIT 许可证 - 详见 :ref:`LICENSE` 文件。

相关链接
========

* `GitHub 仓库 <https://github.com/leowzz/fn_cache>`_
* `PyPI 包 <https://pypi.org/project/fn-cache/>`_
* `问题反馈 <https://github.com/leowzz/fn_cache/issues>`_
* `更新日志 <https://github.com/leowzz/fn_cache/releases>`_ 