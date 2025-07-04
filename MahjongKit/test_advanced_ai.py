#!/usr/bin/env python3
"""
测试高级AI策略
验证定缺策略、避免花猪策略、杠牌决策等功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from MahjongKit.core import Tile, TilesConverter, SuitType, PlayerState, Meld, MeldType
from MahjongKit.analyzer import AdvancedAIStrategy, HandAnalyzer, AdvancedAIDecisionEngine


def test_missing_suit_strategy():
    """测试定缺策略"""
    print("=== 测试定缺策略 ===")
    
    test_cases = [
        {
            "name": "多万字情况",
            "tiles": "1123456789m11s",  # 万字多，但很有用
            "expected_suit": "s",  # 应该定缺条子
            "reason": "条子牌数少且孤立"
        },
        {
            "name": "孤立牌多的情况", 
            "tiles": "123m456s19p99m",  # 筒子有孤立的1、9
            "expected_suit": "p",
            "reason": "筒子有孤立牌"
        },
        {
            "name": "均匀分布情况",
            "tiles": "123m456s789p99s",  # 比较均匀
            "expected_suit": "m",  # 通常选择第一个或价值最低的
            "reason": "相对价值最低"
        }
    ]
    
    for case in test_cases:
        tiles = TilesConverter.string_to_tiles(case["tiles"])
        missing_suit, analysis = AdvancedAIStrategy.choose_missing_suit(tiles)
        
        print(f"\n{case['name']}:")
        print(f"  手牌: {case['tiles']}")
        print(f"  建议定缺: {missing_suit.value}")
        print(f"  分析理由: {analysis['reasoning']}")
        print(f"  花色分析:")
        for suit, detail in analysis['suit_analyses'].items():
            print(f"    {suit}: {detail['tile_count']}张, 有用度{detail['usefulness_score']:.1f}, 移除得分{detail['removal_score']:.1f}")
        
        # 验证建议的合理性
        if missing_suit.value == case["expected_suit"]:
            print("  ✅ 定缺建议符合预期")
        else:
            print(f"  ⚠️ 定缺建议({missing_suit.value})与预期({case['expected_suit']})不同，但可能合理")


def test_flower_pig_strategy():
    """测试避免花猪策略"""
    print("\n=== 测试避免花猪策略 ===")
    
    test_cases = [
        {
            "name": "三门花色-花猪",
            "tiles": "123m456s789p99m",
            "expected_risk": 5,
            "should_avoid": True
        },
        {
            "name": "两门花色-安全",
            "tiles": "123456789m99s",
            "expected_risk": 2,
            "should_avoid": False
        },
        {
            "name": "两门花色-高风险",
            "tiles": "1m2s3456789m99s",  # 万字很多，条子很少
            "expected_risk": 4,
            "should_avoid": True
        },
        {
            "name": "单门花色-最安全",
            "tiles": "11223344556677m",
            "expected_risk": 1,
            "should_avoid": False
        }
    ]
    
    for case in test_cases:
        tiles = TilesConverter.string_to_tiles(case["tiles"])
        should_avoid, analysis = AdvancedAIStrategy.should_avoid_flower_pig(tiles)
        
        print(f"\n{case['name']}:")
        print(f"  手牌: {case['tiles']}")
        print(f"  花色数: {analysis['current_suit_count']}")
        print(f"  风险等级: {analysis['risk_level']}/5")
        print(f"  是否需要避免: {should_avoid}")
        print(f"  包含花色: {analysis['suits_present']}")
        
        if analysis['avoidance_strategy']:
            strategy = analysis['avoidance_strategy']
            print(f"  避免策略: 优先打出{strategy['target_suit_to_eliminate']}的牌")
            print(f"  建议打出: {strategy['tiles_to_discard']}")
        
        # 验证风险评估
        if analysis['risk_level'] == case["expected_risk"]:
            print("  ✅ 风险评估准确")
        else:
            print(f"  ⚠️ 风险评估({analysis['risk_level']})与预期({case['expected_risk']})不同")
        
        if should_avoid == case["should_avoid"]:
            print("  ✅ 避免建议正确")
        else:
            print(f"  ❌ 避免建议({should_avoid})与预期({case['should_avoid']})不符")


def test_kong_decision():
    """测试杠牌决策"""
    print("\n=== 测试杠牌决策 ===")
    
    test_cases = [
        {
            "name": "序盘明杠-有利",
            "tiles": "1111234567889m",
            "kong_tile": "1m",
            "game_situation": {"danger_level": 1},
            "expected_decision": True,
            "reason": "序盘杠牌增加根数有利"
        },
        {
            "name": "终盘明杠-危险",
            "tiles": "1111234567889m", 
            "kong_tile": "1m",
            "game_situation": {"danger_level": 5, "opponent_ting": [True]},
            "expected_decision": False,
            "reason": "终盘对手听牌时杠牌危险"
        },
        {
            "name": "清一色杠牌-有利",
            "tiles": "1111234567889m",
            "kong_tile": "1m", 
            "game_situation": {"danger_level": 2},
            "expected_decision": True,
            "reason": "清一色情况下杠牌有额外价值"
        },
        {
            "name": "破坏结构杠牌-不利",
            "tiles": "1234567891111m",  # 杠1会破坏顺子可能性
            "kong_tile": "1m",
            "game_situation": {"danger_level": 3},
            "expected_decision": False,
            "reason": "杠牌会破坏手牌结构"
        }
    ]
    
    for case in test_cases:
        tiles = TilesConverter.string_to_tiles(case["tiles"])
        kong_tile = Tile.from_string(case["kong_tile"])
        
        should_kong, analysis = AdvancedAIStrategy.should_declare_kong(
            kong_tile, tiles, [], case["game_situation"])
        
        print(f"\n{case['name']}:")
        print(f"  手牌: {case['tiles']}")
        print(f"  杠牌: {case['kong_tile']}")
        print(f"  游戏局势: {case['game_situation']}")
        print(f"  是否可杠: {analysis['can_kong']}")
        print(f"  建议杠牌: {should_kong}")
        print(f"  决策得分: {analysis['decision_score']:.1f}")
        print(f"  AI建议: {analysis['recommendation']}")
        
        if analysis['benefits']:
            print(f"  好处: {', '.join(analysis['benefits']['benefits'])}")
        if analysis['risks']:
            print(f"  风险: {', '.join(analysis['risks']['risks'])}")
        
        # 验证决策合理性
        if should_kong == case["expected_decision"]:
            print("  ✅ 杠牌决策符合预期")
        else:
            print(f"  ⚠️ 杠牌决策({should_kong})与预期({case['expected_decision']})不同")


def test_integrated_ai_analysis():
    """测试整合的AI分析"""
    print("\n=== 测试整合AI分析 ===")
    
    # 创建测试玩家状态
    player = PlayerState(0)
    
    # 测试手牌：有花猪风险，有杠牌机会，需要定缺决策
    tiles_str = "1111m234s567p89m"
    tiles = TilesConverter.string_to_tiles(tiles_str)
    
    for tile in tiles:
        player.add_tile(tile)
    
    # 添加一个副露
    pong_tiles = TilesConverter.string_to_tiles("222s")
    pong = Meld(MeldType.PENG, pong_tiles)
    player.add_meld(pong)
    
    print(f"测试玩家状态:")
    print(f"  手牌: {TilesConverter.tiles_to_string(player.hand_tiles)}")
    print(f"  副露: {[str(meld) for meld in player.melds]}")
    print(f"  是否花猪: {player.is_flower_pig()}")
    
    # 获取综合AI分析
    game_context = {"danger_level": 3}
    analysis = AdvancedAIDecisionEngine.get_comprehensive_analysis(player, game_context)
    
    print(f"\n综合AI分析结果:")
    print(f"  当前向听: {analysis['basic_analysis']['current_shanten']}")
    
    if analysis['missing_suit_strategy']:
        strategy = analysis['missing_suit_strategy']
        print(f"  定缺建议: {strategy['recommended_suit']}")
        print(f"  定缺理由: {strategy['analysis']['reasoning']}")
    
    pig_strategy = analysis['flower_pig_strategy']
    print(f"  花猪风险: {pig_strategy['analysis']['risk_level']}/5")
    print(f"  需要避免花猪: {pig_strategy['should_avoid']}")
    
    if analysis['kong_opportunities']:
        print(f"  杠牌机会:")
        for opp in analysis['kong_opportunities']:
            print(f"    {opp['tile']}({opp['type']}): {opp['should_declare']}")
    
    print(f"  整体建议:")
    for rec in analysis['overall_recommendations']:
        print(f"    {rec}")
    
    # 测试AI决策
    print(f"\nAI决策测试:")
    available_actions = ["discard", "kong"]
    decision = AdvancedAIDecisionEngine.make_decision(player, available_actions, game_context)
    
    print(f"  推荐行动: {decision['action']}")
    print(f"  目标: {decision.get('target', 'N/A')}")
    print(f"  置信度: {decision['confidence']:.1f}")
    print(f"  理由: {decision['reasoning']}")


def test_enhanced_hand_analyzer():
    """测试增强的手牌分析器"""
    print("\n=== 测试增强的手牌分析器 ===")
    
    # 创建测试玩家
    player = PlayerState(0)
    tiles_str = "123m456s789p12m"  # 混合花色手牌
    tiles = TilesConverter.string_to_tiles(tiles_str)
    
    for tile in tiles:
        player.add_tile(tile)
    
    print(f"测试手牌: {tiles_str}")
    
    # 获取增强的手牌分析
    situation = HandAnalyzer.analyze_hand_situation(player)
    
    print(f"增强分析结果:")
    print(f"  当前向听: {situation['current_shanten']}")
    print(f"  是否听牌: {situation['is_ting']}")
    print(f"  最佳弃牌: {situation['best_discard']}")
    print(f"  是否花猪: {situation['is_flower_pig']}")
    
    print(f"  AI建议:")
    for suggestion in situation['suggestions']:
        print(f"    {suggestion}")
    
    # 测试摸牌模拟
    draw_tile = Tile.from_string("3m")
    print(f"\n模拟摸牌: {draw_tile}")
    
    draw_result = HandAnalyzer.simulate_draw_tile(player, draw_tile)
    print(f"  推荐行动: {draw_result['action']}")
    print(f"  目标: {draw_result.get('discard_tile', draw_result.get('kong_tile', 'N/A'))}")
    print(f"  消息: {draw_result['message']}")
    
    if 'advanced_strategy' in draw_result:
        strategy = draw_result['advanced_strategy']
        print(f"  花猪风险: {strategy['flower_pig_risk']}")
        if strategy['kong_opportunity']:
            print(f"  杠牌机会: {strategy['kong_opportunity']}")


if __name__ == "__main__":
    print("血战到底麻将库 - 高级AI策略测试")
    print("=" * 50)
    
    test_missing_suit_strategy()
    test_flower_pig_strategy()
    test_kong_decision()
    test_integrated_ai_analysis()
    test_enhanced_hand_analyzer()
    
    print("\n" + "=" * 50)
    print("高级AI策略测试完成")