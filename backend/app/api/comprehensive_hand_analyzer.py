"""
综合手牌分析API - 支持三种分析方法
1. 天凤网站结果 (Tenhou Website)
2. 本地模拟天凤结果 (Local Tenhou Simulation)  
3. 穷举算法结果 (Exhaustive Algorithm)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Literal
import sys
from pathlib import Path
import time

# 添加backend目录到Python路径
current_file = Path(__file__).resolve()
backend_dir = current_file.parent.parent.parent  # backend/
sys.path.insert(0, str(backend_dir))

router = APIRouter()

AnalysisMethod = Literal["tenhou_website", "local_simulation", "exhaustive"]

class ComprehensiveAnalysisRequest(BaseModel):
    """综合分析请求"""
    hand: str  # 手牌字符串，例如: "111222333m456p77s"
    methods: List[AnalysisMethod] = ["local_simulation"]  # 要使用的分析方法
    tile_format: Literal["mps", "frontend"] = "mps"  # 输入格式

class SingleAnalysisResult(BaseModel):
    """单个分析方法的结果"""
    method: AnalysisMethod
    method_name: str
    success: bool
    error_message: Optional[str] = None
    choices: List[Dict[str, Any]] = []  # 打牌选择
    analysis_time: float = 0.0
    timestamp: str

class ComprehensiveAnalysisResponse(BaseModel):
    """综合分析响应"""
    hand: str
    hand_display: str
    results: List[SingleAnalysisResult]
    comparison: Optional[Dict[str, Any]] = None

def convert_frontend_to_mps(hand_frontend: str) -> str:
    """
    转换前端格式到mps格式
    前端: "1wan2wan3wan" -> mps: "123m"
    统一命名规范：p代表筒，s代表条，m代表万
    """
    conversion_map = {
        'wan': 'm',   # 万 -> m
        'tiao': 's',  # 条 -> s  
        'tong': 'p'   # 筒 -> p
    }
    
    result = ""
    current_numbers = ""
    current_suit = None
    
    # 解析前端格式
    i = 0
    while i < len(hand_frontend):
        if hand_frontend[i].isdigit():
            current_numbers += hand_frontend[i]
            i += 1
        else:
            # 查找花色
            for frontend_suit, mps_suit in conversion_map.items():
                if hand_frontend[i:].startswith(frontend_suit):
                    if current_suit != mps_suit:
                        if current_suit and current_numbers:
                            result += current_numbers + current_suit
                        current_numbers = ""
                        current_suit = mps_suit
                    i += len(frontend_suit)
                    break
            else:
                i += 1
    
    # 添加最后一组
    if current_suit and current_numbers:
        result += current_numbers + current_suit
    
    return result

def convert_mps_to_display(hand_mps: str) -> str:
    """
    转换mps格式到显示格式
    mps: "123m456s789p" -> display: "123万456条789筒"
    """
    conversion_map = {
        'm': '万',
        's': '条',  
        'p': '筒'
    }
    
    result = ""
    current_numbers = ""
    
    for char in hand_mps:
        if char.isdigit():
            current_numbers += char
        elif char in conversion_map:
            result += current_numbers + conversion_map[char]
            current_numbers = ""
    
    return result

@router.post("/comprehensive-analyze", response_model=ComprehensiveAnalysisResponse)
async def comprehensive_analyze(request: ComprehensiveAnalysisRequest):
    """
    综合手牌分析，支持多种分析方法
    """
    try:
        # 转换输入格式
        if request.tile_format == "frontend":
            hand_mps = convert_frontend_to_mps(request.hand)
        else:
            hand_mps = request.hand
        
        hand_display = convert_mps_to_display(hand_mps)
        
        results = []
        method_names = {
            "tenhou_website": "天凤网站",
            "local_simulation": "本地模拟天凤",
            "exhaustive": "穷举算法"
        }
        
        for method in request.methods:
            start_time = time.time()
            timestamp = time.strftime('%H:%M:%S')
            
            try:
                if method == "tenhou_website":
                    result = await _analyze_with_tenhou_website(hand_mps)
                elif method == "local_simulation":
                    result = await _analyze_with_local_simulation(hand_mps)
                elif method == "exhaustive":
                    result = await _analyze_with_exhaustive(hand_mps)
                else:
                    raise ValueError(f"Unknown analysis method: {method}")
                
                analysis_time = time.time() - start_time
                
                results.append(SingleAnalysisResult(
                    method=method,
                    method_name=method_names[method],
                    success=True,
                    choices=result,
                    analysis_time=analysis_time,
                    timestamp=timestamp
                ))
                
            except Exception as e:
                analysis_time = time.time() - start_time
                results.append(SingleAnalysisResult(
                    method=method,
                    method_name=method_names[method],
                    success=False,
                    error_message=str(e),
                    analysis_time=analysis_time,
                    timestamp=timestamp
                ))
        
        # 生成对比分析
        comparison = _generate_comparison(results) if len(results) > 1 else None
        
        return ComprehensiveAnalysisResponse(
            hand=hand_mps,
            hand_display=hand_display,
            results=results,
            comparison=comparison
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

async def _analyze_with_tenhou_website(hand_mps: str) -> List[Dict[str, Any]]:
    """使用天凤网站分析"""
    try:
        import asyncio
        import platform
        from concurrent.futures import ThreadPoolExecutor
        from tenhou_playwright_plus import get_tenhou_analysis_sync
        
        # 在线程池中运行，避免事件循环问题，并设置超时
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            # 设置30秒超时
            result = await asyncio.wait_for(
                loop.run_in_executor(executor, get_tenhou_analysis_sync, hand_mps),
                timeout=30.0
            )
        
        if isinstance(result, list) and len(result) > 0:
            # 过滤掉无效结果
            valid_results = [r for r in result if r.get('number', 0) > 0]
            if valid_results:
                return valid_results[:6]  # 返回前6个有效选择
            else:
                # 如果没有有效结果，使用原始结果
                return result[:6]
        else:
            raise Exception("天凤网站返回空结果")
            
    except ImportError:
        raise Exception("天凤Playwright模块不可用")
    except asyncio.TimeoutError:
        raise Exception("天凤网站分析超时（30秒）")
    except Exception as e:
        # 记录详细错误信息
        error_msg = f"天凤网站分析失败: {str(e)}"
        print(f"天凤分析错误详情: {error_msg}")
        raise Exception(error_msg)

async def _analyze_with_local_simulation(hand_mps: str) -> List[Dict[str, Any]]:
    """使用本地模拟天凤分析"""
    try:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        from mahjong_analyzer_final import simple_analyze
        
        # 在线程池中运行同步函数，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, simple_analyze, hand_mps)
        
        if isinstance(result, list):
            return result[:6]  # 返回前6个选择
        else:
            raise Exception(f"本地模拟分析失败: {result}")
    except ImportError:
        raise Exception("本地模拟模块不可用")

async def _analyze_with_exhaustive(hand_mps: str) -> List[Dict[str, Any]]:
    """使用穷举算法分析"""
    try:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        from mahjong_analyzer_exhaustive_fixed import simple_analyze_exhaustive_fixed
        
        # 在线程池中运行同步函数，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, simple_analyze_exhaustive_fixed, hand_mps)
        
        if isinstance(result, list):
            return result[:6]  # 返回前6个选择
        else:
            raise Exception(f"穷举算法分析失败: {result}")
    except ImportError:
        raise Exception("穷举算法模块不可用")

def _generate_comparison(results: List[SingleAnalysisResult]) -> Dict[str, Any]:
    """生成分析结果对比"""
    comparison = {
        "success_rate": {},
        "performance": {},
        "choice_consistency": {},
        "summary": {}
    }
    
    # 成功率统计
    for result in results:
        comparison["success_rate"][result.method_name] = result.success
        comparison["performance"][result.method_name] = f"{result.analysis_time:.3f}s"
    
    # 选择一致性分析
    successful_results = [r for r in results if r.success and r.choices]
    
    if len(successful_results) >= 2:
        # 对比前4个选择的一致性
        first_choices = []
        for result in successful_results:
            if result.choices:
                first_choices.append([
                    choice.get('tile', '') for choice in result.choices[:4]
                ])
        
        if len(first_choices) >= 2:
            matches = 0
            total_comparisons = min(4, min(len(choices) for choices in first_choices))
            
            for i in range(total_comparisons):
                if len(set(choices[i] for choices in first_choices)) == 1:
                    matches += 1
            
            comparison["choice_consistency"]["match_rate"] = f"{matches}/{total_comparisons}"
            comparison["choice_consistency"]["percentage"] = f"{matches/total_comparisons*100:.1f}%" if total_comparisons > 0 else "0%"
    
    # 生成总结
    successful_count = sum(1 for r in results if r.success)
    comparison["summary"]["total_methods"] = len(results)
    comparison["summary"]["successful_methods"] = successful_count
    
    if successful_count > 0:
        comparison["summary"]["fastest_method"] = min(
            (r.method_name for r in results if r.success), 
            key=lambda m: next(r.analysis_time for r in results if r.method_name == m),
            default=None
        )
    
    return comparison

@router.post("/convert-hand-format")
async def convert_hand_format(
    hand: str, 
    from_format: Literal["mps", "frontend"], 
    to_format: Literal["mps", "frontend", "display"]
):
    """
    转换手牌格式
    """
    try:
        if from_format == "frontend" and to_format == "mps":
            result = convert_frontend_to_mps(hand)
        elif from_format == "mps" and to_format == "display":
            result = convert_mps_to_display(hand)
        elif from_format == "frontend" and to_format == "display":
            mps_format = convert_frontend_to_mps(hand)
            result = convert_mps_to_display(mps_format)
        else:
            result = hand  # 无需转换
        
        return {
            "original": hand,
            "converted": result,
            "from_format": from_format,
            "to_format": to_format
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Format conversion failed: {str(e)}")