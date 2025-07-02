# 剩余牌数计算问题诊断

## 🎯 问题描述

用户反馈：对家已经有了10张麻将牌（4张手牌+6张碰杠牌），但"选择麻将牌"显示区域的7万数量没有相应减少。

## 🔍 问题分析

### 期望行为
- 对家碰了7万（3张牌），7万的剩余数量应该从4减少到1
- 选择区域应该显示7万右上角数字为1

### 实际行为  
- 对家确实有碰杠牌（界面显示正确）
- 但选择区域的7万数量没有减少

## 🛠️ 诊断步骤

### 1. 检查浏览器控制台
按F12打开开发者工具，查看Console标签页的调试信息：

```
🔍 开始计算剩余牌数...
📦 初始牌数: {wan-7: 4, ...}
🏠 处理玩家2: {手牌数量: 4, 碰杠数量: 2}
🎴 处理玩家2的第0个碰杠: {类型: "peng", 牌内容: ["7wan", "7wan", "7wan"]}
👁️ 收集明牌: ["7wan", "7wan", "7wan"]
✅ 最终剩余牌数: {wan-7: 1, ...}
```

### 2. 可能的问题原因

#### A. 数据同步问题
- 前端状态没有完全同步后端数据
- 计算使用的是旧状态

#### B. 数据类型问题  
- API返回的枚举值类型不匹配
- key生成不一致

#### C. 计算时机问题
- 状态更新后计算没有触发
- React依赖数组问题

## 🔧 解决方案

### 方案1：强制重新同步
1. 点击"⬇️ 从后端同步"按钮
2. 检查控制台输出
3. 查看剩余牌数是否正确

### 方案2：检查数据结构
确认melds数据结构正确：
```javascript
// 期望的数据结构
{
  type: "peng",
  tiles: [
    {type: "wan", value: 7},
    {type: "wan", value: 7}, 
    {type: "wan", value: 7}
  ],
  exposed: true
}
```

### 方案3：手动验证计算
在控制台执行：
```javascript
// 获取当前状态
const state = useGameStore.getState().gameState;

// 手动计算7万的使用数量
let wanSevenUsed = 0;
Object.values(state.player_hands).forEach(hand => {
  hand.melds.forEach(meld => {
    meld.tiles.forEach(tile => {
      if (tile.type === "wan" && tile.value === 7) {
        wanSevenUsed++;
      }
    });
  });
});

console.log('7万已使用数量:', wanSevenUsed);
console.log('7万剩余数量:', 4 - wanSevenUsed);
```

## 🔍 调试工具

### 新增功能
1. **详细调试日志** - 在控制台查看完整计算过程
2. **刷新统计按钮** - 强制重新计算剩余牌数
3. **状态监控** - 实时显示游戏状态变化

### 使用调试信息
```javascript
// 查看具体某张牌的统计
console.log('🔍 查看7万统计:');
const gameState = useGameStore.getState().gameState;
const remainingCounts = calculateRemainingTilesByType(gameState);
console.log('7万剩余:', remainingCounts['wan-7']);
```

## ✅ 预期修复效果

修复后应该看到：
1. **控制台输出** - 正确显示7万被使用3次
2. **剩余统计** - wan-7: 1  
3. **界面显示** - 7万右上角显示数字1
4. **逻辑一致** - 总牌数 = 手牌 + 碰杠 + 弃牌 + 剩余 = 108

## 🐛 如果问题持续

如果问题仍然存在，请提供：
1. 浏览器控制台的完整输出
2. 网络请求的响应数据
3. 具体的操作步骤

这样我们可以进一步定位问题的根本原因。 