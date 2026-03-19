#!/usr/bin/env python3
"""
执行器控制模块

功能：
- 控制灌溉系统
- 控制补光系统
- 控制通风系统
- 控制遮阳系统
- 设备状态监控
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

# 尝试导入 RPi.GPIO
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("RPi.GPIO 不可用，使用模拟模式")

logger = logging.getLogger(__name__)


class DeviceState(Enum):
    """设备状态枚举"""
    OFF = "关闭"
    ON = "开启"
    AUTO = "自动"
    ERROR = "错误"


class ActuatorController:
    """执行器控制器类"""
    
    def __init__(
        self,
        irrigation_pin: int = 17,
        light_pin: int = 27,
        fan_pin: int = 22,
        shade_pin: int = 23,
        use_simulation: bool = True
    ):
        """
        初始化执行器控制器
        
        Args:
            irrigation_pin: 灌溉控制引脚
            light_pin: 补光控制引脚
            fan_pin: 通风控制引脚
            shade_pin: 遮阳控制引脚
            use_simulation: 是否使用模拟模式
        """
        self.irrigation_pin = irrigation_pin
        self.light_pin = light_pin
        self.fan_pin = fan_pin
        self.shade_pin = shade_pin
        self.use_simulation = use_simulation
        
        # 设备状态
        self.states: Dict[str, DeviceState] = {
            'irrigation': DeviceState.OFF,
            'light': DeviceState.OFF,
            'fan': DeviceState.OFF,
            'shade': DeviceState.OFF
        }
        
        # 设备运行时间记录
        self.runtime: Dict[str, float] = {
            'irrigation': 0,
            'light': 0,
            'fan': 0,
            'shade': 0
        }
        
        # 设备启动时间
        self._start_times: Dict[str, float] = {
            'irrigation': 0,
            'light': 0,
            'fan': 0,
            'shade': 0
        }
        
        # 初始化 GPIO
        if not self.use_simulation and GPIO_AVAILABLE:
            self._init_gpio()
    
    def _init_gpio(self):
        """初始化 GPIO"""
        try:
            GPIO.setmode(GPIO.BCM)
            
            # 设置输出引脚
            pins = [self.irrigation_pin, self.light_pin, self.fan_pin, self.shade_pin]
            for pin in pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
            
            logger.info("GPIO 执行器初始化完成")
            
        except Exception as e:
            logger.error(f"GPIO 初始化失败：{e}")
            self.use_simulation = True
    
    def set_irrigation(self, state: bool):
        """
        设置灌溉状态
        
        Args:
            state: True 开启，False 关闭
        """
        self._set_device_state('irrigation', state)
    
    def set_light(self, state: bool):
        """
        设置补光状态
        
        Args:
            state: True 开启，False 关闭
        """
        self._set_device_state('light', state)
    
    def set_fan(self, state: bool):
        """
        设置通风状态
        
        Args:
            state: True 开启，False 关闭
        """
        self._set_device_state('fan', state)
    
    def set_shade(self, state: bool):
        """
        设置遮阳状态
        
        Args:
            state: True 开启，False 关闭
        """
        self._set_device_state('shade', state)
    
    def _set_device_state(self, device: str, state: bool):
        """
        设置设备状态
        
        Args:
            device: 设备名称
            state: True 开启，False 关闭
        """
        current_state = self.states[device]
        new_state = DeviceState.ON if state else DeviceState.OFF
        
        if current_state == new_state:
            logger.debug(f"{device} 已经是{new_state.value}状态")
            return
        
        try:
            if self.use_simulation:
                self._simulate_control(device, state)
            else:
                self._hardware_control(device, state)
            
            # 更新状态
            self.states[device] = new_state
            
            # 更新运行时间记录
            if state:
                self._start_times[device] = time.time()
            else:
                if self._start_times[device] > 0:
                    self.runtime[device] += time.time() - self._start_times[device]
                    self._start_times[device] = 0
            
            logger.info(f"{device}已{ '开启' if state else '关闭'}")
            
        except Exception as e:
            logger.error(f"{device}控制失败：{e}")
            self.states[device] = DeviceState.ERROR
    
    def _hardware_control(self, device: str, state: bool):
        """硬件控制"""
        if not GPIO_AVAILABLE:
            raise RuntimeError("GPIO 不可用")
        
        pin_map = {
            'irrigation': self.irrigation_pin,
            'light': self.light_pin,
            'fan': self.fan_pin,
            'shade': self.shade_pin
        }
        
        pin = pin_map.get(device)
        if pin:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
    
    def _simulate_control(self, device: str, state: bool):
        """模拟控制"""
        # 模拟设备响应延迟
        time.sleep(0.1)
        logger.debug(f"模拟 {device} {'开启' if state else '关闭'}")
    
    def turn_off_all(self):
        """关闭所有设备"""
        logger.info("关闭所有设备...")
        
        for device in self.states:
            if self.states[device] == DeviceState.ON:
                self._set_device_state(device, False)
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取所有设备状态
        
        Returns:
            设备状态字典
        """
        status = {
            'devices': {},
            'total_runtime': {},
            'timestamp': datetime.now().isoformat()
        }
        
        for device, state in self.states.items():
            status['devices'][device] = {
                'state': state.value,
                'is_on': state == DeviceState.ON
            }
            
            # 计算当前运行时间
            runtime = self.runtime[device]
            if self._start_times[device] > 0:
                runtime += time.time() - self._start_times[device]
            
            status['total_runtime'][device] = round(runtime, 2)
        
        return status
    
    def get_device_status(self, device: str) -> Dict[str, Any]:
        """
        获取单个设备状态
        
        Args:
            device: 设备名称
            
        Returns:
            设备状态信息
        """
        state = self.states.get(device, DeviceState.OFF)
        
        # 计算当前运行时间
        runtime = self.runtime[device]
        if self._start_times[device] > 0:
            runtime += time.time() - self._start_times[device]
        
        return {
            'device': device,
            'state': state.value,
            'is_on': state == DeviceState.ON,
            'total_runtime_hours': round(runtime / 3600, 2),
            'pin': getattr(self, f'{device}_pin', None)
        }
    
    def set_auto_mode(self, device: str, conditions: Dict[str, Any]):
        """
        设置设备为自动模式
        
        Args:
            device: 设备名称
            conditions: 自动控制条件
        """
        self.states[device] = DeviceState.AUTO
        logger.info(f"{device}已设置为自动模式")
    
    def schedule_irrigation(self, duration_seconds: int, start_delay: int = 0):
        """
        计划灌溉
        
        Args:
            duration_seconds: 灌溉持续时间（秒）
            start_delay: 启动延迟（秒）
        """
        def irrigation_task():
            if start_delay > 0:
                time.sleep(start_delay)
            
            logger.info("开始灌溉...")
            self.set_irrigation(True)
            time.sleep(duration_seconds)
            self.set_irrigation(False)
            logger.info("灌溉完成")
        
        import threading
        thread = threading.Thread(target=irrigation_task, daemon=True)
        thread.start()
        
        return {'status': 'scheduled', 'duration': duration_seconds, 'delay': start_delay}
    
    def emergency_stop(self):
        """紧急停止所有设备"""
        logger.warning("紧急停止！")
        self.turn_off_all()
    
    def cleanup(self):
        """清理资源"""
        self.turn_off_all()
        
        if GPIO_AVAILABLE and not self.use_simulation:
            GPIO.cleanup()
            logger.info("GPIO 资源已清理")