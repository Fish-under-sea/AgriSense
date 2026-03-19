#!/usr/bin/env python3
"""
土壤湿度传感器模块

功能：
- 读取土壤湿度值（支持多个点位）
- 湿度阈值判断
- 模拟/真实硬件支持
"""

import logging
from typing import Dict, Any, Optional
from random import uniform

# 尝试导入 RPi.GPIO，如果不可用则使用模拟模式
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("RPi.GPIO 不可用，使用模拟模式")

logger = logging.getLogger(__name__)


class SoilMoistureSensor:
    """土壤湿度传感器类"""
    
    def __init__(
        self,
        pin: int = 4,
        threshold_low: float = 30.0,
        threshold_high: float = 70.0,
        use_simulation: bool = True
    ):
        """
        初始化土壤湿度传感器
        
        Args:
            pin: GPIO 引脚号（ADC 传感器连接）
            threshold_low: 低湿度阈值（低于此值启动灌溉）
            threshold_high: 高湿度阈值（高于此值停止灌溉）
            use_simulation: 是否使用模拟模式
        """
        self.pin = pin
        self.threshold_low = threshold_low
        self.threshold_high = threshold_high
        self.use_simulation = use_simulation or not GPIO_AVAILABLE
        
        # 模拟数据缓存
        self._sim_data: Dict[int, float] = {}
        
        # 初始化 GPIO（如果使用真实硬件）
        if not self.use_simulation and GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            # 注意：ADC 传感器可能需要不同的配置
            # 这里假设使用模拟 - 数字转换器
            logger.info(f"土壤湿度传感器初始化 - 引脚：{pin}")
    
    def read_moisture(self, point_id: int = 0) -> Dict[str, Any]:
        """
        读取指定点位的土壤湿度
        
        Args:
            point_id: 传感器点位 ID（0-2，对应 3 个点位）
            
        Returns:
            包含湿度数据的字典
        """
        if self.use_simulation:
            moisture_value = self._read_simulation(point_id)
        else:
            moisture_value = self._read_hardware(point_id)
        
        # 判断状态
        status = self._determine_status(moisture_value)
        
        result = {
            'point_id': point_id,
            'moisture': moisture_value,
            'status': status,
            'timestamp': self._get_timestamp()
        }
        
        logger.debug(f"土壤湿度 - 点位{point_id}: {moisture_value}% - {status}")
        return result
    
    def _read_simulation(self, point_id: int) -> float:
        """
        模拟读取土壤湿度
        
        Args:
            point_id: 传感器点位 ID
            
        Returns:
            模拟的湿度值（0-100）
        """
        # 为不同点位生成略有差异的数据
        base_value = uniform(25, 75)
        variation = uniform(-5, 5) * point_id
        return round(max(0, min(100, base_value + variation)), 2)
    
    def _read_hardware(self, point_id: int) -> float:
        """
        从真实硬件读取土壤湿度
        
        Args:
            point_id: 传感器点位 ID
            
        Returns:
            湿度值（0-100）
        """
        # TODO: 实现真实硬件读取
        # 根据实际使用的 ADC 传感器类型实现
        # 例如：MCP3008 通过 SPI 读取
        
        if not GPIO_AVAILABLE:
            raise RuntimeError("RPi.GPIO 不可用，无法读取硬件")
        
        # 示例：使用 MCP3008 ADC
        # from spidev import SpiDev
        # spi = SpiDev()
        # spi.open(0, 0)
        # adc_value = spi.xfer2([1, (8 + channel) << 4, 0])
        # moisture = (adc_value[1] << 8) + adc_value[2]
        # moisture_percent = 100 - (moisture / 1023 * 100)
        
        raise NotImplementedError("真实硬件读取尚未实现")
    
    def _determine_status(self, moisture: float) -> str:
        """
        根据湿度值判断状态
        
        Args:
            moisture: 湿度值（0-100）
            
        Returns:
            状态字符串
        """
        if moisture < self.threshold_low:
            return "dry"  # 干燥，需要灌溉
        elif moisture > self.threshold_high:
            return "wet"  # 湿润，可能过湿
        else:
            return "optimal"  # 最佳状态
    
    def should_irrigate(self, point_id: int = 0) -> bool:
        """
        判断是否需要灌溉
        
        Args:
            point_id: 传感器点位 ID
            
        Returns:
            需要灌溉返回 True
        """
        result = self.read_moisture(point_id)
        return result['status'] == 'dry'
    
    def get_average_moisture(self) -> float:
        """
        获取所有点位的平均湿度
        
        Returns:
            平均湿度值
        """
        total = 0
        count = 0
        for i in range(3):
            result = self.read_moisture(i)
            total += result['moisture']
            count += 1
        return round(total / count, 2) if count > 0 else 0
    
    def read_all(self) -> Dict[str, Any]:
        """
        读取所有点位的土壤湿度
        
        Returns:
            包含所有点位数据的字典
        """
        return {
            'points': [self.read_moisture(i) for i in range(3)],
            'average': self.get_average_moisture(),
            'timestamp': self._get_timestamp()
        }
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def calibrate(self, dry_value: float = 0, wet_value: float = 100):
        """
        校准传感器
        
        Args:
            dry_value: 干燥时的基准值
            wet_value: 湿润时的基准值
        """
        # TODO: 实现校准逻辑
        logger.info(f"传感器校准 - 干燥：{dry_value}, 湿润：{wet_value}")
    
    def cleanup(self):
        """清理 GPIO 资源"""
        if GPIO_AVAILABLE and not self.use_simulation:
            GPIO.cleanup()
            logger.info("土壤湿度传感器资源已清理")