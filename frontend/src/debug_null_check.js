// 调试脚本：检查牌谱数据中是否有 null 值
// 在浏览器控制台中运行此脚本

function debugNullValues(replayData) {
  console.log("🔍 调试牌谱数据中的 null 值");
  
  if (!replayData || !replayData.actions) {
    console.error("❌ 牌谱数据无效");
    return;
  }
  
  console.log(`📊 总动作数: ${replayData.actions.length}`);
  
  // 检查所有动作的 target_player 字段
  let nullTargetCount = 0;
  let pengActions = [];
  let gangActions = [];
  
  replayData.actions.forEach((action, index) => {
    if (action.type === 'peng') {
      pengActions.push({
        sequence: action.sequence,
        player_id: action.player_id,
        target_player: action.target_player,
        tile: action.tile,
        index: index
      });
      
      if (action.target_player === null || action.target_player === undefined) {
        nullTargetCount++;
        console.warn(`⚠️ 碰牌动作缺少 target_player: 序号${action.sequence}`);
      }
    }
    
    if (action.type === 'gang') {
      gangActions.push({
        sequence: action.sequence,
        player_id: action.player_id,
        target_player: action.target_player,
        gang_type: action.gang_type,
        tile: action.tile,
        index: index
      });
      
      if (action.gang_type === 'ming_gang' && (action.target_player === null || action.target_player === undefined)) {
        nullTargetCount++;
        console.warn(`⚠️ 明杠动作缺少 target_player: 序号${action.sequence}`);
      }
    }
  });
  
  console.log(`\n📋 碰牌动作 (${pengActions.length}个):`);
  pengActions.forEach(action => {
    console.log(`  序号${action.sequence}: 玩家${action.player_id} 碰 玩家${action.target_player} 的 ${action.tile}`);
  });
  
  console.log(`\n📋 杠牌动作 (${gangActions.length}个):`);
  gangActions.forEach(action => {
    console.log(`  序号${action.sequence}: 玩家${action.player_id} ${action.gang_type} ${action.tile} (target: ${action.target_player})`);
  });
  
  if (nullTargetCount === 0) {
    console.log("✅ 所有碰杠动作的 target_player 字段都有效");
  } else {
    console.error(`❌ 发现 ${nullTargetCount} 个 null target_player`);
  }
  
  return {
    pengActions,
    gangActions,
    nullTargetCount
  };
}

// 使用方法：
// 1. 在前端导入牌谱文件
// 2. 在浏览器控制台运行：debugNullValues(replayData)
console.log("🛠️ 调试工具已准备好，使用 debugNullValues(replayData) 检查数据");