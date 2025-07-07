#!/usr/bin/env python3
"""
综合对比测试：三种算法版本的全面比较
1. 天凤网站Playwright版 (真实天凤结果)
2. 本地模拟天凤版 (我们的天凤模拟算法)
3. 穷举版 (纯数学计算)
"""

import json
import time
from typing import List, Dict, Any

def read_test_hands(filename: str) -> List[str]:
    """读取测试手牌文件"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            hands = [line.strip() for line in f.readlines() if line.strip()]
        return hands
    except FileNotFoundError:
        print(f"错误：找不到测试文件 {filename}")
        return []

def get_tenhou_results(hands: List[str]) -> Dict[str, Any]:
    """获取天凤网站结果"""
    print("🌐 正在获取天凤网站结果...")
    
    try:
        from tenhou_playwright_plus import get_tenhou_analysis_sync
        results = {}
        
        for i, hand in enumerate(hands, 1):
            print(f"  处理手牌 {i}/{len(hands)}: {hand}")
            try:
                result = get_tenhou_analysis_sync(hand)
                results[hand] = result
                time.sleep(1)  # 避免请求过快
            except Exception as e:
                print(f"    ❌ 获取失败: {e}")
                results[hand] = f"错误: {e}"
        
        return results
    except ImportError:
        print("❌ 无法导入天凤Playwright模块")
        return {}

def get_local_tenhou_results(hands: List[str]) -> Dict[str, Any]:
    """获取本地模拟天凤结果"""
    print("🏠 正在计算本地模拟天凤结果...")
    
    try:
        from mahjong_analyzer_final import simple_analyze
        results = {}
        
        for i, hand in enumerate(hands, 1):
            print(f"  处理手牌 {i}/{len(hands)}: {hand}")
            try:
                result = simple_analyze(hand)
                results[hand] = result
            except Exception as e:
                print(f"    ❌ 计算失败: {e}")
                results[hand] = f"错误: {e}"
        
        return results
    except ImportError:
        print("❌ 无法导入本地天凤模拟模块")
        return {}

def get_exhaustive_results(hands: List[str]) -> Dict[str, Any]:
    """获取穷举算法结果"""
    print("🔢 正在计算穷举算法结果...")
    
    try:
        from mahjong_analyzer_exhaustive_fixed import simple_analyze_exhaustive_fixed
        results = {}
        
        for i, hand in enumerate(hands, 1):
            print(f"  处理手牌 {i}/{len(hands)}: {hand}")
            try:
                result = simple_analyze_exhaustive_fixed(hand)
                results[hand] = result
            except Exception as e:
                print(f"    ❌ 计算失败: {e}")
                results[hand] = f"错误: {e}"
        
        return results
    except ImportError:
        print("❌ 无法导入穷举算法模块")
        return {}

def compare_results(hand: str, tenhou_result: Any, local_result: Any, exhaustive_result: Any):
    """对比单个手牌的三种结果"""
    print(f"\n【手牌分析】{hand}")
    print("=" * 80)
    
    # 检查结果有效性
    valid_results = {}
    
    if isinstance(tenhou_result, list) and tenhou_result:
        valid_results['天凤网站'] = tenhou_result[:4]
    else:
        print(f"❌ 天凤网站结果无效: {tenhou_result}")
    
    if isinstance(local_result, list) and local_result:
        valid_results['本地模拟'] = local_result[:4]
    else:
        print(f"❌ 本地模拟结果无效: {local_result}")
    
    if isinstance(exhaustive_result, list) and exhaustive_result:
        valid_results['穷举算法'] = exhaustive_result[:4]
    else:
        print(f"❌ 穷举算法结果无效: {exhaustive_result}")
    
    if not valid_results:
        print("⚠️ 所有算法都没有有效结果")
        return
    
    # 显示每种算法的前4个选择
    max_choices = 4
    for algorithm_name, result in valid_results.items():
        print(f"\n【{algorithm_name}】")
        for i, choice in enumerate(result[:max_choices], 1):
            tiles_str = ', '.join(choice['tiles'][:6])
            if len(choice['tiles']) > 6:
                tiles_str += f"... (共{len(choice['tiles'])}种)"
            print(f"  {i}. 打{choice['tile']} - 有效牌数: {choice['number']}枚")
            print(f"     有效牌: [{tiles_str}]")
    
    # 算法间对比分析
    if len(valid_results) >= 2:
        print(f"\n【算法对比分析】")
        
        algorithms = list(valid_results.keys())
        
        # 对比打牌选择
        print("打牌选择对比:")
        for i in range(max_choices):
            choices = []
            for alg in algorithms:
                if i < len(valid_results[alg]):
                    choices.append(f"{alg}={valid_results[alg][i]['tile']}")
                else:
                    choices.append(f"{alg}=N/A")
            print(f"  第{i+1}选择: {' | '.join(choices)}")
        
        # 对比有效牌数量
        print("\n有效牌数量对比:")
        for i in range(max_choices):
            numbers = []
            for alg in algorithms:
                if i < len(valid_results[alg]):
                    numbers.append(f"{alg}={valid_results[alg][i]['number']}")
                else:
                    numbers.append(f"{alg}=N/A")
            print(f"  第{i+1}选择: {' | '.join(numbers)}")
        
        # 计算匹配度
        if '天凤网站' in valid_results:
            tenhou_choices = valid_results['天凤网站']
            
            for alg_name, alg_result in valid_results.items():
                if alg_name == '天凤网站':
                    continue
                
                matches = 0
                for i in range(min(len(tenhou_choices), len(alg_result))):
                    if tenhou_choices[i]['tile'] == alg_result[i]['tile']:
                        matches += 1
                
                match_rate = matches / min(len(tenhou_choices), 4) * 100
                print(f"\n{alg_name} vs 天凤网站打牌匹配度: {matches}/4 = {match_rate:.1f}%")

def save_detailed_results(hands: List[str], tenhou_results: Dict, local_results: Dict, exhaustive_results: Dict):
    """保存详细结果到文件"""
    detailed_data = {
        'test_hands': hands,
        'results': {
            'tenhou_website': tenhou_results,
            'local_simulation': local_results,
            'exhaustive_algorithm': exhaustive_results
        },
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    filename = 'comprehensive_test_results.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(detailed_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 详细结果已保存到: {filename}")

def generate_summary_report(hands: List[str], tenhou_results: Dict, local_results: Dict, exhaustive_results: Dict):
    """生成总结报告"""
    print("\n" + "=" * 80)
    print("📊 综合测试总结报告")
    print("=" * 80)
    
    # 统计成功率
    success_stats = {
        '天凤网站': sum(1 for r in tenhou_results.values() if isinstance(r, list)),
        '本地模拟': sum(1 for r in local_results.values() if isinstance(r, list)),
        '穷举算法': sum(1 for r in exhaustive_results.values() if isinstance(r, list))
    }
    
    print("🎯 算法成功率:")
    for alg, success_count in success_stats.items():
        rate = success_count / len(hands) * 100
        print(f"  {alg}: {success_count}/{len(hands)} = {rate:.1f}%")
    
    # 计算总体匹配度
    if success_stats['天凤网站'] > 0:
        print("\n🔍 与天凤网站的总体匹配度:")
        
        for alg_name, alg_results in [('本地模拟', local_results), ('穷举算法', exhaustive_results)]:
            total_matches = 0
            total_comparisons = 0
            
            for hand in hands:
                if (isinstance(tenhou_results.get(hand), list) and 
                    isinstance(alg_results.get(hand), list)):
                    
                    tenhou_choices = tenhou_results[hand][:4]
                    alg_choices = alg_results[hand][:4]
                    
                    for i in range(min(len(tenhou_choices), len(alg_choices))):
                        if tenhou_choices[i]['tile'] == alg_choices[i]['tile']:
                            total_matches += 1
                        total_comparisons += 1
            
            if total_comparisons > 0:
                match_rate = total_matches / total_comparisons * 100
                print(f"  {alg_name}: {total_matches}/{total_comparisons} = {match_rate:.1f}%")
    
    # 算法特点总结
    print("\n📋 算法特点总结:")
    print("  🌐 天凤网站: 真实权威结果，实战导向，考虑牌效价值")
    print("  🏠 本地模拟: 模拟天凤逻辑，包含启发式规则和稳定性筛选")
    print("  🔢 穷举算法: 纯数学计算，找出所有理论有效进张，逻辑透明")

def main():
    """主函数"""
    print("🎮 麻将算法综合对比测试")
    print("=" * 80)
    
    # 读取测试手牌
    test_file = 'test.txt'
    hands = read_test_hands(test_file)
    
    if not hands:
        print("❌ 没有找到有效的测试手牌")
        return
    
    print(f"📋 共找到 {len(hands)} 个测试手牌:")
    for i, hand in enumerate(hands, 1):
        print(f"  {i}. {hand}")
    
    print("\n🚀 开始算法对比测试...\n")
    
    # 获取三种算法的结果
    tenhou_results = get_tenhou_results(hands)
    local_results = get_local_tenhou_results(hands)
    exhaustive_results = get_exhaustive_results(hands)
    
    print("\n" + "=" * 80)
    print("📈 逐手牌详细对比分析")
    print("=" * 80)
    
    # 逐个对比每个手牌
    for hand in hands:
        compare_results(
            hand,
            tenhou_results.get(hand),
            local_results.get(hand),
            exhaustive_results.get(hand)
        )
    
    # 保存详细结果
    save_detailed_results(hands, tenhou_results, local_results, exhaustive_results)
    
    # 生成总结报告
    generate_summary_report(hands, tenhou_results, local_results, exhaustive_results)
    
    print(f"\n✅ 综合对比测试完成！")

if __name__ == "__main__":
    main()