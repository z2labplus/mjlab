#!/usr/bin/env python3
"""
SichuanMahjongKit Demo
血战到底麻将库演示程序

分析牌谱文件，为玩家0提供最优出牌建议
"""

import json
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

# 添加父目录到模块搜索路径
sys.path.append(str(Path(__file__).parent.parent))

from MahjongKit.core import Tile, TilesConverter, SuitType, PlayerState, Meld, MeldType
from MahjongKit.fixed_validator import WinValidator, TingValidator
from MahjongKit.analyzer import HandAnalyzer, GameAnalyzer


class ReplayAnalyzer:
    """牌谱分析器"""
    
    def __init__(self, replay_file: str):
        self.replay_file = replay_file
        self.game_data = self._load_replay()
        self.players = self._initialize_players()
        self.known_tiles = []  # 已知的牌(弃牌、副露等)
        self.analysis_results = []
        self.output_lines = []  # 存储输出内容
    
    def _load_replay(self) -> Dict[str, Any]:
        """加载牌谱文件"""
        try:
            with open(self.replay_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ 找不到牌谱文件: {self.replay_file}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"❌ 牌谱文件格式错误: {self.replay_file}")
            sys.exit(1)
    
    def _initialize_players(self) -> List[PlayerState]:
        """初始化玩家状态"""
        players = []
        
        for i in range(4):
            player = PlayerState(i)
            
            # 设置定缺
            if str(i) in self.game_data.get("misssuit", {}):
                missing_suit_str = self.game_data["misssuit"][str(i)]
                suit_map = {"万": SuitType.WAN, "条": SuitType.TIAO, "筒": SuitType.TONG}
                if missing_suit_str in suit_map:
                    player.set_missing_suit(suit_map[missing_suit_str])
            
            # 设置初始手牌
            if str(i) in self.game_data.get("initial_hands", {}):
                initial_tiles = self.game_data["initial_hands"][str(i)]["tiles"]
                for tile_str in initial_tiles:
                    tile = Tile.from_chinese(tile_str)
                    player.add_tile(tile)
            
            players.append(player)
        
        return players
    
    def _print_and_store(self, text: str, console_only: bool = False):
        """打印并存储输出内容"""
        print(text)
        if not console_only:
            self.output_lines.append(text)
    
    def analyze_replay(self):
        """分析牌谱，为玩家0提供建议"""
        self._print_and_store("=== 血战到底麻将分析 ===")
        self._print_and_store(f"牌谱文件: {self.replay_file}")
        self._print_and_store(f"游戏类型: {self.game_data.get('mjtype', 'unknown')}")
        self._print_and_store(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 显示定缺信息
        self._print_and_store("\n玩家定缺:")
        for i, player in enumerate(self.players):
            missing = player.missing_suit.value if player.missing_suit else "未知"
            self._print_and_store(f"  玩家{i}: {missing}")
        
        # 显示初始手牌(仅玩家0)
        initial_hand_str = TilesConverter.tiles_to_string(self.players[0].hand_tiles)
        self._print_and_store(f"\n玩家0初始手牌: {initial_hand_str}")
        self._print_and_store(f"初始向听数: {TingValidator.calculate_shanten(self.players[0].hand_tiles)}")
        
        # 分析每个动作
        self._print_and_store("\n" + "="*80)
        self._print_and_store("=== 详细动作分析 ===")
        for action in self.game_data.get("actions", []):
            self._process_action(action)
        
        # 生成最终分析报告
        self._generate_final_report()
        
        # 写入文件
        self._write_to_file()
    
    def _calculate_remaining_tiles(self) -> Dict[str, int]:
        """计算剩余牌数"""
        remaining = {}
        for suit in SuitType:
            for value in range(1, 10):
                tile = Tile(suit, value)
                remaining[str(tile)] = 4
        
        # 减去手牌
        for tile in self.players[0].hand_tiles:
            if str(tile) in remaining:
                remaining[str(tile)] -= 1
        
        # 减去副露
        for meld in self.players[0].melds:
            for tile in meld.tiles:
                if str(tile) in remaining:
                    remaining[str(tile)] -= 1
        
        # 减去已知牌
        for tile in self.known_tiles:
            if str(tile) in remaining:
                remaining[str(tile)] -= 1
        
        return remaining
    
    def _process_action(self, action: Dict[str, Any]):
        """处理单个动作"""
        sequence = action.get("sequence", 0)
        player_id = action.get("player_id", 0)
        action_type = action.get("type", "")
        tile_str = action.get("tile", "")
        
        # 处理不同类型的动作
        if action_type == "draw" and player_id == 0:
            # 玩家0摸牌 - 这是我们需要分析的关键时刻
            self._analyze_draw_action(sequence, tile_str)
        
        elif action_type == "discard":
            # 弃牌
            tile = Tile.from_chinese(tile_str)
            self.players[player_id].add_discard(tile)
            self.known_tiles.append(tile)
            
            # 从手牌中移除
            if player_id == 0:
                self.players[0].remove_tile(tile)
        
        elif action_type == "peng":
            # 碰牌
            tile = Tile.from_chinese(tile_str)
            target_player = action.get("target_player", 0)
            
            # 创建碰牌副露
            meld = Meld(MeldType.PENG, [tile, tile, tile], target_player)
            self.players[player_id].add_meld(meld)
            
            # 从手牌中移除2张
            if player_id == 0:
                self.players[0].remove_tile(tile)
                self.players[0].remove_tile(tile)
            
            # 记录已知牌
            self.known_tiles.extend([tile, tile, tile])
        
        elif action_type == "jiagang":
            # 加杠
            tile = Tile.from_chinese(tile_str)
            if player_id == 0:
                # 更新副露(从碰变成杠)
                for meld in self.players[0].melds:
                    if (meld.meld_type == MeldType.PENG and 
                        meld.tiles[0] == tile):
                        meld.meld_type = MeldType.JIAGANG
                        meld.tiles.append(tile)
                        break
                
                # 从手牌中移除
                self.players[0].remove_tile(tile)
            
            self.known_tiles.append(tile)
        
        elif action_type in ["hu", "zimo"]:
            # 胡牌
            tile = Tile.from_chinese(tile_str)
            self.players[player_id].is_winning = True
            self.players[player_id].winning_tile = tile
            self.players[player_id].is_self_draw = (action_type == "zimo")
    
    def _analyze_draw_action(self, sequence: int, tile_str: str):
        """分析玩家0的摸牌动作"""
        draw_tile = Tile.from_chinese(tile_str)
        
        self._print_and_store(f"\n🎯 第{sequence}手 - 玩家0摸牌: {tile_str}")
        self._print_and_store(f"摸牌前手牌: {TilesConverter.tiles_to_string(self.players[0].hand_tiles)}")
        
        # 将摸到的牌加入手牌
        self.players[0].add_tile(draw_tile)
        
        # 计算剩余牌数
        remaining_tiles_count = self._calculate_remaining_tiles()
        
        # 分析手牌状态
        situation = HandAnalyzer.analyze_hand_situation(self.players[0], self.known_tiles)
        
        self._print_and_store(f"摸牌后手牌: {TilesConverter.tiles_to_string(self.players[0].hand_tiles)}")
        self._print_and_store(f"当前向听: {situation['current_shanten']}")
        self._print_and_store(f"是否听牌: {'是' if situation['is_ting'] else '否'}")
        
        # 详细分析所有弃牌选择
        analyses = HandAnalyzer.analyze_discard_options(self.players[0].hand_tiles, self.players[0].melds, remaining_tiles_count)
        
        # 显示最佳出牌建议
        if analyses:
            best = analyses[0]
            self._print_and_store(f"💡 建议打出: {best.discard_tile}")
            self._print_and_store(f"   打出后向听: {best.shanten}")
            
            # 获取详细分析
            detailed = best.get_detailed_analysis(remaining_tiles_count)
            
            if best.shanten == 0:
                # 听牌状态
                self._print_and_store(f"   🎯 听牌! 胡牌张: {detailed['winning_tiles']}")
                
                # 详细显示每张胡牌张的信息
                total_remaining = 0
                self._print_and_store("   📋 胡牌张详情:")
                for tile_str, info in detailed["winning_tiles_detail"].items():
                    remaining = info["remaining_count"]
                    reason = info["reason"]
                    total_remaining += remaining
                    self._print_and_store(f"      {tile_str}: 剩余{remaining}张 ({reason})")
                
                self._print_and_store(f"   📊 总剩余胡牌张: {total_remaining}张")
                
            else:
                # 非听牌状态，显示有效进张
                self._print_and_store(f"   📈 有效进张分析:")
                if detailed["effective_tiles"]:
                    total_effective = 0
                    for tile_info in detailed["effective_tiles"]:
                        tile = tile_info["tile"]
                        remaining = tile_info["remaining_count"]
                        new_shanten = tile_info["new_shanten"]
                        total_effective += remaining
                        self._print_and_store(f"      {tile}: 剩余{remaining}张 (进张后{new_shanten}向听)")
                    self._print_and_store(f"   📊 总有效进张: {total_effective}张")
                else:
                    self._print_and_store("      无有效进张")
            
            # 显示面子分析
            if detailed["meld_analysis"]:
                self._print_and_store("   🔍 面子分析:")
                for meld in detailed["meld_analysis"]:
                    self._print_and_store(f"      {meld}")
        
        # 显示前5个弃牌选择的对比
        self._print_and_store("📊 弃牌选择对比:")
        for i, analysis in enumerate(analyses[:5]):
            detailed = analysis.get_detailed_analysis(remaining_tiles_count)
            if analysis.shanten == 0:
                win_count = sum(info["remaining_count"] for info in detailed["winning_tiles_detail"].values())
                self._print_and_store(f"   {i+1}. 弃{analysis.discard_tile}: {analysis.shanten}向听, 胡牌张{win_count}张, 得分{analysis.score:.1f}")
            else:
                eff_count = sum(tile["remaining_count"] for tile in detailed["effective_tiles"])
                self._print_and_store(f"   {i+1}. 弃{analysis.discard_tile}: {analysis.shanten}向听, 进张{eff_count}张, 得分{analysis.score:.1f}")
        
        # 显示建议
        self._print_and_store("🔍 策略建议:")
        for suggestion in situation['suggestions']:
            self._print_and_store(f"   {suggestion}")
        
        # 保存分析结果
        self.analysis_results.append({
            "sequence": sequence,
            "draw_tile": tile_str,
            "situation": situation,
            "detailed_analysis": detailed if 'detailed' in locals() else None
        })
        
        self._print_and_store("-" * 80)
    
    def _generate_final_report(self):
        """生成最终分析报告"""
        self._print_and_store("\n" + "="*80)
        self._print_and_store("=== 最终分析报告 ===")
        
        # 最终手牌状态
        final_situation = HandAnalyzer.analyze_hand_situation(self.players[0], self.known_tiles)
        
        self._print_and_store(f"最终手牌: {TilesConverter.tiles_to_string(self.players[0].hand_tiles)}")
        self._print_and_store(f"副露: {[str(meld) for meld in self.players[0].melds]}")
        self._print_and_store(f"最终向听: {final_situation['current_shanten']}")
        self._print_and_store(f"是否花猪: {'是' if final_situation['is_flower_pig'] else '否'}")
        
        # 统计分析结果
        if self.analysis_results:
            self._print_and_store(f"\n📈 摸牌分析统计:")
            self._print_and_store(f"总摸牌次数: {len(self.analysis_results)}")
            
            # 向听数统计
            shanten_counts = {}
            for result in self.analysis_results:
                shanten = result["situation"]["current_shanten"]
                shanten_counts[shanten] = shanten_counts.get(shanten, 0) + 1
            
            self._print_and_store("向听数分布:")
            for shanten in sorted(shanten_counts.keys()):
                if shanten == 99:
                    self._print_and_store(f"   花猪状态: {shanten_counts[shanten]}次")
                else:
                    self._print_and_store(f"   {shanten}向听: {shanten_counts[shanten]}次")
            
            # 听牌情况
            ting_count = sum(1 for result in self.analysis_results if result["situation"]["is_ting"])
            self._print_and_store(f"听牌次数: {ting_count}")
            
            # 最佳表现分析
            best_moments = [r for r in self.analysis_results if r["situation"]["current_shanten"] == 0]
            if best_moments:
                self._print_and_store(f"\n🏆 最佳听牌时刻:")
                for moment in best_moments[:3]:  # 显示前3个最佳时刻
                    seq = moment["sequence"]
                    tile = moment["draw_tile"]
                    self._print_and_store(f"   第{seq}手摸{tile}: 达到听牌状态")
        
        # 游戏结果
        self._print_and_store(f"\n🎮 游戏结果:")
        for i, player in enumerate(self.players):
            status = "胡牌" if player.is_winning else "未胡牌"
            if player.is_winning:
                win_type = "自摸" if player.is_self_draw else "点炮"
                self._print_and_store(f"   玩家{i}: {status} ({win_type} {player.winning_tile})")
            else:
                self._print_and_store(f"   玩家{i}: {status}")
        
        # 总结建议
        self._print_and_store(f"\n💡 总结建议:")
        if len([r for r in self.analysis_results if r["situation"]["current_shanten"] == 0]) > 10:
            self._print_and_store("   ✅ 表现优秀：大部分时间保持听牌状态")
        elif len([r for r in self.analysis_results if r["situation"]["current_shanten"] <= 1]) > 8:
            self._print_and_store("   👍 表现良好：多数时间处于低向听状态")
        else:
            self._print_and_store("   🔄 建议改进：关注效率打法，尽快进入听牌")
        
        self._print_and_store("="*80)
    
    def _write_to_file(self):
        """将分析结果写入文件"""
        output_file = Path(self.replay_file).parent / "test_final_result.txt"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.output_lines))
            
            self._print_and_store(f"\n📄 分析结果已保存到: {output_file}", console_only=True)
            
        except Exception as e:
            self._print_and_store(f"\n❌ 保存文件失败: {e}", console_only=True)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python demo.py <牌谱文件>")
        print("示例: python demo.py ../test_final.json")
        sys.exit(1)
    
    replay_file = sys.argv[1]
    
    # 如果文件路径是相对路径，转换为绝对路径
    if not Path(replay_file).is_absolute():
        replay_file = str(Path(__file__).parent / replay_file)
    
    analyzer = ReplayAnalyzer(replay_file)
    analyzer.analyze_replay()


if __name__ == "__main__":
    main()