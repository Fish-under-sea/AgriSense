#!/usr/bin/env python3
"""
LLM 智能顾问模块

功能：
- 基于 LLM 的农业咨询
- 生长建议生成
- 每日报告生成
- 异常情况分析
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# 尝试导入常用库
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests 不可用")

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("ollama 库不可用，将使用 requests 直接调用")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class LLMAdvisor:
    """LLM 智能顾问类"""
    
    # 系统提示词模板 - 基础农业顾问
    SYSTEM_PROMPT = """你是一位专业的农业专家顾问，专注于智能大棚的作物管理。
请根据提供的传感器数据和作物状态，给出专业的农业管理建议。

【重要要求】
- 每条建议控制在 30 字以内
- 简洁明了，直击要点
- 使用短句，避免冗长

你的建议应该包括：
1. 环境调控建议（温度、湿度、光照、CO2）
2. 水肥管理建议
3. 病虫害防治建议
4. 生长促进建议"""
    
    # 对话式 AI 顾问提示词 - 具有自我认知的农业 AI
    CONVERSATIONAL_SYSTEM_PROMPT = """你是 AgriSense AI，一个专门服务于智能农业大棚的 AI 助手。

【你的自我认知】
- 你的名字是：AgriSense AI
- 你是一个专注于农业领域的 AI 助手
- 你服务于智能大棚管理系统，帮助用户管理作物生长
- 你运行在用户的本地计算机上
- 你只在这个 AgriSense 系统中存在，是你的专属农业顾问

【你的能力】
- 分析环境传感器数据（温度、湿度、光照、CO2）
- 分析土壤数据（土壤湿度、EC 值、pH 值）
- 分析作物健康状况（叶片病害检测、生长监测）
- 提供专业的农业管理建议
- 回答农业相关问题

【你的性格】
- 专业但友好
- 耐心细致
- 用通俗易懂的语言解释专业问题
- 会主动关心作物健康状况

【回答格式】
请用自然对话的方式回答，不要使用过于技术化的语言。如果用户问的是数据相关的问题，先分析数据再给出建议。"""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        api_key: str = "",
        base_url: str = "https://free.v36.cm/v1",
        use_simulation: bool = True,
        models_config: dict = None
    ):
        """
        初始化 LLM 顾问
        
        Args:
            model_name: 模型名称（配置中的 key）
            api_key: API 密钥
            base_url: API 基础 URL
            use_simulation: 是否使用模拟模式
            models_config: 多模型配置字典
        """
        self.current_model_key = model_name
        self.models_config = models_config or {}
        self.use_simulation = use_simulation
        
        # 获取当前模型配置
        self._update_current_model()
        
        self.client = None
        self._init_client()
    
    def _update_current_model(self):
        """更新当前模型配置"""
        model_config = self.models_config.get(self.current_model_key, {})
        self.model_name = model_config.get('model', self.current_model_key)
        self.api_key = model_config.get('api_key', '')
        self.base_url = model_config.get('base_url', 'http://localhost:11434')
        self.provider = model_config.get('provider', 'ollama')
        self.model_display_name = model_config.get('name', self.model_name)
    
    def get_available_models(self) -> dict:
        """获取可用模型列表"""
        return {
            key: {
                'name': config.get('name', key),
                'provider': config.get('provider', 'unknown'),
                'model': config.get('model', ''),
                'enabled': config.get('enabled', True)
            }
            for key, config in self.models_config.items()
        }
    
    def switch_model(self, model_key: str) -> bool:
        """
        切换模型
        
        Args:
            model_key: 模型配置 key
            
        Returns:
            是否切换成功
        """
        if model_key not in self.models_config:
            return False
        
        self.current_model_key = model_key
        self._update_current_model()
        self._init_client()
        
        logger.info(f"模型已切换到：{self.model_display_name} ({self.model_name})")
        return True
    
    def get_model_info(self) -> dict:
        """获取当前模型信息"""
        return {
            'key': self.current_model_key,
            'name': self.model_display_name,
            'model': self.model_name,
            'provider': self.provider,
            'base_url': self.base_url,
            'simulation_mode': self.use_simulation
        }
    
    def _init_client(self):
        """初始化 LLM 客户端"""
        try:
            # 根据 provider 类型选择客户端
            if self.provider == 'ollama':
                # 尝试使用 Ollama，但先检测服务是否可用
                if OLLAMA_AVAILABLE and REQUESTS_AVAILABLE:
                    # 检测 Ollama 服务是否运行
                    try:
                        test_response = requests.get(f"{self.base_url}/api/tags", timeout=2)
                        if test_response.status_code == 200:
                            self.client = ollama
                            logger.info("Ollama 客户端已初始化")
                            return
                        else:
                            logger.warning(f"Ollama 服务不可用 (状态码：{test_response.status_code})，使用 requests 直接调用")
                    except Exception as e:
                        logger.warning(f"Ollama 服务未运行：{e}，使用 requests 直接调用")
                    
                    # Ollama 服务不可用，使用 requests
                    logger.info("使用 requests 调用 Ollama API")
                    return
                
                # Ollama 库不可用，使用 requests
                if REQUESTS_AVAILABLE:
                    logger.info("使用 requests 调用 Ollama API")
                    return
                
            elif self.provider == 'openai':
                # 尝试使用 OpenAI 兼容 API
                if OPENAI_AVAILABLE and self.api_key:
                    # 检测 OpenAI 服务是否可用
                    try:
                        test_response = requests.get(f"{self.base_url}/models", timeout=2)
                        if test_response.status_code == 200:
                            self.client = OpenAI(
                                api_key=self.api_key,
                                base_url=self.base_url
                            )
                            logger.info("OpenAI 客户端已初始化")
                            return
                        else:
                            logger.warning(f"OpenAI 服务不可用 (状态码：{test_response.status_code})，使用 requests 直接调用")
                    except Exception as e:
                        logger.warning(f"OpenAI 服务检测失败：{e}，使用 requests 直接调用")
                    
                    # 使用 requests
                    logger.info("使用 requests 调用 OpenAI API")
                    return
                
                # OpenAI 库不可用，使用 requests
                if REQUESTS_AVAILABLE:
                    logger.info("使用 requests 调用 OpenAI API")
                    return
            
            logger.warning("无法初始化 LLM 客户端，使用模拟模式")
            self.use_simulation = True
            
        except Exception as e:
            logger.error(f"初始化 LLM 客户端失败：{e}")
            self.use_simulation = True
    
    def get_advice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取 LLM 建议
        
        Args:
            data: 传感器数据（可以是真实数据或模拟数据）
            
        Returns:
            建议字典
        """
        # 无论是否模拟模式，都调用 AI 进行分析
        # 模拟模式下传入的是模拟数据，但分析由真实 AI 完成
        return self._get_llm_advice(data)
    
    def _get_simulation_advice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成模拟建议
        
        Args:
            data: 传感器数据
            
        Returns:
            模拟建议
        """
        advice = {
            'summary': '',
            'recommendations': [],
            'alerts': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # 基于数据生成建议
        env_data = data.get('environment', {})
        soil_data = data.get('soil', {})
        vision_data = data.get('vision', {})
        
        # 温度建议
        temp = env_data.get('temperature', 25)
        if temp < 18:
            advice['recommendations'].append("温度偏低，建议关闭通风，适当补光增温")
        elif temp > 32:
            advice['recommendations'].append("温度偏高，建议开启通风，必要时遮阳降温")
        else:
            advice['recommendations'].append(f"温度适宜 ({temp:.1f}°C)，保持当前管理")
        
        # 湿度建议
        humidity = env_data.get('humidity', 60)
        if humidity < 45:
            advice['recommendations'].append("湿度偏低，建议减少通风，考虑喷雾增湿")
        elif humidity > 75:
            advice['recommendations'].append("湿度偏高，建议加强通风，预防病害")
        
        # 土壤湿度建议
        if soil_data:
            moistures = []
            for key, value in soil_data.items():
                if isinstance(value, dict):
                    moistures.append(value.get('moisture', 50))
            
            if moistures:
                avg = sum(moistures) / len(moistures)
                if avg < 35:
                    advice['recommendations'].append(f"土壤偏干 (平均{avg:.1f}%)，建议及时灌溉")
                elif avg > 65:
                    advice['recommendations'].append(f"土壤偏湿 (平均{avg:.1f}%)，暂停灌溉")
        
        # 叶片健康建议
        leaf_health = vision_data.get('leaf_health', {})
        if leaf_health:
            health_score = leaf_health.get('health_score', 100)
            if health_score < 70:
                disease = leaf_health.get('disease_type', '病害')
                advice['alerts'].append(f"发现{disease}，健康评分{health_score}，建议及时防治")
                recommendations = leaf_health.get('recommendations', [])
                advice['recommendations'].extend(recommendations[:2])
        
        # 生成总结
        advice['summary'] = self._generate_summary(advice['recommendations'], advice['alerts'])
        
        return advice
    
    def _get_llm_advice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 LLM 获取建议
        
        Args:
            data: 传感器数据
            
        Returns:
            LLM 建议
        """
        try:
            # 构建用户提示
            user_prompt = self._build_prompt(data)
            
            # 调用 LLM
            if OLLAMA_AVAILABLE and self.client:
                response = self.client.chat(
                    model=self.model_name,
                    messages=[
                        {'role': 'system', 'content': self.SYSTEM_PROMPT},
                        {'role': 'user', 'content': user_prompt}
                    ]
                )
                content = response['message']['content']
            
            elif OPENAI_AVAILABLE and self.client:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {'role': 'system', 'content': self.SYSTEM_PROMPT},
                        {'role': 'user', 'content': user_prompt}
                    ]
                )
                content = response.choices[0].message.content
            
            else:
                # 使用 requests 调用，根据 provider 选择正确的 API
                if self.provider == 'ollama':
                    content = self._call_ollama_advice_api(user_prompt)
                else:
                    # OpenAI 兼容 API
                    content = self._call_openai_advice_api(user_prompt)
            
            # 解析响应
            return self._parse_response(content)
            
        except Exception as e:
            logger.error(f"LLM 建议获取失败：{e}")
            return self._get_simulation_advice(data)
    
    def _build_prompt(self, data: Dict[str, Any]) -> str:
        """构建提示词"""
        prompt = "当前大棚状态数据如下：\n\n"
        
        # 环境数据
        env = data.get('environment', {})
        if env:
            prompt += "【环境数据】\n"
            prompt += f"- 温度：{env.get('temperature', 'N/A')}°C\n"
            prompt += f"- 湿度：{env.get('humidity', 'N/A')}%\n"
            prompt += f"- 光照：{env.get('light_intensity', 'N/A')} lux\n"
            prompt += f"- CO2: {env.get('co2', 'N/A')} ppm\n"
            prompt += "\n"
        
        # 土壤数据
        soil = data.get('soil', {})
        if soil:
            prompt += "【土壤数据】\n"
            for key, value in soil.items():
                if isinstance(value, dict):
                    prompt += f"- {key}: {value.get('moisture', 'N/A')}%\n"
            prompt += "\n"
        
        # 视觉数据
        vision = data.get('vision', {})
        if vision:
            leaf = vision.get('leaf_health', {})
            if leaf:
                prompt += "【作物健康】\n"
                prompt += f"- 病害类型：{leaf.get('disease_type', 'N/A')}\n"
                prompt += f"- 健康评分：{leaf.get('health_score', 'N/A')}\n"
                prompt += "\n"
        
        prompt += "请根据以上数据，给出专业的农业管理建议。"
        
        return prompt
    
    def _call_api(self, prompt: str) -> str:
        """调用 LLM API"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "system": self.SYSTEM_PROMPT,
                    "stream": False
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            logger.error(f"API 调用失败：{e}")
            raise
    
    def _call_ollama_advice_api(self, prompt: str) -> str:
        """调用 Ollama API 获取建议"""
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_name,
                "prompt": prompt,
                "system": self.SYSTEM_PROMPT,
                "stream": False
            },
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response.raise_for_status()
        return response.json()['response']
    
    def _call_openai_advice_api(self, prompt: str) -> str:
        """调用 OpenAI 兼容 API 获取建议"""
        url = f"{self.base_url}/chat/completions"
        logger.info(f"调用 OpenAI API: {url}, 模型：{self.model_name}")
        
        response = requests.post(
            url,
            json={
                "model": self.model_name,
                "messages": [
                    {'role': 'system', 'content': self.SYSTEM_PROMPT},
                    {'role': 'user', 'content': prompt}
                ]
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            timeout=120
        )
        
        if response.status_code != 200:
            logger.error(f"API 响应状态码：{response.status_code}")
            logger.error(f"API 响应内容：{response.text}")
            raise Exception(f"API 调用失败：{response.status_code} {response.text}")
        
        data = response.json()
        return data['choices'][0]['message']['content']
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """解析 LLM 响应"""
        return {
            'summary': content,
            'recommendations': [content],  # 简化处理
            'alerts': [],
            'raw_response': content,
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_summary(self, recommendations: List[str], alerts: List[str]) -> str:
        """生成总结"""
        summary_parts = []
        
        if alerts:
            summary_parts.append(f"⚠️ 发现 {len(alerts)} 个需要注意的问题")
        
        if recommendations:
            summary_parts.append(f"💡 共有 {len(recommendations)} 条管理建议")
        
        if not summary_parts:
            return "✅ 当前状态良好，继续保持"
        
        return "；".join(summary_parts)
    
    def get_daily_summary(self, history: List[Dict[str, Any]]) -> str:
        """
        生成每日总结
        
        Args:
            history: 历史数据列表
            
        Returns:
            每日总结文本
        """
        if not history:
            return "暂无数据"
        
        if self.use_simulation:
            return self._generate_simulation_summary(history)
        else:
            return self._generate_llm_summary(history)
    
    def _generate_simulation_summary(self, history: List[Dict[str, Any]]) -> str:
        """生成模拟每日总结"""
        # 计算统计数据
        temps = [d.get('environment', {}).get('temperature', 0) for d in history]
        humidities = [d.get('environment', {}).get('humidity', 0) for d in history]
        soil_moistures = []
        
        for d in history:
            soil = d.get('soil', {})
            for key, value in soil.items():
                if isinstance(value, dict):
                    soil_moistures.append(value.get('moisture', 0))
        
        avg_temp = sum(temps) / len(temps) if temps else 0
        avg_humidity = sum(humidities) / len(humidities) if humidities else 0
        avg_soil = sum(soil_moistures) / len(soil_moistures) if soil_moistures else 0
        
        # 生成总结
        summary = f"""
今日环境概况：
- 平均温度：{avg_temp:.1f}°C（{'适宜' if 18 <= avg_temp <= 30 else '需调节'}）
- 平均湿度：{avg_humidity:.1f}%（{'适宜' if 45 <= avg_humidity <= 75 else '需调节'}）
- 平均土壤湿度：{avg_soil:.1f}%（{'适宜' if 35 <= avg_soil <= 65 else '需调节'}）

"""
        
        # 添加建议
        if avg_temp < 18:
            summary += "• 温度偏低，建议加强保温措施\n"
        elif avg_temp > 30:
            summary += "• 温度偏高，建议加强通风降温\n"
        
        if avg_humidity < 45:
            summary += "• 湿度偏低，考虑喷雾增湿\n"
        elif avg_humidity > 75:
            summary += "• 湿度偏高，加强通风预防病害\n"
        
        if avg_soil < 35:
            summary += "• 土壤偏干，增加灌溉频次\n"
        elif avg_soil > 65:
            summary += "• 土壤偏湿，减少灌溉\n"
        
        return summary
    
    def _generate_llm_summary(self, history: List[Dict[str, Any]]) -> str:
        """使用 LLM 生成每日总结"""
        try:
            # 构建历史数据摘要
            history_summary = self._summarize_history(history)
            
            # 调用 LLM
            prompt = f"请根据以下历史数据生成每日生长报告总结：\n\n{history_summary}"
            
            if OLLAMA_AVAILABLE and self.client:
                response = self.client.chat(
                    model=self.model_name,
                    messages=[
                        {'role': 'system', 'content': '你是一位农业专家，负责生成每日作物生长报告。'},
                        {'role': 'user', 'content': prompt}
                    ]
                )
                return response['message']['content']
            
            elif OPENAI_AVAILABLE and self.client:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {'role': 'system', 'content': '你是一位农业专家，负责生成每日作物生长报告。'},
                        {'role': 'user', 'content': prompt}
                    ]
                )
                return response.choices[0].message.content
            
            else:
                return self._generate_simulation_summary(history)
                
        except Exception as e:
            logger.error(f"LLM 总结生成失败：{e}")
            return self._generate_simulation_summary(history)
    
    def _summarize_history(self, history: List[Dict[str, Any]]) -> str:
        """总结历史数据"""
        summary = []
        
        # 计算统计值
        if history:
            temps = [d.get('environment', {}).get('temperature', 0) for d in history]
            humidities = [d.get('environment', {}).get('humidity', 0) for d in history]
            
            summary.append(f"温度范围：{min(temps):.1f}°C - {max(temps):.1f}°C")
            summary.append(f"湿度范围：{min(humidities):.1f}% - {max(humidities):.1f}%")
            summary.append(f"数据记录数：{len(history)}")
        
        return "\n".join(summary)
    
    def analyze_anomaly(self, data: Dict[str, Any], threshold: float = 2.0) -> Dict[str, Any]:
        """
        分析异常情况
        
        Args:
            data: 当前数据
            threshold: 异常判定阈值（标准差倍数）
            
        Returns:
            异常分析结果
        """
        return {
            'is_anomaly': False,
            'anomalies': [],
            'suggestions': [],
            'timestamp': datetime.now().isoformat()
        }
    
    def chat(self, message: str, context: Dict[str, Any] = None, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        对话式咨询
        
        Args:
            message: 用户消息
            context: 当前传感器数据上下文（可选）
            conversation_history: 对话历史（可选）
            
        Returns:
            AI 回复字典
        """
        # 无论是否模拟模式，都调用真实 AI 进行分析
        # 模拟模式下传入的是模拟数据，但分析由真实 AI 完成
        return self._chat_llm(message, context, conversation_history)
    
    def _chat_simulation(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """模拟对话 - 基于模拟数据进行分析"""
        response_text = f"你好！我是 AgriSense AI，你的专属农业顾问。\n\n"
        response_text += f"你问：\"{message}\"\n\n"
        
        # 如果有上下文数据，基于数据进行分析
        if context:
            response_text += "【当前大棚模拟数据】\n"
            
            # 环境数据
            env = context.get('environment', {})
            if env:
                response_text += "🌡️ 环境数据：\n"
                temp = env.get('temperature', 25)
                humidity = env.get('humidity', 60)
                light = env.get('light_intensity', 2500)
                co2 = env.get('co2', 600)
                
                response_text += f"   - 温度：{temp}°C "
                if temp < 18:
                    response_text += "(偏低⚠️)\n"
                elif temp > 32:
                    response_text += "(偏高⚠️)\n"
                else:
                    response_text += "(适宜✅)\n"
                
                response_text += f"   - 湿度：{humidity}% "
                if humidity < 45:
                    response_text += "(偏低⚠️)\n"
                elif humidity > 75:
                    response_text += "(偏高⚠️)\n"
                else:
                    response_text += "(适宜✅)\n"
                
                response_text += f"   - 光照：{light} lux\n"
                response_text += f"   - CO2: {co2} ppm\n"
            
            # 土壤数据
            soil = context.get('soil', {})
            if soil and 'points' in soil:
                response_text += "\n🌱 土壤数据：\n"
                moistures = [p.get('moisture', 50) for p in soil['points']]
                avg_moisture = sum(moistures) / len(moistures) if moistures else 50
                
                response_text += f"   - 平均土壤湿度：{avg_moisture:.1f}% "
                if avg_moisture < 35:
                    response_text += "(偏干⚠️)\n"
                elif avg_moisture > 65:
                    response_text += "(偏湿⚠️)\n"
                else:
                    response_text += "(适宜✅)\n"
                
                for i, p in enumerate(soil['points']):
                    m = p.get('moisture', 50)
                    status = p.get('status', 'optimal')
                    status_icon = {'dry': '🔴', 'wet': '🔵', 'optimal': '🟢'}.get(status, '⚪')
                    response_text += f"   - 监测点{i+1}: {m}% {status_icon}\n"
            
            # 根据数据生成建议
            response_text += "\n💡 管理建议：\n"
            
            if temp < 18:
                response_text += "   • 温度偏低，建议关闭通风，适当补光增温\n"
            elif temp > 32:
                response_text += "   • 温度偏高，建议开启通风，必要时遮阳降温\n"
            else:
                response_text += "   • 温度适宜，保持当前管理\n"
            
            if humidity < 45:
                response_text += "   • 湿度偏低，建议减少通风，考虑喷雾增湿\n"
            elif humidity > 75:
                response_text += "   • 湿度偏高，建议加强通风，预防病害\n"
            else:
                response_text += "   • 湿度适宜，保持当前管理\n"
            
            if avg_moisture < 35:
                response_text += "   • 土壤偏干，建议及时灌溉\n"
            elif avg_moisture > 65:
                response_text += "   • 土壤偏湿，建议暂停灌溉\n"
            else:
                response_text += "   • 土壤湿度适宜，保持当前灌溉策略\n"
            
            response_text += "\n📝 说明：当前使用模拟数据，实际环境中数据可能有所不同。"
        else:
            response_text += "当前没有传感器数据上下文。\n"
            response_text += "你可以询问我关于大棚管理、作物生长、环境调控等问题。\n\n"
            response_text += "示例问题：\n"
            response_text += "• \"当前环境状况如何？\"\n"
            response_text += "• \"温度多少合适？\"\n"
            response_text += "• \"如何预防作物病害？\"\n"
            response_text += "• \"土壤湿度应该保持在什么范围？\"\n"
        
        return {
            'response': response_text,
            'model': 'simulation',
            'timestamp': datetime.now().isoformat()
        }
    
    def _chat_llm(self, message: str, context: Dict[str, Any] = None, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """使用 LLM 进行对话"""
        try:
            # 构建消息列表
            messages = []
            
            # 添加系统提示
            messages.append({
                'role': 'system',
                'content': self.CONVERSATIONAL_SYSTEM_PROMPT
            })
            
            # 添加对话历史
            if conversation_history:
                for turn in conversation_history[-10:]:  # 只保留最近 10 轮对话
                    messages.append({'role': 'user', 'content': turn['user']})
                    messages.append({'role': 'assistant', 'content': turn['assistant']})
            
            # 添加当前上下文数据（如果有）
            if context:
                context_info = self._format_context(context)
                if context_info:
                    messages.append({
                        'role': 'user',
                        'content': f"当前大棚数据：\n{context_info}\n\n用户问题：{message}"
                    })
                else:
                    messages.append({'role': 'user', 'content': message})
            else:
                messages.append({'role': 'user', 'content': message})
            
            # 调用 LLM
            if OLLAMA_AVAILABLE and self.client:
                response = self.client.chat(
                    model=self.model_name,
                    messages=messages
                )
                content = response['message']['content']
            
            elif OPENAI_AVAILABLE and self.client:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages
                )
                content = response.choices[0].message.content
            
            else:
                # 使用 requests 调用
                content = self._call_chat_api(messages)
            
            return {
                'response': content,
                'model': self.model_name,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"对话失败：{e}")
            return {
                'response': f"抱歉，我遇到了一个问题：{str(e)}。请稍后再试。",
                'model': self.model_name,
                'timestamp': datetime.now().isoformat(),
                'error': True
            }
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """格式化上下文数据"""
        parts = []
        
        env = context.get('environment', {})
        if env:
            parts.append("环境数据：")
            parts.append(f"  - 温度：{env.get('temperature', 'N/A')}°C")
            parts.append(f"  - 湿度：{env.get('humidity', 'N/A')}%")
            parts.append(f"  - 光照：{env.get('light_intensity', 'N/A')} lux")
            parts.append(f"  - CO2: {env.get('co2', 'N/A')} ppm")
        
        soil = context.get('soil', {})
        if soil:
            parts.append("土壤数据：")
            for key, value in soil.items():
                if isinstance(value, dict):
                    parts.append(f"  - {key}: {value.get('moisture', 'N/A')}%")
        
        vision = context.get('vision', {})
        if vision:
            leaf = vision.get('leaf_health', {})
            if leaf:
                parts.append("作物健康：")
                parts.append(f"  - 病害类型：{leaf.get('disease_type', 'N/A')}")
                parts.append(f"  - 健康评分：{leaf.get('health_score', 'N/A')}")
        
        return "\n".join(parts)
    
    def _call_chat_api(self, messages: List[Dict[str, str]]) -> str:
        """调用聊天 API"""
        try:
            # 根据 provider 类型选择正确的 API 端点
            if self.provider == 'ollama':
                # Ollama 使用 /api/generate 端点，需要转换消息格式
                return self._call_ollama_api(messages)
            else:
                # OpenAI 兼容 API 使用 /v1/chat/completions 端点
                return self._call_openai_api(messages)
        except Exception as e:
            logger.error(f"聊天 API 调用失败：{e}")
            raise
    
    def _call_ollama_api(self, messages: List[Dict[str, str]]) -> str:
        """调用 Ollama API"""
        # 将消息列表合并为单个 prompt
        full_prompt = ""
        system_prompt = ""
        
        for msg in messages:
            if msg['role'] == 'system':
                system_prompt = msg['content']
            elif msg['role'] == 'user':
                full_prompt += f"用户：{msg['content']}\n"
            elif msg['role'] == 'assistant':
                full_prompt += f"助手：{msg['content']}\n"
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_name,
                "prompt": full_prompt,
                "system": system_prompt,
                "stream": False
            },
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response.raise_for_status()
        return response.json()['response']
    
    def _call_openai_api(self, messages: List[Dict[str, str]]) -> str:
        """调用 OpenAI 兼容 API"""
        url = f"{self.base_url}/chat/completions"
        logger.info(f"调用 OpenAI API: {url}, 模型：{self.model_name}")
        
        response = requests.post(
            url,
            json={
                "model": self.model_name,
                "messages": messages
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            timeout=120  # 增加超时时间
        )
        
        # 详细错误日志
        if response.status_code != 200:
            logger.error(f"API 响应状态码：{response.status_code}")
            logger.error(f"API 响应内容：{response.text}")
            raise Exception(f"API 调用失败：{response.status_code} {response.text}")
        
        data = response.json()
        return data['choices'][0]['message']['content']
