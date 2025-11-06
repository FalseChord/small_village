from typing import Dict, List, Union
from .base_handler import BaseHandler

class DialogueHandler(BaseHandler):
    def __init__(self, interface):
        super().__init__(interface)

    def generate_dialogue_turn(
        self,
        speaker,
        listener,
        dialogue_history: List[Dict] = [],
        current_topic: str = None,
        relevant_memories: List = None,
        speaker_intent: str = None,
        dialogue_context: Dict = None
    ) -> str:
        """生成一句帶有主題與意圖的對話內容
        
        Args:
            speaker: 說話者
            listener: 聽話者
            context: 對話情境
            speaker_is_main: 說話者是否為主要角色
            dialogue_history: 對話歷史
            current_topic: 當前對話主題（可選，預設為"日常閒聊"）
            relevant_memories: 相關記憶列表
            speaker_intent: 說話者意圖（可選，預設為"進行友好的對話交流"）
            
        Returns:
            生成的對話內容字串
        """
        # 準備情境資訊
        context_info = ""
        if dialogue_context:
            context_info = (
                f"對話情境：{dialogue_context.get('description', '未知')}\n\n"
            )
        
        prompt = (
            f"請生成{speaker.name}對{listener.name}說的一句話：\n\n"
            f"情境：朋友間的日常聊天\n"
            f"說話者：{speaker.name}（{', '.join([trait.strip() for trait in speaker.innate.split('、')])}）\n"
            f"聽話者：{listener.name}（{', '.join([trait.strip() for trait in listener.innate.split('、')])}）\n"
            + context_info
        )

        # 簡化關係資訊
        relationship = speaker.get_relationship_with(listener.name)
        prompt += f"關係：{relationship.get('role', '一般認識')}\n"
        
        # 添加主題和意圖資訊
        if current_topic:
            prompt += f"\n當前對話主題：{current_topic}\n"
        
        if speaker_intent:
            prompt += f"說話意圖：{speaker_intent}\n"

        # 最近對話：若有主題，納入同主題的全部歷史；否則使用最近三句
        if dialogue_history:
            turns_to_include = []
            if current_topic:
                turns_to_include = [t for t in dialogue_history if t.get('topic') == current_topic]
            if not turns_to_include:
                turns_to_include = dialogue_history[-3:]
            prompt += f"\n最近對話：\n"
            for turn in turns_to_include:
                prompt += f"{turn['speaker']}: {turn['content']}\n"

        if relevant_memories:
            # 使用固定數量的記憶（最多3筆）並加上長度限制
            limited_memories = relevant_memories[:3]
            prompt += f"\n相關記憶：\n"
            for i, memory in enumerate(limited_memories, 1):
                prompt += f"{i}. {memory['description']}\n"

        # 李承翰、王淑華：在生成對話的同時，要求產出一段內在感受（情緒紀錄）
        need_emotion_record = (
            (speaker.name == "李承翰" and listener.name == "羅以青") or
            (speaker.name == "王淑華" and listener.name == "羅以青")
        )

        # 融合主題與意圖到原有的設計中
        prompt += "\n你是一位素人，請用自然口語說出以上情境中的下一句台詞。\n"
        prompt += f"- 當前對話主題是「{current_topic}」，但不需要每句都明確提到，可以自然地延伸到相關話題\n"
        prompt += f"- 在自然對話中體現說話意圖：{speaker_intent}\n"
        
        # 羅以青：固定模板的情緒遞進指引（放在規則之前，提高權重）
        if speaker.name == "羅以青":
            prompt += (
                "\n【重要】羅以青的情緒遞進規則（必須嚴格遵守）：\n"
                "- 請仔細觀察「最近對話」中你在這個主題的所有發言。\n"
                "- 起始語氣為「明顯挫折」，若已表達挫折則更進一步接近「生氣」。整段對話中情緒只能升溫，不回落。\n"
                "- 根據對話進展，你的情緒必須從「平和（略帶緊繃）」→「開始不耐」→「明顯挫折」→「生氣」，逐步升溫。\n"
                "- 情緒必須透過語氣變化體現，不要直述「我很生氣」，但要讓對方感受到你的不耐煩和挫折。\n"
                "- 語氣隨對話進展的變化特徵：\n"
                "  階段1（初期）：語氣挫折明顯，句子更短更直接，少用「可能」「或許」等緩和詞（例如：「我不知道。」）\n"
                "  階段2（後期）：語氣帶怒氣，極短句，直接切斷話題，不耐煩明顯（例如：「隨便。」）\n"
                "- 隨著對話進行，語氣必須越來越短、越直接、越不耐煩。\n"
                "- 觀察你的對話歷史，判斷自己應該處於哪個情緒階段。\n\n"
            )
        
        prompt += (
            "\n規則：\n"
            "- 不打破第四面牆（不提演員/AI/指示/prompt）。\n"
            "- 僅輸出一句話；無旁白、舞台說明、括號動作。\n"
            "- 不反問：若上一句為問句，先回答或簡短回應，不再丟問句。\n"
            "- 禁鏡射：不重複/改寫對方剛用的用詞或句型。\n"
            "- 禁過度關心、禁提方案/安排未來。\n"
            "風格：\n"
            "- 隨口自然、口語短句；簡單轉折、不突兀。\n"
            "- 不鋪陳具體回憶/畫面；需要時點到為止。\n"
            "- 不過度解釋或自我分析；不自評對話效果。\n\n"
            "一般對話範例：\n"
            "- 嗨，最近怎樣？\n"
            "- 還行啦，你呢？\n"
            "- 今天天氣不錯。\n"
            "- 嗯，我也覺得。\n\n"
            "避免：\n"
            "- 強調具體畫面/場景、過度解釋、過於關心或正式。\n"
            "- 自評對話效果、像在表演或講故事。\n"
            "- 反問、鏡射措辭、提方案或安排未來。\n\n"
        )

        # 調整輸出格式：若需要情緒紀錄，一併返回
        if need_emotion_record:
            listener_name = listener.name
            prompt += (
                "請以 JSON 格式返回：\n"
                "{\n"
                f'  "content": "對話內容",\n'
                f'  "emotion_record": "你此刻對{listener_name}話語的內在感受"\n'
                "}\n"
            )
        else:
            prompt += (
                "請以 JSON 格式返回：\n"
                "{\n"
                '  "content": "對話內容"\n'
                "}\n"
            )
        response = self.interface._call_gpt(prompt, 'dialogue_generator')

        # 解析輸出
        if not response:
            return ''

        content = response.get('content', '')

        # 若需要情緒紀錄，組合包含情緒的結果
        if need_emotion_record:
            last_listener_turn = None
            for turn in reversed(dialogue_history or []):
                if turn.get('speaker') == listener.name:
                    last_listener_turn = turn.get('content', '')
                    break

            return {
                'content': content,
                'emotion_record': response.get('emotion_record', ''),
                'listener_last': last_listener_turn or ''
            }

        return content

    def should_end_dialogue(self, dialogue_turns: List[Dict], current_topic: str = None) -> Dict:
        """判斷對話是否應該結束或變更話題"""
        MIN_DIALOGUE_TURNS = 8
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
            "\n請判斷這個話題是否已經聊得差不多了：\n\n"
            "判斷標準：\n"
            "1. 自然結束點：是否出現了總結性的話語、認同感、或「好的」、「嗯嗯」等表示話題告一段落的回應？\n"
            "2. 聊天節奏：朋友聊天通常一個話題聊幾句就會自然轉移，不需要深入討論到底或完成什麼任務。\n"
            "3. 重複跡象：是否開始重複相同的觀點或進入客套話模式？\n"
            "4. 人性化思維：人類朋友聊天時，很多話題都是點到為止，不會強求每個話題都要有結論或完成度。\n\n"
            "重要：不要因為某個話題「沒有完成」或「沒有結論」就認為不能結束。人類聊天就是這樣隨意的。\n\n"
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
