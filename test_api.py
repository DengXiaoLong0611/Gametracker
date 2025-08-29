#!/usr/bin/env python3
"""
测试部署的API功能
"""

import requests
import json

BASE_URL = "https://gametracker-m37i.onrender.com"

def test_login():
    """测试登录功能"""
    login_data = {
        "email": "382592406@qq.com",
        "password": "HEROsf4454"
    }
    
    print("测试登录...")
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"登录成功! Token: {token_data['access_token'][:20]}...")
        return token_data['access_token']
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

def test_games_api(token):
    """测试游戏API"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n[GAME] 测试获取游戏数据...")
    response = requests.get(f"{BASE_URL}/api/games", headers=headers)
    
    if response.status_code == 200:
        games = response.json()
        print("[OK] 获取游戏数据成功!")
        print(f"[INFO] 游戏统计:")
        for status, game_list in games.items():
            print(f"   {status}: {len(game_list)} 个游戏")
        return True
    else:
        print(f"[FAIL] 获取游戏数据失败: {response.status_code} - {response.text}")
        return False

def test_add_game(token):
    """测试添加游戏功能"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    game_data = {
        "name": "API测试游戏",
        "status": "active",
        "notes": "这是API功能测试",
        "rating": None,
        "reason": ""
    }
    
    print("\n[ADD] 测试添加游戏...")
    response = requests.post(f"{BASE_URL}/api/games", json=game_data, headers=headers)
    
    if response.status_code == 200:
        game = response.json()
        print(f"[OK] 添加游戏成功! 游戏ID: {game['id']}")
        return game['id']
    else:
        print(f"[FAIL] 添加游戏失败: {response.status_code} - {response.text}")
        return None

def test_active_count(token):
    """测试活跃游戏计数"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n[COUNT] 测试活跃游戏计数...")
    response = requests.get(f"{BASE_URL}/api/active-count", headers=headers)
    
    if response.status_code == 200:
        count_data = response.json()
        print("[OK] 获取计数成功!")
        print(f"[INFO] 活跃游戏: {count_data['count']}/{count_data['limit']}")
        return True
    else:
        print(f"[FAIL] 获取计数失败: {response.status_code} - {response.text}")
        return False

def cleanup_test_game(token, game_id):
    """清理测试游戏"""
    if not game_id:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    print(f"\n[CLEAN] 清理测试游戏 ID: {game_id}...")
    
    response = requests.delete(f"{BASE_URL}/api/games/{game_id}", headers=headers)
    if response.status_code == 200:
        print("[OK] 测试游戏已清理")
    else:
        print(f"[WARN] 清理失败: {response.status_code} - {response.text}")

def main():
    print("[START] 开始API功能测试...")
    
    # 测试登录
    token = test_login()
    if not token:
        print("\n[FAIL] 登录失败，终止测试")
        return
    
    # 测试各项API功能
    success_count = 0
    total_tests = 3
    
    if test_games_api(token):
        success_count += 1
    
    if test_active_count(token):
        success_count += 1
    
    # 测试添加游戏并清理
    game_id = test_add_game(token)
    if game_id:
        success_count += 1
        cleanup_test_game(token, game_id)
    
    # 总结
    print(f"\n[SUMMARY] 测试总结: {success_count}/{total_tests} 项测试通过")
    if success_count == total_tests:
        print("[SUCCESS] 所有API功能正常!")
    else:
        print("[WARN] 部分功能存在问题，需要进一步检查")

if __name__ == "__main__":
    main()