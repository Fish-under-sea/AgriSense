#!/usr/bin/env python3
"""
摄像头传感器模块

功能：
- 控制摄像头拍摄
- 支持 RGB 和红外/多光谱摄像头
- 图像预处理
- 图像保存
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# 尝试导入常用摄像头库
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV 不可用，将使用模拟模式")

try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    logger.warning("picamera2 不可用，将使用模拟模式")


class CameraSensor:
    """摄像头传感器类"""
    
    def __init__(
        self,
        camera_id: int = 0,
        resolution: Tuple[int, int] = (640, 480),
        fps: int = 30,
        use_simulation: bool = True,
        save_path: str = 'captures/'
    ):
        """
        初始化摄像头
        
        Args:
            camera_id: 摄像头 ID（0 表示默认摄像头）
            resolution: 图像分辨率 (width, height)
            fps: 帧率
            use_simulation: 是否使用模拟模式
            save_path: 图像保存路径
        """
        self.camera_id = camera_id
        self.resolution = resolution
        self.fps = fps
        self.use_simulation = use_simulation
        self.save_path = save_path
        
        self.camera = None
        self.cap = None
        
        # 创建保存目录
        os.makedirs(save_path, exist_ok=True)
        
        # 初始化摄像头
        if not self.use_simulation:
            self._init_camera()
    
    def _init_camera(self):
        """初始化真实摄像头"""
        try:
            # 尝试使用 Picamera2（树莓派专用）
            if PICAMERA_AVAILABLE:
                self.camera = Picamera2()
                config = self.camera.create_preview_configuration(
                    main={"size": self.resolution}
                )
                self.camera.configure(config)
                self.camera.start()
                logger.info(f"Picamera2 初始化成功 - 分辨率：{self.resolution}")
                return
            
            # 尝试使用 OpenCV
            if CV2_AVAILABLE:
                self.cap = cv2.VideoCapture(self.camera_id)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                
                if self.cap.isOpened():
                    logger.info(f"OpenCV 摄像头初始化成功 - ID: {self.camera_id}")
                else:
                    logger.warning("OpenCV 摄像头打开失败，切换到模拟模式")
                    self.use_simulation = True
                    
        except Exception as e:
            logger.error(f"摄像头初始化失败：{e}")
            self.use_simulation = True
    
    def capture(self, save: bool = False, prefix: str = 'capture') -> Optional[Any]:
        """
        捕获图像
        
        Args:
            save: 是否保存图像到文件
            prefix: 保存文件的前缀
            
        Returns:
            图像数据（numpy array 或模拟数据）
        """
        if self.use_simulation:
            return self._capture_simulation()
        else:
            return self._capture_hardware(save, prefix)
    
    def _capture_simulation(self) -> Any:
        """
        模拟捕获图像
        
        Returns:
            模拟的图像数据（随机生成的 numpy 数组）
        """
        if not CV2_AVAILABLE:
            # 如果没有 OpenCV，返回 None 表示模拟失败
            return None
        
        import numpy as np
        # 生成随机图像作为模拟
        image = np.random.randint(0, 256, 
                                   (self.resolution[1], self.resolution[0], 3),
                                   dtype=np.uint8)
        return image
    
    def _capture_hardware(self, save: bool, prefix: str) -> Optional[Any]:
        """
        从真实硬件捕获图像
        
        Args:
            save: 是否保存图像
            prefix: 保存文件的前缀
            
        Returns:
            捕获的图像数据
        """
        image = None
        
        try:
            # 使用 Picamera2
            if self.camera and PICAMERA_AVAILABLE:
                image = self.camera.capture_array()
            
            # 使用 OpenCV
            elif self.cap and CV2_AVAILABLE:
                ret, frame = self.cap.read()
                if ret:
                    # OpenCV 读取的是 BGR 格式，转换为 RGB
                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 保存图像
            if save and image is not None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{self.save_path}{prefix}_{timestamp}.jpg"
                
                if CV2_AVAILABLE:
                    # 转换回 BGR 格式保存
                    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(filename, image_bgr)
                else:
                    import numpy as np
                    from PIL import Image
                    pil_image = Image.fromarray(image)
                    pil_image.save(filename)
                
                logger.info(f"图像已保存：{filename}")
            
            return image
            
        except Exception as e:
            logger.error(f"图像捕获失败：{e}")
            return None
    
    def capture_multi_angle(self) -> Dict[str, Any]:
        """
        从多个角度捕获图像（顶部和侧面）
        
        Returns:
            包含多个角度图像的字典
        """
        results = {}
        
        # 顶部视角
        results['top'] = self.capture(save=True, prefix='top')
        
        # 侧面视角（如果有第二个摄像头）
        if hasattr(self, 'side_camera') and self.side_camera:
            results['side'] = self.side_camera.capture(save=True, prefix='side')
        else:
            # 模拟侧面视角（使用顶部图像）
            results['side'] = results['top']
        
        return results
    
    def capture_for_analysis(self) -> Dict[str, Any]:
        """
        捕获用于分析的图像（包括 RGB 和红外）
        
        Returns:
            包含 RGB 和红外图像的字典
        """
        results = {
            'rgb': self.capture(save=True, prefix='rgb'),
            'timestamp': datetime.now().isoformat()
        }
        
        # 如果有红外摄像头
        if hasattr(self, 'ir_camera') and self.ir_camera:
            results['ir'] = self.ir_camera.capture(save=True, prefix='ir')
        else:
            results['ir'] = None
        
        return results
    
    def start_preview(self):
        """启动实时预览"""
        if self.use_simulation:
            logger.info("模拟模式不支持预览")
            return
        
        try:
            if self.camera and PICAMERA_AVAILABLE:
                self.camera.start_preview()
                logger.info("预览已启动")
            elif self.cap and CV2_AVAILABLE:
                logger.info("使用 OpenCV 预览...")
                while True:
                    ret, frame = self.cap.read()
                    if ret:
                        cv2.imshow('AgriSense Camera', frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    else:
                        break
                self.cap.release()
                cv2.destroyAllWindows()
        except Exception as e:
            logger.error(f"预览启动失败：{e}")
    
    def preprocess_image(self, image: Any) -> Optional[Any]:
        """
        图像预处理
        
        Args:
            image: 原始图像
            
        Returns:
            预处理后的图像
        """
        if not CV2_AVAILABLE or image is None:
            return image
        
        try:
            # 1. 调整大小
            image = cv2.resize(image, self.resolution)
            
            # 2. 高斯模糊去噪
            image = cv2.GaussianBlur(image, (5, 5), 0)
            
            # 3. 颜色空间转换（用于后续分析）
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            
            return {
                'rgb': image,
                'hsv': hsv,
                'lab': lab
            }
        except Exception as e:
            logger.error(f"图像预处理失败：{e}")
            return None
    
    def get_camera_info(self) -> Dict[str, Any]:
        """获取摄像头信息"""
        info = {
            'camera_id': self.camera_id,
            'resolution': self.resolution,
            'fps': self.fps,
            'use_simulation': self.use_simulation,
            'save_path': self.save_path,
            'picamera_available': PICAMERA_AVAILABLE,
            'opencv_available': CV2_AVAILABLE
        }
        
        if self.cap and CV2_AVAILABLE:
            info['backend'] = 'OpenCV'
            info['is_opened'] = self.cap.isOpened()
        elif self.camera and PICAMERA_AVAILABLE:
            info['backend'] = 'Picamera2'
            info['is_running'] = True
        else:
            info['backend'] = 'Simulation'
        
        return info
    
    def cleanup(self):
        """清理摄像头资源"""
        if self.camera and PICAMERA_AVAILABLE:
            try:
                self.camera.stop()
            except:
                pass
        
        if self.cap and CV2_AVAILABLE:
            self.cap.release()
            cv2.destroyAllWindows()
        
        logger.info("摄像头资源已清理")


class MultiCameraSystem:
    """多摄像头系统（支持 RGB 和红外/多光谱）"""
    
    def __init__(
        self,
        rgb_camera_id: int = 0,
        ir_camera_id: int = 1,
        resolution: Tuple[int, int] = (640, 480),
        use_simulation: bool = True
    ):
        """
        初始化多摄像头系统
        
        Args:
            rgb_camera_id: RGB 摄像头 ID
            ir_camera_id: 红外摄像头 ID
            resolution: 图像分辨率
            use_simulation: 是否使用模拟模式
        """
        self.rgb_camera = CameraSensor(
            camera_id=rgb_camera_id,
            resolution=resolution,
            use_simulation=use_simulation
        )
        
        self.ir_camera = CameraSensor(
            camera_id=ir_camera_id,
            resolution=resolution,
            use_simulation=use_simulation
        )
        
        logger.info("多摄像头系统初始化完成")
    
    def capture_synchronized(self) -> Dict[str, Any]:
        """
        同步捕获 RGB 和红外图像
        
        Returns:
            包含同步图像的字典
        """
        rgb_image = self.rgb_camera.capture()
        ir_image = self.ir_camera.capture()
        
        return {
            'rgb': rgb_image,
            'ir': ir_image,
            'timestamp': datetime.now().isoformat(),
            'synchronized': True
        }
    
    def calculate_ndvi(self, rgb_image: Any, ir_image: Any) -> Optional[Any]:
        """
        计算 NDVI（归一化植被指数）
        
        NDVI = (IR - R) / (IR + R)
        
        Args:
            rgb_image: RGB 图像
            ir_image: 红外图像
            
        Returns:
            NDVI 图像
        """
        if not CV2_AVAILABLE or rgb_image is None or ir_image is None:
            return None
        
        try:
            import numpy as np
            
            # 提取红色通道
            r_channel = rgb_image[:, :, 2].astype(np.float32)
            
            # 红外图像
            ir_channel = ir_image.astype(np.float32)
            
            # 计算 NDVI
            ndvi = (ir_channel - r_channel) / (ir_channel + r_channel + 1e-6)
            
            # 归一化到 0-255
            ndvi_normalized = ((ndvi + 1) / 2 * 255).astype(np.uint8)
            
            return ndvi_normalized
            
        except Exception as e:
            logger.error(f"NDVI 计算失败：{e}")
            return None
    
    def cleanup(self):
        """清理所有摄像头资源"""
        self.rgb_camera.cleanup()
        self.ir_camera.cleanup()