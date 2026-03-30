"""进程锁管理器 - 防止多个后端实例同时运行"""
import os
import sys
import psutil
from pathlib import Path

class ProcessLock:
    """进程锁 - 确保只有一个后端实例运行"""
    
    def __init__(self, lock_file="backend.lock"):
        self.lock_file = Path(__file__).parent.parent / lock_file
        self.pid = os.getpid()
    
    def acquire(self):
        """获取锁 - 如果已有进程运行则拒绝启动"""
        if self.lock_file.exists():
            # 检查锁文件中的PID是否仍在运行
            try:
                with open(self.lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                
                if psutil.pid_exists(old_pid):
                    try:
                        proc = psutil.Process(old_pid)
                        # 检查是否是Python进程且运行main.py
                        if 'python' in proc.name().lower():
                            cmdline = ' '.join(proc.cmdline())
                            if 'main.py' in cmdline:
                                print(f"[错误] 后端已在运行！PID: {old_pid}")
                                print(f"[提示] 如需重启，请先停止旧进程：")
                                print(f"       Windows: taskkill /F /PID {old_pid}")
                                print(f"       Linux: kill {old_pid}")
                                return False
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # 旧进程已不存在，删除过期锁文件
                self.lock_file.unlink()
                
            except (ValueError, FileNotFoundError):
                # 锁文件损坏，删除
                if self.lock_file.exists():
                    self.lock_file.unlink()
        
        # 创建新锁文件
        with open(self.lock_file, 'w') as f:
            f.write(str(self.pid))
        
        print(f"[进程锁] 已获取锁，PID: {self.pid}")
        return True
    
    def release(self):
        """释放锁"""
        if self.lock_file.exists():
            try:
                with open(self.lock_file, 'r') as f:
                    locked_pid = int(f.read().strip())
                
                if locked_pid == self.pid:
                    self.lock_file.unlink()
                    print(f"[进程锁] 已释放锁，PID: {self.pid}")
            except (ValueError, FileNotFoundError):
                pass
    
    def __enter__(self):
        """上下文管理器支持"""
        if not self.acquire():
            sys.exit(1)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时自动释放锁"""
        self.release()
