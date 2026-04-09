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
import warnings
from datetime import datetime
from typing import Dict, Any, List
from flask import Flask, render_template, jsonify, request, Response, make_response
from flask_cors import CORS

# 静默 TensorFlow 警告和提示
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
# 静默 Keras/TensorFlow Python 警告
warnings.filterwarnings('ignore', message='.*tf\\.losses\\.sparse_softmax_cross_entropy.*')

# 添加父目录到路径以导入其他模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensors.environment import EnvironmentSensor
from sensors.soil_moisture import SoilMoistureSensor
from sensors.camera import CameraSensor as Camera
from vision.leaf_disease import LeafDiseaseAnalyzer
from vision.growth_measure import GrowthAnalyzer as GrowthMeasure
from vision.cnn_crop_analyzer import CNNCropAnalyzer
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
cnn_crop_analyzer = None
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
    global leaf_analyzer, growth_measure, cnn_crop_analyzer
    global rules_engine, llm_advisor, actuator
    
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
    cnn_crop_analyzer = CNNCropAnalyzer(use_simulation=simulation)
    
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

@app.route('/controller')
def controller():
    """控制器页面"""
    response = make_response(render_template('controller.html'))
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


@app.route('/mobile')
def mobile():
    """移动端控制页面"""
    response = make_response(render_template('mobile.html'))
    # 禁用缓存以确保最新内容
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/api/heartbeat')
def heartbeat():
    """心跳检测接口"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


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


# 照片存储配置
MAX_SNAPSHOT_COUNT = 10
SNAPSHOT_DIR = os.path.join(os.getcwd(), 'captures', 'snapshots')

# 确保照片目录存在
os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def cleanup_old_snapshots():
    """清理旧照片，只保留最新的 MAX_SNAPSHOT_COUNT 张"""
    try:
        if not os.path.exists(SNAPSHOT_DIR):
            return
        
        # 获取所有照片文件
        snapshots = []
        for f in os.listdir(SNAPSHOT_DIR):
            if f.endswith('.jpg') or f.endswith('.png'):
                filepath = os.path.join(SNAPSHOT_DIR, f)
                mtime = os.path.getmtime(filepath)
                snapshots.append((filepath, mtime))
        
        # 按修改时间排序（最新的在前）
        snapshots.sort(key=lambda x: x[1], reverse=True)
        
        # 删除多余的照片
        if len(snapshots) > MAX_SNAPSHOT_COUNT:
            for filepath, _ in snapshots[MAX_SNAPSHOT_COUNT:]:
                try:
                    os.remove(filepath)
                    logger.info(f"删除旧照片：{filepath}")
                except Exception as e:
                    logger.warning(f"删除照片失败 {filepath}: {e}")
    except Exception as e:
        logger.error(f"清理照片失败：{e}")


@app.route('/api/snapshot', methods=['POST'])
def take_snapshot():
    """
    拍照接口
    - 模拟模式：返回错误，提示用户上传照片
    - 硬件模式：调用摄像头拍摄并保存
    """
    if not camera:
        return jsonify({'error': '相机未初始化'}), 500
    
    # 如果是模拟模式，返回错误提示用户上传
    if system_status.get('simulation_enabled', True):
        return jsonify({
            'error': '模拟模式下无法拍照，请上传本地图片进行分析',
            'mode': 'simulation',
            'suggest_upload': True
        }), 400
    
    # 硬件模式：调用摄像头拍摄
    try:
        filename = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(SNAPSHOT_DIR, filename)
        
        # 确保目录存在
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        
        # 调用摄像头拍摄并保存
        image = camera.capture(save=False, prefix='snapshot')
        if image is None:
            return jsonify({'error': '摄像头捕获失败'}), 500
        
        # 保存图像
        import cv2
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        cv2.imwrite(filepath, image_bgr)
        
        # 清理旧照片
        cleanup_old_snapshots()
        
        logger.info(f"照片已保存：{filepath}")
        
        return jsonify({
            'filename': filename,
            'path': filepath,
            'mode': 'hardware',
            'success': True
        })
    except Exception as e:
        logger.error(f"拍照失败：{e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/snapshot/upload', methods=['POST'])
def upload_snapshot():
    """
    上传照片进行分析（模拟模式使用）
    """
    if 'image' not in request.files:
        return jsonify({'error': '未找到图像文件'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    
    try:
        # 保存上传的照片
        import uuid
        filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(SNAPSHOT_DIR, filename)
        
        # 确保目录存在
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        
        file.save(filepath)
        
        # 清理旧照片
        cleanup_old_snapshots()
        
        logger.info(f"照片已上传：{filepath}")
        
        return jsonify({
            'filename': filename,
            'path': filepath,
            'mode': 'simulation',
            'success': True
        })
    except Exception as e:
        logger.error(f"上传照片失败：{e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/snapshots/list', methods=['GET'])
def list_snapshots():
    """获取所有已保存的照片列表"""
    try:
        snapshots = []
        if os.path.exists(SNAPSHOT_DIR):
            for f in os.listdir(SNAPSHOT_DIR):
                if f.endswith('.jpg') or f.endswith('.png'):
                    filepath = os.path.join(SNAPSHOT_DIR, f)
                    mtime = os.path.getmtime(filepath)
                    snapshots.append({
                        'filename': f,
                        'path': filepath,
                        'url': f'/api/snapshots/{f}',
                        'timestamp': datetime.fromtimestamp(mtime).isoformat()
                    })
        
        # 按时间排序（最新的在前）
        snapshots.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'snapshots': snapshots,
            'count': len(snapshots),
            'max_count': MAX_SNAPSHOT_COUNT
        })
    except Exception as e:
        logger.error(f"获取照片列表失败：{e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/snapshots/<filename>', methods=['GET'])
def get_snapshot(filename):
    """获取单张照片"""
    filepath = os.path.join(SNAPSHOT_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
    
    from flask import send_file
    return send_file(filepath, mimetype='image/jpeg')


@app.route('/api/snapshots/<filename>', methods=['DELETE'])
def delete_snapshot(filename):
    """删除单张照片"""
    filepath = os.path.join(SNAPSHOT_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
    
    try:
        os.remove(filepath)
        logger.info(f"照片已删除：{filepath}")
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        logger.error(f"删除照片失败：{e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/snapshots/clear', methods=['POST'])
def clear_snapshots():
    """清空所有照片"""
    try:
        if os.path.exists(SNAPSHOT_DIR):
            for f in os.listdir(SNAPSHOT_DIR):
                if f.endswith('.jpg') or f.endswith('.png'):
                    filepath = os.path.join(SNAPSHOT_DIR, f)
                    os.remove(filepath)
        return jsonify({'success': True, 'message': '所有照片已清空'})
    except Exception as e:
        logger.error(f"清空照片失败：{e}")
        return jsonify({'error': str(e)}), 500


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
            'cnn_crop_analyzer': cnn_crop_analyzer is not None,
            'rules_engine': rules_engine is not None,
            'llm_advisor': llm_advisor is not None,
            'actuator': actuator is not None
        }
    })


@app.route('/api/vision/crop-health')
def get_crop_health():
    """获取作物健康分析（基于 CNN）"""
    if not cnn_crop_analyzer:
        return jsonify({'error': 'CNN 作物分析器未初始化'}), 500
    
    # 使用模拟摄像头图像
    result = cnn_crop_analyzer.analyze(None)
    return jsonify(result)


@app.route('/api/vision/crop-health/upload', methods=['POST'])
def upload_crop_health_image():
    """上传图像进行作物健康分析"""
    if not cnn_crop_analyzer:
        return jsonify({'error': 'CNN 作物分析器未初始化'}), 500
    
    if 'image' not in request.files:
        return jsonify({'error': '未找到图像文件'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    
    try:
        # 保存上传的图像到临时目录
        import uuid
        temp_dir = os.path.join(os.getcwd(), 'captures', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # 使用唯一文件名
        unique_filename = f"{uuid.uuid4().hex}.jpg"
        temp_filepath = os.path.join(temp_dir, unique_filename)
        
        # 保存文件
        file.save(temp_filepath)
        
        # 分析图像
        result = cnn_crop_analyzer.analyze_image_file(temp_filepath)
        
        # 延迟删除文件（避免 Windows 文件锁定问题）
        try:
            import time
            import threading
            
            def delayed_delete(filepath, delay_seconds=2):
                time.sleep(delay_seconds)
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except Exception as e:
                    logger.warning(f"删除临时文件失败：{e}")
            
            # 在后台线程中延迟删除
            threading.Thread(target=delayed_delete, args=(temp_filepath, 2), daemon=True).start()
        except Exception:
            pass
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"图像分析失败：{e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/vision/crop-health/classes')
def get_crop_health_classes():
    """获取 CNN 识别的病害类别列表"""
    if not cnn_crop_analyzer:
        return jsonify({'error': 'CNN 作物分析器未初始化'}), 500
    
    return jsonify({
        'classes': cnn_crop_analyzer.get_class_labels(),
        'disease_info': cnn_crop_analyzer.get_disease_info()
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
    if use_context:
        context = {}
        
        # 环境数据
        if environment_sensor:
            env_data = environment_sensor.read_all()
            if system_status['simulation_enabled']:
                for key, value in simulation_config['environment'].items():
                    if key in env_data:
                        env_data[key] = value['value']
            context['environment'] = env_data
        
        # 土壤数据
        if soil_sensor:
            soil_data = soil_sensor.read_all()
            if system_status['simulation_enabled']:
                for i in range(3):
                    point_key = f'point_{i}'
                    if point_key in simulation_config['soil']:
                        soil_data['points'][i] = {
                            'point_id': i,
                            'moisture': simulation_config['soil'][point_key]['value'],
                            'status': 'optimal',
                            'timestamp': datetime.now().isoformat()
                        }
                soil_data['average'] = round(
                    sum(p['moisture'] for p in soil_data['points']) / 3, 2
                )
            context['soil'] = soil_data
        
        # 叶片健康数据
        if leaf_analyzer:
            try:
                leaf_result = leaf_analyzer.analyze(None)
                context['vision'] = context.get('vision', {})
                context['vision']['leaf_health'] = leaf_result
            except Exception as e:
                logger.warning(f"获取叶片健康数据失败：{e}")
        
        # 生长测量数据
        if growth_measure:
            try:
                growth_result = growth_measure.analyze(None)
                context['vision'] = context.get('vision', {})
                context['vision']['growth_measure'] = growth_result
            except Exception as e:
                logger.warning(f"获取生长测量数据失败：{e}")
        
        # CNN 作物健康数据
        if cnn_crop_analyzer:
            try:
                # 使用模拟数据或返回分析结果
                crop_health_result = cnn_crop_analyzer.analyze(None)
                context['vision'] = context.get('vision', {})
                context['vision']['crop_health'] = crop_health_result
            except Exception as e:
                logger.warning(f"获取 CNN 作物健康数据失败：{e}")
        
        # 决策数据
        if rules_engine and llm_advisor:
            try:
                decision_data = {
                    'environment': context.get('environment', {}),
                    'soil': context.get('soil', {}),
                    'vision': context.get('vision', {})
                }
                rules_decision = rules_engine.evaluate(decision_data)
                llm_advice = llm_advisor.get_advice(decision_data)
                context['decisions'] = {
                    'rules': rules_decision,
                    'llm_advice': llm_advice
                }
            except Exception as e:
                logger.warning(f"获取决策数据失败：{e}")
    
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
        'thinking': response.get('thinking', ''),
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


# ========== APK 打包相关路由 ==========

# APK 构建目录配置
APK_BUILD_DIR = os.path.join(os.getcwd(), 'builds', 'apk')
os.makedirs(APK_BUILD_DIR, exist_ok=True)


@app.route('/api/apk/directories', methods=['GET'])
def get_apk_directories():
    """获取可用的输出目录列表"""
    # 获取常见目录
    import platform
    system = platform.system()
    
    directories = [
        os.getcwd(),  # 当前工作目录
        os.path.join(os.getcwd(), 'builds'),  # builds 目录
        os.path.join(os.getcwd(), 'builds', 'apk'),  # APK 构建目录
    ]
    
    # 添加用户目录
    if system == 'Windows':
        directories.extend([
            os.path.join(os.environ.get('USERPROFILE', ''), 'Downloads'),
            os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop'),
        ])
    else:
        directories.extend([
            os.path.join(os.environ.get('HOME', ''), 'Downloads'),
            os.path.join(os.environ.get('HOME', ''), 'Desktop'),
        ])
    
    # 确保目录存在
    for dir_path in directories:
        try:
            os.makedirs(dir_path, exist_ok=True)
        except:
            pass
    
    return jsonify({
        'status': 'success',
        'directories': directories
    })


@app.route('/api/apk/build', methods=['POST'])
def build_apk():
    """
    构建 APK 文件
    使用 PWA 方式将 Web 应用打包为 APK
    """
    data = request.get_json()
    output_dir = data.get('output_dir', APK_BUILD_DIR)
    app_name = data.get('app_name', 'AgriSense')
    version = data.get('version', '1.0.0')
    
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成 APK 文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        apk_filename = f"{app_name.replace(' ', '_')}_{version}_{timestamp}.apk"
        apk_filepath = os.path.join(output_dir, apk_filename)
        
        # 模拟构建过程（实际 APK 构建需要 Android SDK）
        # 这里创建一个模拟的 APK 文件，并返回构建信息
        # 在实际部署中，可以使用以下方法之一：
        # 1. Bubblewrap (Google 官方的 TWA 构建工具)
        # 2. PWABuilder (在线服务)
        # 3. Cordova/Capacitor 等混合框架
        
        # 创建构建信息文件
        build_info = {
            'app_name': app_name,
            'version': version,
            'build_time': datetime.now().isoformat(),
            'web_url': 'http://localhost:5000',  # 实际部署时应该是服务器地址
            'output_dir': output_dir,
            'apk_filename': apk_filename,
            'package_name': 'com.agrisense.monitor',
            'min_sdk': 21,
            'target_sdk': 33
        }
        
        # 创建 APK 构建目录
        build_subdir = os.path.join(APK_BUILD_DIR, f"build_{timestamp}")
        os.makedirs(build_subdir, exist_ok=True)
        
        # 保存构建信息
        info_filepath = os.path.join(build_subdir, 'build_info.json')
        with open(info_filepath, 'w', encoding='utf-8') as f:
            json.dump(build_info, f, indent=2, ensure_ascii=False)
        
        # 创建一个占位 APK 文件（实际构建需要使用 Android 工具链）
        # 这里创建一个简单的文件来模拟 APK
        placeholder_content = f"""
AgriSense APK Build Placeholder
App Name: {app_name}
Version: {version}
Build Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

To build a real APK, you need to:
1. Install Bubblewrap (npm install -g @bubblewrap/cli)
2. Generate a TWA manifest
3. Build using: bubblewrap build

Alternatively, use PWABuilder.com for easier APK generation.
        """
        
        with open(apk_filepath, 'w', encoding='utf-8') as f:
            f.write(placeholder_content)
        
        # 获取文件大小
        file_size = os.path.getsize(apk_filepath)
        
        logger.info(f"APK 构建完成：{apk_filepath}")
        
        return jsonify({
            'status': 'success',
            'apk_file': apk_filepath,
            'apk_filename': apk_filename,
            'apk_size': f"{file_size} bytes",
            'build_info': build_info,
            'message': 'APK 构建完成！注意：这是占位文件，实际 APK 需要使用 Android 构建工具链生成。'
        })
        
    except Exception as e:
        logger.error(f"APK 构建失败：{e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/apk/download', methods=['GET'])
def download_apk():
    """下载 APK 文件"""
    filename = request.args.get('filename')
    
    if not filename:
        return jsonify({'error': '缺少文件名参数'}), 400
    
    # 构建完整文件路径
    apk_file = os.path.join(APK_BUILD_DIR, filename)
    
    if not os.path.exists(apk_file):
        return jsonify({'error': '文件不存在'}), 404
    
    try:
        from flask import send_file
        return send_file(
            apk_file,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"下载 APK 失败：{e}")
        return jsonify({'error': str(e)}), 500
    

@app.route('/api/apk/guide', methods=['GET'])
def get_apk_build_guide():
    """获取 APK 构建指南"""
    return jsonify({
        'status': 'success',
        'guide': {
            'methods': [
                {
                    'name': 'Bubblewrap (推荐)',
                    'description': 'Google 官方的 TWA 构建工具',
                    'steps': [
                        '安装 Node.js',
                        '运行：npm install -g @bubblewrap/cli',
                        '初始化：bubblewrap init --manifest https://your-domain.com/manifest.json',
                        '构建：bubblewrap build'
                    ]
                },
                {
                    'name': 'PWABuilder',
                    'description': '微软提供的在线 PWA 打包服务',
                    'url': 'https://www.pwabuilder.com/',
                    'steps': [
                        '访问 pwabuilder.com',
                        '输入你的 Web 应用 URL',
                        '按照提示完成配置',
                        '下载 APK 文件'
                    ]
                },
                {
                    'name': 'Cordova',
                    'description': '使用 Apache Cordova 进行打包',
                    'steps': [
                        '安装 Cordova: npm install -g cordova',
                        '创建项目：cordova create AgriSense',
                        '添加 Android 平台：cordova platform add android',
                        '将 Web 文件复制到 www 目录',
                        '构建：cordova build android'
                    ]
                }
            ],
            'requirements': [
                'Node.js 14+',
                'Java JDK 8+',
                'Android SDK (仅用于本地构建)',
                'Web 应用可公开访问的 URL'
            ]
        }
    })


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
