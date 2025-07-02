import { useState, useEffect } from 'react';
import { CardBackStyle } from '../components/MahjongTile';

interface Settings {
  cardBackStyle: CardBackStyle;
  enableAnimations: boolean;
  autoSave: boolean;
}

const defaultSettings: Settings = {
  cardBackStyle: 'elegant',
  enableAnimations: true,
  autoSave: true,
};

const SETTINGS_STORAGE_KEY = 'mahjong_settings';

export const useSettings = () => {
  const [settings, setSettings] = useState<Settings>(defaultSettings);

  // 初始化时从localStorage加载设置
  useEffect(() => {
    try {
      const savedSettings = localStorage.getItem(SETTINGS_STORAGE_KEY);
      if (savedSettings) {
        const parsed = JSON.parse(savedSettings);
        // 如果之前保存的是pure，自动替换为elegant
        if (parsed.cardBackStyle === 'pure') {
          parsed.cardBackStyle = 'elegant';
        }
        setSettings({ ...defaultSettings, ...parsed });
      }
    } catch (error) {
      console.warn('加载设置失败，使用默认设置:', error);
    }
  }, []);

  // 保存设置到localStorage
  const saveSettings = (newSettings: Partial<Settings>) => {
    try {
      const updatedSettings = { ...settings, ...newSettings };
      setSettings(updatedSettings);
      localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(updatedSettings));
    } catch (error) {
      console.error('保存设置失败:', error);
    }
  };

  // 单独的设置更新函数
  const updateCardBackStyle = (style: CardBackStyle) => {
    saveSettings({ cardBackStyle: style });
  };

  const updateAnimations = (enabled: boolean) => {
    saveSettings({ enableAnimations: enabled });
  };

  const updateAutoSave = (enabled: boolean) => {
    saveSettings({ autoSave: enabled });
  };

  // 重置设置
  const resetSettings = () => {
    setSettings(defaultSettings);
    localStorage.removeItem(SETTINGS_STORAGE_KEY);
  };

  return {
    settings,
    updateCardBackStyle,
    updateAnimations,
    updateAutoSave,
    resetSettings,
    saveSettings,
  };
}; 