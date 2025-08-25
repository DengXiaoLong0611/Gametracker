#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化游戏追踪器数据库
参考网页信息添加示例游戏数据
"""

from models import GameStatus, GameCreate
from store import GameStore
from datetime import datetime

def init_database():
    """初始化数据库，添加示例游戏数据"""
    print("🚀 初始化游戏追踪器数据库...")
    
    # 创建游戏存储
    store = GameStore(default_limit=3)
    
    # 清空现有数据
    print("📝 清空现有数据...")
    
    # 添加示例游戏数据
    games_data = [
        # 正在游玩的游戏
        {
            "name": "塞尔达传说：王国之泪",
            "status": GameStatus.ACTIVE,
            "notes": "开放世界冒险游戏，探索海拉鲁大陆",
            "rating": None,
            "reason": ""
        },
        {
            "name": "最终幻想16",
            "status": GameStatus.ACTIVE,
            "notes": "动作RPG，体验克莱夫的复仇之旅",
            "rating": None,
            "reason": ""
        },
        
        # 暂时放下的游戏
        {
            "name": "艾尔登法环",
            "status": GameStatus.PAUSED,
            "notes": "魂类游戏，暂时放下休息一下",
            "rating": None,
            "reason": ""
        },
        {
            "name": "赛博朋克2077",
            "status": GameStatus.PAUSED,
            "notes": "开放世界RPG，等待DLC更新",
            "rating": None,
            "reason": ""
        },
        
        # 休闲游戏
        {
            "name": "俄罗斯方块",
            "status": GameStatus.CASUAL,
            "notes": "经典益智游戏，随时可以玩",
            "rating": None,
            "reason": ""
        },
        {
            "name": "炉石传说",
            "status": GameStatus.CASUAL,
            "notes": "卡牌对战游戏，休闲娱乐",
            "rating": None,
            "reason": ""
        },
        
        # 未来要玩的游戏
        {
            "name": "星空",
            "status": GameStatus.PLANNED,
            "notes": "Bethesda太空RPG，期待已久",
            "rating": None,
            "reason": ""
        },
        {
            "name": "博德之门3",
            "status": GameStatus.PLANNED,
            "notes": "经典RPG系列新作，回合制战斗",
            "rating": None,
            "reason": ""
        },
        {
            "name": "死亡搁浅2",
            "status": GameStatus.PLANNED,
            "notes": "小岛秀夫新作，期待剧情发展",
            "rating": None,
            "reason": ""
        },
        
        # 已通关的游戏
        {
            "name": "战神：诸神黄昏",
            "status": GameStatus.FINISHED,
            "notes": "北欧神话背景的动作冒险游戏",
            "rating": 9,
            "reason": "剧情精彩，战斗系统优秀，画面精美"
        },
        {
            "name": "荒野大镖客2",
            "status": GameStatus.FINISHED,
            "notes": "西部题材开放世界游戏",
            "rating": 10,
            "reason": "剧情深刻，角色塑造出色，世界细节丰富"
        },
        
        # 已弃坑的游戏
        {
            "name": "刺客信条：英灵殿",
            "status": GameStatus.DROPPED,
            "notes": "北欧海盗题材动作游戏",
            "rating": 6,
            "reason": "游戏内容重复，任务设计单调"
        }
    ]
    
    print(f"🎮 添加 {len(games_data)} 个示例游戏...")
    
    for i, game_data in enumerate(games_data, 1):
        try:
            game = store.add_game(GameCreate(**game_data))
            print(f"   ✅ {i:2d}. {game.name} - {game.status.value}")
        except Exception as e:
            print(f"   ❌ {i:2d}. {game_data['name']} - 添加失败: {e}")
    
    # 显示统计信息
    print("\n📊 数据库统计信息:")
    active_count = store.get_active_count()
    all_games = store.get_all_games()
    
    print(f"   正在游玩: {active_count['count']}/{active_count['limit']}")
    print(f"   暂时放下: {active_count['paused_count']}")
    print(f"   休闲游戏: {active_count['casual_count']}")
    print(f"   未来要玩: {active_count['planned_count']}")
    print(f"   已通关: {len(all_games['finished'])}")
    print(f"   已弃坑: {len(all_games['dropped'])}")
    
    print("\n🎉 数据库初始化完成！")
    print("💡 提示：你可以启动应用来查看这些游戏数据")

if __name__ == "__main__":
    init_database() 