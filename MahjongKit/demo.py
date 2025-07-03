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

# 添加父目录到模块搜索路径
sys.path.append(str(Path(__file__).parent.parent))

from MahjongKit.core import Tile, TilesConverter, SuitType, PlayerState, Meld, MeldType
from MahjongKit.validator import WinValidator, TingValidator
from MahjongKit.analyzer import HandAnalyzer, GameAnalyzer


class ReplayAnalyzer:
    """牌谱分析器"""
    
    def __init__(self, replay_file: str):
        self.replay_file = replay_file
        self.game_data = self._load_replay()
        self.players = self._initialize_players()
        self.known_tiles = []  # 已知的牌(弃牌、副露等)
        self.analysis_results = []
    
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
    
    def analyze_replay(self):
        """分析牌谱，为玩家0提供建议"""
        print("=== 血战到底麻将分析 ===")
        print(f"牌谱文件: {self.replay_file}")
        print(f"游戏类型: {self.game_data.get('mjtype', 'unknown')}")
        
        # 显示定缺信息
        print("\n玩家定缺:")
        for i, player in enumerate(self.players):
            missing = player.missing_suit.value if player.missing_suit else "未知"
            print(f"  玩家{i}: {missing}")
        
        # 显示初始手牌(仅玩家0)
        print(f"\n玩家0初始手牌: {TilesConverter.tiles_to_string(self.players[0].hand_tiles)}")
        
        # 分析每个动作
        print("\n=== 动作分析 ===")
        for action in self.game_data.get("actions", []):
            self._process_action(action)
        
        # 生成最终分析报告
        self._generate_final_report()
    
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
        
        print(f"\n🎯 第{sequence}手 - 玩家0摸牌: {tile_str}")
        print(f"摸牌前手牌: {TilesConverter.tiles_to_string(self.players[0].hand_tiles)}")
        
        # 将摸到的牌加入手牌
        self.players[0].add_tile(draw_tile)
        
        # 分析手牌状态
        situation = HandAnalyzer.analyze_hand_situation(self.players[0], self.known_tiles)
        
        print(f"摸牌后手牌: {TilesConverter.tiles_to_string(self.players[0].hand_tiles)}")
        print(f"当前向听: {situation['current_shanten']}")
        print(f"是否听牌: {'是' if situation['is_ting'] else '否'}")
        
        # 显示最佳出牌建议
        if situation['best_discard']:
            best = situation['best_discard']
            print(f"💡 建议打出: {best.discard_tile}")
            print(f"   打出后向听: {best.shanten}")
            print(f"   有效进张: {best.effective_draws}张")
            if best.winning_tiles:
                print(f"   胡牌张: {[str(tile) for tile in best.winning_tiles]}")
        
        # 显示所有弃牌选择(前5个)
        print("📊 弃牌选择分析:")
        for i, analysis in enumerate(situation['discard_analyses'][:5]):
            print(f"   {i+1}. {analysis}")
        
        # 显示建议
        print("🔍 策略建议:")
        for suggestion in situation['suggestions']:
            print(f"   {suggestion}")
        
        # 保存分析结果
        self.analysis_results.append({
            "sequence": sequence,
            "draw_tile": tile_str,
            "situation": situation
        })
    
    def _generate_final_report(self):
        """生成最终分析报告"""
        print("\n" + "="*60)
        print("=== 最终分析报告 ===")
        
        # 最终手牌状态
        final_situation = HandAnalyzer.analyze_hand_situation(self.players[0], self.known_tiles)
        
        print(f"最终手牌: {TilesConverter.tiles_to_string(self.players[0].hand_tiles)}")
        print(f"副露: {[str(meld) for meld in self.players[0].melds]}")
        print(f"最终向听: {final_situation['current_shanten']}")
        print(f"是否花猪: {'是' if final_situation['is_flower_pig'] else '否'}")
        
        # 统计分析结果
        if self.analysis_results:
            print(f"\n📈 摸牌分析统计:")
            print(f"总摸牌次数: {len(self.analysis_results)}")
            
            # 向听数统计
            shanten_counts = {}
            for result in self.analysis_results:
                shanten = result["situation"]["current_shanten"]
                shanten_counts[shanten] = shanten_counts.get(shanten, 0) + 1
            
            print("向听数分布:")
            for shanten in sorted(shanten_counts.keys()):
                print(f"   {shanten}向听: {shanten_counts[shanten]}次")
            
            # 听牌情况
            ting_count = sum(1 for result in self.analysis_results if result["situation"]["is_ting"])
            print(f"听牌次数: {ting_count}")
        
        # 游戏结果
        print(f"\n🎮 游戏结果:")
        for i, player in enumerate(self.players):
            status = "胡牌" if player.is_winning else "未胡牌"
            if player.is_winning:
                win_type = "自摸" if player.is_self_draw else "点炮"
                print(f"   玩家{i}: {status} ({win_type} {player.winning_tile})")
            else:
                print(f"   玩家{i}: {status}")


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