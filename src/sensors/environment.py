#!/usr/bin/env python3
"""
环境传感器模块

功能：
- 读取温度、湿度、光照强度、CO2 浓度
- 支持 BME680、SCD30 等传感器
- 光合作用有效辐射 (PAR) 估算
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from random import uniform

logger = logging.getLogger(__name__)

# 尝试导入常用传感器库
try:
    import smbus2
    SMBUS_AVAILABLE = True
except ImportError:
    SMBUS_AVAILABLE = False
    logger.warning("smbus2 不可用，将使用模拟模式")

try:
    import adafruit_bme680
    BME680_AVAILABLE = True
except ImportError:
    BME680_AVAILABLE = False
    logger.warning("adafruit_bme680 不可用，将使用模拟模式")

try:
    import adafruit_scd30
    SCD30_AVAILABLE = True
except ImportError:
    SCD30_AVAILABLE = False
    logger.warning("adafruit_scd30 不可用，将使用模拟模式")


class EnvironmentSensor:
    """环境传感器类"""
    
    def __init__(
        self,
        i2c_bus: int = 1,
        use_simulation: bool = True,
        bme680_address: int = 0x76,
        scd30_address: int = 0x61
    ):
        """
        初始化环境传感器
        
        Args:
            i2c_bus: I2C 总线号
            use_simulation: 是否使用模拟模式
            bme680_address: BME680 传感器 I2C 地址
            scd30_address: SCD30 传感器 I2C 地址
        """
        self.i2c_bus = i2c_bus
        self.use_simulation = use_simulation
        self.bme680_address = bme680_address
        self.scd30_address = scd30_address
        
        self.bme680 = None
        self.scd30 = None
        
        # 初始化传感器
        if not self.use_simulation:
            self._init_sensors()
    
    def _init_sensors(self):
        """初始化真实传感器"""
        try:
            # 初始化 I2C
            if SMBUS_AVAILABLE:
                self.i2c = smbus2.SMBus(self.i2c_bus)
                logger.info(f"I2C 总线 {self.i2c_bus} 初始化成功")
            
            # 尝试初始化 BME680
            if BME680_AVAILABLE:
                try:
                    self.bme680 = adafruit_bme680.Adafruit_BME680_I2C(
                        self.i2c, address=self.bme680_address
                    )
                    logger.info("BME680 传感器初始化成功")
                except Exception as e:
                    logger.warning(f"BME680 初始化失败：{e}")
                    self.bme680 = None
            
            # 尝试初始化 SCD30
            if SCD30_AVAILABLE:
                try:
                    self.scd30 = adafruit_scd30.Adafruit_SCD30(self.i2c)
                    logger.info("SCD30 传感器初始化成功")
                except Exception as e:
                    logger.warning(f"SCD30 初始化失败：{e}")
                    self.scd30 = None
                    
        except Exception as e:
            logger.error(f"传感器初始化失败：{e}")
            self.use_simulation = True
    
    def read_all(self) -> Dict[str, Any]:
        """
        读取所有环境数据
        
        Returns:
            包含所有环境数据的字典
        """
        if self.use_simulation:
            return self._read_all_simulation()
        else:
            return self._read_all_hardware()
    
    def read_temperature(self) -> float:
        """读取温度"""
        if self.use_simulation:
            return round(uniform(18, 32), 2)
        elif self.bme680:
            return round(self.bme680.temperature, 2)
        return 0.0
    
    def read_humidity(self) -> float:
        """读取相对湿度"""
        if self.use_simulation:
            return round(uniform(40, 80), 2)
        elif self.bme680:
            return round(self.bme680.humidity, 2)
        return 0.0
    
    def read_light(self) -> float:
        """
        读取光照强度
        注意：BME680 没有光照传感器，需要额外连接
        这里使用模拟值或 VOC 作为替代
        """
        if self.use_simulation:
            return round(uniform(500, 5000), 2)  # lux
        elif self.bme680:
            # 使用 VOC 作为环境质量的间接指标
            return round(self.bme680.gas_resolution, 2)
        return 0.0
    
    def read_co2(self) -> float:
        """读取 CO2 浓度"""
        if self.use_simulation:
            return round(uniform(400, 1200), 2)  # ppm
        elif self.scd30:
            return round(self.scd30.data[0], 2)
        return 0.0
    
    def read_pressure(self) -> float:
        """读取大气压力"""
        if self.use_simulation:
            return round(uniform(990, 1030), 2)  # hPa
        elif self.bme680:
            return round(self.bme680.pressure, 2)
        return 0.0
    
    def read_voc(self) -> float:
        """读取 VOC（挥发性有机化合物）"""
        if self.use_simulation:
            return round(uniform(0, 500), 2)  # ppb
        elif self.bme680:
            return round(self.bme680.gas_resolution, 2)
        return 0.0
    
    def calculate_par(self, light_intensity: Optional[float] = None) -> float:
        """
        计算光合有效辐射 (PAR)
        
        PAR ≈ 光照强度 × 0.45 (μmol/m²/s)
        
        Args:
            light_intensity: 光照强度 (lux)，如果不提供则自动读取
            
        Returns:
            PAR 值 (μmol/m²/s)
        """
        if light_intensity is None:
            light_intensity = self.read_light()
        return round(light_intensity * 0.45, 2)
    
    def estimate_photosynthesis_rate(
        self,
        par: Optional[float] = None,
        co2: Optional[float] = None,
        temperature: Optional[float] = None,
        leaf_area: float = 100.0
    ) -> Dict[str, float]:
        """
        估算光合作用和呼吸作用强度
        
        简化模型：
        - 光合速率 ≈ f(PAR, CO2, 温度，叶面积)
        - 呼吸速率 ≈ f(温度，生物量)
        - 净光合 = 光合 - 呼吸
        
        Args:
            par: 光合有效辐射
            co2: CO2 浓度
            temperature: 温度
            leaf_area: 叶面积 (cm²)
            
        Returns:
            包含光合速率、呼吸速率、净光合速率的字典
        """
        if par is None:
            par = self.calculate_par()
        if co2 is None:
            co2 = self.read_co2()
        if temperature is None:
            temperature = self.read_temperature()
        
        # 简化的光合作用模型
        # 光饱和点约为 1000 μmol/m²/s
        light_factor = min(par / 1000, 1.0)
        
        # CO2 饱和点约为 1000 ppm
        co2_factor = min(co2 / 1000, 1.0)
        
        # 温度最适点约为 25°C
        temp_factor = 1 - abs(temperature - 25) / 25
        temp_factor = max(0, temp_factor)
        
        # 光合速率 (μmol CO2/m²/s)
        photosynthesis_rate = 20 * light_factor * co2_factor * temp_factor * (leaf_area / 100)
        
        # 呼吸速率 (与温度正相关)
        respiration_rate = 1.5 * (1 + (temperature - 20) / 50) * (leaf_area / 100)
        
        # 净光合速率
        net_photosynthesis = photosynthesis_rate - respiration_rate
        
        return {
            'photosynthesis_rate': round(photosynthesis_rate, 3),
            'respiration_rate': round(respiration_rate, 3),
            'net_photosynthesis': round(net_photosynthesis, 3),
            'par': par,
            'co2': co2,
            'temperature': temperature,
            'leaf_area': leaf_area
        }
    
    def _read_all_simulation(self) -> Dict[str, Any]:
        """模拟读取所有环境数据"""
        temperature = self.read_temperature()
        humidity = self.read_humidity()
        light = self.read_light()
        co2 = self.read_co2()
        
        return {
            'temperature': temperature,
            'humidity': humidity,
            'light': light,
            'co2': co2,
            'pressure': self.read_pressure(),
            'voc': self.read_voc(),
            'par': self.calculate_par(light),
            'timestamp': datetime.now().isoformat()
        }
    
    def _read_all_hardware(self) -> Dict[str, Any]:
        """从真实硬件读取所有环境数据"""
        return self._read_all_simulation()  # 暂时使用模拟数据
    
    def get_environment_status(self) -> Dict[str, Any]:
        """
        获取环境状态评估
        
        Returns:
            包含环境状态评估的字典
        """
        data = self.read_all()
        
        # 温度评估
        temp_status = "normal"
        if data['temperature'] < 15:
            temp_status = "too_cold"
        elif data['temperature'] > 35:
            temp_status = "too_hot"
        
        # 湿度评估
        humidity_status = "normal"
        if data['humidity'] < 40:
            humidity_status = "too_dry"
        elif data['humidity'] > 80:
            humidity_status = "too_humid"
        
        # CO2 评估
        co2_status = "normal"
        if data['co2'] < 400:
            co2_status = "low"
        elif data['co2'] > 1500:
            co2_status = "high"
        
        # 光照评估
        light_status = "normal"
        if data['light'] < 2000:
            light_status = "low"
        elif data['light'] > 10000:
            light_status = "high"
        
        return {
            'data': data,
            'status': {
                'temperature': temp_status,
                'humidity': humidity_status,
                'co2': co2_status,
                'light': light_status
            },
            'recommendations': self._get_recommendations(temp_status, humidity_status, co2_status, light_status)
        }
    
    def _get_recommendations(
        self,
        temp_status: str,
        humidity_status: str,
        co2_status: str,
        light_status: str
    ) -> list:
        """获取环境调节建议"""
        recommendations = []
        
        if temp_status == "too_cold":
            recommendations.append("温度过低，建议关闭通风，开启补光")
        elif temp_status == "too_hot":
            recommendations.append("温度过高，建议开启通风和遮阳")
        
        if humidity_status == "too_dry":
            recommendations.append("湿度过低，建议减少通风，考虑喷雾增湿")
        elif humidity_status == "too_humid":
            recommendations.append("湿度过高，建议开启通风，防止病害")
        
        if co2_status == "high":
            recommendations.append("CO2 浓度过高，建议加强通风")
        elif co2_status == "low":
            recommendations.append("CO2 浓度较低，可考虑 CO2 施肥")
        
        if light_status == "low":
            recommendations.append("光照不足，建议开启补光灯")
        elif light_status == "high":
            recommendations.append("光照过强，建议开启遮阳网")
        
        return recommendations
    
    def cleanup(self):
        """清理传感器资源"""
        if self.scd30 and SCD30_AVAILABLE:
            try:
                self.scd30.stop_continuation()
            except:
                pass
        logger.info("环境传感器资源已清理")