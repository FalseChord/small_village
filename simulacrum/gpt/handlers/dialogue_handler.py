from typing import Dict, List, Union
from .base_handler import BaseHandler

class DialogueHandler(BaseHandler):
    def __init__(self, interface):
        super().__init__(interface)

    def generate_dialogue_turn(
        self,
        speaker,
        listener,
        context: Dict,
        speaker_is_main: bool,
        dialogue_history: List[Dict] = [],
        current_topic: str = None,
        relevant_memories: List = None
    ) -> str:
        """生成一句對話內容"""
        prompt = (
            f"請生成{speaker.name}對{listener.name}說的一句話：\n\n"
            f"情境：朋友間的日常聊天\n"
            f"說話者：{speaker.name}（{', '.join([trait.strip() for trait in speaker.innate.split('、')])}）\n"
            f"聽話者：{listener.name}（{', '.join([trait.strip() for trait in listener.innate.split('、')])}）\n"
        )

        # 簡化關係資訊
        relationship = speaker.get_relationship_with(listener.name)
        prompt += f"關係：{relationship.get('role', '一般認識')}\n"

        # 動態對話歷史長度
        if dialogue_history:
            recent_turns = dialogue_history[-3:]

            prompt += f"\n最近對話：\n"
            for turn in recent_turns:
                prompt += f"{turn['speaker']}: {turn['content']}\n"

        # if current_topic:
        #     prompt += f"\n當前話題：{current_topic}\n"

        if relevant_memories:
            prompt += f"\n相關記憶：{relevant_memories[0]['description'][:50]}...\n"  # 只顯示最相關的1筆記憶

        prompt += (
            "你是一位素人，請用自然口語說出以上情境中的下一句台詞。\n"
            "規則：\n"
            "- 不打破第四面牆（不提演員/AI/指示/prompt）。\n"
            "- 僅輸出一句話；無旁白、舞台說明、括號動作。\n"
            "- 不反問：若上一句為問句，先回答或簡短回應，不再丟問句。\n"
            "- 禁鏡射：不重複/改寫對方剛用的用詞或句型。\n"
            "- 禁過度關心、禁提方案/安排未來。\n"
            "風格：\n"
            "- 隨口自然、口語短句；簡單轉折、不突兀。\n"
            "- 不鋪陳具體回憶/畫面；需要時點到為止。\n"
            "- 不過度解釋或自我分析；不自評對話效果。\n"
            "- 平淡即可，不要表演或金句。\n\n"
            "範例：\n"
            "- 嗨，最近怎樣？\n"
            "- 還行啦，你呢？\n"
            "- 今天天氣不錯。\n"
            "- 嗯，我也覺得。\n\n"
            "避免：\n"
            "- 強調具體畫面/場景、過度解釋、過於關心或正式。\n"
            "- 自評對話效果、像在表演或講故事。\n"
            "- 反問、鏡射措辭、提方案或安排未來。\n\n"
            "請以 JSON 格式返回：\n"
            "{\n"
            '  "content": "對話內容"\n'
            "}\n"
        )
        response = self.interface._call_gpt(prompt, 'dialogue_generator')
        return response.get('content', '') if response else ''

    def should_end_dialogue(self, dialogue_turns: List[Dict], context: Dict, current_topic: str = None) -> Dict:
        """判斷對話是否應該結束或變更話題"""
        MIN_DIALOGUE_TURNS = 12
        prompt = (
            "根據以下對話內容，判斷對話是否應該結束或變更話題：\n\n"
        )

        # 加入當前話題資訊
        if current_topic:
            prompt += f"當前話題：\n主題：{current_topic}\n\n"
        prompt += "當前對話：\n"
        # 格式化對話歷史
        for turn in dialogue_turns:
            prompt += f"{turn['speaker']}: {turn['content']}\n"
        prompt += (
            "\n請仔細分析對話進展情況，判斷是否應該結束對話：\n\n"
            "判斷標準（放寬）：\n"
            "1. 對話推進度：如果最近3-4句對話沒有實質推進話題，陷入問答循環，或雙方都在問問題而沒有人給出實質回答，應該結束。\n"
            "2. 對話品質：如果對話內容重複、偏離主題，或氣氛尷尬無聊，應該結束。\n"
            "3. 預設傾向繼續：如果對話實際上沒有推進，即使話題未完成也應該結束。優先考慮對話的實際效果和進展。\n\n"
            "請以 JSON 格式返回：\n"
            "{\n"
            '  "action": "continue/end",\n'
            '  "reason": "判斷原因"\n'
            "}\n"
        )
        response = self.interface._call_gpt(prompt, 'dialogue_analyzer', temperature=0.3)

        # 若 GPT 建議結束但句數未達下限，傾向繼續
        if response and response.get("action") == "end" and len(dialogue_turns) < MIN_DIALOGUE_TURNS:
            return {"action": "continue", "reason": f"句數未達下限 {MIN_DIALOGUE_TURNS}，避免過早結束"}

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
