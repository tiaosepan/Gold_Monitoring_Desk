"""
主程序入口
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[ENV] 已加载环境配置: {env_path}")
except ImportError:
    pass

from backend.api import router
from backend.database import init_database
from backend.scheduler import scheduler
from backend.utils import main_logger
from backend.utils.process_lock import ProcessLock
from prometheus_client import make_asgi_app

# 进程锁实例（全局）
process_lock = None

# 创建FastAPI应用
app = FastAPI(
    title="黄金监控中台",
    description="Gold Monitoring Desk - 黄金价格监控与反转预警系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(router)

# 挂载Prometheus指标端点
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# 挂载静态文件目录
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global process_lock
    
    main_logger.info("=" * 60)
    main_logger.info("黄金监控中台启动中...")
    main_logger.info("=" * 60)
    
    # 获取进程锁（防止多实例运行）
    main_logger.info("检查进程锁...")
    process_lock = ProcessLock()
    if not process_lock.acquire():
        main_logger.error("无法获取进程锁 - 已有实例在运行！")
        import sys
        sys.exit(1)
    
    # 初始化数据库
    main_logger.info("初始化数据库...")
    init_database()
    main_logger.info("数据库初始化完成")
    
    # 启动任务调度器
    main_logger.info("启动任务调度器...")
    scheduler.start()
    main_logger.info("任务调度器启动完成")
    
    main_logger.info("=" * 60)
    main_logger.info("系统启动完成！")
    main_logger.info("访问地址: http://localhost:8000")
    main_logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    global process_lock
    
    main_logger.info("系统关闭中...")
    scheduler.shutdown()
    
    # 释放进程锁
    if process_lock:
        process_lock.release()
    
    main_logger.info("系统已关闭")


@app.get("/")
async def root():
    """首页"""
    index_file = os.path.join(static_dir, 'index.html')
    if os.path.exists(index_file):
        return FileResponse(index_file)
    else:
        return {
            "message": "黄金监控中台",
            "version": "1.0.0",
            "status": "running"
        }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "黄金监控中台",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    # 运行服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 禁用热重载，避免多进程导致任务重复执行
        log_level="info"
    )
