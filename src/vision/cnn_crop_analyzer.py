#!/usr/bin/env python3
"""
基于 CNN 的番茄叶片病害识别模块

功能：
- 加载训练好的 CNN 模型
- 识别 10 种番茄叶片状态（健康及 9 种病害）
- 支持模拟输入和真实摄像头
- 提供病害处理建议
"""

import logging
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# 尝试导入常用库
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV 不可用")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy 不可用")

try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow 不可用，将使用模拟模式")


class TomatoDiseaseType(Enum):
    """番茄病害类型枚举"""
    HEALTHY = "健康"
    BACTERIAL_SPOT = "细菌性斑点病"
    EARLY_BLIGHT = "早疫病"
    LATE_BLIGHT = "晚疫病"
    LEAF_MOLD = "叶霉病"
    SEPTORIA_LEAF_SPOT = "Septoria 叶斑病"
    SPIDER_MITES = "红蜘蛛虫害"
    TARGET_SPOT = "靶斑病"
    MOSAIC_VIRUS = "花叶病毒病"
    YELLOW_LEAF_CURL_VIRUS = "黄曲叶病毒病"


# 病害处理建议
DISEASE_RECOMMENDATIONS = {
    'Tomato___healthy': "作物健康，继续保持当前管理",
    'Tomato___Bacterial_spot': "发现细菌性斑点病，建议喷施铜制剂，加强通风",
    'Tomato___Early_blight': "发现早疫病，建议摘除病叶，使用杀菌剂防治",
    'Tomato___Late_blight': "发现晚疫病，立即喷施杀菌剂，防止扩散",
    'Tomato___Leaf_Mold': "发现叶霉病，降低湿度，使用嘧菌酯防治",
    'Tomato___Septoria_leaf_spot': "发现 Septoria 叶斑病，喷施代森锰锌，摘除病叶",
    'Tomato___Spider_mites Two-spotted_spider_mite': "发现红蜘蛛，使用阿维菌素或螺螨酯防治",
    'Tomato___Target_Spot': "发现靶斑病，喷施苯醚甲环唑，加强通风",
    'Tomato___Tomato_mosaic_virus': "发现花叶病毒病，拔除病株，防治蚜虫传播",
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus': "发现黄曲叶病毒病，拔除病株，防治粉虱"
}


class CNNCropAnalyzer:
    """基于 CNN 的作物健康分析器"""
    
    # 模型输入尺寸
    INPUT_SIZE = 128
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        use_simulation: bool = True,
        confidence_threshold: float = 0.6
    ):
        """
        初始化 CNN 作物分析器
        
        Args:
            model_path: 训练好的模型文件路径 (.h5)
            use_simulation: 是否使用模拟模式
            confidence_threshold: 置信度阈值
        """
        self.model_path = model_path
        self.use_simulation = use_simulation
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.class_indices = None
        
        # 番茄病害类别（与数据集对应）
        self.class_labels = [
            'Tomato___Bacterial_spot',
            'Tomato___Early_blight',
            'Tomato___healthy',
            'Tomato___Late_blight',
            'Tomato___Leaf_Mold',
            'Tomato___Septoria_leaf_spot',
            'Tomato___Spider_mites Two-spotted_spider_mite',
            'Tomato___Target_Spot',
            'Tomato___Tomato_mosaic_virus',
            'Tomato___Tomato_Yellow_Leaf_Curl_Virus'
        ]
        
        # 加载模型
        if not self.use_simulation:
            self._load_model()
    
    def _load_model(self):
        """加载预训练 CNN 模型"""
        try:
            if not TENSORFLOW_AVAILABLE:
                logger.warning("TensorFlow 不可用，使用模拟模式")
                self.use_simulation = True
                return
            
            # 默认模型路径
            if self.model_path is None:
                self.model_path = 'dataset/cnn_model.h5'
            
            if os.path.exists(self.model_path):
                self.model = tf.keras.models.load_model(self.model_path)
                logger.info(f"CNN 模型加载成功：{self.model_path}")
            else:
                logger.warning(f"模型文件不存在：{self.model_path}，使用模拟模式")
                self.use_simulation = True
                
        except Exception as e:
            logger.error(f"模型加载失败：{e}")
            self.use_simulation = True
    
    def analyze(self, image: Any) -> Dict[str, Any]:
        """
        分析作物健康状态
        
        Args:
            image: 图像数据（numpy array 或文件路径）
            
        Returns:
            分析结果字典
        """
        if image is None:
            return self._get_empty_result("图像为空")
        
        # 如果 image 是字符串，认为是文件路径
        if isinstance(image, str):
            if not CV2_AVAILABLE:
                return self._get_empty_result("OpenCV 不可用")
            image = cv2.cvtColor(cv2.imread(image), cv2.COLOR_BGR2RGB)
        
        if self.use_simulation:
            return self._analyze_simulation(image)
        else:
            return self._analyze_with_cnn(image)
    
    def _analyze_with_cnn(self, image: Any) -> Dict[str, Any]:
        """使用 CNN 模型进行分析"""
        if not TENSORFLOW_AVAILABLE or self.model is None:
            return self._analyze_simulation(image)
        
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            return self._get_empty_result("OpenCV 或 NumPy 不可用")
        
        try:
            # 预处理图像
            processed = cv2.resize(image, (self.INPUT_SIZE, self.INPUT_SIZE))
            processed = processed.astype(np.float32) / 255.0
            processed = np.expand_dims(processed, axis=0)
            
            # 预测
            predictions = self.model.predict(processed, verbose=0)
            
            # 获取预测结果
            max_idx = np.argmax(predictions[0])
            max_confidence = float(predictions[0][max_idx])
            
            # 获取所有类别的置信度
            all_confidences = {}
            for i, label in enumerate(self.class_labels):
                all_confidences[label] = round(float(predictions[0][i]), 4)
            
            # 获取病害类型
            disease_code = self.class_labels[max_idx]
            disease_type = self._get_disease_name(disease_code)
            
            # 获取建议
            recommendation = DISEASE_RECOMMENDATIONS.get(disease_code, "请检查作物状态")
            
            # 计算健康评分
            health_score = self._calculate_health_score(disease_code, max_confidence)
            
            return {
                'disease_type': disease_type,
                'disease_code': disease_code,
                'confidence': round(max_confidence, 4),
                'health_score': health_score,
                'all_predictions': all_confidences,
                'recommendation': recommendation,
                'timestamp': datetime.now().isoformat(),
                'method': 'CNN'
            }
            
        except Exception as e:
            logger.error(f"CNN 预测失败：{e}")
            return self._analyze_simulation(image)
    
    def _analyze_simulation(self, image: Any) -> Dict[str, Any]:
        """模拟分析（基于图像颜色特征）"""
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            return self._get_empty_result("OpenCV 或 NumPy 不可用")
        
        try:
            # 转换到 HSV 颜色空间
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            
            # 计算颜色统计
            mean_color = np.mean(image, axis=(0, 1))
            std_color = np.std(image, axis=(0, 1))
            
            # 检测黄色区域（病害特征）
            yellow_mask = cv2.inRange(hsv, (20, 30, 50), (35, 255, 255))
            yellow_ratio = np.count_nonzero(yellow_mask) / yellow_mask.size
            
            # 检测褐色区域（病斑特征）
            brown_mask = cv2.inRange(hsv, (10, 50, 50), (20, 255, 200))
            brown_ratio = np.count_nonzero(brown_mask) / brown_mask.size
            
            # 检测暗色区域（霉变特征）
            dark_mask = cv2.inRange(hsv, (0, 0, 0), (180, 255, 80))
            dark_ratio = np.count_nonzero(dark_mask) / dark_mask.size
            
            # 基于颜色特征判断病害类型
            if yellow_ratio < 0.1 and brown_ratio < 0.05 and dark_ratio < 0.1:
                disease_code = 'Tomato___healthy'
                confidence = 0.85 + np.random.uniform(0, 0.1)
            elif brown_ratio > 0.15:
                disease_code = 'Tomato___Early_blight'
                confidence = min(0.9, brown_ratio * 2)
            elif yellow_ratio > 0.25:
                disease_code = 'Tomato___Tomato_Yellow_Leaf_Curl_Virus'
                confidence = min(0.85, yellow_ratio * 1.5)
            elif dark_ratio > 0.15:
                disease_code = 'Tomato___Late_blight'
                confidence = min(0.8, dark_ratio * 2)
            else:
                disease_code = 'Tomato___healthy'
                confidence = 0.7
            
            disease_type = self._get_disease_name(disease_code)
            recommendation = DISEASE_RECOMMENDATIONS.get(disease_code, "请检查作物状态")
            health_score = self._calculate_health_score(disease_code, confidence)
            
            return {
                'disease_type': disease_type,
                'disease_code': disease_code,
                'confidence': round(confidence, 4),
                'health_score': health_score,
                'recommendation': recommendation,
                'color_analysis': {
                    'mean_rgb': [round(x, 2) for x in mean_color],
                    'std_rgb': [round(x, 2) for x in std_color],
                    'yellow_ratio': round(yellow_ratio, 4),
                    'brown_ratio': round(brown_ratio, 4),
                    'dark_ratio': round(dark_ratio, 4)
                },
                'timestamp': datetime.now().isoformat(),
                'method': 'Simulation'
            }
            
        except Exception as e:
            logger.error(f"模拟分析失败：{e}")
            return self._get_empty_result(str(e))
    
    def _get_disease_name(self, disease_code: str) -> str:
        """根据病害代码获取中文名称"""
        disease_names = {
            'Tomato___healthy': '健康',
            'Tomato___Bacterial_spot': '细菌性斑点病',
            'Tomato___Early_blight': '早疫病',
            'Tomato___Late_blight': '晚疫病',
            'Tomato___Leaf_Mold': '叶霉病',
            'Tomato___Septoria_leaf_spot': 'Septoria 叶斑病',
            'Tomato___Spider_mites Two-spotted_spider_mite': '红蜘蛛虫害',
            'Tomato___Target_Spot': '靶斑病',
            'Tomato___Tomato_mosaic_virus': '花叶病毒病',
            'Tomato___Tomato_Yellow_Leaf_Curl_Virus': '黄曲叶病毒病'
        }
        return disease_names.get(disease_code, '未知病害')
    
    def _calculate_health_score(self, disease_code: str, confidence: float) -> float:
        """计算健康评分（0-100）"""
        if disease_code == 'Tomato___healthy':
            return round(confidence * 100, 2)
        else:
            severity_map = {
                'Tomato___Bacterial_spot': 0.7,
                'Tomato___Early_blight': 0.6,
                'Tomato___Late_blight': 0.3,
                'Tomato___Leaf_Mold': 0.5,
                'Tomato___Septoria_leaf_spot': 0.6,
                'Tomato___Spider_mites Two-spotted_spider_mite': 0.5,
                'Tomato___Target_Spot': 0.6,
                'Tomato___Tomato_mosaic_virus': 0.3,
                'Tomato___Tomato_Yellow_Leaf_Curl_Virus': 0.2
            }
            base_score = severity_map.get(disease_code, 0.5)
            return round(base_score * (1 - confidence) * 100, 2)
    
    def _get_empty_result(self, error_msg: str) -> Dict[str, Any]:
        """返回空结果"""
        return {
            'disease_type': '未知',
            'disease_code': 'unknown',
            'confidence': 0,
            'health_score': 0,
            'error': error_msg,
            'timestamp': datetime.now().isoformat(),
            'method': 'Simulation'
        }
    
    def preprocess_image(self, image: Any) -> Optional[Any]:
        """图像预处理"""
        if not CV2_AVAILABLE or image is None:
            return None
        
        try:
            image = cv2.resize(image, (self.INPUT_SIZE, self.INPUT_SIZE))
            image = cv2.bilateralFilter(image, 9, 75, 75)
            return image
        except Exception as e:
            logger.error(f"图像预处理失败：{e}")
            return None
    
    def analyze_image_file(self, image_path: str) -> Dict[str, Any]:
        """分析图像文件"""
        if not CV2_AVAILABLE:
            return self._get_empty_result("OpenCV 不可用")
        
        if not os.path.exists(image_path):
            return self._get_empty_result(f"文件不存在：{image_path}")
        
        image = cv2.imread(image_path)
        if image is None:
            return self._get_empty_result("无法读取图像")
        
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        return self.analyze(image)
    
    def get_class_labels(self) -> List[str]:
        """获取所有类别标签"""
        return self.class_labels.copy()
    
    def get_disease_info(self) -> Dict[str, str]:
        """获取病害信息字典"""
        return {code: self._get_disease_name(code) for code in self.class_labels}