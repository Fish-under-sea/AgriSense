#!/usr/bin/env python3
"""
Web 应用模块

功能：
- Flask Web 服务器
- REST API 接口
- 实时数据展示
- 设备控制界面
- 模拟数据控制
"""

import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List
from flask import Flask, render_template, jsonify, request, Response, make_response
from flask_cors import CORS

# 添加父目录到路径以导入其他模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensors.environment import EnvironmentSensor
from sensors.soil_moisture import SoilMoistureSensor
from sensors.camera import CameraSensor as Camera
from vision.leaf_disease import LeafDiseaseAnalyzer
from vision.growth_measure import GrowthAnalyzer as GrowthMeasure
from decision.rules_engine import RulesEngine
from decision.llm_advisor import LLMAdvisor
from control.actuator import ActuatorController

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 全局变量
environment_sensor = None
soil_sensor = None
camera = None
leaf_analyzer = None
growth_measure = None
rules_engine = None
llm_advisor = None
actuator = None

# 数据存储
sensor_history: List[Dict[str, Any]] = []
MAX_HISTORY_SIZE = 100

# 对话历史存储 (按会话 ID)
conversation_histories: Dict[str, List[Dict[str, str]]] = {}
DEFAULT_SESSION_ID = "main"

# 系统状态
system_status = {
    'running': False,
    'mode': 'simulation',
    'last_update': None,
    'simulation_enabled': True
}

# 模拟数据配置
simulation_config = {
    'environment': {
        'temperature': {'min': 18, 'max': 32, 'value': 25},
        'humidity': {'min': 40, 'max': 80, 'value': 60},
        'light': {'min': 500, 'max': 5000, 'value': 2500},
        'co2': {'min': 400, 'max': 1200, 'value': 600},
        'pressure': {'min': 990, 'max': 1030, 'value': 1013},
        'voc': {'min': 0, 'max': 500, 'value': 200}
    },
    'soil': {
        'point_0': {'min': 20, 'max': 80, 'value': 45},
        'point_1': {'min': 20, 'max': 80, 'value': 50},
        'point_2': {'min': 20, 'max': 80, 'value': 48}
    }
}


def load_config():
    """加载配置文件"""
    # 尝试多个可能的路径
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json'),  # src/../config.json
        os.path.join(os.path.dirname(__file__), '..', '..', 'config.json'),  # src/web/../../config.json
        os.path.join(os.getcwd(), 'config.json'),  # 当前工作目录
    ]
    
    for config_path in possible_paths:
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"尝试加载 {config_path} 失败：{e}")
    
    logger.warning("无法加载配置文件，使用默认配置")
    return {}


def initialize_modules(simulation: bool = True):
    """初始化所有模块"""
    global environment_sensor, soil_sensor, camera
    global leaf_analyzer, growth_measure, rules_engine
    global llm_advisor, actuator
    
    # 加载配置
    config = load_config()
    llm_config = config.get('decision', {}).get('llm_advisor', {})
    
    mode = 'simulation' if simulation else 'hardware'
    system_status['mode'] = mode
    system_status['simulation_enabled'] = simulation
    system_status['running'] = True
    system_status['last_update'] = datetime.now().isoformat()
    
    # 初始化传感器
    environment_sensor = EnvironmentSensor(use_simulation=simulation)
    soil_sensor = SoilMoistureSensor(use_simulation=simulation)
    camera = Camera(use_simulation=simulation)
    
    # 初始化视觉分析
    leaf_analyzer = LeafDiseaseAnalyzer(use_simulation=simulation)
    growth_measure = GrowthMeasure(use_simulation=simulation)
    
    # 初始化决策模块
    rules_engine = RulesEngine()
    
    # 支持多模型配置
    default_model = llm_config.get('default_model', 'gpt-4o-mini')
    models_config = llm_config.get('models', {})
    
    llm_advisor = LLMAdvisor(
        model_name=default_model,
        use_simulation=simulation,
        models_config=models_config
    )
    
    # 初始化执行器
    actuator = ActuatorController(use_simulation=simulation)
    
    logger.info(f"所有模块已初始化 (模式：{mode}, LLM 模型：{llm_advisor.model_display_name})")


@app.route('/')
def index():
    """主页"""
    response = make_response(render_template('index.html'))
    # 禁用缓存以确保最新内容
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/simulator')
def simulator():
    """模拟器控制页面"""
    response = make_response(render_template('simulator.html'))
    # 禁用缓存以确保最新内容
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/api/status')
def get_status():
    """获取系统状态"""
    return jsonify({
        'system': system_status,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/simulation/toggle', methods=['POST'])
def toggle_simulation():
    """切换模拟模式"""
    data = request.get_json()
    enabled = data.get('enabled', True)
    
    system_status['simulation_enabled'] = enabled
    system_status['mode'] = 'simulation' if enabled else 'hardware'
    system_status['last_update'] = datetime.now().isoformat()
    
    # 重新初始化模块
    initialize_modules(simulation=enabled)
    
    return jsonify({
        'status': 'success',
        'simulation_enabled': enabled,
        'mode': system_status['mode']
    })


@app.route('/api/simulation/config', methods=['GET'])
def get_simulation_config():
    """获取模拟配置"""
    return jsonify(simulation_config)


@app.route('/api/simulation/config', methods=['POST'])
def update_simulation_config():
    """更新模拟配置"""
    global simulation_config
    
    data = request.get_json()
    category = data.get('category')
    key = data.get('key')
    value = data.get('value')
    
    if category and key and 'value' in data:
        if category in simulation_config and key in simulation_config[category]:
            simulation_config[category][key]['value'] = value
            return jsonify({'status': 'updated', 'config': simulation_config})
    
    return jsonify({'error': '配置更新失败'}), 400


@app.route('/api/simulation/randomize', methods=['POST'])
def randomize_simulation_data():
    """随机化模拟数据"""
    import random
    
    for category, items in simulation_config.items():
        for key, config in items.items():
            min_val = config.get('min', 0)
            max_val = config.get('max', 100)
            config['value'] = round(random.uniform(min_val, max_val), 2)
    
    return jsonify({'status': 'success', 'config': simulation_config})


@app.route('/api/sensors/environment')
def get_environment():
    """获取环境传感器数据"""
    if not environment_sensor:
        return jsonify({'error': '传感器未初始化'}), 500
    
    data = environment_sensor.read_all()
    
    # 如果使用模拟模式，使用配置的值
    if system_status['simulation_enabled']:
        for key, value in simulation_config['environment'].items():
            if key in data:
                # 添加一点随机波动 (±1%)
                import random
                base_value = value['value']
                variation = random.uniform(-1, 1)
                data[key] = round(base_value + variation, 2)
    
    return jsonify(data)


@app.route('/api/sensors/soil')
def get_soil():
    """获取土壤传感器数据"""
    if not soil_sensor:
        return jsonify({'error': '传感器未初始化'}), 500
    
    data = soil_sensor.read_all()
    
    # 如果使用模拟模式，使用配置的值
    if system_status['simulation_enabled']:
        for i in range(3):
            point_key = f'point_{i}'
            if point_key in simulation_config['soil']:
                config = simulation_config['soil'][point_key]
                import random
                base_value = config['value']
                variation = random.uniform(-1, 1)
                moisture = round(base_value + variation, 2)
                
                # 确定状态
                if moisture < 30:
                    status = 'dry'
                elif moisture > 70:
                    status = 'wet'
                else:
                    status = 'optimal'
                
                data['points'][i] = {
                    'point_id': i,
                    'moisture': moisture,
                    'status': status,
                    'timestamp': datetime.now().isoformat()
                }
        
        # 重新计算平均值
        data['average'] = round(sum(p['moisture'] for p in data['points']) / 3, 2)
    
    return jsonify(data)


@app.route('/api/sensors/all')
def get_all_sensors():
    """获取所有传感器数据"""
    data = {
        'timestamp': datetime.now().isoformat(),
        'environment': {},
        'soil': {}
    }
    
    if environment_sensor:
        env_data = environment_sensor.read_all()
        if system_status['simulation_enabled']:
            for key, value in simulation_config['environment'].items():
                if key in env_data:
                    import random
                    base_value = value['value']
                    variation = random.uniform(-1, 1)
                    env_data[key] = round(base_value + variation, 2)
        data['environment'] = env_data
    
    if soil_sensor:
        soil_data = soil_sensor.read_all()
        if system_status['simulation_enabled']:
            for i in range(3):
                point_key = f'point_{i}'
                if point_key in simulation_config['soil']:
                    config = simulation_config['soil'][point_key]
                    import random
                    base_value = config['value']
                    variation = random.uniform(-1, 1)
                    moisture = round(base_value + variation, 2)
                    
                    if moisture < 30:
                        status = 'dry'
                    elif moisture > 70:
                        status = 'wet'
                    else:
                        status = 'optimal'
                    
                    soil_data['points'][i] = {
                        'point_id': i,
                        'moisture': moisture,
                        'status': status,
                        'timestamp': datetime.now().isoformat()
                    }
            
            soil_data['average'] = round(sum(p['moisture'] for p in soil_data['points']) / 3, 2)
        data['soil'] = soil_data
    
    # 添加到历史记录
    sensor_history.append(data)
    if len(sensor_history) > MAX_HISTORY_SIZE:
        sensor_history.pop(0)
    
    return jsonify(data)


@app.route('/api/vision/leaf')
def get_leaf_health():
    """获取叶片健康分析"""
    if not leaf_analyzer:
        return jsonify({'error': '视觉分析未初始化'}), 500
    
    result = leaf_analyzer.analyze(None)
    return jsonify(result)


@app.route('/api/vision/growth')
def get_growth():
    """获取生长测量"""
    if not growth_measure:
        return jsonify({'error': '生长测量未初始化'}), 500
    
    result = growth_measure.analyze(None)
    return jsonify(result)


@app.route('/api/decisions')
def get_decisions():
    """获取决策建议"""
    if not rules_engine or not llm_advisor:
        return jsonify({'error': '决策模块未初始化'}), 500
    
    # 获取传感器数据
    data = {
        'environment': {},
        'soil': {},
        'vision': {}
    }
    
    if environment_sensor:
        env_data = environment_sensor.read_all()
        if system_status['simulation_enabled']:
            for key, value in simulation_config['environment'].items():
                if key in env_data:
                    import random
                    base_value = value['value']
                    variation = random.uniform(-1, 1)
                    env_data[key] = round(base_value + variation, 2)
        data['environment'] = env_data
    
    if soil_sensor:
        soil_data = soil_sensor.read_all()
        if system_status['simulation_enabled']:
            for i in range(3):
                point_key = f'point_{i}'
                if point_key in simulation_config['soil']:
                    config = simulation_config['soil'][point_key]
                    import random
                    base_value = config['value']
                    variation = random.uniform(-1, 1)
                    moisture = round(base_value + variation, 2)
                    
                    if moisture < 30:
                        status = 'dry'
                    elif moisture > 70:
                        status = 'wet'
                    else:
                        status = 'optimal'
                    
                    soil_data['points'][i] = {
                        'point_id': i,
                        'moisture': moisture,
                        'status': status,
                        'timestamp': datetime.now().isoformat()
                    }
            
            soil_data['average'] = round(sum(p['moisture'] for p in soil_data['points']) / 3, 2)
        data['soil'] = soil_data
    
    # 规则引擎决策
    rules_decision = rules_engine.evaluate(data)
    
    # LLM 建议
    llm_advice = llm_advisor.get_advice(data)
    
    return jsonify({
        'rules': rules_decision,
        'llm_advice': llm_advice,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/actuators/status')
def get_actuators_status():
    """获取执行器状态"""
    if not actuator:
        return jsonify({'error': '执行器未初始化'}), 500
    
    return jsonify(actuator.get_status())


@app.route('/api/actuators/<device>/control', methods=['POST'])
def control_actuator(device: str):
    """控制执行器"""
    if not actuator:
        return jsonify({'error': '执行器未初始化'}), 500
    
    data = request.get_json()
    state = data.get('state', False)
    
    if device == 'irrigation':
        actuator.set_irrigation(state)
    elif device == 'light':
        actuator.set_light(state)
    elif device == 'fan':
        actuator.set_fan(state)
    elif device == 'shade':
        actuator.set_shade(state)
    else:
        return jsonify({'error': f'未知设备：{device}'}), 400
    
    return jsonify({
        'device': device,
        'state': state,
        'status': 'success'
    })


@app.route('/api/actuators/stop', methods=['POST'])
def emergency_stop():
    """紧急停止"""
    if actuator:
        actuator.emergency_stop()
    return jsonify({'status': 'emergency_stop'})


@app.route('/api/history')
def get_history():
    """获取历史数据"""
    return jsonify({
        'history': sensor_history,
        'count': len(sensor_history)
    })


@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """清空历史数据"""
    global sensor_history
    sensor_history = []
    return jsonify({'status': 'cleared'})


@app.route('/api/advice/daily')
def get_daily_advice():
    """获取每日建议"""
    if not llm_advisor:
        return jsonify({'error': 'LLM 顾问未初始化'}), 500
    
    summary = llm_advisor.get_daily_summary(sensor_history)
    return jsonify({
        'daily_summary': summary,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/config/rules', methods=['GET'])
def get_rules_config():
    """获取规则配置"""
    if not rules_engine:
        return jsonify({'error': '规则引擎未初始化'}), 500
    
    return jsonify(rules_engine.get_rule_status())


@app.route('/api/config/rules', methods=['POST'])
def update_rules_config():
    """更新规则配置"""
    if not rules_engine:
        return jsonify({'error': '规则引擎未初始化'}), 500
    
    data = request.get_json()
    category = data.get('category')
    key = data.get('key')
    value = data.get('value')
    
    if category and key and value is not None:
        rules_engine.update_rule(category, key, value)
        return jsonify({'status': 'updated'})
    
    return jsonify({'error': '缺少参数'}), 400


@app.route('/api/snapshot', methods=['POST'])
def take_snapshot():
    """拍照"""
    if not camera:
        return jsonify({'error': '相机未初始化'}), 500
    
    filename = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    camera.capture(filename)
    
    return jsonify({
        'filename': filename,
        'path': os.path.join('..', filename)
    })


@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'modules': {
            'environment_sensor': environment_sensor is not None,
            'soil_sensor': soil_sensor is not None,
            'camera': camera is not None,
            'leaf_analyzer': leaf_analyzer is not None,
            'growth_measure': growth_measure is not None,
            'rules_engine': rules_engine is not None,
            'llm_advisor': llm_advisor is not None,
            'actuator': actuator is not None
        }
    })


@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """AI 对话咨询"""
    if not llm_advisor:
        return jsonify({'error': 'AI 顾问未初始化'}), 500
    
    data = request.get_json()
    message = data.get('message', '')
    session_id = data.get('session_id', DEFAULT_SESSION_ID)
    use_context = data.get('use_context', True)
    
    if not message:
        return jsonify({'error': '消息不能为空'}), 400
    
    # 获取当前传感器数据作为上下文
    context = None
    if use_context and environment_sensor and soil_sensor:
        context = {
            'environment': environment_sensor.read_all(),
            'soil': soil_sensor.read_all()
        }
        if system_status['simulation_enabled']:
            # 应用模拟配置值
            for key, value in simulation_config['environment'].items():
                if key in context['environment']:
                    context['environment'][key] = value['value']
            for i in range(3):
                point_key = f'point_{i}'
                if point_key in simulation_config['soil']:
                    context['soil']['points'][i] = {
                        'point_id': i,
                        'moisture': simulation_config['soil'][point_key]['value'],
                        'status': 'optimal',
                        'timestamp': datetime.now().isoformat()
                    }
            context['soil']['average'] = round(
                sum(p['moisture'] for p in context['soil']['points']) / 3, 2
            )
    
    # 获取对话历史
    history = conversation_histories.get(session_id, [])
    
    # 调用 AI 聊天
    response = llm_advisor.chat(message, context, history)
    
    # 保存对话历史
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []
    conversation_histories[session_id].append({
        'user': message,
        'assistant': response.get('response', '')
    })
    
    # 限制对话历史长度
    if len(conversation_histories[session_id]) > 20:
        conversation_histories[session_id] = conversation_histories[session_id][-20:]
    
    return jsonify({
        'response': response.get('response', ''),
        'model': response.get('model', 'unknown'),
        'timestamp': datetime.now().isoformat(),
        'error': response.get('error', False)
    })


@app.route('/api/ai/history', methods=['GET'])
def get_ai_history():
    """获取 AI 对话历史"""
    session_id = request.args.get('session_id', DEFAULT_SESSION_ID)
    history = conversation_histories.get(session_id, [])
    
    return jsonify({
        'history': history,
        'count': len(history),
        'session_id': session_id
    })


@app.route('/api/ai/history', methods=['DELETE'])
def clear_ai_history():
    """清空 AI 对话历史"""
    session_id = request.args.get('session_id', DEFAULT_SESSION_ID)
    
    if session_id in conversation_histories:
        conversation_histories[session_id] = []
    
    return jsonify({
        'status': 'cleared',
        'session_id': session_id
    })


@app.route('/api/ai/info', methods=['GET'])
def get_ai_info():
    """获取 AI 信息"""
    return jsonify({
        'name': 'AgriSense AI',
        'description': '专注于智能农业大棚的 AI 助手',
        'current_model': llm_advisor.get_model_info() if llm_advisor else {},
        'available_models': llm_advisor.get_available_models() if llm_advisor else {},
        'simulation_mode': system_status.get('simulation_enabled', True),
        'capabilities': [
            '分析环境传感器数据',
            '分析土壤数据',
            '分析作物健康状况',
            '提供农业管理建议',
            '回答农业相关问题'
        ]
    })


@app.route('/api/ai/models', methods=['GET'])
def get_available_models():
    """获取可用模型列表"""
    if not llm_advisor:
        return jsonify({'error': 'AI 顾问未初始化'}), 500
    
    return jsonify({
        'current_model': llm_advisor.current_model_key,
        'models': llm_advisor.get_available_models()
    })


@app.route('/api/ai/models/switch', methods=['POST'])
def switch_model():
    """切换模型"""
    if not llm_advisor:
        return jsonify({'error': 'AI 顾问未初始化'}), 500
    
    data = request.get_json()
    model_key = data.get('model_key')
    
    if not model_key:
        return jsonify({'error': '缺少 model_key 参数'}), 400
    
    if llm_advisor.switch_model(model_key):
        return jsonify({
            'status': 'success',
            'current_model': llm_advisor.get_model_info()
        })
    else:
        return jsonify({'error': f'模型 {model_key} 不存在'}), 404


def run_server(host='0.0.0.0', port=5000, debug=False):
    """运行 Web 服务器"""
    # 确保模板目录存在
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    # 初始化模块（模拟模式）
    initialize_modules(simulation=True)
    
    # 运行服务器
    run_server(debug=True)