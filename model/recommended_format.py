#!/usr/bin/env python3
"""
推荐的牌谱格式设计
"""

import json

def create_recommended_format():
    """创建推荐的牌谱格式"""
    
    # 读取当前数据
    with open('game_data_template_gang_fixed.json', 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    print("🎯 推荐的牌谱格式设计")
    print("=" * 60)
    
    recommended_format = {
        "game_info": {
            "game_id": "sample_game_008",
            "description": "血战到底麻将牌谱",
            "format_version": "1.0",
            "data_source": "实际游戏记录"
        },
        
        "game_settings": {
            "mjtype": "xuezhan_daodi",
            "misssuit": {"0": "条", "1": "万", "2": "万", "3": "筒"},
            "dong": "0"
        },
        
        # 核心设计：分层的初始手牌数据
        "initial_hands": {
            # 完全确定的数据
            "confirmed": {
                "0": {
                    "tiles": ["1万","1万","2万","3万","5万","6万","8万","9万","9万","3筒","6筒","7筒","8筒"],
                    "source": "known",
                    "confidence": 1.0,
                    "note": "玩家自己的手牌，完全确定"
                }
            },
            
            # 推导/估算的数据
            "estimated": {
                "1": {
                    "method": "deduction_based",
                    "possible_tiles": ["1条","1筒","2万","3万","4万","5万","6万","7筒","8万","8筒","9万","9筒"],
                    "confidence": 0.3,
                    "note": "基于弃牌和最终手牌推导，存在多种可能性",
                    "alternatives": [
                        {"scenario": "A", "tiles": ["方案A的13张牌"]},
                        {"scenario": "B", "tiles": ["方案B的13张牌"]},
                        {"scenario": "C", "tiles": ["方案C的13张牌"]}
                    ]
                },
                "2": {
                    "method": "deduction_based", 
                    "possible_tiles": ["推导出的可能牌"],
                    "confidence": 0.3,
                    "note": "推导结果，不确定"
                },
                "3": {
                    "method": "deduction_based",
                    "possible_tiles": ["推导出的可能牌"], 
                    "confidence": 0.3,
                    "note": "推导结果，不确定"
                }
            }
        },
        
        # 游戏过程数据
        "actions": game_data['actions'],
        "final_hand": game_data['final_hand'],
        
        # 元数据说明
        "metadata": {
            "data_reliability": {
                "player_0": "100% - 完全确定",
                "player_1": "30% - 推导估算",
                "player_2": "30% - 推导估算", 
                "player_3": "30% - 推导估算"
            },
            "usage_guidance": {
                "for_replay": "使用confirmed数据",
                "for_analysis": "可以使用estimated数据，但需注意不确定性",
                "for_ai_training": "建议只使用confirmed数据"
            },
            "limitations": [
                "其他玩家的初始手牌为推导结果",
                "推导基于观察到的操作",
                "实际初始手牌可能与推导不同"
            ]
        }
    }
    
    # 保存推荐格式
    with open('recommended_replay_format.json', 'w', encoding='utf-8') as f:
        json.dump(recommended_format, f, ensure_ascii=False, indent=2)
    
    print("✅ 推荐格式已创建: recommended_replay_format.json")
    
    # 同时创建简化版本（只包含确定数据）
    simple_format = {
        "game_info": recommended_format["game_info"],
        "game_settings": recommended_format["game_settings"],
        
        # 只包含确定的数据
        "initial_hands": {
            "0": recommended_format["initial_hands"]["confirmed"]["0"]["tiles"]
            # 其他玩家不包含
        },
        
        "actions": game_data['actions'],
        "final_hand": game_data['final_hand'],
        
        "note": "此版本只包含完全确定的数据，符合现实情况"
    }
    
    with open('simple_replay_format.json', 'w', encoding='utf-8') as f:
        json.dump(simple_format, f, ensure_ascii=False, indent=2)
    
    print("✅ 简化格式已创建: simple_replay_format.json")
    
    return recommended_format, simple_format

def compare_formats():
    """比较不同格式的优缺点"""
    
    print(f"\n📊 格式对比分析")
    print("=" * 60)
    
    formats = {
        "完整格式": {
            "特点": "包含所有玩家的初始手牌（推导+确定）",
            "适用场景": ["AI训练（标注数据质量）", "完整性分析", "算法研究"],
            "优点": ["数据完整", "结构统一", "支持各种分析"],
            "缺点": ["包含不确定信息", "可能误导"]
        },
        
        "简化格式": {
            "特点": "只包含确定的初始手牌数据",
            "适用场景": ["真实牌谱回放", "确定性分析", "现实场景模拟"],
            "优点": ["数据真实", "无误导性", "符合现实"],
            "缺点": ["数据不完整", "限制某些分析"]
        },
        
        "分层格式": {
            "特点": "区分确定数据和推导数据",
            "适用场景": ["研究项目", "多场景应用", "数据质量要求高"],
            "优点": ["兼顾完整性和真实性", "灵活使用", "明确标注"],
            "缺点": ["结构复杂", "文件较大"]
        }
    }
    
    for format_name, info in formats.items():
        print(f"\n🎯 {format_name}:")
        print(f"  特点: {info['特点']}")
        print(f"  适用: {', '.join(info['适用场景'])}")
        print(f"  优点: {', '.join(info['优点'])}")
        print(f"  缺点: {', '.join(info['缺点'])}")

def give_recommendation():
    """给出具体建议"""
    
    print(f"\n💡 具体建议")
    print("=" * 60)
    
    print("根据不同用途，建议使用不同格式：")
    
    print(f"\n1️⃣ **日常牌谱回放** → 使用简化格式")
    print("   - 只包含自己的初始手牌")
    print("   - 其他玩家从actions开始")
    print("   - 真实、可靠、无误导")
    
    print(f"\n2️⃣ **AI训练/研究** → 使用分层格式") 
    print("   - 明确区分确定数据和推导数据")
    print("   - 可以选择性使用不同置信度的数据")
    print("   - 支持数据质量控制")
    
    print(f"\n3️⃣ **算法测试** → 使用完整格式")
    print("   - 包含所有推导结果")
    print("   - 便于算法验证和对比")
    print("   - 需要明确标注数据来源")
    
    print(f"\n🎯 **我的推荐**：")
    print("对于您的项目，建议使用 **分层格式**，因为：")
    print("- ✅ 既保持了数据的真实性")
    print("- ✅ 又提供了完整的分析能力") 
    print("- ✅ 用户可以根据需要选择使用哪部分数据")
    print("- ✅ 明确标注了数据的可靠程度")

if __name__ == "__main__":
    recommended, simple = create_recommended_format()
    compare_formats()
    give_recommendation()