#!/usr/bin/env python3
"""
测试API是否正常工作
"""
import requests
import json

def test_backend():
    """测试后端API"""
    base_url = "http://localhost:8000"
    
    # 测试根路径
    try:
        response = requests.get(f"{base_url}/")
        print(f"根路径状态: {response.status_code}")
        print(f"根路径响应: {response.json()}")
    except Exception as e:
        print(f"根路径测试失败: {e}")
        return False
    
    # 测试健康检查
    try:
        response = requests.get(f"{base_url}/health")
        print(f"健康检查状态: {response.status_code}")
        print(f"健康检查响应: {response.json()}")
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False
    
    # 测试API文档
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"API文档状态: {response.status_code}")
    except Exception as e:
        print(f"API文档访问失败: {e}")
    
    # 测试手牌分析API
    test_data = {
        "tiles": ["1wan", "2wan", "3wan"],
        "melds": []
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/mahjong/analyze-hand",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"手牌分析API状态: {response.status_code}")
        if response.status_code == 200:
            print(f"手牌分析API响应: {response.json()}")
        else:
            print(f"手牌分析API错误: {response.text}")
    except Exception as e:
        print(f"手牌分析API测试失败: {e}")
    
    return True

if __name__ == "__main__":
    print("开始测试后端API...")
    test_backend()