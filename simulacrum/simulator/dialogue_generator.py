from typing import Dict, List, Optional, Set
from datetime import datetime
import random
from .persona import Persona

class DialogueGenerator:
    def __init__(self, gpt_interface):
        self.gpt = gpt_interface

    def generate_daily_dialogues(
        self,
        all_personas: Dict[str, Persona],
        current_date: datetime
    ) -> List[Dict]:
        """生成當日對話"""
        dialogues = []

        # 獲取所有角色名稱
        persona_names = list(all_personas.keys())

        # 檢查角色數量
        if len(persona_names) != 2:
            raise ValueError(f"對話生成器只支援恰好2個角色，目前有 {len(persona_names)} 個角色: {persona_names}")

        # 固定配對兩個角色
        persona1_name, persona2_name = persona_names
        persona1 = all_personas[persona1_name]
        persona2 = all_personas[persona2_name]

        # 生成對話
        dialogue = self.generate_dialogue(
            persona1=persona1,
            persona2=persona2,
            context={
                'time': current_date
            }
        )

        if dialogue:
            dialogues.append(dialogue)

        return dialogues

    def generate_dialogue(
        self,
        persona1: Persona,
        persona2: Persona,
        context: Dict
    ) -> Optional[Dict]:
        """生成完整對話"""
        dialogue_turns = []
        is_dialogue_complete = False

        # 生成初始對話主題集
        # conversation_topics = self.generate_conversation_topics(
        #     persona1=persona1,
        #     persona2=persona2,
        #     context=context
        # )

        # print(f"初始對話主題集: {conversation_topics}")

        # 隨機決定第一個說話者
        starts_with_persona1 = random.choice([True, False])

        # 直接生成對話，不使用話題系統
        current_topic = "日常閒聊"
        print(f"使用話題: {current_topic}")

        # while not is_dialogue_complete and conversation_topics:
        #     # 從主題集中選擇一個主題進行對話
        #     current_topic = self.select_topic_from_set(
        #         conversation_topics=conversation_topics,
        #         dialogue_history=dialogue_turns
        #     )
        #     print(f"選擇對話主題: {current_topic}")
        #
        #     # 從主題集中移除當前選中的主題
        #     conversation_topics.discard(current_topic)
        #
        #     print(f"選擇對話主題: {current_topic}")
        #     print(f"剩餘主題: {conversation_topics}")

        # 針對選中的主題進行對話
        dialogue_turn = self.generate_dialogue_turn(
            persona1=persona1,
            persona2=persona2,
            current_topic=current_topic,
            context=context,
            dialogue_history=dialogue_turns,
            starts_with_persona1=starts_with_persona1
        )

        # 將主題對話加入到總對話中
        dialogue_turns.extend(dialogue_turn)

        # 檢查是否應該結束整個對話
        is_dialogue_complete = True
        print("對話完成")

        # if not conversation_topics:
        #     is_dialogue_complete = True
        #     print("所有主題已完成，結束對話")
        # else:
        #     # 檢查是否有新主題被觸發
        #     new_topics = self.detect_new_topics(
        #         dialogue_turns=dialogue_turn,
        #         persona1=persona1,
        #         persona2=persona2,
        #         context=context
        #     )
        #
        #     if new_topics:
        #         conversation_topics.update(new_topics)
        #         print(f"檢測到新主題: {new_topics}")
        #         print(f"更新後的主題集: {conversation_topics}")

        if dialogue_turns:
            return self._compose_dialogue_result(dialogue_turns, context)
        return None

    # def generate_conversation_topics(
    #     self,
    #     persona1: Persona,
    #     persona2: Persona,
    #     context: Dict
    # ) -> Set[str]:
    #     """生成初始對話主題集"""
    #     prompt = (
    #         f"請根據以下資訊，為{persona1.name}和{persona2.name}生成3-5個對話主題：\n\n"
    #         f"{persona1.name}的資料：\n"
    #         f"姓名：{persona1.name}\n"
    #         f"個性：{', '.join([trait.strip() for trait in persona1.innate.split('、')])}\n"
    #         f"背景：{persona1.biography}\n"
    #     )
    #
    #     # 加入關係資訊
    #     relationship = persona1.get_relationship_with(persona2.name)
    #     prompt += (
    #         f"與{persona2.name}的關係：{relationship.get('role', '一般認識')}\n"
    #         f"溝通風格：{relationship.get('communication_style', '普通')}\n"
    #         f"對{persona2.name}的顧慮：{relationship.get('concerns', '無特別顧慮')}\n"
    #     )
    #
    #     prompt += (
    #         f"\n{persona2.name}的資料：\n"
    #         f"姓名：{persona2.name}\n"
    #         f"個性：{', '.join([trait.strip() for trait in persona2.innate.split('、')])}\n"
    #         f"背景：{persona2.biography}\n"
    #     )
    #
    #
    #     prompt += (
    #         f"\n對話情境：\n"
    #         f"時間：{context.get('time', '未指定')}\n"
    #         f"場景：朋友間的日常聊天\n\n"
    #
    #         "請生成3-5個自然的日常對話話題，要求：\n"
    #         "1. 像真實朋友聊天會談論的話題\n"
    #         "2. 簡潔自然，不要過於正式\n"
    #         "3. 話題要多樣化，避免重複\n"
    #         "4. 能產生輕鬆愉快的對話\n\n"
    #
    #         "範例：\n"
    #         "- 最近工作怎麼樣？\n"
    #         "- 週末有什麼計劃？\n"
    #         "- 最近看什麼好電影？\n"
    #         "- 家裡還好嗎？\n"
    #         "- 今天天氣不錯\n"
    #         "- 你最近在忙什麼？\n\n"
    #
    #         "請以 JSON 格式返回：\n"
    #         "{\n"
    #         '  "topics": ["話題1", "話題2", ...]\n'
    #         "}\n"
    #     )
    #
    #     response = self.gpt._call_gpt(prompt, 'topic_generator', temperature=1.0)
    #
    #     if response and 'topics' in response:
    #         return set(response['topics'])
    #     else:
    #         # 預設主題
    #         return {"日常問候", "分享近況", "討論共同興趣"}

    # def select_topic_from_set(
    #     self,
    #     conversation_topics: Set[str],
    #     dialogue_history: List[Dict]
    # ) -> str:
    #     """從主題集中選擇一個主題"""
    #     if not conversation_topics:
    #         return "日常閒聊"
    #
    #     # 如果有對話歷史，考慮對話的連貫性
    #     if dialogue_history:
    #         recent_content = " ".join([turn['content'] for turn in dialogue_history[-2:]])  # 只考慮最近2句
    #
    #         prompt = (
    #             f"從以下話題中選擇一個最適合繼續對話的：\n"
    #             f"話題選項：{list(conversation_topics)}\n"
    #             f"最近對話：{recent_content}\n\n"
    #             f"請直接返回選擇的話題名稱。\n"
    #         )
    #
    #         selected_topic = self.gpt._call_gpt_text(prompt, 'topic_selector', temperature=0.7)  # 提高溫度增加隨機性
    #
    #         # 確保選擇的主題在可用主題集中
    #         if selected_topic and selected_topic in conversation_topics:
    #             return selected_topic
    #
    #     # 如果沒有對話歷史或選擇失敗，隨機選擇
    #     return random.choice(list(conversation_topics))

    def _generate_memory_query(self, speaker, listener, dialogue_history, current_topic):
        """使用現有的 extract_keywords 函數生成單一記憶查詢"""
        if not dialogue_history:
            # 對話開始：檢索與對方的關係建立記憶
            return f"我與{listener.name}的共同經歷"

        # 提取最近3句對話的關鍵內容
        recent_turns = dialogue_history[-3:] if len(dialogue_history) >= 3 else dialogue_history
        recent_content = " ".join([turn['content'] for turn in recent_turns])

        # 基於當前話題和對話內容生成查詢
        query_parts = []

        # 1. 基礎關係查詢
        query_parts.append(f"我與{listener.name}的互動")

        # 2. 當前話題相關
        if current_topic:
            query_parts.append(f"關於{current_topic}的經驗")

        # 3. 使用現有的 extract_keywords 函數分析對話內容
        if recent_content:
            keywords = self.gpt.extract_keywords(recent_content)
            if keywords:
                # 只取前3個最相關的關鍵字
                relevant_keywords = keywords[:3]
                query_parts.append(f"涉及{' '.join(relevant_keywords)}的經歷")

        return " ".join(query_parts)


    def generate_dialogue_turn(
        self,
        persona1: Persona,
        persona2: Persona,
        current_topic: str,
        context: Dict,
        dialogue_history: List[Dict],
        starts_with_persona1: bool
    ) -> List[Dict]:
        """針對特定主題生成對話"""
        dialogue_turns = []
        is_topic_complete = False
        topic_turn_count = 0
        max_topic_turns = 20  # 放寬單一話題的最大句數上限，以延長對話

        print(f"開始討論話題: {current_topic}")

        # 保存上一個 turn 的話題完成狀態
        previous_topic_reason = None

        while not is_topic_complete and topic_turn_count < max_topic_turns:
            # 決定當前說話者和聆聽者
            speaker_is_main = starts_with_persona1 if (len(dialogue_history) + len(dialogue_turns)) % 2 == 0 else not starts_with_persona1

            # 準備話題完成信息，包含上一個 turn 的進展情況
            topic_completion_info = {
                "previous_topic_reason": previous_topic_reason  # 上一個 turn 的話題進展情況
            }

            speaker = persona1 if speaker_is_main else persona2
            listener = persona2 if speaker_is_main else persona1

            # 每次生成對話時重新檢索相關記憶
            print(f"🔍 重新檢索 {speaker.name} 的相關記憶...")

            # 生成記憶查詢
            memory_query = self._generate_memory_query(
                speaker=speaker,
                listener=listener,
                dialogue_history=dialogue_history + dialogue_turns,
                current_topic=current_topic
            )
            print(f"🔍 查詢內容: {memory_query}")

            speaker_memories = speaker.memory.get_relevant_memories(
                query=memory_query,
                limit=3,  # 進一步減少記憶數量
                current_date=context.get('time')
            )
            print(f"📝 {speaker.name} 找到 {len(speaker_memories)} 筆相關記憶")
            for i, mem in enumerate(speaker_memories[:2], 1):  # 只顯示前2筆最相關的記憶
                print(f"  {i}. {mem['description'][:60]}... (強度: {mem['emotional_intensity']:.2f})")

            # 生成對話
            content = self.gpt.dialogue_handler.generate_dialogue_turn(
                speaker=speaker,
                listener=listener,
                context=context,
                speaker_is_main=speaker_is_main,
                dialogue_history=dialogue_history + dialogue_turns,
                current_topic=current_topic,
                relevant_memories=speaker_memories
            )

            if not content:
                break

            # 記錄這句對話
            dialogue_turns.append({
                "speaker": speaker.name,
                "content": content,
                "topic": current_topic
            })

            topic_turn_count += 1

            # 使用全局的對話終止判斷（放寬條件）來決定是否結束
            end_decision = self.gpt.dialogue_handler.should_end_dialogue(
                dialogue_turns=dialogue_history + dialogue_turns,
                context=context,
                current_topic=None
            )

            # 同時保留原本的話題完成檢查作為輔助資訊（不強制）
            topic_status = self.check_topic_completion(
                dialogue_turns=dialogue_turns,
                current_topic=current_topic,
                context=context
            )
            previous_topic_reason = topic_status.get("reason", "")

            if end_decision and end_decision.get("action") == "end":
                is_topic_complete = True
                print(f"對話結束（應分析器）：{end_decision.get('reason', '')}")
            elif topic_turn_count >= max_topic_turns:
                # 達到最大句數，強制結束話題
                is_topic_complete = True
                print(f"話題 '{current_topic}' 達到最大句數限制（{max_topic_turns} 句），強制結束")

        return dialogue_turns

    def check_topic_completion(
        self,
        dialogue_turns: List[Dict],
        current_topic: str,
        context: Dict
    ) -> Dict:
        """檢查當前主題是否已完成"""
        prompt = (
            f"請檢查以下對話是否已經充分討論了主題 '{current_topic}'：\n\n"
            f"主題：{current_topic}\n\n"
            f"對話內容：\n"
        )

        for turn in dialogue_turns:
            prompt += f"{turn['speaker']}: {turn['content']}\n"

        prompt += (
            "\n請判斷：\n"
            "- 是否已經討論了這個主題\n"
            "- 對話是否達到了自然的結束點\n"
            "- 如果已經有3-5句對話且基本達成共識，就可以結束\n"
            "- 避免重複相同的內容\n"
            "- 如果出現重複表達，應該結束話題\n\n"

            "請以 JSON 格式返回：\n"
            "{\n"
            '  "completed": true/false,\n'
            '  "reason": "判斷原因"\n'
            "}\n"
        )

        response = self.gpt._call_gpt(prompt, 'topic_completion_checker', temperature=0.3)

        return response if response else {"completed": True, "reason": "無法判斷，預設完成"}

    def detect_new_topics(
        self,
        dialogue_turns: List[Dict],
        persona1: Persona,
        persona2: Persona,
        context: Dict
    ) -> Set[str]:
        """檢測對話中是否觸發了新的對話主題"""
        if not dialogue_turns:
            return set()

        # 獲取關係資訊
        relationship = persona1.get_relationship_with(persona2.name)

        prompt = (
            f"請嚴格分析以下對話，檢查是否提到了真正需要進一步討論的新主題：\n\n"
            f"{persona1.name}：{', '.join([trait.strip() for trait in persona1.innate.split('、')])}\n"
            f"{persona2.name}：{', '.join([trait.strip() for trait in persona2.innate.split('、')])}\n"
            f"關係：{relationship.get('role', '一般認識')}\n"
            f"溝通風格：{relationship.get('communication_style', '普通')}\n\n"
            f"對話內容：\n"
        )

        for turn in dialogue_turns:
            prompt += f"{turn['speaker']}: {turn['content']}\n"

        prompt += (
            "\n【新主題檢測標準】\n\n"

            "【嚴格標準】只有滿足以下所有條件的主題才能被認定為新主題：\n"
            "1. 緊急程度高：健康問題、工作危機、情感危機、重要決定、安全問題\n"
            "2. 關係影響大：關係發展、信任建立、衝突解決、關係修復\n"
            "3. 時間敏感性：約會安排、會議準備、截止日期、時間緊迫的計劃\n"
            "4. 情感價值高：重要分享、情感支持、慶祝時刻、深度交流\n"
            "5. 共同利益：合作項目、共同目標、互惠事項、團隊事務\n\n"

            "【排除條件】以下情況不應被認定為新主題：\n"
            "- 隨意提及但無實質內容的話題\n"
            "- 已經在當前對話中充分討論過的主題\n"
            "- 與雙方關係和興趣無關的瑣碎話題\n"
            "- 缺乏討論價值或無法深入的話題\n"
            "- 時機不當或不符合當前情境的主題\n"
            "- 重複或相似的主題\n"
            "- 過於細節的技術討論\n\n"

            "【檢測要求】：\n"
            "- 新主題必須具體明確，有明確的目標\n"
            "- 必須符合雙方的個性和關係狀態\n"
            "- 必須有足夠的討論價值\n"
            "- 避免過度細分主題\n"
            "- 必須時機適當，符合當前的情境\n\n"

            "如果發現符合上述嚴格標準的新主題，請以 JSON 格式返回：\n"
            "{\n"
            '  "new_topics": ["新主題1", "新主題2"]\n'
            "}\n"
            "如果沒有發現符合標準的新主題，請返回：\n"
            "{\n"
            '  "new_topics": []\n'
            "}\n"
        )

        response = self.gpt._call_gpt(prompt, 'new_topic_detector', temperature=0.3)

        if response and 'new_topics' in response:
            return set(response['new_topics'])
        else:
            return set()

    def _compose_dialogue_result(self, dialogue_turns: List, context: Dict) -> Dict:
        """組合完整對話結果"""
        content = [f"{turn['speaker']}: {turn['content']}" for turn in dialogue_turns]

        participants = [dialogue_turns[0]['speaker'], dialogue_turns[1]['speaker']]

        # 提取所有討論過的主題
        discussed_topics = set()
        for turn in dialogue_turns:
            if 'topic' in turn and turn['topic']:
                discussed_topics.add(turn['topic'])

        # # 提取關鍵字
        # keywords = self.gpt.keyword_handler.extract(
        #     content,
        #     {
        #         'type': 'dialogue',
        #         'related_people': participants,
        #         'context': context
        #     }
        # )

        # # 計算重要性分數
        # poignancy = self.gpt.poignancy_handler.calculate(content)

        return {
            'type': 'dialogue',
            'participants': participants,
            'content': content,
            'topics': list(discussed_topics),  # 加入討論過的主題列表
            # 'keywords': keywords,
            # 'poignancy': poignancy,
            'context': context
        }