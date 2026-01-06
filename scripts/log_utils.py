#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#!/usr/bin/env python3
"""日志工具脚本"""
import sys
import json
from pathlib import Path

def view_logs(log_file: str, format_type: str = "json", filter_level: str = None):
    """查看日志文件"""
    path = Path(log_file)
    if not path.exists():
        print(f"日志文件不存在: {log_file}")
        return
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            if format_type == "json":
                try:
                    log_entry = json.loads(line)
                    # 按级别过滤
                    if filter_level and log_entry.get('level') != filter_level.upper():
                        continue
                    print(json.dumps(log_entry, indent=2, ensure_ascii=False))
                except json.JSONDecodeError:
                    print(line)
            else:
                print(line)

def clear_logs(log_file: str, keep_backups: bool = True):
    """清理日志"""
    path = Path(log_file)
    if path.exists():
        path.write_text('')
        print(f"已清空日志文件: {log_file}")
    
    if keep_backups:
        # 清理备份文件
        backup_pattern = f"{log_file}.*"
        for backup in path.parent.glob(backup_pattern):
            backup.unlink()
            print(f"已删除备份文件: {backup}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="日志管理工具")
    subparsers = parser.add_subparsers(dest="command")
    
    # view 命令
    view_parser = subparsers.add_parser("view", help="查看日志")
    view_parser.add_argument("file", help="日志文件路径")
    view_parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")
    view_parser.add_argument("--level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="过滤级别")
    
    # clear 命令
    clear_parser = subparsers.add_parser("clear", help="清理日志")
    clear_parser.add_argument("file", help="日志文件路径")
    clear_parser.add_argument("--keep-backups", action="store_true", help="保留备份文件")
    
    args = parser.parse_args()
    
    if args.command == "view":
        view_logs(args.file, args.format, args.level)
    elif args.command == "clear":
        clear_logs(args.file, args.keep_backups)
    else:
        parser.print_help()

