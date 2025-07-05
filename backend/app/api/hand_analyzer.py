"""
手牌分析API - 集成MahjongKit数学工具
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# 添加MahjongKit到Python路径
import os
current_file = Path(__file__).resolve()
backend_dir = current_file.parent.parent.parent  # backend/
project_root = backend_dir.parent  # mjlab/
mahjong_kit_path = project_root / "MahjongKit"

# 打印调试信息
print(f"当前文件: {current_file}")
print(f"项目根目录: {project_root}")
print(f"MahjongKit路径: {mahjong_kit_path}")
print(f"MahjongKit是否存在: {mahjong_kit_path.exists()}")

if mahjong_kit_path.exists():
    sys.path.insert(0, str(mahjong_kit_path))
else:
    # 尝试其他可能的路径
    alt_paths = [
        project_root.parent / "MahjongKit",  # 上级目录
        Path.cwd() / "MahjongKit",  # 当前工作目录
        Path(__file__).parent.parent.parent.parent.parent / "MahjongKit"  # 再上一级
    ]
    for alt_path in alt_paths:
        print(f"尝试路径: {alt_path}, 存在: {alt_path.exists()}")
        if alt_path.exists():
            mahjong_kit_path = alt_path
            sys.path.insert(0, str(mahjong_kit_path))
            break

try:
    from core import Tile, TilesConverter, SuitType, PlayerState, Meld, MeldType
    from analyzer import HandAnalyzer as MahjongHandAnalyzer, AdvancedAIStrategy, AdvancedAIDecisionEngine
    from fixed_validator import WinValidator, TingValidator
except ImportError as e:
    print(f"导入MahjongKit模块失败: {e}")
    print(f"MahjongKit路径: {mahjong_kit_path}")
    print(f"路径是否存在: {mahjong_kit_path.exists()}")
    raise

router = APIRouter()

class HandAnalysisRequest(BaseModel):
    tiles: List[str]  # 牌的字符串表示，如 ["1wan", "2wan", "3wan"]
    melds: List[Dict] = []  # 副露信息

class HandAnalysisResponse(BaseModel):
    is_winning: bool
    shanten: int
    effective_draws: List[Dict[str, Any]]
    winning_tiles: List[Dict[str, Any]]
    detailed_analysis: Dict[str, Any]

def parse_tile_string(tile_str: str) -> Tile:
    """解析牌的字符串表示为Tile对象"""
    # 支持多种格式: "1wan", "1w", "1m"
    tile_str = tile_str.lower().strip()
    
    # 提取数值和花色
    if len(tile_str) >= 2:
        value_str = tile_str[0]
        suit_str = tile_str[1:]
        
        try:
            value = int(value_str)
        except ValueError:
            raise ValueError(f"Invalid tile value: {value_str}")
        
        # 花色映射
        suit_mapping = {
            'wan': SuitType.WAN, 'w': SuitType.WAN, 'm': SuitType.WAN,
            'tiao': SuitType.TIAO, 't': SuitType.TIAO, 's': SuitType.TIAO,
            'tong': SuitType.TONG, 'p': SuitType.TONG
        }
        
        if suit_str in suit_mapping:
            return Tile(suit_mapping[suit_str], value)
        else:
            raise ValueError(f"Invalid suit: {suit_str}")
    else:
        raise ValueError(f"Invalid tile format: {tile_str}")

def tile_to_dict(tile: Tile) -> Dict[str, Any]:
    """将Tile对象转换为字典"""
    return {
        "type": tile.suit.value,
        "value": tile.value
    }

@router.post("/analyze-hand", response_model=HandAnalysisResponse)
async def analyze_hand(request: HandAnalysisRequest):
    """
    分析手牌，返回向听数、有效进张、胡牌张等信息
    """
    try:
        # 解析手牌
        tiles = []
        for tile_str in request.tiles:
            tile = parse_tile_string(tile_str)
            tiles.append(tile)
        
        # 检查手牌数量
        if len(tiles) > 14:
            raise HTTPException(status_code=400, detail="手牌不能超过14张")
        
        # 检查每种牌不超过4张
        tile_counts = {}
        for tile in tiles:
            key = f"{tile.value}{tile.suit.value}"
            tile_counts[key] = tile_counts.get(key, 0) + 1
            if tile_counts[key] > 4:
                raise HTTPException(status_code=400, detail=f"牌 {key} 超过4张")
        
        # 创建玩家状态
        player_state = PlayerState(0)
        for tile in tiles:
            player_state.add_tile(tile)
        
        # 分析手牌
        analysis_result = {
            "is_winning": False,
            "shanten": 99,
            "effective_draws": [],
            "winning_tiles": [],
            "detailed_analysis": {}
        }
        
        # 检查是否胡牌
        if len(tiles) == 14:
            is_winning = WinValidator.is_winning_hand(tiles)
            analysis_result["is_winning"] = is_winning
            
            if is_winning:
                analysis_result["shanten"] = 0
                # 对于胡牌状态，不需要计算有效进张
                analysis_result["detailed_analysis"] = {
                    "current_shanten": 0,
                    "patterns": ["胡牌"],
                    "suggestions": ["🎉 恭喜！当前手牌已胡牌！"]
                }
            else:
                # 计算向听数
                shanten = TingValidator.calculate_shanten(tiles)
                analysis_result["shanten"] = shanten
                
                # 获取有效进张
                effective_draws = []
                for suit in SuitType:
                    for value in range(1, 10):
                        test_tile = Tile(suit, value)
                        test_tiles = tiles + [test_tile]
                        
                        # 检查是否超过4张限制
                        test_counts = {}
                        valid_test = True
                        for t in test_tiles:
                            key = f"{t.value}{t.suit.value}"
                            test_counts[key] = test_counts.get(key, 0) + 1
                            if test_counts[key] > 4:
                                valid_test = False
                                break
                        
                        if valid_test:
                            new_shanten = TingValidator.calculate_shanten(test_tiles)
                            if new_shanten < shanten:
                                effective_draws.append(tile_to_dict(test_tile))
                
                analysis_result["effective_draws"] = effective_draws
                
                # 生成详细分析
                analysis_result["detailed_analysis"] = {
                    "current_shanten": shanten,
                    "effective_draws_count": len(effective_draws),
                    "patterns": _analyze_patterns(tiles),
                    "suggestions": _generate_suggestions(tiles, shanten, len(effective_draws))
                }
        
        elif len(tiles) == 13:
            # 13张牌，检查听牌
            shanten = TingValidator.calculate_shanten(tiles)
            analysis_result["shanten"] = shanten
            
            if shanten == 0:
                # 听牌状态，计算胡牌张
                winning_tiles = []
                for suit in SuitType:
                    for value in range(1, 10):
                        test_tile = Tile(suit, value)
                        test_tiles = tiles + [test_tile]
                        
                        # 检查是否超过4张限制
                        test_counts = {}
                        valid_test = True
                        for t in test_tiles:
                            key = f"{t.value}{t.suit.value}"
                            test_counts[key] = test_counts.get(key, 0) + 1
                            if test_counts[key] > 4:
                                valid_test = False
                                break
                        
                        if valid_test and WinValidator.is_winning_hand(test_tiles):
                            winning_tiles.append(tile_to_dict(test_tile))
                
                analysis_result["winning_tiles"] = winning_tiles
                analysis_result["detailed_analysis"] = {
                    "current_shanten": 0,
                    "winning_tiles_count": len(winning_tiles),
                    "patterns": ["听牌"],
                    "suggestions": [f"🎯 已听牌！胡牌张: {len(winning_tiles)}种"]
                }
            else:
                # 计算有效进张
                effective_draws = []
                for suit in SuitType:
                    for value in range(1, 10):
                        test_tile = Tile(suit, value)
                        test_tiles = tiles + [test_tile]
                        
                        # 检查是否超过4张限制
                        test_counts = {}
                        valid_test = True
                        for t in test_tiles:
                            key = f"{t.value}{t.suit.value}"
                            test_counts[key] = test_counts.get(key, 0) + 1
                            if test_counts[key] > 4:
                                valid_test = False
                                break
                        
                        if valid_test:
                            new_shanten = TingValidator.calculate_shanten(test_tiles)
                            if new_shanten < shanten:
                                effective_draws.append(tile_to_dict(test_tile))
                
                analysis_result["effective_draws"] = effective_draws
                analysis_result["detailed_analysis"] = {
                    "current_shanten": shanten,
                    "effective_draws_count": len(effective_draws),
                    "patterns": _analyze_patterns(tiles),
                    "suggestions": _generate_suggestions(tiles, shanten, len(effective_draws))
                }
        else:
            # 其他情况
            shanten = TingValidator.calculate_shanten(tiles) if tiles else 8
            analysis_result["shanten"] = shanten
            analysis_result["detailed_analysis"] = {
                "current_shanten": shanten,
                "patterns": _analyze_patterns(tiles),
                "suggestions": _generate_suggestions(tiles, shanten, 0)
            }
        
        return HandAnalysisResponse(**analysis_result)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

def _analyze_patterns(tiles: List[Tile]) -> List[str]:
    """分析牌型特征"""
    if not tiles:
        return ["空手牌"]
    
    patterns = []
    
    # 统计花色
    suits = set(tile.suit for tile in tiles)
    if len(suits) == 1:
        patterns.append("清一色")
    elif len(suits) == 2:
        patterns.append("两门")
    elif len(suits) >= 3:
        patterns.append("三门/花猪风险")
    
    # 统计每种牌的数量
    tile_counts = {}
    for tile in tiles:
        key = f"{tile.value}{tile.suit.value}"
        tile_counts[key] = tile_counts.get(key, 0) + 1
    
    # 分析牌型结构
    pairs = sum(1 for count in tile_counts.values() if count == 2)
    triplets = sum(1 for count in tile_counts.values() if count == 3)
    quads = sum(1 for count in tile_counts.values() if count == 4)
    
    if pairs >= 3:
        patterns.append("多对子")
    if triplets > 0:
        patterns.append(f"{triplets}刻子")
    if quads > 0:
        patterns.append(f"{quads}杠")
    
    # 检查七对倾向
    if pairs + quads * 2 >= 4 and len(tiles) >= 8:
        patterns.append("七对倾向")
    
    return patterns if patterns else ["基础牌型"]

def _generate_suggestions(tiles: List[Tile], shanten: int, effective_count: int) -> List[str]:
    """生成AI建议"""
    suggestions = []
    
    if not tiles:
        suggestions.append("请选择手牌开始分析")
        return suggestions
    
    if shanten == 0:
        suggestions.append("🎯 已听牌！等待胡牌张")
    elif shanten == 1:
        suggestions.append("🔥 一向听！继续优化手牌")
    elif shanten <= 3:
        suggestions.append(f"📈 {shanten}向听，有进步空间")
    else:
        suggestions.append(f"🚀 {shanten}向听，需要大幅调整")
    
    if effective_count > 0:
        suggestions.append(f"⚡ 有{effective_count}种有效进张")
        if effective_count >= 10:
            suggestions.append("进张数量丰富，手牌潜力不错")
        elif effective_count >= 5:
            suggestions.append("进张数量适中，可以继续发展")
        else:
            suggestions.append("进张较少，需要调整策略")
    
    # 花色建议
    suits = set(tile.suit for tile in tiles)
    if len(suits) >= 3:
        suggestions.append("⚠️ 三门牌有花猪风险，建议定缺")
    elif len(suits) == 1:
        suggestions.append("🏆 清一色路线，倍数可观")
    
    return suggestions

# 额外的工具接口
@router.post("/get-effective-draws")
async def get_effective_draws(request: HandAnalysisRequest):
    """获取有效进张详细信息"""
    try:
        tiles = [parse_tile_string(tile_str) for tile_str in request.tiles]
        
        if not tiles:
            return {"effective_draws": []}
        
        current_shanten = TingValidator.calculate_shanten(tiles)
        effective_draws = []
        
        for suit in SuitType:
            for value in range(1, 10):
                test_tile = Tile(suit, value)
                test_tiles = tiles + [test_tile]
                
                # 检查4张限制
                test_counts = {}
                valid_test = True
                for t in test_tiles:
                    key = f"{t.value}{t.suit.value}"
                    test_counts[key] = test_counts.get(key, 0) + 1
                    if test_counts[key] > 4:
                        valid_test = False
                        break
                
                if valid_test:
                    new_shanten = TingValidator.calculate_shanten(test_tiles)
                    if new_shanten < current_shanten:
                        effective_draws.append({
                            "tile": tile_to_dict(test_tile),
                            "old_shanten": current_shanten,
                            "new_shanten": new_shanten,
                            "improvement": current_shanten - new_shanten
                        })
        
        return {
            "current_shanten": current_shanten,
            "effective_draws": effective_draws
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-winning")
async def check_winning(request: HandAnalysisRequest):
    """检查是否胡牌"""
    try:
        tiles = [parse_tile_string(tile_str) for tile_str in request.tiles]
        
        if len(tiles) != 14:
            return {
                "is_winning": False,
                "reason": f"胡牌需要14张牌，当前{len(tiles)}张"
            }
        
        is_winning = WinValidator.is_winning_hand(tiles)
        
        return {
            "is_winning": is_winning,
            "reason": "胡牌" if is_winning else "未胡牌"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))