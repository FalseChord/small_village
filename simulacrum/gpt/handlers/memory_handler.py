from typing import Dict, List
from .base_handler import BaseHandler

class MemoryHandler(BaseHandler):
    """記憶處理器

    負責將事件和對話分割成不同類型的記憶，使用 GPT API 進行智能分析
    """

    def __init__(self, interface):
        super().__init__(interface)

    def breakdown_event_to_memories(self, event: Dict, persona_data: Dict) -> Dict:
        """將事件分割成多種記憶類型

        Args:
            event: 事件字典，包含事件描述、類型、參與者等資訊
            persona_data: 角色資料，包含姓名、狀態、特質等

        Returns:
            包含多種記憶類型的字典：
            {
                'semantic': [記憶1, 記憶2, ...],      # 語意記憶列表
                'episodic': [記憶1, 記憶2, ...],      # 情節記憶列表
                'emotional': [記憶1, 記憶2, ...]      # 情緒記憶列表
            }

        Raises:
            RuntimeError: 當 GPT API 呼叫失敗時拋出錯誤
        """
        # 創建事件記憶分割的 prompt
        prompt = self._create_event_memory_prompt(event, persona_data)

        # 呼叫 GPT API 進行記憶分割
        # 降低溫度與嚴格 JSON 要求，減少非 JSON 回覆導致的解析失敗
        prompt += "請只輸出有效 JSON 物件，無任何解釋或其他文字。\n"
        response = self.interface._call_gpt(prompt, 'memory_analyzer', temperature=0.3)

        if response:
            return self._process_memory_response(response, 'event')
        else:
            # 如果 GPT 呼叫失敗，直接拋出錯誤
            raise RuntimeError("GPT API 呼叫失敗，無法進行事件記憶分割")

    def breakdown_dialogue_to_memories(self, dialogue: Dict, persona_data: Dict) -> Dict:
        """將對話分割成多種記憶類型

        Args:
            dialogue: 對話字典，包含對話內容、參與者、主題等資訊
            persona_data: 角色資料，包含姓名、狀態、特質等

        Returns:
            包含多種記憶類型的字典：
            {
                'semantic': [記憶1, 記憶2, ...],      # 語意記憶列表
                'episodic': [記憶1, 記憶2, ...],      # 情節記憶列表
                'emotional': [記憶1, 記憶2, ...]      # 情緒記憶列表
            }

        Raises:
            RuntimeError: 當 GPT API 呼叫失敗時拋出錯誤
        """
        # 創建對話記憶分割的 prompt
        prompt = self._create_dialogue_memory_prompt(dialogue, persona_data)

        # 呼叫 GPT API 進行記憶分割
        # 降低溫度與嚴格 JSON 要求，減少非 JSON 回覆導致的解析失敗
        prompt += "請只輸出有效 JSON 物件，無任何解釋或其他文字。\n"
        response = self.interface._call_gpt(prompt, 'memory_analyzer', temperature=0.3)

        if response:
            return self._process_memory_response(response, 'dialogue')
        else:
            # 如果 GPT 呼叫失敗，直接拋出錯誤
            raise RuntimeError("GPT API 呼叫失敗，無法進行對話記憶分割")

    def _create_event_memory_prompt(self, event: Dict, persona_data: Dict) -> str:
        """創建事件記憶分割的 prompt"""
        prompt = (
            "請分析以下事件，並將其分割成三種不同類型的記憶。\n\n"
            f"事件描述：{event.get('description', '')}\n"
            f"事件類型：{event.get('type', 'general')}\n"
            f"參與者：{', '.join(event.get('participants', []))}\n"
            f"地點：{event.get('location', '')}\n"
            f"時間：{event.get('time', '')}\n\n"

            f"角色資訊：\n"
            f"姓名：{persona_data.get('name', '')}\n"
            f"天生特質：{', '.join(persona_data.get('innate_traits', []))}\n\n"

            "請將這個事件分割成以下三種記憶類型：\n\n"

            "1. 語意記憶（semantic）：\n"
            "   - 從事件中學到的知識、概念、事實\n"
            "   - 可以包含多個記憶點\n"
            "   - 每個記憶都要有描述、關鍵字、情緒強度\n\n"

            "2. 情節記憶（episodic）：\n"
            "   - 具體的事件經歷和體驗\n"
            "   - 可以包含多個記憶點\n"
            "   - 每個記憶都要有描述、關鍵字、情緒強度\n\n"

            "3. 情緒記憶（emotional）：\n"
            "   - 在事件中感受到的情感和情緒\n"
            "   - 可以包含多個記憶點\n"
            "   - 每個記憶都要有描述、關鍵字、情緒強度\n\n"

            "請以 JSON 格式返回，格式如下：\n"
            "{\n"
            '  "semantic": [\n'
            '    {\n'
            '      "description": "記憶描述",\n'
            '      "keywords": ["關鍵字1", "關鍵字2"],\n'
            '      "emotional_intensity": 0.7\n'
            '    }\n'
            '  ],\n'
            '  "episodic": [\n'
            '    {\n'
            '      "description": "記憶描述",\n'
            '      "keywords": ["關鍵字1", "關鍵字2"],\n'
            '      "emotional_intensity": 0.6\n'
            '    }\n'
            '  ],\n'
            '  "emotional": [\n'
            '    {\n'
            '      "description": "記憶描述",\n'
            '      "keywords": ["關鍵字1", "關鍵字2"],\n'
            '      "emotional_intensity": 0.8\n'
            '    }\n'
            '  ]\n'
            "}\n\n"

            "注意事項：\n"
            "- 每種記憶類型可以包含 0-3 個記憶點\n"
            "- 情緒強度範圍：0.0-1.0\n"
            "- 關鍵字數量：3-6 個\n"
            "- 描述要具體且個人化\n"
        )

        return prompt

    def _create_dialogue_memory_prompt(self, dialogue: Dict, persona_data: Dict) -> str:
        """創建對話記憶分割的 prompt"""
        prompt = (
            "請分析以下對話，並將其分割成三種不同類型的記憶。\n\n"
            f"對話內容：{dialogue.get('content', '')}\n"
            f"參與者：{', '.join(dialogue.get('participants', []))}\n"
            f"主題：{', '.join(dialogue.get('topics', []))}\n"
            f"心情：{dialogue.get('mood', 'neutral')}\n"
            f"時間：{dialogue.get('time', '')}\n\n"

            f"角色資訊：\n"
            f"姓名：{persona_data.get('name', '')}\n"
            f"天生特質：{', '.join(persona_data.get('innate_traits', []))}\n\n"

            "請將這個對話分割成以下三種記憶類型：\n\n"

            "1. 語意記憶（semantic）：\n"
            "   - 從對話中學到的知識、概念、事實\n"
            "   - 可以包含多個記憶點\n"
            "   - 每個記憶都要有描述、關鍵字、情緒強度\n\n"

            "2. 情節記憶（episodic）：\n"
            "   - 具體的對話經歷和互動\n"
            "   - 可以包含多個記憶點\n"
            "   - 每個記憶都要有描述、關鍵字、情緒強度\n\n"

            "3. 情緒記憶（emotional）：\n"
            "   - 在對話中感受到的情感和情緒\n"
            "   - 可以包含多個記憶點\n"
            "   - 每個記憶都要有描述、關鍵字、情緒強度\n\n"

            "請以 JSON 格式返回，格式如下：\n"
            "{\n"
            '  "semantic": [\n'
            '    {\n'
            '      "description": "記憶描述",\n'
            '      "keywords": ["關鍵字1", "關鍵字2"],\n'
            '      "emotional_intensity": 0.7\n'
            '    }\n'
            '  ],\n'
            '  "episodic": [\n'
            '    {\n'
            '      "description": "記憶描述",\n'
            '      "keywords": ["關鍵字1", "關鍵字2"],\n'
            '      "emotional_intensity": 0.6\n'
            '    }\n'
            '  ],\n'
            '  "emotional": [\n'
            '    {\n'
            '      "description": "記憶描述",\n'
            '      "keywords": ["關鍵字1", "關鍵字2"],\n'
            '      "emotional_intensity": 0.8\n'
            '    }\n'
            '  ]\n'
            "}\n\n"

            "注意事項：\n"
            "- 每種記憶類型可以包含 0-3 個記憶點\n"
            "- 情緒強度範圍：0.0-1.0\n"
            "- 關鍵字數量：3-6 個\n"
            "- 描述要具體且個人化\n"
        )

        return prompt

    def _process_memory_response(self, response: Dict, memory_type: str) -> Dict:
        """處理 GPT 回應的記憶分割結果"""
        try:
            # 確保回應包含所有必要的記憶類型
            memory_types = ['semantic', 'episodic', 'emotional']
            processed_memories = {}

            for mem_type in memory_types:
                if mem_type in response and isinstance(response[mem_type], list):
                    # 驗證每個記憶的結構
                    validated_memories = []
                    for memory in response[mem_type]:
                        if self._validate_memory_structure(memory):
                            validated_memories.append(memory)

                    processed_memories[mem_type] = validated_memories
                else:
                    # 如果某個記憶類型不存在或格式錯誤，使用預設值
                    processed_memories[mem_type] = []

            return processed_memories

        except Exception as e:
            self.logger.error(f"處理記憶回應時發生錯誤: {e}")
            # 返回預設記憶結構
            return {
                'semantic': [],
                'episodic': [],
                'emotional': []
            }

    def _validate_memory_structure(self, memory: Dict) -> bool:
        """驗證記憶結構是否正確"""
        required_fields = ['description', 'keywords', 'emotional_intensity']

        # 檢查必要欄位是否存在
        for field in required_fields:
            if field not in memory:
                return False

        # 檢查描述是否為字串且不為空
        if not isinstance(memory['description'], str) or not memory['description'].strip():
            return False

        # 檢查關鍵字是否為列表且不為空
        if not isinstance(memory['keywords'], list) or len(memory['keywords']) == 0:
            return False

        # 檢查情緒強度是否為數字且在有效範圍內
        try:
            intensity = float(memory['emotional_intensity'])
            if not (0.0 <= intensity <= 1.0):
                return False
        except (ValueError, TypeError):
            return False

        return True

