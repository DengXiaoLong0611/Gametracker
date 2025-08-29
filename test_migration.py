#!/usr/bin/env python3
"""
测试数据库迁移API端点
"""

import requests
import json

BASE_URL = "https://gametracker-m37i.onrender.com"

def test_migration():
    """测试数据库迁移功能"""
    
    # 1. 登录获取token
    login_data = {
        "email": "382592406@qq.com",
        "password": "HEROsf4454"
    }
    
    print("登录获取token...")
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"登录失败: {response.status_code} - {response.text}")
        return False
        
    token_data = response.json()
    token = token_data['access_token']
    print(f"登录成功! Token: {token[:20]}...")
    
    # 2. 调用迁移API
    headers = {"Authorization": f"Bearer {token}"}
    
    print("调用数据库迁移API...")
    response = requests.post(f"{BASE_URL}/api/admin/migrate-legacy-data", headers=headers)
    
    print(f"迁移API响应: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print("迁移结果:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  消息: {result.get('message', 'No message')}")
        if 'games_migrated' in result:
            print(f"  迁移游戏数量: {result['games_migrated']}")
        if 'books_migrated' in result:
            print(f"  迁移书籍数量: {result['books_migrated']}")
        if 'errors' in result and result['errors']:
            print(f"  错误: {result['errors']}")
        return result.get('success', False)
    else:
        print(f"迁移失败: {response.status_code}")
        return False

if __name__ == "__main__":
    success = test_migration()
    if success:
        print("数据库迁移测试完成!")
    else:
        print("数据库迁移测试失败!")