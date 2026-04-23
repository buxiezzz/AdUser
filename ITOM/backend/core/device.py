from fastapi import Request


def detect_device(request: Request) -> str:
    """
    通过解析 HTTP 请求中的 User-Agent 头部，自动判断操作来源终端。
    支持识别：移动浏览器、UniApp 客户端、PDA 手持设备。
    """
    ua = (request.headers.get("user-agent") or "").lower()
    
    # UniApp 移动客户端标识
    if "uni-app" in ua or "uniapp" in ua:
        return "📱手机端"
    
    # 常见移动端浏览器 / 操作系统标识
    mobile_keywords = ["mobile", "android", "iphone", "ipad", "ipod", "webos", "opera mini", "opera mobi", "windows phone", "blackberry"]
    if any(kw in ua for kw in mobile_keywords):
        return "📱手机端"
    
    return "💻电脑端"
