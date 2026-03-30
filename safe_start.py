"""安全启动脚本 - 检查并清理旧进程后启动"""
import os
import sys
import psutil
import time
from pathlib import Path

def find_backend_processes():
    """查找所有运行中的后端进程"""
    backend_pids = []
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.pid == current_pid:
                continue
            
            # 检查是否是Python进程且运行main.py
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'main.py' in cmdline and 'Gold_Monitoring_Desk' in cmdline:
                    backend_pids.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
            continue
    
    return backend_pids

def stop_process(pid):
    """停止指定进程"""
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        
        # 等待进程终止（最多5秒）
        try:
            proc.wait(timeout=5)
            return True
        except psutil.TimeoutExpired:
            # 强制杀死
            proc.kill()
            proc.wait(timeout=2)
            return True
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        print(f"[警告] 无法停止进程 {pid}: {e}")
        return False

def main():
    print("=" * 80)
    print("黄金监控中台 - 安全启动")
    print("=" * 80)
    
    # 1. 检查旧进程
    print("\n[1] 检查现有后端进程...")
    old_pids = find_backend_processes()
    
    if old_pids:
        print(f"发现 {len(old_pids)} 个旧进程: {old_pids}")
        print("\n正在停止旧进程...")
        
        for pid in old_pids:
            print(f"  停止进程 PID {pid}...", end=' ')
            if stop_process(pid):
                print("✓")
            else:
                print("✗")
        
        print("\n等待进程完全终止...")
        time.sleep(2)
        
        # 再次检查
        remaining = find_backend_processes()
        if remaining:
            print(f"[错误] 以下进程仍在运行: {remaining}")
            print("请手动终止这些进程后再启动")
            return 1
        
        print("[成功] 所有旧进程已停止")
    else:
        print("[成功] 未发现旧进程")
    
    # 2. 删除锁文件
    print("\n[2] 清理进程锁文件...")
    lock_file = Path(__file__).parent / 'backend.lock'
    if lock_file.exists():
        lock_file.unlink()
        print(f"[成功] 已删除锁文件: {lock_file}")
    else:
        print("[成功] 无锁文件需要清理")
    
    # 3. 启动新进程
    print("\n[3] 启动后端服务...")
    print("=" * 80)
    
    backend_dir = Path(__file__).parent / 'backend'
    os.chdir(backend_dir)
    
    # 启动main.py
    os.system('python main.py')
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[用户中断] 启动已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n[错误] 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
