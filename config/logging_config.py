#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import json
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid
from contextvars import ContextVar

# 全局 trace_id 上下文变量
trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')

class TraceFilter(logging.Filter):
    """为日志记录添加 trace_id"""
    def filter(self, record):
        record.trace_id = trace_id_var.get()
        return True

class JSONFormatter(logging.Formatter):
    """JSON 格式日志格式化器"""
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加 trace_id（如果存在）
        trace_id = trace_id_var.get()
        if trace_id:
            log_obj['trace_id'] = trace_id

        # 添加进程/线程信息
        log_obj['process'] = record.process
        log_obj['process_name'] = record.processName
        log_obj['thread'] = record.thread
        log_obj['thread_name'] = record.threadName

        # 添加异常信息
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, 'extra_fields'):
            log_obj.update(record.extra_fields)

        return json.dumps(log_obj, ensure_ascii=False)

class StructuredTextFormatter(logging.Formatter):
    """结构化的文本格式日志（人类可读）"""
    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # 基础格式
        log_parts = [
            f"[{timestamp}]",
            f"[{record.levelname:^7}]",
            f"[{record.name}]",
        ]
        
        # 添加 trace_id（如果存在）
        trace_id = trace_id_var.get()
        if trace_id:
            log_parts.append(f"[trace:{trace_id[:8]}]")
        
        # 添加位置信息
        log_parts.append(f"[{record.module}:{record.funcName}:{record.lineno}]")
        
        # 添加消息
        log_parts.append(f" {record.getMessage()}")
        
        # 添加异常
        if record.exc_info:
            log_parts.append(f"\n{self.formatException(record.exc_info)}")
        
        return ''.join(log_parts)

def setup_logging(
    level: str = "INFO",
    format_type: str = "text",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True
) -> None:
    """
    设置全局日志配置
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: 输出格式 ("text" 或 "json")
        log_file: 日志文件路径，如果为 None 则不写入文件
        max_bytes: 日志文件最大字节数（用于轮转）
        backup_count: 保留的备份文件数量
        enable_console: 是否启用控制台输出
    """
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 创建并添加 trace filter
    trace_filter = TraceFilter()
    root_logger.addFilter(trace_filter)
    
    # 选择格式化器
    if format_type.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = StructuredTextFormatter()
    
    # 控制台处理器
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, level.upper()))
        root_logger.addHandler(console_handler)
    
    # 文件处理器（如果需要）
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用 RotatingFileHandler 实现日志轮转
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, level.upper()))
        root_logger.addHandler(file_handler)
    
    # 设置一些常用库的日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    root_logger.info(f"Logging initialized. Level: {level}, Format: {format_type}")

def get_logger(name: str) -> logging.Logger:
    """获取日志记录器（包装函数）"""
    return logging.getLogger(name)

def set_trace_id(trace_id: Optional[str] = None) -> str:
    """
    设置当前上下文的 trace_id
    
    Args:
        trace_id: 如果不提供，则生成一个新的 UUID
    
    Returns:
        设置的 trace_id
    """
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    
    trace_id_var.set(trace_id)
    return trace_id

def get_trace_id() -> str:
    """获取当前上下文的 trace_id"""
    return trace_id_var.get()

class TraceContext:
    """上下文管理器，用于管理 trace_id"""
    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id
        self.token = None
    
    def __enter__(self):
        self.token = trace_id_var.set(self.trace_id or str(uuid.uuid4()))
        return trace_id_var.get()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            trace_id_var.reset(self.token)

# 从环境变量读取配置
def setup_logging_from_env():
    """从环境变量初始化日志配置"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "text").lower()
    log_file = os.getenv("LOG_FILE")
    
    # 验证日志级别
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_levels:
        log_level = "INFO"
        print(f"Warning: Invalid LOG_LEVEL '{log_level}', using 'INFO'")
    
    # 验证格式
    if log_format not in ["text", "json"]:
        log_format = "text"
        print(f"Warning: Invalid LOG_FORMAT '{log_format}', using 'text'")
    
    setup_logging(
        level=log_level,
        format_type=log_format,
        log_file=log_file,
        enable_console=True
    )

# 导出常用函数
__all__ = [
    'setup_logging',
    'setup_logging_from_env',
    'get_logger',
    'set_trace_id',
    'get_trace_id',
    'TraceContext',
    'JSONFormatter',
    'StructuredTextFormatter',
    'TraceFilter',
]

