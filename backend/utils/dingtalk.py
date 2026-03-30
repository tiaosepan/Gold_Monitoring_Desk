"""
钉钉推送工具
"""
import time
import hmac
import hashlib
import base64
import urllib.parse
import aiohttp
from typing import Dict, Optional
from datetime import datetime


class DingTalkPusher:
    """钉钉机器人推送客户端"""
    
    def __init__(self, webhook_url: str, secret: Optional[str] = None):
        """
        初始化钉钉推送客户端
        
        Args:
            webhook_url: Webhook地址
            secret: 安全密钥（可选）
        """
        self.webhook_url = webhook_url
        self.secret = secret
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    def _generate_sign(self, timestamp: int) -> str:
        """
        生成签名
        
        Args:
            timestamp: 时间戳（毫秒）
            
        Returns:
            签名字符串
        """
        if not self.secret:
            return ""
        
        # 构建待签名字符串
        string_to_sign = f"{timestamp}\n{self.secret}"
        string_to_sign_enc = string_to_sign.encode('utf-8')
        
        # 使用HmacSHA256算法计算签名
        hmac_code = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign_enc,
            digestmod=hashlib.sha256
        ).digest()
        
        # Base64编码
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        
        return sign
    
    def _build_url(self) -> str:
        """
        构建完整的Webhook URL（包含签名）
        
        Returns:
            完整的URL
        """
        if not self.secret:
            return self.webhook_url
        
        # 获取当前时间戳（毫秒）
        timestamp = int(time.time() * 1000)
        
        # 生成签名
        sign = self._generate_sign(timestamp)
        
        # 构建URL
        url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
        
        return url
    
    async def send_text(self, content: str, at_mobiles: list = None, is_at_all: bool = False) -> Dict:
        """
        发送文本消息
        
        Args:
            content: 消息内容
            at_mobiles: @的手机号列表
            is_at_all: 是否@所有人
            
        Returns:
            响应结果
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # 构建消息体
        message = {
            "msgtype": "text",
            "text": {
                "content": content
            },
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": is_at_all
            }
        }
        
        return await self._send_message(message)
    
    async def send_markdown(self, title: str, text: str, at_mobiles: list = None, is_at_all: bool = False) -> Dict:
        """
        发送Markdown消息
        
        Args:
            title: 消息标题
            text: Markdown格式的消息内容
            at_mobiles: @的手机号列表
            is_at_all: 是否@所有人
            
        Returns:
            响应结果
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # 构建消息体
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            },
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": is_at_all
            }
        }
        
        return await self._send_message(message)
    
    async def _send_message(self, message: Dict) -> Dict:
        """
        发送消息
        
        Args:
            message: 消息体
            
        Returns:
            响应结果
        """
        url = self._build_url()
        
        try:
            async with self.session.post(
                url,
                json=message,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                result = await response.json()
                
                if result.get('errcode') == 0:
                    return {
                        'success': True,
                        'message': '发送成功',
                        'response': result
                    }
                else:
                    return {
                        'success': False,
                        'message': result.get('errmsg', '发送失败'),
                        'response': result
                    }
        except Exception as e:
            return {
                'success': False,
                'message': f'发送异常: {str(e)}',
                'response': None
            }
    
    async def send_alert(self, alert_type: str, level: int, content: str) -> Dict:
        """
        发送警报消息
        
        Args:
            alert_type: 警报类型
            level: 警报等级
            content: 警报内容
            
        Returns:
            响应结果
        """
        # 等级对应的emoji
        level_emoji = {
            1: "🟢",
            2: "🟡",
            3: "🟠",
            4: "🔴",
            5: "🔴🔴"
        }
        
        emoji = level_emoji.get(level, "⚠️")
        
        # 构建Markdown消息
        title = f"{emoji} 黄金监控警报"
        text = f"""### {emoji} {alert_type}
        
**警报等级**: {level}级

**警报内容**: 
{content}

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
*黄金监控中台自动推送*
"""
        
        return await self.send_markdown(title, text, is_at_all=(level >= 4))
    
    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()


# 测试代码
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # 请替换为实际的webhook_url和secret
        webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
        secret = "YOUR_SECRET"
        
        async with DingTalkPusher(webhook_url, secret) as pusher:
            # 测试发送文本消息
            result = await pusher.send_text("测试消息")
            print("文本消息:", result)
            
            # 测试发送警报
            result = await pusher.send_alert("价格反转警报", 3, "SGE溢价超过阈值")
            print("警报消息:", result)
    
    # asyncio.run(test())
    print("请配置webhook_url和secret后再测试")
