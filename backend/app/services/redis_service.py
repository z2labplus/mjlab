import redis
import json
import logging
from typing import Any, Optional, Dict
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisService:
    """Redis服务类，管理Redis连接和基本操作"""
    
    def __init__(self):
        self.redis_client = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                password=getattr(settings, 'REDIS_PASSWORD', None),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}")
            self.redis_client = None
    
    def is_connected(self) -> bool:
        """检查Redis连接状态"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置键值对"""
        if not self.is_connected():
            logger.warning("Redis未连接，无法设置值")
            return False
        
        try:
            # 如果是字典或列表，转换为JSON字符串
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            # 如果已经是字符串，直接使用
            elif not isinstance(value, str):
                value = str(value)
            
            result = self.redis_client.set(key, value, ex=expire)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis设置失败: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """获取值"""
        if not self.is_connected():
            logger.warning("Redis未连接，无法获取值")
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # 直接返回字符串，不进行JSON解析
            # 让调用方决定是否解析JSON
            return value
        except Exception as e:
            logger.error(f"Redis获取失败: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除键"""
        if not self.is_connected():
            logger.warning("Redis未连接，无法删除值")
            return False
        
        try:
            result = self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis删除失败: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis检查存在失败: {e}")
            return False
    
    def hset(self, hash_key: str, field: str, value: Any) -> bool:
        """设置哈希字段"""
        if not self.is_connected():
            logger.warning("Redis未连接，无法设置哈希值")
            return False
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            result = self.redis_client.hset(hash_key, field, value)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis哈希设置失败: {e}")
            return False
    
    def hget(self, hash_key: str, field: str) -> Optional[Any]:
        """获取哈希字段值"""
        if not self.is_connected():
            logger.warning("Redis未连接，无法获取哈希值")
            return None
        
        try:
            value = self.redis_client.hget(hash_key, field)
            if value is None:
                return None
            
            # 尝试解析JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Redis哈希获取失败: {e}")
            return None
    
    def hgetall(self, hash_key: str) -> Dict[str, Any]:
        """获取哈希所有字段"""
        if not self.is_connected():
            logger.warning("Redis未连接，无法获取哈希所有值")
            return {}
        
        try:
            data = self.redis_client.hgetall(hash_key)
            result = {}
            for field, value in data.items():
                try:
                    result[field] = json.loads(value)
                except json.JSONDecodeError:
                    result[field] = value
            return result
        except Exception as e:
            logger.error(f"Redis哈希获取所有值失败: {e}")
            return {}
    
    def keys(self, pattern: str) -> list:
        """获取匹配模式的键列表"""
        if not self.is_connected():
            logger.warning("Redis未连接，无法获取键列表")
            return []
        
        try:
            return self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis获取键列表失败: {e}")
            return []

# 创建全局Redis服务实例
redis_service = RedisService() 