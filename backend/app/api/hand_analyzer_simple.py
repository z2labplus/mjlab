"""
手牌分析API - 简化版本，避免复杂的模块导入
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum

router = APIRouter()

class SuitType(Enum):
    WAN = "wan"
    TIAO = "tiao"
    TONG = "tong"

class Tile:
    def __init__(self, suit: SuitType, value: int):
        self.suit = suit
        self.value = value
    
    def __eq__(self, other):
        return isinstance(other, Tile) and self.suit == other.suit and self.value == other.value
    
    def __hash__(self):
        return hash((self.suit, self.value))
    
    def __repr__(self):
        return f"{self.value}{self.suit.value}"

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
    tile_str = tile_str.lower().strip()
    
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

def tiles_to_array(tiles: List[Tile]) -> List[int]:
    """将牌转换为27位数组表示"""
    array = [0] * 27
    for tile in tiles:
        if tile.suit == SuitType.WAN:
            index = tile.value - 1
        elif tile.suit == SuitType.TIAO:
            index = 9 + tile.value - 1
        else:  # TONG
            index = 18 + tile.value - 1
        array[index] += 1
    return array

def calculate_shanten_simple(tiles: List[Tile]) -> int:
    """简化的向听数计算"""
    if not tiles:
        return 8
    
    array = tiles_to_array(tiles)
    
    # 检查七对
    pairs = 0
    singles = 0
    for count in array:
        if count >= 2:
            pairs += count // 2
            if count % 2 == 1:
                singles += 1
        elif count == 1:
            singles += 1
    
    # 七对向听数
    seven_pairs_shanten = 6 - pairs + singles
    
    # 标准形向听数（简化计算）
    total_tiles = len(tiles)
    groups = 0
    pairs_count = 0
    
    # 统计刻子和对子
    for count in array:
        groups += count // 3
        remaining = count % 3
        if remaining >= 2:
            pairs_count += 1
    
    # 简化的标准形向听数计算
    if total_tiles == 14:
        # 14张牌时检查是否胡牌
        if groups == 4 and pairs_count >= 1:
            return 0
        else:
            return max(0, 4 - groups + (1 if pairs_count == 0 else 0))
    elif total_tiles == 13:
        # 13张牌时的向听数
        needed_groups = 4 - groups
        has_pair = pairs_count > 0
        return max(0, needed_groups + (0 if has_pair else 1))
    else:
        # 其他情况的估算
        needed_groups = 4 - groups
        return max(1, needed_groups + (1 if pairs_count == 0 else 0))

def is_winning_hand_simple(tiles: List[Tile]) -> bool:
    """简化的胡牌检查"""
    if len(tiles) != 14:
        return False
    
    array = tiles_to_array(tiles)
    
    # 检查七对
    pairs = 0
    for count in array:
        if count == 2:
            pairs += 1
        elif count != 0:
            break
    if pairs == 7:
        return True
    
    # 检查标准形（4个面子+1个对子）
    def check_standard_form(arr, groups=0, has_pair=False):
        if groups == 4 and has_pair:
            return True
        if groups > 4:
            return False
        
        # 找第一个非零位置
        first_nonzero = -1
        for i in range(27):
            if arr[i] > 0:
                first_nonzero = i
                break
        
        if first_nonzero == -1:
            return groups == 4 and has_pair
        
        # 尝试刻子
        if arr[first_nonzero] >= 3:
            new_arr = arr[:]
            new_arr[first_nonzero] -= 3
            if check_standard_form(new_arr, groups + 1, has_pair):
                return True
        
        # 尝试对子（如果还没有对子）
        if not has_pair and arr[first_nonzero] >= 2:
            new_arr = arr[:]
            new_arr[first_nonzero] -= 2
            if check_standard_form(new_arr, groups, True):
                return True
        
        # 尝试顺子（只对万、条、筒有效）
        if first_nonzero % 9 <= 6:  # 可以形成顺子
            suit_base = (first_nonzero // 9) * 9
            if (first_nonzero + 1 < suit_base + 9 and 
                first_nonzero + 2 < suit_base + 9 and
                arr[first_nonzero + 1] > 0 and arr[first_nonzero + 2] > 0):
                new_arr = arr[:]
                new_arr[first_nonzero] -= 1
                new_arr[first_nonzero + 1] -= 1
                new_arr[first_nonzero + 2] -= 1
                if check_standard_form(new_arr, groups + 1, has_pair):
                    return True
        
        return False
    
    return check_standard_form(array)

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
            is_winning = is_winning_hand_simple(tiles)
            analysis_result["is_winning"] = is_winning
            
            if is_winning:
                analysis_result["shanten"] = 0
                analysis_result["detailed_analysis"] = {
                    "current_shanten": 0,
                    "patterns": ["胡牌"],
                    "suggestions": ["🎉 恭喜！当前手牌已胡牌！"]
                }
            else:
                shanten = calculate_shanten_simple(tiles)
                analysis_result["shanten"] = shanten
                analysis_result["detailed_analysis"] = {
                    "current_shanten": shanten,
                    "patterns": _analyze_patterns(tiles),
                    "suggestions": _generate_suggestions(tiles, shanten, 0)
                }
        
        elif len(tiles) == 13:
            # 13张牌，检查听牌
            shanten = calculate_shanten_simple(tiles)
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
                        
                        if valid_test and is_winning_hand_simple(test_tiles):
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
                            new_shanten = calculate_shanten_simple(test_tiles)
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
            shanten = calculate_shanten_simple(tiles) if tiles else 8
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
        
        current_shanten = calculate_shanten_simple(tiles)
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
                    new_shanten = calculate_shanten_simple(test_tiles)
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
        
        is_winning = is_winning_hand_simple(tiles)
        
        return {
            "is_winning": is_winning,
            "reason": "胡牌" if is_winning else "未胡牌"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))