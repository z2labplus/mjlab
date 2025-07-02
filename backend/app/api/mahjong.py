from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
import json
from datetime import datetime

from ..models.mahjong import (
    GameRequest, GameResponse, GameState, Tile, TileType, 
    TileOperationRequest, GameOperationResponse, GameStateRequest, 
    ResetGameResponse, GangType
)
from ..algorithms.mahjong_analyzer import MahjongAnalyzer
# from ..services.game_manager import GameManager  # WebSocket已移除
from ..services.mahjong_game_service import MahjongGameService

router = APIRouter(tags=["mahjong"])

# 创建全局实例
analyzer = MahjongAnalyzer()
# game_manager = GameManager()  # WebSocket已移除
game_service = MahjongGameService()


@router.post("/analyze", response_model=GameResponse)
async def analyze_game(request: GameRequest):
    """分析游戏状态并返回建议"""
    try:
        analysis = analyzer.analyze_game_state(request.game_state, request.target_player)
        
        return GameResponse(
            success=True,
            analysis=analysis,
            message="分析完成"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/analyze-ultimate")
async def analyze_ultimate(request: dict):
    """使用 ultimate_analyzer.py 进行血战到底分析"""
    try:
        import sys
        import os
        
        # 添加 model/first_hand 路径到 sys.path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, '../../../model/first_hand')
        if model_path not in sys.path:
            sys.path.append(model_path)
        
        from ultimate_analyzer import XuezhanAnalyzer
        
        # 获取请求参数
        hand_tiles = request.get('hand_tiles', [])
        visible_tiles = request.get('visible_tiles', [])
        missing_suit = request.get('missing_suit', '')
        
        if not hand_tiles:
            raise ValueError("手牌不能为空")
        
        # 创建分析器并分析
        ultimate_analyzer = XuezhanAnalyzer()
        results = ultimate_analyzer.analyze_discard_options(hand_tiles, visible_tiles, missing_suit)
        
        # 格式化返回结果
        formatted_results = []
        for result in results:
            discard_tile = result['discard']
            useful_tiles = result['useful_tiles']
            useful_count = result['useful_count'] 
            expected_value = int(result['expected_value'])  # 收益
            
            # 计算进张种类数
            jinzhang_types = len(set(useful_tiles))
            
            # 格式化进张信息（显示前几种主要的牌及其数量）
            tile_counts = {}
            for tile in useful_tiles:
                tile_counts[tile] = tile_counts.get(tile, 0) + 1
            
            # 按数量排序，取前几个
            sorted_tiles = sorted(tile_counts.items(), key=lambda x: x[1], reverse=True)
            jinzhang_detail = ''.join([f"{tile}（{count}）" for tile, count in sorted_tiles[:6]])
            
            formatted_results.append({
                'discard_tile': discard_tile,
                'expected_value': expected_value,  # 收益
                'jinzhang_types': jinzhang_types,  # 进张种类数
                'jinzhang_count': useful_count,   # 总进张数
                'jinzhang_detail': jinzhang_detail,  # 详细进张信息
                'shanten': result.get('shanten', 14),
                'can_win': result.get('can_win', False),
                'is_forced': result.get('is_forced', False),
                'patterns': result.get('patterns', [])
            })
        
        return {
            "success": True,
            "message": "血战到底分析完成",
            "results": formatted_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"血战到底分析失败: {str(e)}")


@router.post("/create-tile")
async def create_tile(tile_type: str, value: int):
    """创建麻将牌"""
    try:
        tile_type_enum = TileType(tile_type)
        tile = Tile(type=tile_type_enum, value=value)
        return {"success": True, "tile": tile, "code": tile.to_code()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建麻将牌失败: {str(e)}")


@router.get("/tile-codes")
async def get_tile_codes():
    """获取所有麻将牌编码信息"""
    try:
        # 生成所有可能的麻将牌
        tiles = []
        for tile_type in ["wan", "tiao", "tong"]:
            for value in range(1, 10):
                tiles.append({
                    "type": tile_type,
                    "value": value,
                    "code": f"{value}{tile_type[0]}"  # 例如：1w, 2t, 3t
                })
        
        return {
            "success": True,
            "message": "获取麻将牌信息成功",
            "tiles": tiles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取麻将牌信息失败: {str(e)}")


# ============ 游戏操作 API ============

@router.post("/operation", response_model=GameOperationResponse)
async def perform_tile_operation(request: TileOperationRequest):
    """执行麻将牌操作（添加手牌、弃牌、碰牌、杠牌等）"""
    try:
        success, message = game_service.process_operation(request)
        
        if success:
            current_state = game_service.get_game_state()
            return GameOperationResponse(
                success=True,
                message=message,
                game_state=current_state
            )
        else:
            return GameOperationResponse(
                success=False,
                message=message
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


@router.get("/game-state", response_model=GameOperationResponse)
async def get_current_game_state():
    """获取当前游戏状态"""
    try:
        current_state = game_service.get_game_state()
        return GameOperationResponse(
            success=True,
            message="获取游戏状态成功",
            game_state=current_state
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取游戏状态失败: {str(e)}")


@router.post("/set-game-state", response_model=GameOperationResponse)
async def set_game_state(request: GameStateRequest):
    """设置游戏状态"""
    try:
        success = game_service.set_game_state(request.game_state)
        
        if success:
            return GameOperationResponse(
                success=True,
                message="设置游戏状态成功",
                game_state=game_service.get_game_state()
            )
        else:
            return GameOperationResponse(
                success=False,
                message="设置游戏状态失败"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置游戏状态失败: {str(e)}")


@router.post("/reset")
async def reset_game():
    """重置游戏状态"""
    try:
        game_service.reset_game()
        current_state = game_service.get_game_state()
        
        # 游戏状态已更新，前端可通过API获取
        
        return {
            "success": True,
            "message": "游戏重置成功",
            "game_state": current_state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置游戏失败: {str(e)}")


# 已移除重复的 /game-state 路由，使用上面的 get_current_game_state 函数


@router.post("/discard-tile")
async def discard_tile(
    player_id: int,
    tile_type: str,
    tile_value: int
):
    """弃牌操作"""
    try:
        # 创建牌对象
        tile = Tile(type=TileType(tile_type), value=tile_value)
        
        # 创建操作请求
        request = TileOperationRequest(
            player_id=player_id,
            operation_type="discard",
            tile=tile
        )
        
        # 处理弃牌操作
        success, message = game_service.process_operation(request)
        
        if success:
            # 获取更新后的游戏状态
            current_state = game_service.get_game_state()
            
            # 游戏状态已更新，前端可通过API获取
            
            return {
                "success": True,
                "message": message,
                "game_state": current_state
            }
        else:
            return {
                "success": False,
                "message": message
            }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"弃牌失败: {str(e)}")


# ============ 便捷操作 API ============

@router.post("/add-hand-tile")
async def add_hand_tile(
    player_id: int, 
    tile_type: str, 
    tile_value: int,
    game_id: Optional[str] = None
):
    """为玩家添加手牌
    
    注意：
    - 玩家0（我）：添加具体牌面
    - 其他玩家：只增加手牌数量
    """
    try:
        tile = Tile(type=TileType(tile_type), value=tile_value)
        request = TileOperationRequest(
            player_id=player_id,
            operation_type="hand",
            tile=tile,
            game_id=game_id
        )
        
        success, message = game_service.process_operation(request)
        
        return {
            "success": success,
            "message": message,
            "tile": tile.dict() if player_id == 0 else None,  # 其他玩家不返回具体牌面
            "player_id": player_id,
            "game_id": game_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"添加手牌失败: {str(e)}")


@router.post("/add-hand-count")
async def add_hand_count(
    player_id: int,
    count: int = 1
):
    """为其他玩家修改手牌数量（不指定具体牌面）
    
    注意：
    - 只能用于其他玩家（1、2、3）
    - 玩家0（我）请使用 add-hand-tile 接口
    - count可以为正数（增加）或负数（减少）
    """
    try:
        if player_id == 0:
            raise ValueError("玩家0（我）请使用 add-hand-tile 接口添加具体牌面")
        
        if count == 0:
            raise ValueError("数量不能为0")
        
        # 获取当前游戏状态
        current_state = game_service.get_game_state()
        player_id_str = str(player_id)
        
        # 确保玩家存在
        if player_id_str not in current_state["player_hands"]:
            current_state["player_hands"][player_id_str] = {
                "tiles": None,
                "tile_count": 0,
                "melds": []
            }
        
        # 修改手牌数量（可以增加或减少）
        if count > 0:
            current_state["player_hands"][player_id_str]["tile_count"] += count
            action_msg = f"玩家{player_id}手牌数量+{count}"
        else:
            # 减少手牌数量，但不能低于0
            current_count = current_state["player_hands"][player_id_str]["tile_count"]
            new_count = max(0, current_count + count)  # count是负数
            current_state["player_hands"][player_id_str]["tile_count"] = new_count
            actual_change = new_count - current_count
            action_msg = f"玩家{player_id}手牌数量{actual_change:+d}"
        
        # 保存状态
        game_service.set_game_state_dict(current_state)
        
        return {
            "success": True,
            "message": action_msg,
            "player_id": player_id,
            "change_count": count,
            "total_count": current_state["player_hands"][player_id_str]["tile_count"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"增加手牌数量失败: {str(e)}")


@router.post("/peng")
async def peng_tile_endpoint(
    player_id: int, 
    tile_type: str, 
    tile_value: int,
    source_player_id: Optional[int] = None
):
    """碰牌操作"""
    try:
        tile = Tile(type=TileType(tile_type), value=tile_value)
        request = TileOperationRequest(
            player_id=player_id,
            operation_type="peng",
            tile=tile,
            source_player_id=source_player_id
        )
        
        success, message = game_service.process_operation(request)
        
        return {
            "success": success,
            "message": message,
            "tile": tile.dict(),
            "player_id": player_id,
            "source_player_id": source_player_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"碰牌失败: {str(e)}")


@router.post("/gang")
async def gang_tile_endpoint(
    player_id: int,
    tile_type: str,
    tile_value: int,
    gang_type: str,  # "angang", "zhigang", "jiagang"
    source_player_id: Optional[int] = None
):
    """杠牌操作"""
    try:
        tile = Tile(type=TileType(tile_type), value=tile_value)
        
        # 转换杠牌类型
        operation_type_map = {
            "angang": "angang",
            "zhigang": "zhigang", 
            "jiagang": "jiagang"
        }
        
        if gang_type not in operation_type_map:
            raise ValueError(f"不支持的杠牌类型: {gang_type}")
        
        request = TileOperationRequest(
            player_id=player_id,
            operation_type=operation_type_map[gang_type],
            tile=tile,
            source_player_id=source_player_id
        )
        
        success, message = game_service.process_operation(request)
        
        return {
            "success": success,
            "message": message,
            "tile": tile.dict(),
            "player_id": player_id,
            "gang_type": gang_type,
            "source_player_id": source_player_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"杠牌失败: {str(e)}") 


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        return {
            "success": True,
            "message": "服务正常运行",
            "status": "healthy"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "status": "unhealthy"
        }


@router.get("/")
async def get_api_info():
    """获取API信息"""
    return {
        "name": "血战麻将 API",
        "version": "1.0.0",
        "description": "智能血战麻将辅助分析工具API",
        "docs_url": "/docs",
        "status": "running"
    }


@router.get("/connections")
async def get_connections():
    """获取所有已连接的客户端和游戏信息"""
    try:
        # WebSocket已移除，返回空的客户端列表
        clients = []
        
        # 获取所有活跃的游戏
        games = []
        if game_service._game_state:
            game_info = {
                "game_id": game_service._game_state.get("game_id", "unknown"),
                "created_at": datetime.now().isoformat(),  # 实际应该存储真实的创建时间
                "player_count": len(game_service._game_state.get("player_hands", {})),
                "status": "active" if game_service._game_state.get("game_started", False) else "waiting"
            }
            games.append(game_info)
        
        return {
            "success": True,
            "message": "获取连接信息成功",
            "clients": clients,
            "games": games
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取连接信息失败: {str(e)}")


@router.post("/set-test-mode")
async def set_test_mode(enabled: bool = True):
    """设置测试模式（允许任意玩家进行操作，跳过回合检查）"""
    try:
        # 获取当前游戏状态
        current_state = game_service.get_game_state()
        
        # 设置测试模式
        current_state["test_mode"] = enabled
        
        # 保存状态
        success = game_service.set_game_state_dict(current_state)
        
        return {
            "success": success,
            "message": f"测试模式已{'启用' if enabled else '禁用'}",
            "test_mode": enabled
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置测试模式失败: {str(e)}")


# ============ 定缺相关 API ============

@router.post("/set-missing-suit")
async def set_missing_suit(
    player_id: int,
    missing_suit: str
):
    """设置玩家定缺花色"""
    try:
        # 验证花色是否有效
        valid_suits = ["wan", "tiao", "tong"]
        if missing_suit not in valid_suits:
            return {
                "success": False,
                "message": f"无效的花色，必须是: {', '.join(valid_suits)}"
            }
        
        # 获取当前游戏状态
        current_state = game_service.get_game_state()
        player_id_str = str(player_id)
        
        # 确保玩家存在
        if player_id_str not in current_state.get("player_hands", {}):
            current_state.setdefault("player_hands", {})[player_id_str] = {
                "tiles": None,
                "tile_count": 0,
                "melds": [],
                "missing_suit": None
            }
        
        # 设置定缺
        current_state["player_hands"][player_id_str]["missing_suit"] = missing_suit
        
        # 保存状态
        success = game_service.set_game_state_dict(current_state)
        
        if success:
            # WebSocket已移除，不再广播
            # await game_manager.broadcast({
            #     "type": "missing_suit_update",
            #     "data": {
            #         "player_id": player_id,
            #         "missing_suit": missing_suit,
            #         "game_state": current_state
            #     }
            # })
            
            return {
                "success": True,
                "message": f"玩家{player_id}定缺设置成功: {missing_suit}",
                "player_id": player_id,
                "missing_suit": missing_suit,
                "game_state": current_state
            }
        else:
            return {
                "success": False,
                "message": "设置定缺失败"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置定缺失败: {str(e)}")


@router.get("/missing-suits")
async def get_missing_suits():
    """获取所有玩家的定缺信息"""
    try:
        current_state = game_service.get_game_state()
        missing_suits = {}
        
        for player_id, hand in current_state.get("player_hands", {}).items():
            missing_suits[player_id] = hand.get("missing_suit", None)
        
        return {
            "success": True,
            "message": "获取定缺信息成功",
            "missing_suits": missing_suits
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取定缺信息失败: {str(e)}")


@router.post("/reset-missing-suits")
async def reset_missing_suits():
    """重置所有玩家的定缺"""
    try:
        current_state = game_service.get_game_state()
        
        # 重置所有玩家的定缺
        for player_id, hand in current_state.get("player_hands", {}).items():
            hand["missing_suit"] = None
        
        # 保存状态
        success = game_service.set_game_state_dict(current_state)
        
        if success:
            # 定缺已重置，前端可通过API获取
            
            return {
                "success": True,
                "message": "所有玩家定缺已重置",
                "game_state": current_state
            }
        else:
            return {
                "success": False,
                "message": "重置定缺失败"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置定缺失败: {str(e)}")


# ============ 牌谱管理 API ============

@router.get("/export-game-record")
async def export_game_record():
    """导出当前游戏牌谱"""
    try:
        # 获取当前游戏状态
        current_state = game_service.get_game_state()
        
        # 构建牌谱数据
        game_record = {
            "game_info": {
                "game_id": current_state.get("game_id", "unknown"),
                "start_time": datetime.now().isoformat(),
                "player_count": 4,
                "game_mode": "xuezhan_daodi",  # 血战到底
                "export_time": datetime.now().isoformat()
            },
            "players": {
                "0": {"name": "我", "position": "我"},
                "1": {"name": "下家", "position": "下家"},
                "2": {"name": "对家", "position": "对家"},
                "3": {"name": "上家", "position": "上家"}
            },
            "missing_suits": {},
            "actions": current_state.get("actions_history", []),
            "final_state": {
                "player_hands": current_state.get("player_hands", {}),
                "player_discarded_tiles": current_state.get("player_discarded_tiles", {}),
                "discarded_tiles": current_state.get("discarded_tiles", [])
            }
        }
        
        # 添加定缺信息
        for player_id in ["0", "1", "2", "3"]:
            player_missing = game_service.get_player_missing_suit(int(player_id))
            if player_missing:
                game_record["missing_suits"][player_id] = player_missing
        
        # 添加统计信息
        total_actions = len(game_record["actions"])
        game_record["statistics"] = {
            "total_actions": total_actions,
            "action_types": {},
            "players_hu_count": 0
        }
        
        # 统计操作类型
        for action in game_record["actions"]:
            action_type = action.get("action_type", "unknown")
            if action_type in game_record["statistics"]["action_types"]:
                game_record["statistics"]["action_types"][action_type] += 1
            else:
                game_record["statistics"]["action_types"][action_type] = 1
        
        return {
            "success": True,
            "message": "牌谱导出成功",
            "data": game_record
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出牌谱失败: {str(e)}")


@router.post("/import-game-record")
async def import_game_record(request: dict):
    """导入游戏牌谱"""
    try:
        game_record = request.get("game_record")
        if not game_record:
            return {
                "success": False,
                "message": "请提供有效的牌谱数据"
            }
        
        # 重置游戏状态
        game_service.reset_game()
        
        # 导入定缺设置
        missing_suits = game_record.get("missing_suits", {})
        for player_id_str, missing_suit in missing_suits.items():
            player_id = int(player_id_str)
            game_service.set_player_missing_suit(player_id, missing_suit)
        
        # 导入最终状态
        final_state = game_record.get("final_state", {})
        if final_state:
            # 设置玩家手牌
            player_hands = final_state.get("player_hands", {})
            for player_id_str, hand_data in player_hands.items():
                game_service._game_state["player_hands"][player_id_str] = hand_data
            
            # 设置弃牌记录
            player_discarded = final_state.get("player_discarded_tiles", {})
            game_service._game_state["player_discarded_tiles"] = player_discarded
            
            # 设置公共弃牌
            discarded_tiles = final_state.get("discarded_tiles", [])
            game_service._game_state["discarded_tiles"] = discarded_tiles
        
        # 导入操作历史
        actions = game_record.get("actions", [])
        game_service._game_state["actions_history"] = actions
        
        # 保存状态
        game_service._save_state()
        
        return {
            "success": True,
            "message": f"牌谱导入成功，共导入{len(actions)}个操作",
            "game_state": game_service.get_game_state()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入牌谱失败: {str(e)}")


# ============ 游戏流程控制 API ============

@router.post("/set-current-player")
async def set_current_player(player_id: int):
    """设置当前轮到操作的玩家"""
    try:
        if player_id < 0 or player_id > 3:
            return {
                "success": False,
                "message": "玩家ID必须在0-3之间"
            }
        
        # 获取当前游戏状态
        current_state = game_service.get_game_state()
        
        # 设置当前玩家
        current_state["current_player"] = player_id
        
        # 保存状态
        success = game_service.set_game_state_dict(current_state)
        
        if success:
            # 当前玩家已变更，前端可通过API获取
            
            player_names = {0: "我", 1: "下家", 2: "对家", 3: "上家"}
            return {
                "success": True,
                "message": f"当前玩家已切换为: {player_names[player_id]}",
                "current_player": player_id,
                "game_state": current_state
            }
        else:
            return {
                "success": False,
                "message": "设置当前玩家失败"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置当前玩家失败: {str(e)}")


@router.post("/next-player")
async def next_player():
    """切换到下一个玩家"""
    try:
        # 获取当前游戏状态
        current_state = game_service.get_game_state()
        current_player = current_state.get("current_player", 0)
        
        # 切换到下一个玩家 (0->1->2->3->0)
        next_player_id = (current_player + 1) % 4
        
        # 设置下一个玩家
        current_state["current_player"] = next_player_id
        
        # 保存状态
        success = game_service.set_game_state_dict(current_state)
        
        if success:
            player_names = {0: "我", 1: "下家", 2: "对家", 3: "上家"}
            return {
                "success": True,
                "message": f"轮到下一个玩家: {player_names[next_player_id]}",
                "previous_player": current_player,
                "current_player": next_player_id,
                "game_state": current_state
            }
        else:
            return {
                "success": False,
                "message": "切换玩家失败"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切换玩家失败: {str(e)}")


@router.post("/player-win")
async def player_win(
    player_id: int,
    win_type: str,  # "zimo" 或 "dianpao"
    win_tile_type: Optional[str] = None,
    win_tile_value: Optional[int] = None,
    dianpao_player_id: Optional[int] = None
):
    """玩家胡牌（自摸或点炮）"""
    try:
        current_state = game_service.get_game_state()
        
        # 设置玩家胜利状态
        player_id_str = str(player_id)
        if "player_hands" not in current_state:
            current_state["player_hands"] = {}
        
        # 🔧 重要修复：确保玩家数据存在，但不覆盖已有的手牌数据
        if player_id_str not in current_state["player_hands"]:
            # 只有当玩家数据完全不存在时才创建新的
            current_state["player_hands"][player_id_str] = {
                "tiles": None if player_id != 0 else [],
                "tile_count": 0,
                "melds": []
            }
        
        # 对于已存在的玩家数据，只确保必要字段存在，不覆盖现有数据
        player_hand = current_state["player_hands"][player_id_str]
        if "tiles" not in player_hand:
            player_hand["tiles"] = None if player_id != 0 else []
        if "tile_count" not in player_hand:
            player_hand["tile_count"] = 0
        if "melds" not in player_hand:
            player_hand["melds"] = []
        
        # 设置胜利状态
        current_state["player_hands"][player_id_str]["is_winner"] = True
        current_state["player_hands"][player_id_str]["win_type"] = win_type
        
        # 🔧 调试：检查设置胜利状态后手牌数据是否完整
        tiles = player_hand.get("tiles")
        tiles_count = len(tiles) if tiles else 0
        print(f"🏆 设置玩家{player_id}胜利状态后，手牌数据: {tiles_count}张, tiles类型={type(tiles)}")
        
        # 设置胡牌信息
        if win_tile_type and win_tile_value:
            current_state["player_hands"][player_id_str]["win_tile"] = {
                "type": win_tile_type,
                "value": win_tile_value
            }
        
        # 如果是点炮，设置点炮者信息
        if win_type == "dianpao" and dianpao_player_id is not None:
            current_state["player_hands"][player_id_str]["dianpao_player_id"] = dianpao_player_id
        
        # 更新游戏状态
        game_service.set_game_state_dict(current_state)
        
        # 注意：胜利信息已保存到游戏状态中，前端可通过轮询获取
        
        player_names = {0: "我", 1: "下家", 2: "对家", 3: "上家"}
        return {
            "success": True,
            "message": f"{player_names[player_id]}胜利标识设置成功",
            "game_state": current_state
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置玩家胜利失败: {str(e)}")


@router.post("/reveal-all-hands")
async def reveal_all_hands():
    """牌局结束后显示所有玩家手牌"""
    try:
        current_state = game_service.get_game_state()
        
        # 设置显示所有手牌的标志和游戏结束标志
        current_state["show_all_hands"] = True
        current_state["game_ended"] = True
        
        # 注释：真实手牌应该在调用此API前通过其他方式设置
        # 不再自动生成随机手牌，因为会在脚本中设置真实手牌
        
        # 更新游戏状态
        game_service.set_game_state_dict(current_state)
        
        return {
            "success": True,
            "message": "已显示所有玩家手牌",
            "game_state": current_state
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"显示所有手牌失败: {str(e)}")


# ============ HTTP API 连接 ============
# WebSocket 功能已移除，现在只使用 HTTP API