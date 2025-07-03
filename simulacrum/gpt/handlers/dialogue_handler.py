from typing import Dict, List, Union
from .base_handler import BaseHandler

class DialogueHandler(BaseHandler):
    def __init__(self, interface):
        super().__init__(interface)
        # self.topic_categories = {
        #     'personal_life': [
        #         'daily_routine', 'health', 'work_study', 'hobbies',
        #         'future_plans', 'personal_growth', 'life_changes'
        #     ],
        #     'relationships': [
        #         'family', 'friends', 'colleagues', 'romantic',
        #         'social_activities', 'conflicts', 'support'
        #     ],
        #     'current_events': [
        #         'news', 'trends', 'local_events', 'cultural_events',
        #         'weather', 'seasonal_topics'
        #     ],
        #     'shared_interests': [
        #         'common_hobbies', 'shared_experiences', 'mutual_friends',
        #         'past_memories', 'future_plans'
        #     ],
        #     'emotional_support': [
        #         'comfort', 'advice', 'encouragement', 'venting',
        #         'celebration', 'sympathy'
        #     ]
        # }

    def select_conversation_topic(self, speaker, listener, context: Dict, dialogue_history: List[Dict] = []) -> str:
        """選擇合適的對話主題，直接回傳主題字串"""
        prompt = (
            f"請根據以下資訊，為{speaker.name}和{listener.name}選擇一個合適的對話主題：\n\n"
            f"說話者資料：\n"
            f"姓名：{speaker.name}\n"
            f"個性：{', '.join(speaker.innate_traits)}\n"
        )
        
        # 只有主人格才加入當前狀態
        if hasattr(speaker, 'get_current_state'):
            prompt += f"當前狀態：{speaker.get_current_state()}\n"
        
        # 加入關係資訊
        if hasattr(speaker, 'get_relationship_with'):
            relationship = speaker.get_relationship_with(listener.name)
            prompt += (
                f"與{listener.name}的關係：{relationship.get('role', '一般認識')}\n"
                f"溝通風格：{relationship.get('communication_style', '普通')}\n"
            )
        
        # 加入最近的對話記憶
        recent_memories = speaker.memory.get_relevant_memories(
            query=f"與{listener.name}的對話",
            limit=5
        )
        if recent_memories:
            prompt += "\n最近的對話記憶：\n"
            for memory in recent_memories:
                prompt += f"- {memory['description']}\n"
        
        # 加入對話歷史，並分析已討論過的話題
        if dialogue_history:
            prompt += "\n當前的對話：\n"
            for turn in dialogue_history:
                prompt += f"{turn['speaker']}: {turn['content']}\n"
            
            # 分析已討論過的話題
            prompt += "\n已討論過的話題：\n"
            discussed_topics = set()
            for turn in dialogue_history:
                content = turn['content']
                content = ''.join(char for char in content if char not in '，。！？、；：""''（）【】《》')
                words = content.split()
                discussed_topics.update(word for word in words if len(word) > 1)
            if discussed_topics:
                prompt += "關鍵詞：\n"
                for topic in discussed_topics:
                    prompt += f"- {topic}\n"
        prompt += (
            "\n請選擇一個合適的對話主題，需要：\n"
            "1. 考慮雙方的個性和關係\n"
            "2. 避免重複當前對話中討論過的話題\n"
            "請直接返回主題內容字串\n"
        )
        response = self.interface._call_gpt(prompt, 'topic_selector', temperature=0.7)
        return response

    def generate_speaking_intent(
        self, 
        speaker,
        listener,
        context: Dict,
        speaker_is_main: bool,
        dialogue_history: List[Dict] = [],
        current_topic: str = None
    ) -> Dict:
        """生成說話意圖"""
        prompt = (
            f"請根據以下資訊，生成{speaker.name}對{listener.name}說話的意圖：\n\n"
            f"說話者資料：\n"
            f"姓名：{speaker.name}\n"
            f"個性：{', '.join(speaker.innate_traits)}\n"
            f"背景：{speaker.biography}\n"
        )
        
        # 根據 speaker_is_main 判斷
        if speaker_is_main:
            relationship = speaker.get_relationship_with(listener.name)
            prompt += (
                f"當前狀態：{speaker.get_current_state()}\n"
                f"{listener.name}的身份：{relationship.get('role', '一般認識')}\n"
                f"對{listener.name}的態度：{relationship.get('attitude', '一般')}\n"
                f"對{listener.name}慣用的溝通風格：{relationship.get('communication_style', '普通')}\n"
                f"對{listener.name}的顧慮：{relationship.get('concerns', '無特別顧慮')}\n"
            )
        else:
            prompt += (
                f"對{listener.name}的身份：{speaker.relationship_with_main['role']}\n"
                f"對{listener.name}的期待：{speaker.relationship_with_main['expectations']}\n"
                f"對{listener.name}慣用的溝通風格：{speaker.relationship_with_main['communication_style']}\n"
                f"對{listener.name}顧慮：{speaker.relationship_with_main['concerns']}\n"
            )
        prompt += (
            f"\n聽話者資料：\n"
            f"姓名：{listener.name}\n"
            f"個性：{', '.join(listener.innate_traits)}\n"
        )
        
        # 根據 speaker_is_main 的相反狀態判斷聽話者
        if not speaker_is_main:
            prompt += f"當前狀態：{listener.get_current_state()}\n"
        
        # 加入相關記憶
        recent_memories = speaker.memory.get_relevant_memories(
            query=f"與{listener.name}相關的記憶",
            limit=3
        )
        if recent_memories:
            prompt += "\n相關記憶：\n"
            for memory in recent_memories:
                prompt += f"- {memory['description']}\n"
        
        # 加入對話歷史
        if dialogue_history:
            prompt += "\n之前的對話：\n"
            for turn in dialogue_history:
                prompt += f"{turn['speaker']}: {turn['content']}\n"
        
        # 加入當前話題
        if current_topic:
            prompt += f"\n當前話題：\n主題：{current_topic}\n\n"
        prompt += (
            "請生成說話意圖，需要：\n"
            "1. 考慮雙方的性格和關係\n"
            "2. 如果當前有話題，意圖要圍繞該話題展開\n"
            "3. 自然且貼近生活\n"
            "4. 意圖要具體且明確，要能推動對話的發展\n\n"
            "請以 JSON 格式返回：\n"
            "{\n"
            '  "intent": "說話的目的（例如：關心、疑問、詢問、抱怨、分享）",\n'
            '  "expectation": "期望得到的結果",\n'
            "}\n"
        )
        
        response = self.interface._call_gpt(prompt, 'intent_analyzer', temperature=0.7)
        return response

    def generate_dialogue_turn(
        self,
        speaker,
        listener,
        intent: Dict,
        context: Dict,
        speaker_is_main: bool,
        dialogue_history: List[Dict] = [],
        current_topic: str = None
    ) -> str:
        """生成一句對話內容"""
        prompt = (
            f"請根據以下資訊，生成{speaker.name}對{listener.name}說的一句話：\n\n"
            f"說話者資料：\n"
            f"姓名：{speaker.name}\n"
            f"個性：{', '.join(speaker.innate_traits)}\n"
            f"背景：{speaker.biography}\n"
        )
        
        # 根據 speaker_is_main 判斷
        if speaker_is_main:
            relationship = speaker.get_relationship_with(listener.name)
            prompt += (
                f"當前狀態：{speaker.get_current_state()}\n"
                f"對方身份：{relationship.get('role', '一般認識')}\n"
                f"對{listener.name}的態度：{relationship.get('attitude', '一般')}\n"
                f"對{listener.name}慣用的溝通風格：{relationship.get('communication_style', '普通')}\n"
                f"對{listener.name}特別的顧慮：{relationship.get('concerns', '無特別顧慮')}\n"
            )
        else:
            prompt += (
                f"對{listener.name}的身份：{speaker.relationship_with_main['role']}\n"
                f"對{listener.name}的期待：{speaker.relationship_with_main['expectations']}\n"
                f"對{listener.name}慣用的溝通風格：{speaker.relationship_with_main['communication_style']}\n"
                f"對{listener.name}特別的顧慮：{speaker.relationship_with_main['concerns']}\n"
            )
        
        prompt += (
            f"\n聽話者資料：\n"
            f"姓名：{listener.name}\n"
            f"個性：{', '.join(listener.innate_traits)}\n"
        )
        
        # 加入相關記憶
        recent_memories = speaker.memory.get_relevant_memories(
            query=f"與{listener.name}相關的記憶",
            limit=3
        )
        if recent_memories:
            prompt += "\n相關記憶：\n"
            for memory in recent_memories:
                prompt += f"- {memory['description']}\n"

        # 加入對話歷史
        if dialogue_history:
            prompt += "\n之前的對話：\n"
            for turn in dialogue_history:
                prompt += f"{turn['speaker']}: {turn['content']}\n"
        prompt += (
            f"\n說話意圖：\n"
            f"意圖：{intent['intent']}\n"
            f"期望：{intent['expectation']}\n\n"
        )
        
        # 加入當前話題
        if current_topic:
            prompt += f"當前話題：\n主題：{current_topic}\n\n"
        prompt += (
            "請生成一句自然的、符合真實聊天對話的句子，需要：\n"
            "1. 使用口語化的表達方式，避免過於正式或文鄒鄒的用詞\n"
            "2. 符合說話者的性格和說話風格\n"
            "3. 符合當前的意圖與話題\n"
            "4. 句子長度要自然，不要太長\n"
            "請以 JSON 格式返回：\n"
            "{\n"
            '  "content": "對話內容"\n'
            "}\n"
        )
        response = self.interface._call_gpt(prompt, 'dialogue_generator')
        return response.get('content', '') if response else ''

    def should_end_dialogue(self, dialogue_turns: List[Dict], context: Dict, current_topic: str = None) -> Dict:
        """判斷對話是否應該結束或變更話題"""
        # MIN_DIALOGUE_TURNS = 10
        prompt = (
            "根據以下對話內容，判斷對話是否應該結束或變更話題：\n\n"
            f"對話場景：\n"
            f"時間：{context.get('time', '未指定')}\n"
            f"場合：{context.get('occasion', '未指定')}\n\n"
        )
        
        # 加入當前話題資訊
        if current_topic:
            prompt += f"當前話題：\n主題：{current_topic}\n\n"
        prompt += "當前對話：\n"
        # 格式化對話歷史
        for turn in dialogue_turns:
            prompt += f"{turn['speaker']}: {turn['content']}\n"
        prompt += (
            "\n請判斷：\n"
            "1. 是否已經充分討論了當前話題的具體主題\n"
            "2. 目前的對話是否適合結束對話或轉換話題，如果剛開始新話題，則不會立即結束\n"
            "3. 最後二到三句對話中，如果陷入自我重複或迴圈，就可以結束對話\n"
            "4. 如果對話已經達到自然結束點，則可以結束對話\n"
            "請以 JSON 格式返回：\n"
            "{\n"
            '  "action": "continue/end",\n'
            '  "reason": "判斷原因"\n'
            "}\n"
        )
        response = self.interface._call_gpt(prompt, 'dialogue_analyzer', temperature=0.3)
    
        # 如果 GPT 返回 end 但對話句數不足，強制改為 change_topic
        # if response and response.get("action") == "end" and len(dialogue_turns) < MIN_DIALOGUE_TURNS:
        #     return {"action": "change_topic", "reason": f"對話已達到自然結束點，但句數不足 {MIN_DIALOGUE_TURNS} 句，轉換話題"}

        return response if response else {"action": "end", "reason": "無法判斷對話狀態"}

    def summarize_dialogue(self, content: str, participants: List[str]) -> Dict:
        """總結對話內容"""
        prompt = self._create_summary_prompt(content, participants)
        return self.interface._call_gpt(prompt, 'dialogue_summarizer')

    def _create_summary_prompt(self, content: str, participants: List[str]) -> str:
        return (
            f"請總結以下對話內容：\n\n"
            f"參與者：{', '.join(participants)}\n"
            f"對話內容：\n" + "\n".join(content) + "\n\n"
            "請生成簡潔的對話摘要，包含：\n"
            "1. 對話的主要內容\n"
            "2. 重要的情感交流\n"
            "3. 關鍵的決定或結論\n\n"
            
            "請以 JSON 格式返回：\n"
            "{\n"
            '  "description": "對話摘要"\n'
            "}\n"
        )
