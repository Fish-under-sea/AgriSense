#!/usr/bin/env python3
"""
AgriSense - AI 智能大棚农产品监测系统
主入口文件

功能：
- 初始化所有传感器和模块
- 主循环：数据采集 -> 分析 -> 决策 -> 控制
- 数据持久化
- Web 服务启动
"""

import logging
import threading
import time
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

# 添加当前目录到路径
sys_path = os.path.dirname(os.path.abspath(__file__))
if sys_path not in __import__('sys').path:
    __import__('sys').path.insert(0, sys_path)

from sensors.soil_moisture import SoilMoistureSensor
from sensors.environment import EnvironmentSensor
from sensors.camera import CameraSensor
from vision.leaf_disease import LeafDiseaseAnalyzer
from vision.growth_measure import GrowthAnalyzer
from decision.rules_engine import RulesEngine
from decision.llm_advisor import LLMAdvisor
from control.actuator import ActuatorController

# 确保日志目录存在
os.makedirs('logs', exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agrisense.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AgriSenseSystem:
    """AgriSense 主系统类"""
    
    def __init__(self, use_simulation: bool = True):
        """
        初始化系统
        
        Args:
            use_simulation: 是否使用模拟模式（True=模拟，False=真实硬件）
        """
        self.use_simulation = use_simulation
        self.running = False
        self.data_history: list = []
        
        mode = "模拟模式" if use_simulation else "硬件模式"
        logger.info(f"初始化 AgriSense 系统 ({mode})...")
        
        # 初始化传感器
        logger.info("初始化传感器模块...")
        self.soil_sensor = SoilMoistureSensor(use_simulation=use_simulation)
        self.env_sensor = EnvironmentSensor(use_simulation=use_simulation)
        self.camera = CameraSensor(use_simulation=use_simulation)
        
        # 初始化视觉分析模块
        logger.info("初始化视觉分析模块...")
        self.leaf_analyzer = LeafDiseaseAnalyzer(use_simulation=use_simulation)
        self.growth_analyzer = GrowthAnalyzer(use_simulation=use_simulation)
        
        # 初始化决策模块
        logger.info("初始化决策模块...")
        self.rules_engine = RulesEngine()
        
        # 加载 LLM 配置
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            llm_config = config.get('decision', {}).get('llm_advisor', {})
            model_name = llm_config.get('model', 'qwen3.5')
            base_url = llm_config.get('base_url', 'http://localhost:11434')
            api_key = llm_config.get('api_key', '')
        except Exception as e:
            logger.warning(f"无法加载 LLM 配置：{e}，使用默认配置")
            model_name = 'qwen3.5'
            base_url = 'http://localhost:11434'
            api_key = ''
        
        self.llm_advisor = LLMAdvisor(
            model_name=model_name,
            base_url=base_url,
            api_key=api_key,
            use_simulation=use_simulation
        )
        logger.info(f"LLM 顾问已初始化 (模型：{model_name}, 地址：{base_url})")
        
        # 初始化执行器
        logger.info("初始化执行器模块...")
        self.actuator = ActuatorController(use_simulation=use_simulation)
        
        logger.info("系统初始化完成!")
    
    def collect_data(self) -> Dict[str, Any]:
        """
        收集所有传感器数据
        
        Returns:
            包含所有传感器数据的字典
        """
        data = {
            'timestamp': datetime.now().isoformat(),
            'soil': {},
            'environment': {},
            'vision': {}
        }
        
        # 采集土壤湿度数据（3 个点位）
        for i in range(3):
            data['soil'][f'point_{i}'] = self.soil_sensor.read_moisture(i)
        
        # 采集环境数据
        env_data = self.env_sensor.read_all()
        data['environment'] = {
            'temperature': env_data.get('temperature', 0),
            'humidity': env_data.get('humidity', 0),
            'light_intensity': env_data.get('light', 0),
            'co2': env_data.get('co2', 0),
            'par': env_data.get('light', 0) * 0.45  # 估算光合有效辐射
        }
        
        # 视觉分析
        try:
            image = self.camera.capture()
            if image is not None:
                # 叶片病害分析
                leaf_result = self.leaf_analyzer.analyze(image)
                data['vision']['leaf_health'] = leaf_result
                
                # 生长状态分析
                growth_result = self.growth_analyzer.analyze(image)
                data['vision']['growth'] = growth_result
        except Exception as e:
            logger.error(f"视觉分析失败：{e}")
            data['vision'] = {'error': str(e)}
        
        return data
    
    def make_decision(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于采集的数据做出决策
        
        Args:
            data: 传感器数据
            
        Returns:
            决策结果字典
        """
        # 规则引擎决策
        rule_decision = self.rules_engine.evaluate(data)
        
        # LLM 建议
        llm_advice = self.llm_advisor.get_advice(data)
        
        return {
            'rule_based': rule_decision,
            'llm_advice': llm_advice,
            'timestamp': datetime.now().isoformat()
        }
    
    def execute_actions(self, decision: Dict[str, Any]):
        """
        执行决策动作
        
        Args:
            decision: 决策结果
        """
        actions = decision.get('rule_based', {})
        
        # 控制灌溉
        if 'irrigation' in actions:
            self.actuator.set_irrigation(actions['irrigation'])
            logger.info(f"灌溉状态：{'开启' if actions['irrigation'] else '关闭'}")
        
        # 控制补光
        if 'light' in actions:
            self.actuator.set_light(actions['light'])
            logger.info(f"补光状态：{'开启' if actions['light'] else '关闭'}")
        
        # 控制通风
        if 'fan' in actions:
            self.actuator.set_fan(actions['fan'])
            logger.info(f"通风状态：{'开启' if actions['fan'] else '关闭'}")
    
    def save_data(self, data: Dict[str, Any], decision: Dict[str, Any]):
        """
        保存数据到历史记录
        
        Args:
            data: 传感器数据
            decision: 决策结果
        """
        record = {
            **data,
            'decision': decision
        }
        self.data_history.append(record)
        
        # 限制历史记录大小
        if len(self.data_history) > 1000:
            self.data_history.pop(0)
    
    def generate_daily_report(self) -> str:
        """
        生成每日生长报告
        
        Returns:
            报告文本
        """
        if not self.data_history:
            return "暂无数据"
        
        # 计算统计数据
        avg_soil = sum(
            sum(d['soil'].get(f'point_{i}', {}).get('moisture', 0) for i in range(3))
            / 3 for d in self.data_history
        ) / len(self.data_history)
        
        avg_temp = sum(d['environment'].get('temperature', 0) for d in self.data_history) / len(self.data_history)
        avg_humidity = sum(d['environment'].get('humidity', 0) for d in self.data_history) / len(self.data_history)
        
        report = f"""
=== AgriSense 每日生长报告 ===
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【环境概况】
- 平均温度：{avg_temp:.1f}°C
- 平均湿度：{avg_humidity:.1f}%
- 平均土壤湿度：{avg_soil:.1f}%

【作物健康】
- 叶片状态：{self.data_history[-1].get('vision', {}).get('leaf_health', {}).get('status', '未知')}
- 生长阶段：{self.data_history[-1].get('vision', {}).get('growth', {}).get('stage', '未知')}

【AI 建议】
{self.llm_advisor.get_daily_summary(self.data_history)}

========================
"""
        return report
    
    def data_collection_loop(self, interval: int = 60):
        """数据采集主循环
        
        Args:
            interval: 采集间隔（秒）
        """
        logger.info(f"启动数据采集循环 (间隔：{interval}秒)...")
        
        while self.running:
            try:
                logger.info("开始数据采集...")
                
                # 采集数据
                data = self.collect_data()
                
                # 做出决策
                decision = self.make_decision(data)
                
                # 执行动作
                self.execute_actions(decision)
                
                # 保存数据
                self.save_data(data, decision)
                
                logger.info(f"数据采集完成 - 土壤湿度：{data['soil']}")
                
            except Exception as e:
                logger.error(f"数据采集循环错误：{e}")
            
            # 等待下一个采集周期
            time.sleep(interval)
    
    def start(self, web_port: int = 5000, collection_interval: int = 60):
        """启动系统
        
        Args:
            web_port: Web 服务器端口
            collection_interval: 数据采集间隔（秒）
        """
        logger.info("启动 AgriSense 系统...")
        self.running = True
        
        # 启动数据采集线程
        data_thread = threading.Thread(
            target=self.data_collection_loop,
            args=(collection_interval,),
            daemon=True
        )
        data_thread.start()
        
        # 启动 Web 服务器
        from web.app import initialize_modules, run_server
        initialize_modules(simulation=self.use_simulation)
        run_server(host='0.0.0.0', port=web_port, debug=False)
    
    def stop(self):
        """停止系统"""
        logger.info("停止 AgriSense 系统...")
        self.running = False
        self.actuator.emergency_stop()


def main():
    """主函数"""
    import signal
    import sys
    
    # 从命令行参数读取模拟模式设置
    # 用法：python main.py --simulation (默认) 或 python main.py --hardware
    use_simulation = True
    web_port = 5000
    collection_interval = 60
    
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == '--hardware' or arg == '--no-simulation':
            use_simulation = False
        elif arg == '--simulation':
            use_simulation = True
        elif arg == '--port' and i + 1 < len(args):
            web_port = int(args[i + 1])
        elif arg == '--interval' and i + 1 < len(args):
            collection_interval = int(args[i + 1])
    
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    system = AgriSenseSystem(use_simulation=use_simulation)
    
    def signal_handler(sig, frame):
        logger.info("收到退出信号，正在关闭...")
        system.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        mode = "模拟模式" if use_simulation else "硬件模式"
        logger.info(f"========================================")
        logger.info(f"AgriSense 系统启动")
        logger.info(f"运行模式：{mode}")
        logger.info(f"Web 端口：{web_port}")
        logger.info(f"采集间隔：{collection_interval}秒")
        logger.info(f"========================================")
        system.start(web_port=web_port, collection_interval=collection_interval)
    except Exception as e:
        logger.error(f"系统错误：{e}")
        system.stop()


if __name__ == '__main__':
    main()