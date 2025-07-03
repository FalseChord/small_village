from typing import Dict, List, Optional, Set
from datetime import datetime
import random
from .persona import SecondaryPersona, MainPersona

class DialogueGenerator:
    def __init__(self, gpt_interface):
        self.gpt = gpt_interface
        
    def generate_daily_dialogues(
        self,
        main_persona: MainPersona,
        secondary_personas: Dict[str, SecondaryPersona],
        current_date: datetime
    ) -> List[Dict]:
        """生成當日對話"""
        dialogues = []
        
        # 隨機選擇1-3個次要人格進行對話
        interaction_count = random.randint(1, 1) # 目前設定為一個人
        selected_personas = random.sample(list(secondary_personas.items()), interaction_count)
        
        for name, persona in selected_personas:
            # 獲取相關記憶作為對話上下文
            recent_memories = main_persona.memory.get_relevant_memories(
                query=f"與{name}相關的記憶",
                limit=3
            )
            
            dialogue = self.generate_dialogue(
                main_persona=main_persona,
                secondary_persona=persona,
                context={
                    'time': current_date,
                    'occasion': "日常互動"
                },
                recent_memories=recent_memories
            )
            
            if dialogue:
                dialogues.append(dialogue)
                
        return dialogues
        
    def generate_dialogue(
        self,
        main_persona: MainPersona,
        secondary_persona: SecondaryPersona,
        context: Dict,
        recent_memories: List
    ) -> Optional[Dict]:
        """生成完整對話"""
        dialogue_turns = []
        is_dialogue_complete = False
        
        # 生成初始對話主題集
        conversation_topics = self.generate_conversation_topics(
            main_persona=main_persona,
            secondary_persona=secondary_persona,
            context=context,
            recent_memories=recent_memories
        )
        
        print(f"初始對話主題集: {conversation_topics}")
        
        # 隨機決定第一個說話者
        starts_with_main = random.choice([True, False])
        
        while not is_dialogue_complete and conversation_topics:
            # 從主題集中選擇一個主題進行對話
            current_topic = self.select_topic_from_set(
                conversation_topics=conversation_topics,
                dialogue_history=dialogue_turns
            )
            print(f"選擇對話主題: {current_topic}")
            
            # 從主題集中移除當前選中的主題
            conversation_topics.discard(current_topic)
            
            print(f"選擇對話主題: {current_topic}")
            print(f"剩餘主題: {conversation_topics}")
            
            # 針對選中的主題進行對話
            dialogue_turn = self.generate_dialogue_turn(
                main_persona=main_persona,
                secondary_persona=secondary_persona,
                current_topic=current_topic,
                context=context,
                dialogue_history=dialogue_turns,
                starts_with_main=starts_with_main
            )
            
            # 將主題對話加入到總對話中
            dialogue_turns.extend(dialogue_turn)
            
            # 檢查是否應該結束整個對話
            if not conversation_topics:
                is_dialogue_complete = True
                print("所有主題已完成，結束對話")
            else:
                # 檢查是否有新主題被觸發
                new_topics = self.detect_new_topics(
                    dialogue_turns=dialogue_turn,
                    main_persona=main_persona,
                    secondary_persona=secondary_persona,
                    context=context
                )
                
                if new_topics:
                    conversation_topics.update(new_topics)
                    print(f"檢測到新主題: {new_topics}")
                    print(f"更新後的主題集: {conversation_topics}")
        
        if dialogue_turns:
            return self._compose_dialogue_result(dialogue_turns, context)
        return None
    
    def generate_conversation_topics(
        self,
        main_persona: MainPersona,
        secondary_persona: SecondaryPersona,
        context: Dict,
        recent_memories: List
    ) -> Set[str]:
        """生成初始對話主題集"""
        prompt = (
            f"請根據以下資訊，為{main_persona.name}和{secondary_persona.name}生成3-5個對話主題：\n\n"
            f"主人格資料：\n"
            f"姓名：{main_persona.name}\n"
            f"個性：{', '.join(main_persona.innate_traits)}\n"
            f"當前狀態：{main_persona.get_current_state()}\n"
            f"背景：{main_persona.biography}\n"
        )
        
        # 加入關係資訊
        relationship = main_persona.get_relationship_with(secondary_persona.name)
        prompt += (
            f"與{secondary_persona.name}的關係：{relationship.get('role', '一般認識')}\n"
            f"溝通風格：{relationship.get('communication_style', '普通')}\n"
            f"對{secondary_persona.name}的顧慮：{relationship.get('concerns', '無特別顧慮')}\n"
        )
        
        prompt += (
            f"\n次人格資料：\n"
            f"姓名：{secondary_persona.name}\n"
            f"個性：{', '.join(secondary_persona.innate_traits)}\n"
            f"背景：{secondary_persona.biography}\n"
            f"對{main_persona.name}的期待：{secondary_persona.relationship_with_main['expectations']}\n"
            f"對{main_persona.name}的顧慮：{secondary_persona.relationship_with_main['concerns']}\n"
        )
        
        # 加入相關記憶
        if recent_memories:
            prompt += "\n相關記憶：\n"
            for memory in recent_memories:
                prompt += f"- {memory['description']}\n"
        
        prompt += (
            f"\n對話情境：\n"
            f"時間：{context.get('time', '未指定')}\n"
            f"場合：{context.get('occasion', '未指定')}\n\n"
            
            "請生成1-3個對話主題，每個主題必須嚴格符合以下條件：\n\n"
            
            "【重要性門檻機制】主題必須滿足以下條件之一：\n"
            "1. 緊急程度高（如：健康問題、工作危機、情感危機、重要決定）\n"
            "2. 與雙方關係有影響（如：關係發展、信任建立、衝突解決）\n"
            "3. 時間敏感性強（如：約會安排、會議準備、截止日期）\n"
            "4. 情感價值高（如：重要分享、情感支持、慶祝時刻）\n"
            "5. 共同利益相關（如：合作項目、共同目標、互惠事項）\n\n"
            
            "【人格驅動機制】根據雙方個性調整主題：\n"
            f"- {main_persona.name}的個性：{', '.join(main_persona.innate_traits)}\n"
            f"- {secondary_persona.name}的個性：{', '.join(secondary_persona.innate_traits)}\n"
            f"- 關係親密度：{relationship.get('role', '一般認識')}\n"
            "• 內向人格傾向深入討論少數主題，避免過於廣泛的話題\n"
            "• 外向人格可能涉及更多相關主題，但也要有邏輯關聯\n"
            "• 親密關係允許更多個人和情感主題\n"
            "• 正式關係傾向實用性和目標導向的主題\n\n"
            
            "【主題品質要求】：\n"
            "1. 能產生有意義的對話和互動\n"
            "2. 考慮雙方的背景和關注點\n"
            "3. 時機適當：符合當前的情境和關係狀態\n\n"
            
            "請以 JSON 格式返回：\n"
            "{\n"
            '  "topics": ["主題1", "主題2", ...]\n'
            "}\n"
        )
        
        response = self.gpt._call_gpt(prompt, 'topic_generator', temperature=0.7)
        
        if response and 'topics' in response:
            return set(response['topics'])
        else:
            # 預設主題
            return {"日常問候", "分享近況", "討論共同興趣"}
    
    def select_topic_from_set(
        self,
        conversation_topics: Set[str],
        dialogue_history: List[Dict]
    ) -> str:
        """從主題集中選擇一個主題"""
        if not conversation_topics:
            return "日常閒聊"
        
        # 如果有對話歷史，考慮對話的連貫性
        if dialogue_history:
            prompt = (
                f"請從以下主題集中選擇一個最適合繼續當前對話的主題：\n\n"
                f"可用主題：{list(conversation_topics)}\n\n"
                f"當前對話：\n"
            )
            
            for turn in dialogue_history[-3:]:  # 只考慮最近3句
                prompt += f"{turn['speaker']}: {turn['content']}\n"
            
            prompt += (
                "\n請選擇一個能夠自然延續當前對話的主題，或者選擇一個新的主題開始新的討論。\n"
                "請直接返回選擇的主題名稱。\n"
            )
            
            response = self.gpt._call_gpt(prompt, 'topic_selector', temperature=0.5)
            selected_topic = response.strip() if response else list(conversation_topics)[0]
            
            # 確保選擇的主題在可用主題集中
            if selected_topic in conversation_topics:
                return selected_topic
        
        # 如果沒有對話歷史或選擇失敗，隨機選擇
        return random.choice(list(conversation_topics))
    
    def generate_dialogue_turn(
        self,
        main_persona: MainPersona,
        secondary_persona: SecondaryPersona,
        current_topic: str,
        context: Dict,
        dialogue_history: List[Dict],
        starts_with_main: bool
    ) -> List[Dict]:
        """針對特定主題生成對話"""
        dialogue_turns = []
        is_topic_complete = False
        topic_turn_count = 0
        max_topic_turns = 8  # 每個主題最多8句對話
        
        while not is_topic_complete and topic_turn_count < max_topic_turns:
            # 決定當前說話者和聆聽者
            speaker_is_main = starts_with_main if (len(dialogue_history) + len(dialogue_turns)) % 2 == 0 else not starts_with_main
            speaker = main_persona if speaker_is_main else secondary_persona
            listener = secondary_persona if speaker_is_main else main_persona
            
            # 生成說話意圖
            intent = self.gpt.dialogue_handler.generate_speaking_intent(
                speaker=speaker,
                listener=listener,
                context=context,
                speaker_is_main=speaker_is_main,
                dialogue_history=dialogue_history + dialogue_turns,
                current_topic=current_topic
            )
            
            if not intent:
                break
                
            # 生成這句對話
            content = self.gpt.dialogue_handler.generate_dialogue_turn(
                speaker=speaker,
                listener=listener,
                intent=intent,
                context=context,
                speaker_is_main=speaker_is_main,
                dialogue_history=dialogue_history + dialogue_turns,
                current_topic=current_topic
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
            
            # 檢查當前主題是否完成
            topic_status = self.check_topic_completion(
                dialogue_turns=dialogue_turns,
                current_topic=current_topic,
                context=context
            )
            
            if topic_status["completed"]:
                is_topic_complete = True
                print(f"主題 '{current_topic}' 已完成")
        
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
            "1. 是否已經充分討論了這個主題\n"
            "2. 對話是否達到了自然的結束點\n"
            "3. 是否還有需要進一步討論的內容\n\n"
            
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
        main_persona: MainPersona,
        secondary_persona: SecondaryPersona,
        context: Dict
    ) -> Set[str]:
        """檢測對話中是否觸發了新的對話主題"""
        if not dialogue_turns:
            return set()
        
        # 獲取關係資訊
        relationship = main_persona.get_relationship_with(secondary_persona.name)
        
        prompt = (
            f"請嚴格分析以下對話，檢查是否提到了真正需要進一步討論的新主題：\n\n"
            f"主人格：{main_persona.name}（{', '.join(main_persona.innate_traits)}）\n"
            f"次人格：{secondary_persona.name}（{', '.join(secondary_persona.innate_traits)}）\n"
            f"關係：{relationship.get('role', '一般認識')}\n"
            f"溝通風格：{relationship.get('communication_style', '普通')}\n\n"
            f"對話內容：\n"
        )
        
        for turn in dialogue_turns:
            prompt += f"{turn['speaker']}: {turn['content']}\n"
        
        prompt += (
            "\n【新主題檢測標準】\n\n"
            
            "【重要性門檻機制】只有滿足以下條件之一的主題才能被認定為新主題：\n"
            "1. 緊急程度高：健康問題、工作危機、情感危機、重要決定、安全問題\n"
            "2. 關係影響大：關係發展、信任建立、衝突解決、關係修復\n"
            "3. 時間敏感性：約會安排、會議準備、截止日期、時間緊迫的計劃\n"
            "4. 情感價值高：重要分享、情感支持、慶祝時刻、深度交流\n"
            "5. 共同利益：合作項目、共同目標、互惠事項、團隊事務\n"
            "6. 邏輯延伸：與當前主題高度相關的自然延伸，有明確的討論價值\n\n"
            
            "【人格驅動機制】根據雙方個性調整主題：\n"
            f"- {main_persona.name}的個性：{', '.join(main_persona.innate_traits)}\n"
            f"- {secondary_persona.name}的個性：{', '.join(secondary_persona.innate_traits)}\n"
            f"- 關係親密度：{relationship.get('role', '一般認識')}\n"
            "• 內向人格傾向深入討論少數主題，避免過於廣泛的話題\n"
            "• 外向人格可能涉及更多相關主題，但也要有邏輯關聯\n"
            "• 親密關係允許更多個人和情感主題\n"
            "• 正式關係傾向實用性和目標導向的主題\n\n"

            "【排除條件】以下情況不應被認定為新主題：\n"
            "1. 隨意提及但無實質內容的話題\n"
            "2. 已經在當前對話中充分討論過的主題\n"
            "3. 與雙方關係和興趣無關的瑣碎話題\n"
            "4. 缺乏討論價值或無法深入的話題\n"
            "5. 時機不當或不符合當前情境的主題\n\n"

            "【檢測要求】：\n"
            "1. 新主題必須具體明確，有明確的目標\n"
            "2. 必須符合雙方的個性和關係狀態\n"
            "3. 必須時機適當，符合當前的情境\n\n"
            
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
        
        # 提取關鍵字
        keywords = self.gpt.keyword_handler.extract(
            content,
            {
                'type': 'dialogue',
                'related_people': participants,
                'context': context
            }
        )
        
        # 計算重要性分數
        poignancy = self.gpt.poignancy_handler.calculate(content)

        return {
            'type': 'dialogue',
            'participants': participants,
            'content': content,
            'topics': list(discussed_topics),  # 加入討論過的主題列表
            'keywords': keywords,
            'poignancy': poignancy,
            'context': context
        }