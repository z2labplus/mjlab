#!/usr/bin/env python3
"""
天凤麻将分析器 - Playwright增强版
返回结构化的JSON数据
"""

import asyncio
import re
from playwright.async_api import async_playwright

async def get_tenhou_analysis_json(hand_string):
    """
    使用Playwright获取天凤分析结果并返回JSON格式
    
    Args:
        hand_string: 手牌字符串，如 "2245667m1234588s"
        
    Returns:
        list: 包含打牌建议的字典列表
        [
            {
                "tile": "2m",
                "tiles": ['3m','5m','8m','3s','6s'],
                "number": "18"
            },
            ...
        ]
    """
    
    async with async_playwright() as p:
        # 启动浏览器（headless模式）
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        try:
            # 创建新页面
            page = await browser.new_page()
            
            # 设置用户代理
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # 访问天凤分析页面
            url = f"https://tenhou.net/2/?q={hand_string}"
            await page.goto(url)
            
            # 等待页面加载完成
            await page.wait_for_load_state('domcontentloaded')
            await page.wait_for_load_state('networkidle')
            
            # 额外等待JavaScript执行
            await asyncio.sleep(2)
            
            # 等待分析结果元素出现
            await page.wait_for_selector('#m2', timeout=10000)
            
            # 获取分析结果
            m2_element = await page.query_selector('#m2')
            if not m2_element:
                return []
            
            # 获取HTML内容
            analysis_html = await m2_element.inner_html()
            
            # 解析结果并转换为JSON格式
            result = parse_to_json(analysis_html, hand_string)
            return result
            
        except Exception as e:
            print(f"获取失败: {e}")
            return []
        
        finally:
            await browser.close()

def parse_to_json(html_content, hand_string):
    """
    解析HTML内容并转换为JSON格式
    
    Args:
        html_content: HTML内容
        hand_string: 原始手牌字符串
        
    Returns:
        list: 结构化的打牌建议列表
    """
    
    # 移除HTML标签
    clean_text = re.sub(r'<[^>]+>', '', html_content)
    
    # 查找手牌位置
    hand_pattern = rf'{re.escape(hand_string)}'
    hand_match = re.search(hand_pattern, clean_text)
    
    if not hand_match:
        return []
    
    # 从手牌位置开始提取分析
    start_pos = hand_match.end()
    analysis_text = clean_text[start_pos:]
    
    # 提取打牌建议的模式
    pattern = r'打(\w+)\s*摸\[([^\]]+?)\s*(\d+)枚\]'
    matches = re.findall(pattern, analysis_text)
    
    result = []
    
    for match in matches:
        discard_tile = match[0]  # 要打出的牌
        draw_tiles_str = match[1].strip()  # 可以摸到的牌字符串
        count = match[2]  # 有效牌数
        
        # 解析摸牌列表
        draw_tiles = parse_draw_tiles(draw_tiles_str)
        
        # 构建结果字典
        suggestion = {
            "tile": discard_tile,
            "tiles": draw_tiles,
            "number": count
        }
        
        result.append(suggestion)
    
    return result

def parse_draw_tiles(tiles_str):
    """
    解析摸牌字符串，转换为牌的列表
    
    Args:
        tiles_str: 如 "2m3m4m5m6m7m8m9m1s2s3s4s5s6s8s"
        
    Returns:
        list: 牌的列表，如 ['2m','3m','4m',...]
    """
    
    # 使用正则表达式匹配所有的牌
    # 匹配格式：数字+字母(m/p/s/z)
    pattern = r'(\d[mpsz])'
    matches = re.findall(pattern, tiles_str)
    
    # 去重并保持顺序
    seen = set()
    unique_tiles = []
    for tile in matches:
        if tile not in seen:
            seen.add(tile)
            unique_tiles.append(tile)
    
    return unique_tiles

def get_tenhou_analysis_sync(hand_string):
    """
    同步版本的分析函数（便于调用）
    
    Args:
        hand_string: 手牌字符串
        
    Returns:
        list: 结构化的打牌建议列表
    """
    # 检查是否已在事件循环中
    try:
        loop = asyncio.get_running_loop()
        # 如果已在事件循环中，创建任务
        if loop.is_running():
            # 创建新的事件循环在线程中运行
            import concurrent.futures
            import threading
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(get_tenhou_analysis_json(hand_string))
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()
        else:
            return asyncio.run(get_tenhou_analysis_json(hand_string))
    except RuntimeError:
        # 没有运行的事件循环
        return asyncio.run(get_tenhou_analysis_json(hand_string))

# 格式化输出函数
def format_analysis_result(result):
    """
    格式化输出分析结果
    
    Args:
        result: get_tenhou_analysis_json返回的结果
        
    Returns:
        str: 格式化的文本
    """
    
    if not result:
        return "未获取到分析结果"
    
    output_lines = []
    output_lines.append(f"找到 {len(result)} 个打牌建议:")
    output_lines.append("")
    
    for i, suggestion in enumerate(result, 1):
        tile = suggestion['tile']
        tiles = suggestion['tiles']
        number = suggestion['number']
        
        tiles_str = ', '.join(f"'{t}'" for t in tiles)
        line = f"{i:2d}. 打{tile} - 摸牌[{tiles_str}] - 有效牌数: {number}枚"
        output_lines.append(line)
    
    return '\n'.join(output_lines)

async def test_function():
    """
    测试函数
    """
    print("天凤麻将分析器 - JSON格式输出测试")
    print("=" * 60)
    
    # 测试用例
    test_hands = [
        "2245667m1234588s",
        "1245589m1244588s",
    ]
    
    for hand in test_hands:
        print(f"\n分析手牌: {hand}")
        print("-" * 40)
        
        try:
            # 获取JSON格式结果
            result = await get_tenhou_analysis_json(hand)
            
            if result:
                print("✅ 获取成功！")
                print(f"JSON结果 ({len(result)} 项):")
                
                # 打印JSON格式
                import json
                print(json.dumps(result, ensure_ascii=False, indent=2))
                
                print("\n格式化显示:")
                formatted = format_analysis_result(result)
                print(formatted)
                
            else:
                print("❌ 未获取到结果")
                
        except Exception as e:
            print(f"❌ 分析失败: {e}")
        
        print("-" * 60)

def demo_sync():
    """
    同步版本演示
    """
    print("\n=== 同步版本演示 ===")
    
    hand = "2245667m1234588s"
    print(f"分析手牌: {hand}")
    
    result = get_tenhou_analysis_sync(hand)
    
    if result:
        print("✅ 同步获取成功！")
        
        # 显示JSON
        import json
        print("JSON结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 格式化显示
        print("\n格式化结果:")
        print(format_analysis_result(result))
    else:
        print("❌ 同步获取失败")

def usage_examples():
    """
    使用示例
    """
    
    examples = '''
=== 使用示例 ===

1. 异步版本（推荐）:
```python
import asyncio
from tenhou_playwright_plus import get_tenhou_analysis_json

async def main():
    result = await get_tenhou_analysis_json("2245667m1234588s")
    print(result)

asyncio.run(main())
```

2. 同步版本（简单）:
```python
from tenhou_playwright_plus import get_tenhou_analysis_sync

result = get_tenhou_analysis_sync("2245667m1234588s")
print(result)
```

3. 格式化输出:
```python
from tenhou_playwright_plus import get_tenhou_analysis_sync, format_analysis_result

result = get_tenhou_analysis_sync("2245667m1234588s")
formatted = format_analysis_result(result)
print(formatted)
```

4. 处理结果:
```python
result = get_tenhou_analysis_sync("2245667m1234588s")

for suggestion in result:
    tile = suggestion['tile']
    tiles = suggestion['tiles']
    count = suggestion['number']
    
    print(f"打出 {tile}，可摸 {len(tiles)} 种牌，总计 {count} 枚")
```
'''
    
    print(examples)

async def main():
    """
    主函数
    """
    # 测试功能
    await test_function()
    
    # 使用示例
    usage_examples()

def demo_main():
    """
    演示主函数（避免嵌套事件循环）
    """
    print("=== 同步版本演示 ===")
    
    hand = "2245667m1234588s"
    print(f"分析手牌: {hand}")
    
    result = get_tenhou_analysis_sync(hand)
    
    if result:
        print("✅ 同步获取成功！")
        
        # 显示JSON
        import json
        print("JSON结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 格式化显示
        print("\n格式化结果:")
        print(format_analysis_result(result))
    else:
        print("❌ 同步获取失败")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
    
    print("\n" + "=" * 60)
    
    # 同步版本演示
    demo_main()