#!/usr/bin/env python3
"""
规则引擎决策模块

功能：
- 基于规则的专家系统
- 土壤湿度控制逻辑
- 环境参数控制逻辑
- 病害预警逻辑
"""

import logging
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """决策类型枚举"""
    IRRIGATION = "灌溉"
    LIGHTING = "补光"
    VENTILATION = "通风"
    FERTIGATION = "水肥一体化"
    ALERT = "预警"
    ADVICE = "建议"


class RulesEngine:
    """规则引擎类"""
    
    # 默认规则配置
    DEFAULT_RULES = {
        'soil_moisture': {
            'dry_threshold': 30,      # 低于此值需要灌溉
            'wet_threshold': 70,      # 高于此值停止灌溉
            'optimal_min': 40,        # 最佳范围下限
            'optimal_max': 60         # 最佳范围上限
        },
        'temperature': {
            'min': 15,                # 最低温度
            'max': 35,                # 最高温度
            'optimal_min': 20,        # 最佳范围下限
            'optimal_max': 30,        # 最佳范围上限
            'critical_low': 10,       # 低温警戒
            'critical_high': 40       # 高温警戒
        },
        'humidity': {
            'min': 40,                # 最低湿度
            'max': 80,                # 最高湿度
            'optimal_min': 50,        # 最佳范围下限
            'optimal_max': 70         # 最佳范围上限
        },
        'light': {
            'min': 2000,              # 最低光照 (lux)
            'max': 10000,             # 最高光照
            'optimal_min': 3000,      # 最佳范围下限
            'optimal_max': 8000       # 最佳范围上限
        },
        'co2': {
            'min': 400,               # 最低 CO2 浓度
            'max': 1500,              # 最高 CO2 浓度
            'optimal_min': 600,       # 最佳范围下限
            'optimal_max': 1200       # 最佳范围上限
        },
        'disease_threshold': {
            'health_score_low': 70,   # 健康评分低警戒
            'health_score_critical': 50  # 健康评分危急
        }
    }
    
    def __init__(self, rules_config: Optional[str] = None, custom_rules: Optional[Dict] = None):
        """
        初始化规则引擎
        
        Args:
            rules_config: 规则配置文件路径
            custom_rules: 自定义规则字典
        """
        self.rules = self.DEFAULT_RULES.copy()
        self.custom_rules = custom_rules or {}
        
        # 加载配置文件
        if rules_config and os.path.exists(rules_config):
            self._load_config(rules_config)
        
        logger.info("规则引擎初始化完成")
    
    def _load_config(self, config_path: str):
        """加载规则配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并配置
                for key, value in config.items():
                    if key in self.rules:
                        self.rules[key].update(value)
                    else:
                        self.rules[key] = value
            logger.info(f"规则配置已加载：{config_path}")
        except Exception as e:
            logger.error(f"加载规则配置失败：{e}")
    
    def evaluate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估传感器数据并返回决策
        
        Args:
            data: 传感器数据字典
            
        Returns:
            决策结果字典
        """
        decisions = {
            'irrigation': False,
            'light': False,
            'fan': False,
            'alerts': [],
            'advice': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. 评估土壤湿度
        soil_decision = self._evaluate_soil_moisture(data.get('soil', {}))
        decisions['irrigation'] = soil_decision.get('irrigation', False)
        decisions['alerts'].extend(soil_decision.get('alerts', []))
        
        # 2. 评估环境参数
        env_decision = self._evaluate_environment(data.get('environment', {}))
        decisions['light'] = env_decision.get('light', False)
        decisions['fan'] = env_decision.get('fan', False)
        decisions['alerts'].extend(env_decision.get('alerts', []))
        decisions['advice'].extend(env_decision.get('advice', []))
        
        # 3. 评估叶片健康
        health_decision = self._evaluate_leaf_health(data.get('vision', {}))
        decisions['alerts'].extend(health_decision.get('alerts', []))
        decisions['advice'].extend(health_decision.get('advice', []))
        
        # 4. 综合决策优化
        decisions = self._optimize_decisions(decisions, data)
        
        return decisions
    
    def _evaluate_soil_moisture(self, soil_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估土壤湿度"""
        result = {
            'irrigation': False,
            'alerts': [],
            'advice': []
        }
        
        if not soil_data:
            return result
        
        # 获取各点位湿度
        moistures = []
        for key, value in soil_data.items():
            if isinstance(value, dict):
                moistures.append(value.get('moisture', 50))
            elif isinstance(value, (int, float)):
                moistures.append(value)
        
        if not moistures:
            return result
        
        avg_moisture = sum(moistures) / len(moistures)
        min_moisture = min(moistures)
        
        # 获取阈值
        dry_threshold = self.rules['soil_moisture']['dry_threshold']
        wet_threshold = self.rules['soil_moisture']['wet_threshold']
        optimal_min = self.rules['soil_moisture']['optimal_min']
        optimal_max = self.rules['soil_moisture']['optimal_max']
        
        # 决策逻辑
        if min_moisture < dry_threshold:
            result['irrigation'] = True
            result['alerts'].append({
                'type': 'warning',
                'message': f'土壤湿度过低 ({min_moisture:.1f}%)，需要立即灌溉',
                'priority': 'high'
            })
        elif avg_moisture < optimal_min:
            result['irrigation'] = True
            result['advice'].append(f'土壤湿度偏低 ({avg_moisture:.1f}%)，建议适当灌溉')
        elif avg_moisture > optimal_max and avg_moisture < wet_threshold:
            result['advice'].append(f'土壤湿度适宜 ({avg_moisture:.1f}%)，保持当前状态')
        elif avg_moisture >= wet_threshold:
            result['irrigation'] = False
            result['alerts'].append({
                'type': 'info',
                'message': f'土壤湿度较高 ({avg_moisture:.1f}%)，暂停灌溉',
                'priority': 'low'
            })
        
        return result
    
    def _evaluate_environment(self, env_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估环境参数"""
        result = {
            'light': False,
            'fan': False,
            'alerts': [],
            'advice': []
        }
        
        if not env_data:
            return result
        
        temperature = env_data.get('temperature', 25)
        humidity = env_data.get('humidity', 60)
        light = env_data.get('light_intensity', 5000)
        co2 = env_data.get('co2', 800)
        
        # 温度决策
        temp_rules = self.rules['temperature']
        if temperature < temp_rules['min']:
            result['fan'] = False
            result['alerts'].append({
                'type': 'warning',
                'message': f'温度过低 ({temperature:.1f}°C)，建议关闭通风',
                'priority': 'medium'
            })
        elif temperature > temp_rules['max']:
            result['fan'] = True
            result['alerts'].append({
                'type': 'warning',
                'message': f'温度过高 ({temperature:.1f}°C)，建议开启通风',
                'priority': 'high'
            })
        
        # 光照决策
        light_rules = self.rules['light']
        if light < light_rules['min']:
            result['light'] = True
            result['advice'].append(f'光照不足 ({light:.0f} lux)，建议开启补光灯')
        elif light > light_rules['max']:
            result['light'] = False
            result['advice'].append('光照过强，建议开启遮阳网')
        
        # 湿度决策
        humidity_rules = self.rules['humidity']
        if humidity > humidity_rules['max']:
            result['fan'] = True
            result['alerts'].append({
                'type': 'info',
                'message': f'湿度过高 ({humidity:.1f}%)，建议加强通风防止病害',
                'priority': 'medium'
            })
        elif humidity < humidity_rules['min']:
            result['advice'].append(f'湿度过低 ({humidity:.1f}%)，考虑喷雾增湿')
        
        # CO2 决策
        co2_rules = self.rules['co2']
        if co2 > co2_rules['max']:
            result['fan'] = True
            result['advice'].append(f'CO2 浓度过高 ({co2:.0f} ppm)，建议加强通风')
        elif co2 < co2_rules['min']:
            result['advice'].append('CO2 浓度较低，可考虑 CO2 施肥')
        
        return result
    
    def _evaluate_leaf_health(self, vision_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估叶片健康"""
        result = {
            'alerts': [],
            'advice': []
        }
        
        if not vision_data:
            return result
        
        # 获取叶片健康数据
        leaf_health = vision_data.get('leaf_health', {})
        
        if not leaf_health:
            return result
        
        # 健康评分
        health_score = leaf_health.get('health_score', 100)
        disease_type = leaf_health.get('disease_type', '健康')
        
        # 获取阈值
        health_low = self.rules['disease_threshold']['health_score_low']
        health_critical = self.rules['disease_threshold']['health_score_critical']
        
        # 决策逻辑
        if health_score <= health_critical:
            result['alerts'].append({
                'type': 'critical',
                'message': f'作物健康状况危急 (评分：{health_score})，{disease_type}',
                'priority': 'critical'
            })
            result['advice'].append('建议立即采取防治措施')
        elif health_score <= health_low:
            result['alerts'].append({
                'type': 'warning',
                'message': f'作物健康状况不佳 (评分：{health_score})，{disease_type}',
                'priority': 'high'
            })
        
        # 获取具体建议
        recommendations = leaf_health.get('recommendations', [])
        result['advice'].extend(recommendations)
        
        return result
    
    def _optimize_decisions(
        self,
        decisions: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        优化决策，避免冲突
        
        例如：高温时不应同时开启补光和关闭通风
        """
        env_data = data.get('environment', {})
        temperature = env_data.get('temperature', 25)
        
        # 高温优化：温度高时，补光应谨慎
        if temperature > 30 and decisions['light']:
            decisions['advice'].append(
                '温度较高时补光需谨慎，避免加剧高温'
            )
        
        # 湿度优化：湿度高时，减少灌溉
        humidity = env_data.get('humidity', 60)
        if humidity > 75 and decisions['irrigation']:
            decisions['advice'].append(
                '湿度较高，建议减少灌溉量'
            )
        
        return decisions
    
    def get_rule_status(self) -> Dict[str, Any]:
        """获取当前规则状态"""
        return {
            'rules': self.rules,
            'custom_rules': self.custom_rules,
            'timestamp': datetime.now().isoformat()
        }
    
    def update_rule(self, category: str, key: str, value: Any):
        """
        更新规则
        
        Args:
            category: 规则类别
            key: 规则键
            value: 规则值
        """
        if category not in self.rules:
            self.rules[category] = {}
        self.rules[category][key] = value
        logger.info(f"规则已更新：{category}.{key} = {value}")
    
    def save_config(self, config_path: str):
        """保存规则配置到文件"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, indent=2, ensure_ascii=False)
            logger.info(f"规则配置已保存：{config_path}")
        except Exception as e:
            logger.error(f"保存规则配置失败：{e}")