
def format_cache_key(*args, **kwargs) -> str:
    """
    格式化缓存键

    :param args: 位置参数
    :param kwargs: 关键字参数
    :return: 格式化的缓存键
    """
    parts = []

    if args:
        parts.append(":".join(str(arg) for arg in args))

    if kwargs:
        sorted_items = sorted(kwargs.items())
        parts.append(":".join(f"{k}={v}" for k, v in sorted_items))

    return ":".join(parts) if parts else "default"


def validate_cache_key(key: str) -> bool:
    """
    验证缓存键是否有效

    :param key: 缓存键
    :return: 是否有效
    """
    if not key or not isinstance(key, str):
        return False

    # 检查长度
    if len(key) > 250:
        return False

    # 检查是否包含无效字符
    invalid_chars = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07',
                     '\x08', '\x09', '\x0a', '\x0b', '\x0c', '\x0d', '\x0e', '\x0f',
                     '\x10', '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17',
                     '\x18', '\x19', '\x1a', '\x1b', '\x1c', '\x1d', '\x1e', '\x1f']

    for char in invalid_chars:
        if char in key:
            return False

    return True
