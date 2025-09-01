#!/usr/bin/env python3
"""
测试强制数据库迁移API端点
"""

import requests

BASE_URL = "https://gametracker-m37i.onrender.com"

def test_force_migration():
    """测试强制数据库迁移功能"""
    
    print("调用强制数据库迁移API...")
    response = requests.post(f"{BASE_URL}/api/admin/force-migrate")
    
    print(f"强制迁移API响应: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print("迁移结果:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  消息: {result.get('message', 'No message')}")
        if 'log' in result:
            print("  详细日志:")
            for log_entry in result['log']:
                print(f"    {log_entry}")
        return result.get('success', False)
    else:
        print(f"迁移失败: {response.status_code}")
        return False

if __name__ == "__main__":
    success = test_force_migration()
    if success:
        print("强制数据库迁移测试完成!")
    else:
        print("强制数据库迁移测试失败!")