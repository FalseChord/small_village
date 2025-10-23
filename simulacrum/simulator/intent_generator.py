from typing import Dict, List, Optional
from .persona import Persona

class IntentGenerator:
    def __init__(self, gpt_interface):
        self.gpt = gpt_interface
    
    def generate_intents_for_topic(
        self,
        topic: str,
        personas: Dict[str, Persona],
        dialogue_context: Dict = None
    ) -> Dict[str, str]:
        """為特定主題生成每個角色的對話意圖
        
        Args:
            topic: 對話主題
            personas: 參與對話的角色字典
            
        Returns:
            角色名稱到意圖的字典映射
        """
        intents = {}
        
        for persona_name, persona in personas.items():
            intent = self._generate_intent_for_persona(topic, persona, personas, dialogue_context)
            if intent:
                intents[persona_name] = intent
            else:
                # 如果生成失敗，使用預設意圖
                intents[persona_name] = f"想要與朋友就{topic}進行輕鬆的交流"
        
        return intents
    
    def _generate_intent_for_persona(
        self,
        topic: str,
        persona: Persona,
        all_personas: Dict[str, Persona],
        dialogue_context: Dict = None
    ) -> Optional[str]:
        """為特定角色生成對話意圖"""
        
        # 準備角色資訊
        persona_info = self._prepare_persona_info(persona)
        
        # 準備其他參與者資訊
        other_participants = []
        for name, other_persona in all_personas.items():
            if name != persona.name:
                relationship = persona.get_relationship_with(name)
                other_info = {
                    'name': name,
                    'relationship': relationship.get('role', '朋友') if relationship else '朋友',
                    'attitude': relationship.get('attitude', '友好') if relationship else '友好'
                }
                other_participants.append(other_info)
        
        prompt = self._create_intent_prompt(topic, persona_info, other_participants, dialogue_context)
        
        response = self.gpt._call_gpt(prompt, 'intent_generator', temperature=0.7)
        
        if response and 'intent' in response:
            return response['intent']
        else:
            print(f"⚠️ 為 {persona.name} 生成意圖失敗")
            return None
    
    def _prepare_persona_info(self, persona: Persona) -> Dict:
        """準備角色資訊"""
        return {
            'name': persona.name,
            'age': persona.age,
            'innate_traits': persona.innate_traits,
            'learned': persona.learned,
            'lifestyle': persona.lifestyle,
            'biography': persona.biography
        }
    
    def _create_intent_prompt(
        self,
        topic: str,
        persona_info: Dict,
        other_participants: List[Dict],
        dialogue_context: Dict = None
    ) -> str:
        """創建意圖生成的提示詞"""
        
        # 準備其他參與者資訊
        participants_info = []
        for participant in other_participants:
            participants_info.append(
                f"- {participant['name']}（關係：{participant['relationship']}，態度：{participant['attitude']}）"
            )
        participants_str = "\n".join(participants_info)
        
        # 準備情境資訊
        context_info = ""
        if dialogue_context:
            context_info = (
                f"對話情境：{dialogue_context.get('description', '未知')}\n\n"
            )
        
        prompt = (
            f"請根據以下角色資訊和對話主題，生成該角色在朋友聊天時的自然動機：\n\n"
            f"角色資訊：\n"
            f"姓名：{persona_info['name']}\n"
            f"年齡：{persona_info['age']}\n"
            f"個性特質：{', '.join(persona_info['innate_traits'])}\n"
            f"學習經歷：{persona_info['learned']}\n"
            f"生活方式：{persona_info['lifestyle']}\n"
            f"背景故事：{persona_info['biography']}\n\n"
            f"對話參與者：\n{participants_str}\n\n"
            f"對話主題：{topic}\n\n"
            + context_info +
            f"請生成該角色在聊這個話題時的自然想法，要求：\n"
            f"1. 基於角色的個性特質和背景\n"
            f"2. 考慮與其他參與者的關係\n"
            f"3. 像朋友聊天時會有的自然動機\n"
            f"4. 一句話簡潔描述\n"
            f"5. 避免正式或任務導向的表達\n"
            f"6. 考慮當前對話情境的類別和描述\n\n"
            f"範例：\n"
            f"- 想分享近況\n"
            f"- 關心朋友\n"
            f"- 聊聊想法\n"
            f"- 聽聽意見\n\n"
            f"避免的複雜範例：\n"
            f"- 想跟你輕鬆聊聊暑期班和我拍短片的點子、順便邀你來一次不露臉的 IG Live 合作\n"
            f"- 想分享一個讓我會心一笑的學生小故事，輕鬆一下，也讓你更了解學生平常的反應\n\n"
            f"請以 JSON 格式返回：\n"
            f'{{\n'
            f'  "intent": "對話意圖"\n'
            f'}}\n'
        )
        
        return prompt
