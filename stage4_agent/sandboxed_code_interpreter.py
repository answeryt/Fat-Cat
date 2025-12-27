#!/usr/bin/env python
# coding: utf-8

# In[1]:


# stage4_agent/sandboxed_code_interpreter.py
import subprocess
import tempfile
import os
import resource
from pathlib import Path
from typing import Tuple, Optional
import traceback
from RestrictedPython import compile_restricted, safe_builtins, utility_builtins
import RestrictedPython.Guards

class CodeSandbox:
    """安全代码执行沙箱"""
    
    def __init__(self, timeout: int = 30, memory_limit_mb: int = 256):
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
        self.allowed_modules = {
            'math', 'datetime', 'json', 're', 'collections', 
            'itertools', 'functools', 'random', 'statistics',
            'string', 'typing', 'decimal', 'fractions'
        }
    
    def _create_safe_builtins(self):
        """创建安全的builtins环境"""
        safe_globals = {
            '__builtins__': {
                **safe_builtins,
                **utility_builtins,
                'max': max,
                'min': min,
                'sum': sum,
                'abs': abs,
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'sorted': sorted,
                'reversed': reversed,
                'isinstance': isinstance,
                'issubclass': issubclass,
                'hasattr': hasattr,
                'getattr': getattr,
                'setattr': setattr,
                # 限制版的print
                'print': lambda *args, **kwargs: print(*args, **kwargs) 
                    if len(str(args)) < 1000 else print('[Output truncated]')
            }
        }
        return safe_globals
    
    def _validate_and_sanitize_code(self, code: str) -> Tuple[bool, str, str]:
        """
        验证并清理代码
        返回: (是否安全, 清理后的代码, 错误信息)
        """
        # 1. 检查危险关键词
        dangerous_patterns = [
            r'__import__\s*\(',
            r'eval\s*\(',
            r'exec\s*\(',
            r'compile\s*\(',
            r'open\s*\(',
            r'os\.',
            r'subprocess\.',
            r'sys\.',
            r'import\s+os\b',
            r'import\s+sys\b',
            r'import\s+subprocess\b',
            r'import\s+pickle\b',
            r'import\s+marshal\b',
            r'from\s+os\s+import',
            r'rm\s+-rf',
            r'chmod\s+777',
            r'import\s+ctypes\b',
            r'import\s+mmap\b',
        ]
        
        import re
        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False, code, f"危险模式被阻止: {pattern}"
        
        # 2. 限制导入的模块
        import_statements = re.findall(r'import\s+(\w+)', code)
        from_statements = re.findall(r'from\s+(\w+)', code)
        all_imports = set(import_statements + from_statements)
        
        for imp in all_imports:
            if imp not in self.allowed_modules:
                return False, code, f"禁止导入模块: {imp}"
        
        # 3. 限制代码长度（防止DoS）
        if len(code) > 10000:
            return False, code, "代码过长（超过10k字符）"
        
        # 4. 限制循环和递归
        if 'while True:' in code or 'def factorial' in code:  # 简单示例，实际需要更复杂检测
            return False, code, "检测到可能的无限循环/递归"
        
        return True, code, ""
    
    def execute_with_restrictedpython(self, code: str) -> Tuple[bool, str, str]:
        """使用RestrictedPython执行（第一层防护）"""
        try:
            # 验证代码
            is_safe, sanitized_code, error = self._validate_and_sanitize_code(code)
            if not is_safe:
                return False, "", error
            
            # 编译限制代码
            byte_code = compile_restricted(
                sanitized_code,
                '<sandboxed>',
                'exec'
            )
            
            # 准备安全环境
            safe_globals = self._create_safe_builtins()
            safe_globals['_print_'] = safe_globals['__builtins__']['print']
            safe_globals['_getiter_'] = RestrictedPython.Guards.guarded_iter
            
            # 执行
            exec(byte_code, safe_globals)
            
            # 获取结果
            result = safe_globals.get('_result_', '执行完成（无输出）')
            return True, str(result), ""
            
        except Exception as e:
            return False, "", f"RestrictedPython执行错误: {str(e)}"
    
    def execute_with_subprocess(self, code: str) -> Tuple[bool, str, str]:
        """使用子进程隔离执行（第二层防护）"""
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.py', 
                delete=False,
                dir='/tmp'  # 确保在临时目录
            ) as f:
                # 写入包装代码
                wrapper = f'''
import sys
import resource

# 设置内存限制
resource.setrlimit(resource.RLIMIT_AS, 
    ({self.memory_limit_mb * 1024 * 1024}, {self.memory_limit_mb * 1024 * 1024}))
resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout))

# 设置递归深度限制
sys.setrecursionlimit(50)

# 安全执行用户代码
try:
    {code}
    print("\\n=== 执行成功 ===")
except Exception as e:
    print(f"错误: {{e}}")
    sys.exit(1)
'''
                f.write(wrapper)
                temp_file = f.name
            
            # 设置安全环境变量
            env = os.environ.copy()
            env['PYTHONPATH'] = ''  # 清空Python路径
            env['PATH'] = '/usr/bin:/bin'  # 最小化PATH
            
            # 执行子进程
            result = subprocess.run(
                ['python3', temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
                cwd='/tmp',  # 工作目录设为临时目录
            )
            
            # 清理临时文件
            try:
                os.unlink(temp_file)
            except:
                pass
            
            # 检查结果
            if result.returncode == 0:
                output = result.stdout
                # 截断过长的输出
                if len(output) > 2000:
                    output = output[:2000] + "\n...[输出截断]"
                return True, output, ""
            else:
                error_msg = result.stderr or f"进程退出码: {result.returncode}"
                return False, "", error_msg
                
        except subprocess.TimeoutExpired:
            return False, "", f"执行超时（{self.timeout}秒）"
        except Exception as e:
            return False, "", f"子进程执行错误: {str(e)}"
    
    def execute(self, code: str, isolation_level: str = "high") -> dict:
        """
        执行代码
        isolation_level: "low"（仅RestrictedPython）, 
                       "medium"（仅子进程）, 
                       "high"（双重保护）
        """
        # 记录执行日志（审计用）
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"沙箱执行代码，长度: {len(code)}, 隔离级别: {isolation_level}")
        
        if isolation_level == "low":
            success, output, error = self.execute_with_restrictedpython(code)
        elif isolation_level == "medium":
            success, output, error = self.execute_with_subprocess(code)
        else:  # high - 双重防护
            # 先用RestrictedPython验证
            is_safe, _, error = self._validate_and_sanitize_code(code)
            if not is_safe:
                return {
                    "success": False,
                    "output": "",
                    "error": f"代码验证失败: {error}",
                    "method": "validation"
                }
            
            # 再用子进程执行
            success, output, error = self.execute_with_subprocess(code)
            method = "subprocess+validation"
        
        return {
            "success": success,
            "output": output,
            "error": error,
            "method": method if isolation_level == "high" else isolation_level,
            "code_size": len(code),
            "timestamp": datetime.datetime.now().isoformat()
        }
