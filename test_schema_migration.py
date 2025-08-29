#!/usr/bin/env python3
"""
测试数据库模式迁移API端点
"""

import requests

BASE_URL = "https://gametracker-m37i.onrender.com"

def test_schema_migration():
    """测试数据库模式迁移功能"""
    
    print("调用数据库模式迁移API...")
    response = requests.post(f"{BASE_URL}/api/admin/migrate-schema")
    
    print(f"模式迁移API响应: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print("迁移结果:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  消息: {result.get('message', 'No message')}")
        return result.get('success', False)
    else:
        print(f"迁移失败: {response.status_code}")
        return False

if __name__ == "__main__":
    success = test_schema_migration()
    if success:
        print("数据库模式迁移测试完成!")
    else:
        print("数据库模式迁移测试失败!")