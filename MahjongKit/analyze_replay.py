#!/usr/bin/env python3
"""
分析test_final.json牌谱，为玩家0提供AI出牌建议
"""

import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from MahjongKit.core import Tile, TilesConverter, SuitType, PlayerState, Meld, MeldType
from MahjongKit.analyzer import AdvancedAIDecisionEngine, HandAnalyzer, AdvancedAIStrategy


def parse_chinese_tile(tile_str):
    """将中文牌转换为英文格式"""
    suit_map = {'万': 'm', '条': 's', '筒': 'p'}
    value = tile_str[0]
    suit_char = tile_str[1]
    return f"{value}{suit_map[suit_char]}"


def analyze_critical_decision_point():
    """分析序列57的关键决策点：玩家0摸到1条时的决策"""
    
    print("=" * 60)
    print("🎯 血战到底麻将AI分析 - test_final.json 牌谱")
    print("=" * 60)
    
    # 构建序列57时玩家0的状态
    player0 = PlayerState(0)
    
    # 玩家0定缺筒
    player0.set_missing_suit(SuitType.TONG)
    
    # 根据牌谱重建手牌状态（序列57之前）
    # 从最终手牌和行动逆推当时的手牌
    current_hand_chinese = [
        "2条", "3条", "4条", "6条", "7条", "8条", 
        "9条", "9条", "9条"  # 序列57摸牌前的手牌
    ]
    
    # 转换为英文格式并添加到玩家手牌
    for tile_str in current_hand_chinese:
        tile_en = parse_chinese_tile(tile_str)
        tile = Tile.from_string(tile_en)
        player0.add_tile(tile)
    
    # 添加1条的碰子（序列39获得）
    peng_tiles = [Tile.from_string("1s"), Tile.from_string("1s"), Tile.from_string("1s")]
    peng = Meld(MeldType.PENG, peng_tiles, target_player=1)
    player0.add_meld(peng)
    
    # 摸到的牌：1条
    draw_tile = Tile.from_string("1s")
    
    print(f"🎴 当前局面分析 (序列57)")
    print(f"  玩家0定缺: 筒")
    print(f"  当前手牌: {TilesConverter.tiles_to_string(player0.hand_tiles)}")
    print(f"  当前副露: {[str(meld) for meld in player0.melds]}")
    print(f"  摸到牌: {draw_tile}")
    print(f"  是否花猪: {player0.is_flower_pig()}")
    
    # 构建游戏上下文
    game_context = {
        "danger_level": 3,  # 中盘阶段
        "opponent_ting": [False, False, False],  # 假设对手未听牌
        "round_number": 57
    }
    
    print(f"\n🧠 高级AI分析开始...")
    
    # 获取综合AI分析
    analysis = AdvancedAIDecisionEngine.get_comprehensive_analysis(player0, game_context)
    
    print(f"\n📊 基础手牌分析:")
    basic = analysis["basic_analysis"]
    print(f"  当前向听数: {basic['current_shanten']}")
    print(f"  是否听牌: {basic['is_ting']}")
    
    # 分析杠牌机会（重点分析）
    print(f"\n🎲 杠牌决策分析:")
    should_kong, kong_analysis = AdvancedAIStrategy.should_declare_kong(
        draw_tile, player0.hand_tiles + [draw_tile], player0.melds, game_context)
    
    print(f"  可以加杠1条: {kong_analysis['can_kong']}")
    print(f"  建议杠牌: {should_kong}")
    print(f"  决策得分: {kong_analysis['decision_score']:.1f}")
    print(f"  AI建议: {kong_analysis['recommendation']}")
    
    if kong_analysis['benefits']:
        print(f"  杠牌好处:")
        for benefit in kong_analysis['benefits']['benefits']:
            print(f"    ✓ {benefit}")
    
    if kong_analysis['risks']:
        print(f"  杠牌风险:")
        for risk in kong_analysis['risks']['risks']:
            print(f"    ⚠ {risk}")
    
    # 花猪分析
    print(f"\n🐷 花猪风险分析:")
    flower_pig = analysis["flower_pig_strategy"]
    print(f"  当前风险等级: {flower_pig['analysis']['risk_level']}/5")
    print(f"  需要避免: {flower_pig['should_avoid']}")
    print(f"  包含花色: {flower_pig['analysis']['suits_present']}")
    
    # 如果不杠牌，分析最佳弃牌
    print(f"\n💡 弃牌选择分析:")
    test_hand = player0.hand_tiles + [draw_tile]
    discard_analyses = HandAnalyzer.analyze_discard_options(test_hand, player0.melds)
    
    print(f"  最佳弃牌选择:")
    for i, analysis in enumerate(discard_analyses[:3]):
        print(f"    {i+1}. {analysis}")
    
    # AI最终决策
    print(f"\n🎯 AI最终决策:")
    available_actions = ["kong", "discard"]
    
    # 手动构造更准确的决策，因为我们有了杠牌分析
    if should_kong:
        decision = {
            "action": "kong",
            "target": str(draw_tile),
            "confidence": 0.9,
            "reasoning": kong_analysis['recommendation']
        }
    else:
        decision = AdvancedAIDecisionEngine.make_decision(player0, ["discard"], game_context)
    
    print(f"  推荐行动: {decision['action']}")
    print(f"  目标: {decision.get('target', 'N/A')}")
    print(f"  置信度: {decision['confidence']:.1f}")
    print(f"  决策理由: {decision['reasoning']}")
    
    # 对比实际牌谱中的选择
    print(f"\n📋 与实际牌谱对比:")
    print(f"  实际选择: 加杠1条 (序列58)")
    print(f"  AI建议: {decision['action']} {decision.get('target', '')}")
    
    if decision['action'] == 'kong':
        print(f"  ✅ AI建议与实际选择一致!")
    else:
        print(f"  ⚠️ AI建议与实际选择不同")
    
    # 详细策略建议
    print(f"\n💎 专业级策略分析:")
    print(f"  🎯 当前局面：玩家0已定缺筒，手牌纯条子，无花猪风险")
    print(f"  🎲 杠牌价值：增加1根(倍数x2)，获得额外摸牌，保持清一色")
    print(f"  ⏰ 时机评估：中盘阶段，杠牌风险较低，收益明显")
    print(f"  🔮 后续规划：杠牌后专注条子清一色，追求高倍数胡牌")
    
    if should_kong:
        print(f"  ✅ 建议：立即加杠1条，这是最优选择！")
        print(f"     理由：①增加倍数 ②额外摸牌机会 ③维持清一色结构")
    else:
        print(f"  ❌ 建议：谨慎考虑，当前杠牌风险较高")
    
    return analysis, decision


def analyze_alternative_scenarios():
    """分析其他关键决策点"""
    print(f"\n" + "=" * 60)
    print(f"🔍 其他关键决策点分析")
    print(f"=" * 60)
    
    # 分析序列15：玩家0弃9万的决策
    print(f"\n📌 序列15分析：弃9万的决策")
    
    player0_seq15 = PlayerState(0)
    player0_seq15.set_missing_suit(SuitType.TONG)
    
    # 序列15前的手牌状态（推测）
    hand_seq15 = ["9m", "9m", "1s", "2s", "3s", "3s", "4s", "6s", "7s", "9s", "9s", "9s", "4s"]
    for tile_str in hand_seq15:
        tile = Tile.from_string(tile_str)
        player0_seq15.add_tile(tile)
    
    print(f"  手牌: {TilesConverter.tiles_to_string(player0_seq15.hand_tiles)}")
    print(f"  定缺: 筒")
    
    # 分析最佳弃牌
    discard_analyses = HandAnalyzer.analyze_discard_options(player0_seq15.hand_tiles)
    best_discard = discard_analyses[0]
    
    print(f"  AI建议弃牌: {best_discard.discard_tile}")
    print(f"  实际弃牌: 9万")
    print(f"  分析: {best_discard}")
    
    # 定缺策略分析
    print(f"\n📌 定缺策略回顾分析")
    missing_suit, missing_analysis = AdvancedAIStrategy.choose_missing_suit(
        player0_seq15.hand_tiles)
    
    print(f"  AI建议定缺: {missing_suit.value}")
    print(f"  实际定缺: 筒")
    print(f"  分析理由: {missing_analysis['reasoning']}")


def generate_comprehensive_strategy_guide():
    """生成综合策略指南"""
    print(f"\n" + "=" * 60)
    print(f"📚 玩家0专业级出牌策略指南")
    print(f"=" * 60)
    
    print(f"\n🎯 **核心策略：清一色路线**")
    print(f"   - 已定缺筒子，专注万字+条子的组合")
    print(f"   - 当前手牌已纯化为条子，价值极高")
    print(f"   - 优先保持清一色结构，追求高倍数")
    
    print(f"\n🎲 **杠牌时机把握：**")
    print(f"   ✅ 序列57：加杠1条 - 最佳时机，强烈推荐")
    print(f"   - 理由：中盘阶段，风险较低，收益明显")
    print(f"   - 价值：+1根(倍数x2) + 额外摸牌 + 维持清一色")
    
    print(f"\n🛡️ **风险控制要点：**")
    print(f"   - 已避免花猪风险(单一花色)")
    print(f"   - 定缺执行到位(无筒子牌)")
    print(f"   - 注意对手听牌状态，适时保守")
    
    print(f"\n📈 **胡牌路线规划：**")
    print(f"   1. 短期目标：完成清一色基本形")
    print(f"   2. 中期目标：寻找七对或标准胡牌机会")  
    print(f"   3. 长期目标：清一色(4倍) + 可能的龙七对(8倍)")
    
    print(f"\n💡 **关键决策原则：**")
    print(f"   🔥 优先级1：维持清一色完整性")
    print(f"   🎯 优先级2：增加根数获得倍数加成")
    print(f"   ⚡ 优先级3：提高胡牌效率")
    print(f"   🛡️ 优先级4：防守安全出牌")
    
    print(f"\n🏆 **预期收益分析：**")
    print(f"   - 基础清一色：4倍")
    print(f"   - 加杠1根：4倍 × 2 = 8倍")
    print(f"   - 如果自摸：8倍 × 2 = 16倍")
    print(f"   - 潜在龙七对：8倍基础 + 根数加成")


if __name__ == "__main__":
    try:
        # 分析关键决策点
        analysis, decision = analyze_critical_decision_point()
        
        # 分析其他场景
        analyze_alternative_scenarios()
        
        # 生成综合策略指南
        generate_comprehensive_strategy_guide()
        
        print(f"\n" + "=" * 60)
        print(f"✅ AI分析完成 - 专业级策略建议已生成")
        print(f"=" * 60)
        
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()