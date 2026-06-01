"""
禁用异常的RSS源
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.database import SessionLocal, RSSSource


def disable_bad_sources():
    """禁用已知异常的RSS源"""
    print("=" * 60)
    print("禁用异常RSS源...")
    print("=" * 60)
    
    # 已知异常的RSS源URL
    bad_urls = [
        'http://rss.jintiankansha.me/rss/GM3DSNZUGJ6DOYTEG5RWENZRGUZDENLDGAYGMMDGMRSTONBRMUYWMM3FMQ2DGYZXMZSTGNDGG4YQ====',  # 金十数据1
        'http://rss.jintiankansha.me/rss/GM4DKMRUG56DIYZTHE2TAY3EGNTDAMLGMQZWKMRRGNRWCZBQMY2TSZLEGEYTQN3DMQYDSNZUGQYA====',  # 金十数据2 (非RSS格式)
        'http://rss.jintiankansha.me/rss/GM4DKMRUG56DIYZTHE2TAY3EGNTDAMLGMQZWKMRRGNRWZCYBGEYTSZLEGEYTQN3DMQYDSNZUGQYA====',  # 金十数据2 (404)
    ]
    
    db = SessionLocal()
    disabled_count = 0
    
    try:
        for url in bad_urls:
            source = db.query(RSSSource).filter_by(url=url).first()
            if source and source.is_active == 1:
                source.is_active = 0
                print(f"[禁用] {source.name} - {url[:80]}")
                disabled_count += 1
            elif source:
                print(f"[跳过] {source.name} - 已经是禁用状态")
            else:
                print(f"[跳过] 未找到源 - {url[:80]}")
        
        db.commit()
        
        print("\n" + "-" * 60)
        print(f"共禁用 {disabled_count} 个RSS源")
        
        # 显示当前活跃源列表
        active_sources = db.query(RSSSource).filter_by(is_active=1).all()
        print(f"\n当前活跃RSS源: {len(active_sources)} 个")
        for source in active_sources:
            print(f"  - {source.name} ({source.category})")
        
        print("=" * 60)
        
    finally:
        db.close()


if __name__ == "__main__":
    disable_bad_sources()
