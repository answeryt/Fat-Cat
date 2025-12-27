#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import json
import logging
import tempfile
from pathlib import Path
from config import setup_logging, get_logger, TraceContext

def test_logging_configuration():
    """测试日志配置"""
    # 测试文本格式
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        log_file = f.name
    
    try:
        setup_logging(level="DEBUG", format_type="text", log_file=log_file)
        logger = get_logger("test")
        
        logger.debug("Debug 消息")
        logger.info("Info 消息")
        logger.warning("Warning 消息")
        logger.error("Error 消息")
        
        # 检查文件内容
        content = Path(log_file).read_text()
        assert "Debug 消息" in content
        assert "Info 消息" in content
        
    finally:
        Path(log_file).unlink()

def test_json_logging():
    """测试 JSON 格式日志"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        log_file = f.name
    
    try:
        setup_logging(level="INFO", format_type="json", log_file=log_file)
        logger = get_logger("test_json")
        
        with TraceContext("test-trace-123"):
            logger.info("带 trace_id 的日志")
        
        # 检查 JSON 格式
        lines = Path(log_file).read_text().strip().split('\n')
        for line in lines:
            if line:
                log_entry = json.loads(line)
                assert "timestamp" in log_entry
                assert "level" in log_entry
                assert "message" in log_entry
                
                if "带 trace_id 的日志" in line:
                    assert log_entry.get("trace_id") == "test-trace-123"
        
    finally:
        Path(log_file).unlink()

def test_log_rotation():
    """测试日志轮转"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        
        setup_logging(
            level="INFO",
            format_type="text",
            log_file=str(log_file),
            max_bytes=100,  # 很小的限制，便于测试轮转
            backup_count=2
        )
        
        logger = get_logger("test_rotation")
        
        # 写入大量日志触发轮转
        for i in range(100):
            logger.info(f"测试日志消息 {i}")
        
        # 检查是否创建了备份文件
        backup_files = list(log_file.parent.glob(f"{log_file.name}.*"))
        assert len(backup_files) <= 2  # 不超过 backup_count
        
        print("✅ 所有日志测试通过")

if __name__ == "__main__":
    test_logging_configuration()
    test_json_logging()
    test_log_rotation()
    print("所有测试通过！")

