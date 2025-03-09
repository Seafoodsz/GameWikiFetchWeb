#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库管理模块
用于管理数据的存储和检索
"""

import os
import json
import sqlite3
import ijson
import psutil
import gc
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Iterator, Tuple, Union, Generator

try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

from utils.logger import get_logger, ContextLogger, exception_handler

class DatabaseManager:
    """数据库管理器，用于管理数据的存储和检索"""
    
    def __init__(self, config):
        """初始化数据库管理器
        
        Args:
            config (Config): 配置对象
        """
        self.config = config
        self.logger = ContextLogger('database', 'manager')
        self.db_type = config.database.get("type", "json").lower()
        self.logger.info(f"初始化数据库管理器，类型: {self.db_type}")
        
        # 批处理配置
        self.batch_size = config.get('database.batch_size', 100)
        self.memory_limit = config.get('database.memory_limit_mb', 500) * 1024 * 1024  # 转换为字节
        
        # 初始化数据库连接
        self._init_db()
        
        # 内存中的数据缓存
        self.data = {
            "character": {},
            "skill": {},
            "item": {},
            "enemy": {},
            "location": {},
            "quest": {},
            "relation": {}
        }
        
        # 内存监控
        self.memory_usage_history = []
        self.record_memory_usage()
    
    def record_memory_usage(self):
        """记录当前内存使用情况"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_usage = {
            'timestamp': datetime.now(),
            'rss': memory_info.rss,  # 物理内存使用
            'vms': memory_info.vms,  # 虚拟内存使用
            'percent': process.memory_percent()
        }
        self.memory_usage_history.append(memory_usage)
        
        # 只保留最近100条记录
        if len(self.memory_usage_history) > 100:
            self.memory_usage_history = self.memory_usage_history[-100:]
        
        # 记录日志
        self.logger.debug(f"内存使用: {memory_usage['rss'] / (1024 * 1024):.2f} MB "
                         f"({memory_usage['percent']:.2f}%)")
        
        # 如果内存使用超过限制，触发垃圾回收
        if memory_usage['rss'] > self.memory_limit:
            self.logger.warning(f"内存使用超过限制 ({self.memory_limit / (1024 * 1024):.2f} MB)，"
                              f"触发垃圾回收")
            gc.collect()
    
    def _init_db(self):
        """初始化数据库连接"""
        if self.db_type == "mongodb":
            if not MONGODB_AVAILABLE:
                self.logger.warning("未安装 pymongo，将使用 JSON 作为备用存储方式")
                self.db_type = "json"
            else:
                self._init_mongodb()
        elif self.db_type == "sqlite":
            self._init_sqlite()
        else:
            self.logger.info("使用 JSON 文件作为存储方式")
    
    def _init_mongodb(self):
        """初始化 MongoDB 连接"""
        try:
            uri = self.config.database.get("mongodb_uri", "mongodb://localhost:27017/")
            db_name = self.config.database.get("mongodb_db", "stoneshard")
            
            self.mongo_client = pymongo.MongoClient(uri)
            self.mongo_db = self.mongo_client[db_name]
            
            # 测试连接
            self.mongo_client.server_info()
            self.logger.info(f"已连接到 MongoDB: {uri}, 数据库: {db_name}")
        except Exception as e:
            self.logger.error(f"连接 MongoDB 失败: {str(e)}")
            self.logger.warning("将使用 JSON 作为备用存储方式")
            self.db_type = "json"
    
    def _init_sqlite(self):
        """初始化 SQLite 连接"""
        try:
            db_path = self.config.database.get("sqlite_path", "stoneshard.db")
            
            # 确保目录存在
            db_dir = os.path.dirname(db_path)
            if db_dir:
                Path(db_dir).mkdir(parents=True, exist_ok=True)
            
            self.sqlite_conn = sqlite3.connect(db_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            
            # 创建表
            self._create_sqlite_tables()
            
            self.logger.info(f"已连接到 SQLite 数据库: {db_path}")
        except Exception as e:
            self.logger.error(f"连接 SQLite 数据库失败: {str(e)}")
            self.logger.warning("将使用 JSON 作为备用存储方式")
            self.db_type = "json"
    
    def _create_sqlite_tables(self):
        """创建 SQLite 表"""
        cursor = self.sqlite_conn.cursor()
        
        # 创建数据表
        tables = {
            "character": """
                CREATE TABLE IF NOT EXISTS character (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """,
            "skill": """
                CREATE TABLE IF NOT EXISTS skill (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """,
            "item": """
                CREATE TABLE IF NOT EXISTS item (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """,
            "enemy": """
                CREATE TABLE IF NOT EXISTS enemy (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """,
            "location": """
                CREATE TABLE IF NOT EXISTS location (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """,
            "quest": """
                CREATE TABLE IF NOT EXISTS quest (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """,
            "relation": """
                CREATE TABLE IF NOT EXISTS relation (
                    id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
        }
        
        for table_name, create_sql in tables.items():
            cursor.execute(create_sql)
        
        # 创建索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_character_name ON character (name)",
            "CREATE INDEX IF NOT EXISTS idx_skill_name ON skill (name)",
            "CREATE INDEX IF NOT EXISTS idx_item_name ON item (name)",
            "CREATE INDEX IF NOT EXISTS idx_item_category ON item (category)",
            "CREATE INDEX IF NOT EXISTS idx_enemy_name ON enemy (name)",
            "CREATE INDEX IF NOT EXISTS idx_location_name ON location (name)",
            "CREATE INDEX IF NOT EXISTS idx_quest_name ON quest (name)",
            "CREATE INDEX IF NOT EXISTS idx_relation_source ON relation (source_type, source_id)",
            "CREATE INDEX IF NOT EXISTS idx_relation_target ON relation (target_type, target_id)",
            "CREATE INDEX IF NOT EXISTS idx_relation_type ON relation (relation_type)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        self.sqlite_conn.commit()
    
    def save(self, collection, data, id_field="id"):
        """保存数据
        
        Args:
            collection (str): 集合/表名
            data (dict): 数据
            id_field (str, optional): ID 字段名
        
        Returns:
            str: 数据 ID
        """
        # 确保数据有 ID
        if id_field not in data:
            raise ValueError(f"数据缺少 ID 字段: {id_field}")
        
        data_id = data[id_field]
        
        # 添加时间戳
        now = datetime.now().isoformat()
        if "created_at" not in data:
            data["created_at"] = now
        data["updated_at"] = now
        
        # 保存到内存缓存
        if collection not in self.data:
            self.data[collection] = {}
        self.data[collection][data_id] = data
        
        # 根据数据库类型保存
        if self.db_type == "mongodb":
            return self._save_mongodb(collection, data, data_id)
        elif self.db_type == "sqlite":
            return self._save_sqlite(collection, data, data_id)
        else:
            return data_id  # JSON 模式下只保存在内存中
    
    def _save_mongodb(self, collection, data, data_id):
        """保存数据到 MongoDB
        
        Args:
            collection (str): 集合名
            data (dict): 数据
            data_id (str): 数据 ID
        
        Returns:
            str: 数据 ID
        """
        try:
            self.mongo_db[collection].update_one(
                {"_id": data_id},
                {"$set": data},
                upsert=True
            )
            return data_id
        except Exception as e:
            self.logger.error(f"保存数据到 MongoDB 失败: {str(e)}")
            return data_id
    
    def _save_sqlite(self, collection, data, data_id):
        """保存数据到 SQLite
        
        Args:
            collection (str): 表名
            data (dict): 数据
            data_id (str): 数据 ID
        
        Returns:
            str: 数据 ID
        """
        try:
            cursor = self.sqlite_conn.cursor()
            
            # 将数据转换为 JSON 字符串
            data_json = json.dumps(data, ensure_ascii=False)
            
            if collection == "relation":
                # 关系表有特殊结构
                cursor.execute(
                    f"""
                    INSERT OR REPLACE INTO {collection}
                    (id, source_type, source_id, target_type, target_id, relation_type, data, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data_id,
                        data.get("source_type", ""),
                        data.get("source_id", ""),
                        data.get("target_type", ""),
                        data.get("target_id", ""),
                        data.get("relation_type", ""),
                        data_json,
                        data.get("created_at", ""),
                        data.get("updated_at", "")
                    )
                )
            elif collection == "item":
                # 物品表有 category 字段
                cursor.execute(
                    f"""
                    INSERT OR REPLACE INTO {collection}
                    (id, name, category, data, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data_id,
                        data.get("name", ""),
                        data.get("category", ""),
                        data_json,
                        data.get("created_at", ""),
                        data.get("updated_at", "")
                    )
                )
            else:
                # 其他表有通用结构
                cursor.execute(
                    f"""
                    INSERT OR REPLACE INTO {collection}
                    (id, name, data, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        data_id,
                        data.get("name", ""),
                        data_json,
                        data.get("created_at", ""),
                        data.get("updated_at", "")
                    )
                )
            
            self.sqlite_conn.commit()
            return data_id
        except Exception as e:
            self.logger.error(f"保存数据到 SQLite 失败: {str(e)}")
            return data_id
    
    def get(self, collection, data_id):
        """获取数据
        
        Args:
            collection (str): 集合/表名
            data_id (str): 数据 ID
        
        Returns:
            dict: 数据，如果不存在则返回 None
        """
        # 先从内存缓存中获取
        if collection in self.data and data_id in self.data[collection]:
            return self.data[collection][data_id]
        
        # 从数据库中获取
        if self.db_type == "mongodb":
            return self._get_mongodb(collection, data_id)
        elif self.db_type == "sqlite":
            return self._get_sqlite(collection, data_id)
        
        return None
    
    def _get_mongodb(self, collection, data_id):
        """从 MongoDB 获取数据
        
        Args:
            collection (str): 集合名
            data_id (str): 数据 ID
        
        Returns:
            dict: 数据，如果不存在则返回 None
        """
        try:
            data = self.mongo_db[collection].find_one({"_id": data_id})
            if data:
                # 更新内存缓存
                if collection not in self.data:
                    self.data[collection] = {}
                self.data[collection][data_id] = data
            return data
        except Exception as e:
            self.logger.error(f"从 MongoDB 获取数据失败: {str(e)}")
            return None
    
    def _get_sqlite(self, collection, data_id):
        """从 SQLite 获取数据
        
        Args:
            collection (str): 表名
            data_id (str): 数据 ID
        
        Returns:
            dict: 数据，如果不存在则返回 None
        """
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(f"SELECT data FROM {collection} WHERE id = ?", (data_id,))
            row = cursor.fetchone()
            
            if row:
                data = json.loads(row[0])
                # 更新内存缓存
                if collection not in self.data:
                    self.data[collection] = {}
                self.data[collection][data_id] = data
                return data
            
            return None
        except Exception as e:
            self.logger.error(f"从 SQLite 获取数据失败: {str(e)}")
            return None
    
    def find(self, collection, query=None, sort=None, limit=None):
        """查找数据
        
        Args:
            collection (str): 集合/表名
            query (dict, optional): 查询条件
            sort (list, optional): 排序条件，格式为 [(field, direction)]
            limit (int, optional): 限制返回数量
        
        Returns:
            list: 数据列表
        """
        if self.db_type == "mongodb":
            return self._find_mongodb(collection, query, sort, limit)
        elif self.db_type == "sqlite":
            return self._find_sqlite(collection, query, sort, limit)
        else:
            # JSON 模式下从内存中查找
            return self._find_memory(collection, query, sort, limit)
    
    def _find_mongodb(self, collection, query=None, sort=None, limit=None):
        """从 MongoDB 查找数据
        
        Args:
            collection (str): 集合名
            query (dict, optional): 查询条件
            sort (list, optional): 排序条件，格式为 [(field, direction)]
            limit (int, optional): 限制返回数量
        
        Returns:
            list: 数据列表
        """
        try:
            cursor = self.mongo_db[collection].find(query or {})
            
            if sort:
                cursor = cursor.sort(sort)
            
            if limit:
                cursor = cursor.limit(limit)
            
            return list(cursor)
        except Exception as e:
            self.logger.error(f"从 MongoDB 查找数据失败: {str(e)}")
            return []
    
    def _find_sqlite(self, collection, query=None, sort=None, limit=None):
        """从 SQLite 查找数据
        
        Args:
            collection (str): 表名
            query (dict, optional): 查询条件
            sort (list, optional): 排序条件，格式为 [(field, direction)]
            limit (int, optional): 限制返回数量
        
        Returns:
            list: 数据列表
        """
        try:
            cursor = self.sqlite_conn.cursor()
            
            # 构建查询 SQL
            sql = f"SELECT data FROM {collection}"
            params = []
            
            if query:
                conditions = []
                for key, value in query.items():
                    if key == "name":
                        conditions.append("name LIKE ?")
                        params.append(f"%{value}%")
                    elif key == "category" and collection == "item":
                        conditions.append("category = ?")
                        params.append(value)
                    elif collection == "relation" and key in ["source_type", "source_id", "target_type", "target_id", "relation_type"]:
                        conditions.append(f"{key} = ?")
                        params.append(value)
                
                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)
            
            if sort:
                order_clauses = []
                for field, direction in sort:
                    if field == "name" or (collection == "item" and field == "category") or (collection == "relation" and field in ["source_type", "source_id", "target_type", "target_id", "relation_type"]):
                        order_clauses.append(f"{field} {'ASC' if direction == 1 else 'DESC'}")
                
                if order_clauses:
                    sql += " ORDER BY " + ", ".join(order_clauses)
            
            if limit:
                sql += f" LIMIT {limit}"
            
            cursor.execute(sql, params)
            
            result = []
            for row in cursor.fetchall():
                result.append(json.loads(row[0]))
            
            return result
        except Exception as e:
            self.logger.error(f"从 SQLite 查找数据失败: {str(e)}")
            return []
    
    def _find_memory(self, collection, query=None, sort=None, limit=None):
        """从内存中查找数据
        
        Args:
            collection (str): 集合名
            query (dict, optional): 查询条件
            sort (list, optional): 排序条件，格式为 [(field, direction)]
            limit (int, optional): 限制返回数量
        
        Returns:
            list: 数据列表
        """
        if collection not in self.data:
            return []
        
        result = list(self.data[collection].values())
        
        # 应用查询条件
        if query:
            filtered_result = []
            for item in result:
                match = True
                for key, value in query.items():
                    if key not in item:
                        match = False
                        break
                    
                    if isinstance(value, str) and isinstance(item[key], str):
                        # 字符串使用模糊匹配
                        if value.lower() not in item[key].lower():
                            match = False
                            break
                    elif item[key] != value:
                        match = False
                        break
                
                if match:
                    filtered_result.append(item)
            
            result = filtered_result
        
        # 应用排序
        if sort:
            for field, direction in reversed(sort):
                result.sort(
                    key=lambda x: x.get(field, ""),
                    reverse=(direction == -1)
                )
        
        # 应用限制
        if limit and limit < len(result):
            result = result[:limit]
        
        return result
    
    def delete(self, collection, data_id):
        """删除数据
        
        Args:
            collection (str): 集合/表名
            data_id (str): 数据 ID
        
        Returns:
            bool: 是否成功
        """
        # 从内存缓存中删除
        if collection in self.data and data_id in self.data[collection]:
            del self.data[collection][data_id]
        
        # 从数据库中删除
        if self.db_type == "mongodb":
            return self._delete_mongodb(collection, data_id)
        elif self.db_type == "sqlite":
            return self._delete_sqlite(collection, data_id)
        
        return True
    
    def _delete_mongodb(self, collection, data_id):
        """从 MongoDB 删除数据
        
        Args:
            collection (str): 集合名
            data_id (str): 数据 ID
        
        Returns:
            bool: 是否成功
        """
        try:
            result = self.mongo_db[collection].delete_one({"_id": data_id})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"从 MongoDB 删除数据失败: {str(e)}")
            return False
    
    def _delete_sqlite(self, collection, data_id):
        """从 SQLite 删除数据
        
        Args:
            collection (str): 表名
            data_id (str): 数据 ID
        
        Returns:
            bool: 是否成功
        """
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(f"DELETE FROM {collection} WHERE id = ?", (data_id,))
            self.sqlite_conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"从 SQLite 删除数据失败: {str(e)}")
            return False
    
    def export_all(self, output_path):
        """导出所有数据
        
        Args:
            output_path (str): 输出文件路径
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 记录内存使用
        self.record_memory_usage()
        
        # 使用流式处理导出
        self._export_streaming(output_path)
        
        self.logger.info(f"数据导出完成: {output_path}")
    
    def _export_streaming(self, output_path: str) -> None:
        """使用流式处理导出所有数据
        
        Args:
            output_path (str): 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入开始的大括号
            f.write("{\n")
            
            # 遍历所有集合
            for i, collection in enumerate(self.data.keys()):
                # 写入集合名称
                f.write(f'  "{collection}": [\n')
                
                # 获取集合数据
                items = []
                if self.db_type == "mongodb":
                    cursor = self.mongo_db[collection].find({}, {"_id": 0})
                    # 分批处理
                    batch_count = 0
                    for item in cursor:
                        self._write_json_item(f, item, batch_count > 0)
                        batch_count += 1
                        
                        # 记录内存使用
                        if batch_count % self.batch_size == 0:
                            self.record_memory_usage()
                elif self.db_type == "sqlite":
                    cursor = self.sqlite_conn.cursor()
                    cursor.execute(f"SELECT data FROM {collection}")
                    
                    # 分批获取和处理
                    batch_count = 0
                    while True:
                        rows = cursor.fetchmany(self.batch_size)
                        if not rows:
                            break
                        
                        for j, row in enumerate(rows):
                            item = json.loads(row[0])
                            self._write_json_item(f, item, batch_count > 0 or j > 0)
                            batch_count += 1
                        
                        # 记录内存使用
                        self.record_memory_usage()
                else:
                    # 内存模式
                    items = list(self.data[collection].values())
                    for j, item in enumerate(items):
                        self._write_json_item(f, item, j > 0)
                        
                        # 记录内存使用
                        if j % self.batch_size == 0:
                            self.record_memory_usage()
                
                # 写入集合结束
                f.write("\n  ]")
                
                # 如果不是最后一个集合，添加逗号
                if i < len(self.data.keys()) - 1:
                    f.write(",")
                
                f.write("\n")
            
            # 写入结束的大括号
            f.write("}")
    
    def _write_json_item(self, file, item, need_comma):
        """写入单个JSON项
        
        Args:
            file: 文件对象
            item: 要写入的项
            need_comma: 是否需要前置逗号
        """
        # 转换为JSON字符串
        json_str = json.dumps(item, ensure_ascii=False)
        
        # 写入项，如果需要则添加逗号
        if need_comma:
            file.write(",\n    ")
        else:
            file.write("    ")
        
        file.write(json_str)
    
    @exception_handler
    def stream_json(self, file_path: str) -> Generator[Dict[str, Any], None, None]:
        """流式解析JSON文件
        
        Args:
            file_path (str): JSON文件路径
        
        Yields:
            Dict[str, Any]: 解析的JSON对象
        """
        self.logger.info(f"流式解析JSON文件: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # 使用ijson流式解析
                if file_path.endswith('.json'):
                    # 如果是JSON文件，使用ijson解析
                    objects = ijson.items(f, 'item')
                    for obj in objects:
                        yield obj
                        # 记录内存使用
                        self.record_memory_usage()
                else:
                    # 如果不是JSON文件，尝试按行解析
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                obj = json.loads(line)
                                yield obj
                                # 记录内存使用
                                self.record_memory_usage()
                            except json.JSONDecodeError:
                                self.logger.warning(f"无法解析行: {line[:100]}...")
        except Exception as e:
            self.logger.error(f"流式解析JSON文件失败: {str(e)}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.db_type == "mongodb" and hasattr(self, "mongo_client"):
            self.mongo_client.close()
            self.logger.info("已关闭 MongoDB 连接")
        
        if self.db_type == "sqlite" and hasattr(self, "sqlite_conn"):
            self.sqlite_conn.close()
            self.logger.info("已关闭 SQLite 连接") 