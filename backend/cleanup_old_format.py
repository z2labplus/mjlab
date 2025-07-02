#!/usr/bin/env python3
"""
清理旧格式文件的脚本
现在系统已经完全支持新的标准格式，可以安全地清理旧文件
"""

import os
from pathlib import Path

def cleanup_old_format_files():
    """清理旧格式文件"""
    
    print("🧹 清理旧格式文件")
    print("=" * 50)
    
    # 要清理的旧文件列表
    old_files = [
        "sample_replay_sample_game_8e683015.json.backup",  # 备份的旧文件
        "convert_standard_replay.py",  # 转换脚本（现在不需要了）
        "converted_replay_standard_converted_game.json",  # 转换生成的文件
    ]
    
    cleaned_count = 0
    
    for file_path in old_files:
        if Path(file_path).exists():
            try:
                os.remove(file_path)
                print(f"✅ 已删除: {file_path}")
                cleaned_count += 1
            except Exception as e:
                print(f"❌ 删除失败: {file_path} - {e}")
        else:
            print(f"⏭️ 文件不存在: {file_path}")
    
    # 检查其他可能的旧文件
    temp_files = [
        "sample_replay_sample_game_*.json",  # 动态生成的样例文件
    ]
    
    print(f"\n📊 清理完成:")
    print(f"   删除文件数: {cleaned_count}")
    print(f"   系统现在完全使用新的标准格式")
    
    # 确认新格式文件存在
    new_format_file = "/root/claude/hmjai/model/first_hand/sample_mahjong_game_final.json"
    if Path(new_format_file).exists():
        print(f"✅ 新格式文件正常: {new_format_file}")
    else:
        print(f"⚠️ 新格式文件缺失: {new_format_file}")
    
    return cleaned_count

if __name__ == "__main__":
    cleanup_old_format_files()