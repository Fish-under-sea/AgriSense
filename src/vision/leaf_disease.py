#!/usr/bin/env python3
"""
叶片病害识别模块

功能：
- 识别叶片病害（白粉病、霜霉病、叶斑病等）
- 识别虫害（蚜虫、红蜘蛛等）
- 营养缺乏诊断（缺氮黄叶、缺钾焦边等）
- 基于 CNN 的迁移学习模型
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

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow 不可用，将使用模拟模式")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class DiseaseType(Enum):
    """病害类型枚举"""
    HEALTHY = "健康"
    POWDERY_MILDEW = "白粉病"
    DOWNY_MILDEW = "霜霉病"
    LEAF_SPOT = "叶斑病"
    ANTHRACNOSE = "炭疽病"
    BLOSSOM_END_ROT = "脐腐病"
    EARLY_BLIGHT = "早疫病"
    LATE_BLIGHT = "晚疫病"


class PestType(Enum):
    """虫害类型枚举"""
    NO_PEST = "无虫害"
    APHID = "蚜虫"
    SPIDER_MITE = "红蜘蛛"
    WHITEFLY = "白粉虱"
    THRIPS = "蓟马"
    SCALE = "介壳虫"


class NutrientDeficiency(Enum):
    """营养缺乏类型"""
    NONE = "营养充足"
    NITROGEN = "缺氮"
    PHOSPHORUS = "缺磷"
    POTASSIUM = "缺钾"
    MAGNESIUM = "缺镁"
    IRON = "缺铁"
    CALCIUM = "缺钙"


class LeafDiseaseAnalyzer:
    """叶片病害分析器"""
    
    # 病害颜色特征（HSV 范围）
    DISEASE_COLORS = {
        'powdery_mildew': {'h_range': (20, 40), 's_range': (20, 80)},  # 白色/灰色粉末
        'downy_mildew': {'h_range': (30, 60), 's_range': (30, 100)},   # 黄褐色
        'leaf_spot': {'h_range': (10, 30), 's_range': (50, 150)},      # 褐色斑点
        'yellowing': {'h_range': (20, 35), 's_range': (30, 100)},      # 黄色
    }
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        use_simulation: bool = True,
        confidence_threshold: float = 0.6
    ):
        """
        初始化叶片病害分析器
        
        Args:
            model_path: 模型文件路径
            use_simulation: 是否使用模拟模式
            confidence_threshold: 置信度阈值
        """
        self.model_path = model_path
        self.use_simulation = use_simulation
        self.confidence_threshold = confidence_threshold
        self.model = None
        
        # 类别标签
        self.class_labels = [
            'healthy', 'powdery_mildew', 'downy_mildew', 'leaf_spot',
            'anthracnose', 'blossom_end_rot', 'early_blight', 'late_blight'
        ]
        
        # 加载模型
        if not self.use_simulation:
            self._load_model()
    
    def _load_model(self):
        """加载预训练模型"""
        try:
            if TENSORFLOW_AVAILABLE and self.model_path and os.path.exists(self.model_path):
                self.model = tf.keras.models.load_model(self.model_path)
                logger.info(f"模型加载成功：{self.model_path}")
            else:
                logger.warning("TensorFlow 不可用或模型不存在，使用模拟模式")
                self.use_simulation = True
        except Exception as e:
            logger.error(f"模型加载失败：{e}")
            self.use_simulation = True
    
    def analyze(self, image: Any) -> Dict[str, Any]:
        """
        分析叶片健康状况
        
        Args:
            image: 图像数据（numpy array）
            
        Returns:
            分析结果字典
        """
        if image is None:
            return self._get_empty_result("图像为空")
        
        if self.use_simulation:
            return self._analyze_simulation(image)
        else:
            return self._analyze_hardware(image)
    
    def _analyze_simulation(self, image: Any) -> Dict[str, Any]:
        """
        模拟分析（基于图像颜色特征进行简单判断）
        
        Args:
            image: 图像数据
            
        Returns:
            模拟分析结果
        """
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            return self._get_empty_result("OpenCV 或 NumPy 不可用")
        
        # 转换到 HSV 颜色空间
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # 计算颜色统计
        mean_color = np.mean(image, axis=(0, 1))
        std_color = np.std(image, axis=(0, 1))
        
        # 检测黄色区域（可能表示病害或营养缺乏）
        yellow_mask = cv2.inRange(hsv, (20, 30, 50), (35, 255, 255))
        yellow_ratio = np.count_nonzero(yellow_mask) / yellow_mask.size
        
        # 检测褐色区域（可能表示斑点病）
        brown_mask = cv2.inRange(hsv, (10, 50, 50), (20, 255, 200))
        brown_ratio = np.count_nonzero(brown_mask) / brown_mask.size
        
        # 检测白色区域（可能表示白粉病）
        white_mask = cv2.inRange(hsv, (0, 0, 200), (20, 30, 255))
        white_ratio = np.count_nonzero(white_mask) / white_mask.size
        
        # 判断病害类型
        disease_type = DiseaseType.HEALTHY
        confidence = 0.9
        
        if white_ratio > 0.1:
            disease_type = DiseaseType.POWDERY_MILDEW
            confidence = min(0.95, white_ratio * 2)
        elif brown_ratio > 0.05:
            disease_type = DiseaseType.LEAF_SPOT
            confidence = min(0.9, brown_ratio * 3)
        elif yellow_ratio > 0.2:
            disease_type = DiseaseType.DOWNY_MILDEW
            confidence = min(0.85, yellow_ratio * 2)
        
        # 判断营养缺乏
        nutrient_deficiency = self._detect_nutrient_deficiency(image, hsv)
        
        # 判断虫害（简化版）
        pest_type = self._detect_pest(image)
        
        return {
            'disease_type': disease_type.value,
            'disease_code': disease_type.name,
            'confidence': round(confidence, 3),
            'nutrient_deficiency': nutrient_deficiency['type'].value,
            'nutrient_confidence': nutrient_deficiency['confidence'],
            'pest_type': pest_type['type'].value,
            'pest_confidence': pest_type['confidence'],
            'health_score': self._calculate_health_score(disease_type, nutrient_deficiency, pest_type),
            'color_analysis': {
                'mean_rgb': [round(x, 2) for x in mean_color],
                'std_rgb': [round(x, 2) for x in std_color],
                'yellow_ratio': round(yellow_ratio, 4),
                'brown_ratio': round(brown_ratio, 4),
                'white_ratio': round(white_ratio, 4)
            },
            'recommendations': self._get_recommendations(disease_type, nutrient_deficiency, pest_type),
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_hardware(self, image: Any) -> Dict[str, Any]:
        """
        使用真实模型分析
        
        Args:
            image: 图像数据
            
        Returns:
            分析结果
        """
        if not TENSORFLOW_AVAILABLE or self.model is None:
            return self._analyze_simulation(image)
        
        try:
            # 预处理图像
            input_size = 224
            processed = cv2.resize(image, (input_size, input_size))
            processed = processed.astype(np.float32) / 255.0
            processed = np.expand_dims(processed, axis=0)
            
            # 预测
            predictions = self.model.predict(processed, verbose=0)
            max_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][max_idx])
            
            disease_code = self.class_labels[max_idx]
            disease_type = DiseaseType.HEALTHY
            
            # 映射到病害类型
            disease_mapping = {
                'healthy': DiseaseType.HEALTHY,
                'powdery_mildew': DiseaseType.POWDERY_MILDEW,
                'downy_mildew': DiseaseType.DOWNY_MILDEW,
                'leaf_spot': DiseaseType.LEAF_SPOT,
                'anthracnose': DiseaseType.ANTHRACNOSE,
                'blossom_end_rot': DiseaseType.BLOSSOM_END_ROT,
                'early_blight': DiseaseType.EARLY_BLIGHT,
                'late_blight': DiseaseType.LATE_BLIGHT
            }
            disease_type = disease_mapping.get(disease_code, DiseaseType.HEALTHY)
            
            return {
                'disease_type': disease_type.value,
                'disease_code': disease_code,
                'confidence': round(confidence, 3),
                'health_score': round(confidence * 100 if disease_code == 'healthy' else (1 - confidence) * 100, 2),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"模型预测失败：{e}")
            return self._analyze_simulation(image)
    
    def _detect_nutrient_deficiency(self, image: Any, hsv: Any) -> Dict[str, Any]:
        """检测营养缺乏"""
        if not NUMPY_AVAILABLE:
            return {'type': NutrientDeficiency.NONE, 'confidence': 0.9}
        
        # 计算颜色特征
        mean_hsv = np.mean(hsv, axis=(0, 1))
        
        # 缺氮：整体发黄
        # 缺钾：叶缘焦枯
        # 缺镁：叶脉间黄化
        # 缺铁：新叶黄化
        
        # 简化判断
        h_mean = mean_hsv[0]
        s_mean = mean_hsv[1]
        
        if h_mean > 25 and s_mean < 100:
            return {'type': NutrientDeficiency.NITROGEN, 'confidence': 0.7}
        elif h_mean > 20 and s_mean > 100:
            return {'type': NutrientDeficiency.IRON, 'confidence': 0.6}
        
        return {'type': NutrientDeficiency.NONE, 'confidence': 0.8}
    
    def _detect_pest(self, image: Any) -> Dict[str, Any]:
        """检测虫害"""
        # 简化版：基于图像纹理分析
        # 实际应用中需要使用专门的虫害检测模型
        
        if not CV2_AVAILABLE:
            return {'type': PestType.NO_PEST, 'confidence': 0.9}
        
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # 计算边缘
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.count_nonzero(edges) / edges.size
        
        # 如果边缘密度异常高，可能有虫害
        if edge_density > 0.1:
            return {'type': PestType.APID, 'confidence': 0.5}
        
        return {'type': PestType.NO_PEST, 'confidence': 0.85}
    
    def _calculate_health_score(
        self,
        disease: DiseaseType,
        nutrient: Dict[str, Any],
        pest: Dict[str, Any]
    ) -> float:
        """计算健康评分（0-100）"""
        score = 100.0
        
        # 病害扣分
        if disease != DiseaseType.HEALTHY:
            score -= 30
        
        # 营养缺乏扣分
        if nutrient['type'] != NutrientDeficiency.NONE:
            score -= 20
        
        # 虫害扣分
        if pest['type'] != PestType.NO_PEST:
            score -= 25
        
        return max(0, min(100, score))
    
    def _get_recommendations(
        self,
        disease: DiseaseType,
        nutrient: Dict[str, Any],
        pest: Dict[str, Any]
    ) -> List[str]:
        """获取处理建议"""
        recommendations = []
        
        # 病害建议
        disease_recommendations = {
            DiseaseType.HEALTHY: "叶片健康，继续保持当前管理",
            DiseaseType.POWDERY_MILDEW: "发现白粉病症状，建议加强通风，使用生物制剂防治",
            DiseaseType.DOWNY_MILDEW: "发现霜霉病症状，建议降低湿度，使用铜制剂防治",
            DiseaseType.LEAF_SPOT: "发现叶斑病症状，建议摘除病叶，使用杀菌剂",
            DiseaseType.ANTHRACNOSE: "发现炭疽病症状，建议及时防治，避免雨水传播",
            DiseaseType.BLOSSOM_END_ROT: "发现脐腐病症状，建议补充钙肥，保持土壤湿度稳定",
            DiseaseType.EARLY_BLIGHT: "发现早疫病症状，建议加强通风，使用杀菌剂",
            DiseaseType.LATE_BLIGHT: "发现晚疫病症状，建议立即防治，防止扩散"
        }
        recommendations.append(disease_recommendations.get(disease, "请检查作物状态"))
        
        # 营养缺乏建议
        nutrient_recommendations = {
            NutrientDeficiency.NONE: "",
            NutrientDeficiency.NITROGEN: "建议补充氮肥，可使用尿素或有机肥",
            NutrientDeficiency.PHOSPHORUS: "建议补充磷肥，促进根系发育",
            NutrientDeficiency.POTASSIUM: "建议补充钾肥，增强抗病能力",
            NutrientDeficiency.MAGNESIUM: "建议补充镁肥，可使用硫酸镁",
            NutrientDeficiency.IRON: "建议补充铁肥，可使用螯合铁",
            NutrientDeficiency.CALCIUM: "建议补充钙肥，可使用硝酸钙"
        }
        if nutrient['type'] != NutrientDeficiency.NONE:
            recommendations.append(nutrient_recommendations.get(nutrient['type'], ""))
        
        # 虫害建议
        pest_recommendations = {
            PestType.NO_PEST: "",
            PestType.APID: "发现蚜虫，建议使用肥皂水或吡虫啉防治",
            PestType.SPIDER_MITE: "发现红蜘蛛，建议使用阿维菌素防治，增加湿度",
            PestType.WHITEFLY: "发现白粉虱，建议使用黄色粘虫板",
            PestType.THRIPS: "发现蓟马，建议使用蓝色粘虫板，使用乙基多杀菌素",
            PestType.SCALE: "发现介壳虫，建议使用物理清除或矿物油"
        }
        if pest['type'] != PestType.NO_PEST:
            recommendations.append(pest_recommendations.get(pest['type'], ""))
        
        return [r for r in recommendations if r]
    
    def _get_empty_result(self, error_msg: str) -> Dict[str, Any]:
        """返回空结果"""
        return {
            'disease_type': '未知',
            'disease_code': 'unknown',
            'confidence': 0,
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }
    
    def preprocess_image(self, image: Any) -> Optional[Any]:
        """图像预处理"""
        if not CV2_AVAILABLE or image is None:
            return None
        
        try:
            # 1. 调整大小
            image = cv2.resize(image, (224, 224))
            
            # 2. 去噪
            image = cv2.bilateralFilter(image, 9, 75, 75)
            
            return image
        except Exception as e:
            logger.error(f"图像预处理失败：{e}")
            return None