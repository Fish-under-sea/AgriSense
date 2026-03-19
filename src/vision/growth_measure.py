#!/usr/bin/env python3
"""
植株生长分析模块

功能：
- 测量株高
- 测量冠幅
- 叶片计数
- 果实数量/大小估算
- 生长阶段判断
- 生长速率计算
"""

import logging
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
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

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class GrowthStage(Enum):
    """生长阶段枚举"""
    SEEDLING = "幼苗期"
    VEGETATIVE = "营养生长期"
    FLOWERING = "开花期"
    FRUITING = "结果期"
    RIPENING = "成熟期"


class GrowthAnalyzer:
    """生长分析器"""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        reference_size: float = 10.0,  # cm
        use_simulation: bool = True,
        resolution: Tuple[int, int] = (640, 480)
    ):
        """
        初始化生长分析器
        
        Args:
            model_path: 分割模型路径
            reference_size: 参照物实际尺寸 (cm)，用于像素到实际尺寸的换算
            use_simulation: 是否使用模拟模式
            resolution: 图像分辨率
        """
        self.model_path = model_path
        self.reference_size = reference_size  # cm
        self.use_simulation = use_simulation
        self.resolution = resolution
        self.model = None
        
        # 历史记录（用于计算生长速率）
        self.history: List[Dict[str, Any]] = []
        
        # 像素到厘米的换算比例（需要校准）
        self.pixel_to_cm = 1.0
        
        # 加载模型
        if not self.use_simulation:
            self._load_model()
    
    def _load_model(self):
        """加载分割模型"""
        try:
            if TENSORFLOW_AVAILABLE and self.model_path and os.path.exists(self.model_path):
                self.model = tf.keras.models.load_model(self.model_path)
                logger.info(f"分割模型加载成功：{self.model_path}")
            elif TORCH_AVAILABLE and self.model_path and os.path.exists(self.model_path):
                self.model = torch.load(self.model_path)
                logger.info(f"分割模型加载成功：{self.model_path}")
            else:
                logger.warning("模型不可用，使用模拟模式")
                self.use_simulation = True
        except Exception as e:
            logger.error(f"模型加载失败：{e}")
            self.use_simulation = True
    
    def analyze(self, image: Any) -> Dict[str, Any]:
        """
        分析植株生长状态
        
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
        模拟分析（基于图像特征进行简单测量）
        
        Args:
            image: 图像数据
            
        Returns:
            模拟分析结果
        """
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            return self._get_empty_result("OpenCV 或 NumPy 不可用")
        
        # 1. 图像预处理
        image_rgb = image if len(image.shape) == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        image_resized = cv2.resize(image_rgb, self.resolution)
        
        # 2. 植物分割（基于颜色）
        hsv = cv2.cvtColor(image_resized, cv2.COLOR_RGB2HSV)
        
        # 绿色植物掩码
        lower_green = np.array([25, 40, 50])
        upper_green = np.array([75, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # 形态学操作
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 3. 计算植物区域
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return self._get_empty_result("未检测到植物")
        
        # 获取最大轮廓（主植株）
        largest_contour = max(contours, key=cv2.contourArea)
        plant_area = cv2.contourArea(largest_contour)
        
        if plant_area < 100:
            return self._get_empty_result("植物区域过小")
        
        # 4. 计算株高
        height_pixels = self._calculate_height(largest_contour, mask)
        
        # 5. 计算冠幅
        canopy_width, canopy_area = self._calculate_canopy(largest_contour)
        
        # 6. 叶片计数
        leaf_count = self._count_leaves(mask, contours)
        
        # 7. 计算像素到厘米的换算（基于参照物）
        self.pixel_to_cm = self.reference_size / self._find_reference_size(image_resized)
        
        # 8. 计算实际尺寸
        height_cm = height_pixels * self.pixel_to_cm
        canopy_width_cm = canopy_width * self.pixel_to_cm
        canopy_area_cm2 = canopy_area * (self.pixel_to_cm ** 2)
        
        # 9. 判断生长阶段
        growth_stage = self._determine_growth_stage(height_cm, leaf_count, canopy_width_cm)
        
        # 10. 计算健康指数
        health_index = self._calculate_health_index(image_resized, mask)
        
        # 11. 计算生长速率（基于历史记录）
        growth_rate = self._calculate_growth_rate()
        
        # 保存历史记录
        record = {
            'timestamp': datetime.now().isoformat(),
            'height_cm': height_cm,
            'canopy_width_cm': canopy_width_cm,
            'leaf_count': leaf_count,
            'health_index': health_index
        }
        self.history.append(record)
        
        # 限制历史记录大小
        if len(self.history) > 100:
            self.history.pop(0)
        
        return {
            'stage': growth_stage.value,
            'stage_code': growth_stage.name,
            'height_cm': round(height_cm, 2),
            'height_pixels': height_pixels,
            'canopy_width_cm': round(canopy_width_cm, 2),
            'canopy_area_cm2': round(canopy_area_cm2, 2),
            'leaf_count': leaf_count,
            'plant_area_pixels': int(plant_area),
            'health_index': round(health_index, 3),
            'growth_rate': growth_rate,
            'pixel_to_cm': round(self.pixel_to_cm, 4),
            'measurements': {
                'timestamp': datetime.now().isoformat(),
                'height_cm': round(height_cm, 2),
                'canopy_width_cm': round(canopy_width_cm, 2),
                'leaf_count': leaf_count
            },
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
        # 暂时使用模拟分析
        return self._analyze_simulation(image)
    
    def _calculate_height(self, contour: Any, mask: Any) -> int:
        """计算植株高度（像素）"""
        if not CV2_AVAILABLE:
            return 0
        
        # 获取边界矩形
        x, y, w, h = cv2.boundingRect(contour)
        
        # 使用凸包获取更准确的高度
        hull = cv2.convexHull(contour)
        hull_x, hull_y, hull_w, hull_h = cv2.boundingRect(hull)
        
        return max(h, hull_h)
    
    def _calculate_canopy(self, contour: Any) -> Tuple[int, int]:
        """计算冠幅（宽度，面积）"""
        if not CV2_AVAILABLE:
            return 0, 0
        
        # 获取最小外接矩形
        rect = cv2.minAreaRect(contour)
        (center), (width, height), angle = rect
        
        # 冠幅取较大维度
        canopy_width = max(width, height)
        canopy_area = cv2.contourArea(contour)
        
        return int(canopy_width), int(canopy_area)
    
    def _count_leaves(self, mask: Any, contours: List) -> int:
        """
        估算叶片数量
        
        使用轮廓层次和形状分析来估算
        """
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            return 0
        
        # 简化方法：基于轮廓数量和面积
        # 实际应用中需要使用专门的叶片检测模型
        
        leaf_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 500 < area < 50000:  # 过滤过小的轮廓
                # 检查形状因子（接近叶片的形状）
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    if 0.1 < circularity < 0.7:  # 叶片通常不是圆形
                        leaf_contours.append(contour)
        
        # 估算叶片数量
        return max(1, len(leaf_contours))
    
    def _find_reference_size(self, image: Any) -> float:
        """
        查找参照物大小（像素）
        
        实际应用中需要使用已知尺寸的参照物
        这里返回一个估算值
        """
        # 简化：返回图像高度的 1/10 作为估算
        return image.shape[0] / 10
    
    def _determine_growth_stage(
        self,
        height_cm: float,
        leaf_count: int,
        canopy_width_cm: float
    ) -> GrowthStage:
        """
        判断生长阶段
        
        基于株高、叶片数和冠幅进行判断
        """
        # 简化判断逻辑
        if height_cm < 10 and leaf_count < 5:
            return GrowthStage.SEEDLING
        elif height_cm < 30 and leaf_count < 15:
            return GrowthStage.VEGETATIVE
        elif canopy_width_cm < 20:
            return GrowthStage.FLOWERING
        elif height_cm > 50:
            return GrowthStage.RIPENING
        else:
            return GrowthStage.FRUITING
    
    def _calculate_health_index(
        self,
        image: Any,
        mask: Any
    ) -> float:
        """
        计算健康指数（0-1）
        
        基于颜色均匀性、叶片完整性等
        """
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            return 0.5
        
        try:
            # 1. 计算绿色区域的颜色均匀性
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            h_channel = hsv[:, :, 0]
            
            # 在植物区域内计算色调标准差
            plant_h = h_channel[mask > 0]
            if len(plant_h) > 0:
                h_std = np.std(plant_h)
                # 颜色越均匀，健康指数越高
                color_health = max(0, 1 - h_std / 50)
            else:
                color_health = 0.5
            
            # 2. 计算植物区域占比
            plant_ratio = np.count_nonzero(mask) / mask.size
            ratio_health = min(1, plant_ratio * 2)
            
            # 3. 综合健康指数
            health_index = (color_health * 0.6 + ratio_health * 0.4)
            
            return min(1, max(0, health_index))
            
        except Exception as e:
            logger.error(f"健康指数计算失败：{e}")
            return 0.5
    
    def _calculate_growth_rate(self) -> Dict[str, float]:
        """
        计算生长速率
        
        基于历史记录计算
        """
        if len(self.history) < 2:
            return {
                'height_rate': 0,
                'canopy_rate': 0,
                'leaf_rate': 0,
                'unit': 'cm/day'
            }
        
        # 获取最近两条记录
        recent = self.history[-1]
        previous = self.history[-2]
        
        # 计算时间差（天）
        try:
            recent_time = datetime.fromisoformat(recent['timestamp'])
            previous_time = datetime.fromisoformat(previous['timestamp'])
            days_diff = (recent_time - previous_time).total_seconds() / 86400
            
            if days_diff <= 0:
                days_diff = 1
        except:
            days_diff = 1
        
        # 计算生长速率
        height_rate = (recent['height_cm'] - previous['height_cm']) / days_diff
        canopy_rate = (recent['canopy_width_cm'] - previous['canopy_width_cm']) / days_diff
        leaf_rate = (recent['leaf_count'] - previous['leaf_count']) / days_diff
        
        return {
            'height_rate': round(height_rate, 3),
            'canopy_rate': round(canopy_rate, 3),
            'leaf_rate': round(leaf_rate, 3),
            'unit': 'per day'
        }
    
    def _get_empty_result(self, error_msg: str) -> Dict[str, Any]:
        """返回空结果"""
        return {
            'stage': '未知',
            'stage_code': 'unknown',
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }
    
    def calibrate(self, reference_pixels: float, reference_cm: float):
        """
        校准像素到厘米的换算
        
        Args:
            reference_pixels: 参照物像素尺寸
            reference_cm: 参照物实际尺寸 (cm)
        """
        self.pixel_to_cm = reference_cm / reference_pixels
        logger.info(f"校准完成：1 像素 = {self.pixel_to_cm:.4f} cm")
    
    def get_growth_trend(self, days: int = 7) -> Dict[str, Any]:
        """
        获取生长趋势
        
        Args:
            days: 获取最近几天的数据
            
        Returns:
            生长趋势数据
        """
        if not self.history:
            return {'error': '无历史记录'}
        
        # 筛选指定天数内的记录
        cutoff_time = datetime.now() - timedelta(days=days)
        filtered = []
        
        for record in self.history:
            try:
                record_time = datetime.fromisoformat(record['timestamp'])
                if record_time >= cutoff_time:
                    filtered.append(record)
            except:
                filtered.append(record)
        
        if not filtered:
            filtered = self.history
        
        # 计算趋势
        heights = [r['height_cm'] for r in filtered]
        canopy_widths = [r['canopy_width_cm'] for r in filtered]
        leaf_counts = [r['leaf_count'] for r in filtered]
        
        return {
            'period_days': days,
            'record_count': len(filtered),
            'height_trend': {
                'values': heights,
                'min': round(min(heights), 2) if heights else 0,
                'max': round(max(heights), 2) if heights else 0,
                'avg': round(sum(heights) / len(heights), 2) if heights else 0
            },
            'canopy_trend': {
                'values': canopy_widths,
                'min': round(min(canopy_widths), 2) if canopy_widths else 0,
                'max': round(max(canopy_widths), 2) if canopy_widths else 0,
                'avg': round(sum(canopy_widths) / len(canopy_widths), 2) if canopy_widths else 0
            },
            'leaf_trend': {
                'values': leaf_counts,
                'min': min(leaf_counts) if leaf_counts else 0,
                'max': max(leaf_counts) if leaf_counts else 0,
                'avg': round(sum(leaf_counts) / len(leaf_counts), 2) if leaf_counts else 0
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def clear_history(self):
        """清除历史记录"""
        self.history.clear()
        logger.info("生长历史记录已清除")