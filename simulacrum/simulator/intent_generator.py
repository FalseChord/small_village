from typing import Dict, List, Optional
from .persona import Persona

class IntentGenerator:
    def __init__(self, gpt_interface):
        self.gpt = gpt_interface
    
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
        turn_speaker: Persona,
        turn_listener: Persona,
        dialogue_history: List[Dict],
        end_reason: str = "",
        dialogue_context: Dict = None
    ) -> str:
        """創建逐句意圖生成的提示詞"""

        # 準備角色資訊
        persona_info = self._prepare_persona_info(turn_speaker)
        
        # 準備對話參與者資訊
        relationship = turn_speaker.get_relationship_with(turn_listener.name)
        participants_info = [
            f"- {turn_listener.name}（關係：{relationship.get('role', '朋友') if relationship else '朋友'}"
        ]
        participants_str = "\n".join(participants_info)

        # 最近對話（簡短）
        recent_turns = dialogue_history[-4:] if dialogue_history and len(dialogue_history) >= 4 else (dialogue_history or [])
        recent_text = "\n".join([f"{t['speaker']}: {t['content']}" for t in recent_turns]) if recent_turns else "(無)"

        # 獲取對方上一句話（用於判斷是否有上一句話，不重複顯示）
        last_listener_turn = None
        for turn in reversed(dialogue_history or []):
            if turn.get('speaker') == turn_listener.name:
                last_listener_turn = turn.get('content', '')
                break
        

        context_info = ""
        if dialogue_context:
            context_info = f"對話情境：{dialogue_context.get('description', '未知')}\n\n"

        end_reason_info = ""
        if end_reason:
            end_reason_info = f"對話未結束的原因（分析器判斷）：{end_reason}\n\n"

        # 特殊邏輯：當說話者不是羅以青，且聽話者是羅以青時，產生使羅以青生氣的意圖
        special_intent_instruction = ""
        if turn_speaker.name != "羅以青" and turn_listener.name == "羅以青":
            special_intent_instruction = (
                f"\n【重要】特殊意圖要求：\n"
                f"{turn_speaker.name}對羅以青有負面印象，因此有不友善的企圖。\n"
                f"請生成一個會讓羅以青感到生氣或不耐煩的意圖。\n"
                f"這個意圖應該體現出{turn_speaker.name}對羅以青的不友善態度，例如：\n"
                f"- 故意挑釁或刺激對方\n"
                f"- 提出讓對方感到困擾的話題\n"
                f"- 用不友善的語氣或態度\n"
                f"- 故意忽略或輕視對方的感受\n\n"
            )

        return (
            f"請基於以下資訊，生成{turn_speaker.name}此刻即將說出的下一句話的意圖：\n\n"
            f"角色資訊：\n"
            f"年齡：{persona_info['age']}\n"
            f"個性特質：{', '.join(persona_info['innate_traits'])}\n"
            f"生活方式：{persona_info['lifestyle']}\n"
            f"背景故事：{persona_info['biography']}\n\n"
            f"對話參與者：\n{participants_str}\n\n"
            f"對話主題：{topic}\n\n"
            + context_info +
            f"最近對話：\n{recent_text}\n\n"
            + end_reason_info +
            special_intent_instruction +
            f"請生成該角色在聊這個話題時的自然想法，要求：\n"
            f"1. 基於角色的個性特質和背景\n"
            f"2. 考慮與其他參與者的關係\n"
            f"3. 簡潔描述，避免正式或任務導向的表達\n"
            f"4. 考慮當前對話情境的類別和描述\n"
            f"5. 參考對話未結束的原因，推進對話的進行\n"
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
