from typing import Dict, List, Optional, Set
from datetime import datetime
import random
from .persona import Persona
from .topic_generator import TopicGenerator
from .intent_generator import IntentGenerator
from .dialogue_context_generator import DialogueContextGenerator

class DialogueGenerator:
    def __init__(self, gpt_interface):
        self.gpt = gpt_interface
        self.topic_generator = TopicGenerator(gpt_interface)
        self.intent_generator = IntentGenerator(gpt_interface)
        self.context_generator = DialogueContextGenerator(gpt_interface)
        self.min_turns_per_topic = 8  # 每個主題最少8句對話
        self.max_turns_per_topic = 20  # 每個主題最多20句對話
        self.max_topics = 3  # 3個主題後結束對話

    def generate_daily_dialogues(
        self,
        all_personas: Dict[str, Persona],
        current_date: datetime
    ) -> List[Dict]:
        """生成當日對話：固定讓羅以青與李承翰、王淑華各聊天一次"""
        dialogues = []

        # 固定配對：羅以青 vs 李承翰、羅以青 vs 王淑華
        required_names = ["羅以青", "李承翰", "王淑華"]
        missing_names = [name for name in required_names if name not in all_personas]

        if missing_names:
            raise ValueError(f"缺少必要的角色: {missing_names}。目前可用的角色: {list(all_personas.keys())}")

        # 固定生成兩個對話
        # 1. 羅以青 vs 李承翰
        dialogue1 = self.generate_dialogue(
            persona1=all_personas["羅以青"],
            persona2=all_personas["李承翰"],
            current_date=current_date
        )
        if dialogue1:
            dialogues.append(dialogue1)

        # 2. 羅以青 vs 王淑華
        dialogue2 = self.generate_dialogue(
            persona1=all_personas["羅以青"],
            persona2=all_personas["王淑華"],
            current_date=current_date
        )
        if dialogue2:
            dialogues.append(dialogue2)

        return dialogues

    def generate_dialogue(
        self,
        persona1: Persona,
        persona2: Persona,
        current_date: datetime
    ) -> Optional[Dict]:
        """生成完整對話（支援多主題）"""
        all_personas = {persona1.name: persona1, persona2.name: persona2}
        dialogue_topics = []  # 儲存所有主題的對話
        topic_count = 0
        all_dialogue_history = []  # 累積所有對話歷史，跨主題參考

        # 隨機決定第一個說話者
        starts_with_persona1 = random.choice([True, False])

        print(f"🎯 開始生成多主題對話，最多 {self.max_topics} 個主題")
        
        # 0. 生成對話情境
        dialogue_context = self.context_generator.generate_dialogue_context(
            persona1=persona1,
            persona2=persona2,
            current_time=current_date
        )
        
        if dialogue_context:
            print(f"🎭 對話情境: {dialogue_context['description']}")
            print(f"📂 類別: {dialogue_context['context_category']}")
        else:
            print("⚠️ 情境生成失敗，使用預設情境")
            dialogue_context = {
                'context_category': '日常偶遇',
                'description': f"{persona1.name}和{persona2.name}偶遇並開始聊天"
            }
        
        while topic_count < self.max_topics:
            topic_count += 1
            print(f"\n=== 主題 {topic_count} ===")
            
            # 1. 生成主題
            recent_three_turns = all_dialogue_history[-3:] if len(all_dialogue_history) >= 3 else all_dialogue_history
            current_topic = self.topic_generator.generate_topic_from_memories(
                personas=all_personas,
                dialogue_context=dialogue_context,
                recent_dialogue_turns=recent_three_turns
            )
            
            if not current_topic:
                print("⚠️ 無法生成新主題，結束對話")
                break
                
            print(f"📝 主題: {current_topic}")
            
            # 2. 生成該主題的對話
            topic_dialogue = self.generate_dialogue_turn(
                persona1=persona1,
                persona2=persona2,
                current_topic=current_topic,
                dialogue_history=all_dialogue_history,  # 傳入累積的對話歷史
                starts_with_persona1=starts_with_persona1,
                dialogue_context=dialogue_context,
                current_date=current_date
            )

            # 取得回傳的 (純對話回合, 情緒紀錄)
            topic_turns, topic_emotion_records = topic_dialogue

            if topic_turns:
                dialogue_topics.append({
                    'topic': current_topic,
                    'turns': topic_turns,
                    'emotion_records': topic_emotion_records
                })
                all_dialogue_history.extend(topic_turns)
                print(f"✅ 主題 {topic_count} 完成，共 {len(topic_turns)} 句對話")
                print(f"📚 累積對話歷史：{len(all_dialogue_history)} 句")
            else:
                print(f"⚠️ 主題 {topic_count} 生成失敗，跳過")
            
            # 4. 檢查是否應該結束對話
            if topic_count >= 3:  # 3個主題後結束對話
                print(f"🏁 完成 {topic_count} 個主題，結束對話")
                break
        
        if dialogue_topics:
            return self._compose_multi_topic_dialogue_result(dialogue_topics, dialogue_context)
        return None

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
        dialogue_history: List[Dict],
        starts_with_persona1: bool,
        dialogue_context: Dict = None,
        current_date: datetime = None
    ) -> List[Dict]:
        """針對特定主題生成對話"""
        dialogue_turns = []
        topic_emotion_records = []  # 收集本主題內的情緒紀錄
        turn_count = 0
        last_end_reason = ""
        
        print(f"🗣️ 開始生成主題對話：{current_topic}，最少 {self.min_turns_per_topic} 句")
        
        while True:
            # 決定當前說話者
            speaker_is_persona1 = starts_with_persona1 if turn_count % 2 == 0 else not starts_with_persona1
            speaker = persona1 if speaker_is_persona1 else persona2
            listener = persona2 if speaker_is_persona1 else persona1
            
            # 組合完整的對話歷史
            complete_dialogue_history = dialogue_history + dialogue_turns

            # 根據目前對話與上一輪未結束原因，為本句即時生成說話意圖
            end_reason = last_end_reason

            # 使用意圖產生器逐句模式
            intent_prompt = self.intent_generator._create_intent_prompt(
                topic=current_topic,
                turn_speaker=speaker,
                turn_listener=listener,
                dialogue_history=complete_dialogue_history,
                end_reason=end_reason,
                dialogue_context=dialogue_context
            )
            intent_resp = self.gpt._call_gpt(intent_prompt, 'intent_generator', temperature=0.7) or {}
            speaker_intent = intent_resp.get('intent', "進行友好的對話")
            
            # 獲取相關記憶
            memory_query = self._generate_memory_query(
                speaker=speaker,
                listener=listener,
                dialogue_history=complete_dialogue_history,
                current_topic=current_topic
            )
            print(f"🔍 記憶查詢: {memory_query}")
            
            speaker_memories = speaker.memory.get_relevant_memories(
                query=memory_query,
                limit=3,
                current_date=current_date
            )
            print(f"📝 {speaker.name} 找到 {len(speaker_memories)} 筆相關記憶")

            # 生成對話內容
            dialogue_result = self.gpt.dialogue_handler.generate_dialogue_turn(
                speaker=speaker,
                listener=listener,
                dialogue_history=complete_dialogue_history,
                current_topic=current_topic,
                relevant_memories=speaker_memories,
                speaker_intent=speaker_intent,
                dialogue_context=dialogue_context
            )

            # 解析對話結果
            if isinstance(dialogue_result, dict):
                content = dialogue_result.get('content', '')
                self_emotion = dialogue_result.get('self_emotion', '')
                perceived_emotion = dialogue_result.get('perceived_emotion', '')
            else:
                # 向後相容：如果返回的是字串
                content = dialogue_result if dialogue_result else ''
                self_emotion = ''
                perceived_emotion = ''

            if not content:
                break

            turn_data = {
                "speaker": speaker.name,
                "content": content,
                "intent": speaker_intent,  # 保存每句的意圖
                "self_emotion": self_emotion,
                "perceived_emotion": perceived_emotion
            }
            
            dialogue_turns.append(turn_data)
            
            turn_count += 1
            
            # 避免無限循環
            if turn_count >= self.max_turns_per_topic:
                print(f"⚠️ 達到最大句數限制（{self.max_turns_per_topic} 句），結束主題對話")
                break

            # 未達最小句數：呼叫分析器取得 reason，但強制繼續（不結束）
            if turn_count < self.min_turns_per_topic:
                end_decision = self.gpt.dialogue_handler.should_end_dialogue(
                    dialogue_turns=dialogue_turns,
                    current_topic=current_topic
                ) or {"action": "continue", "reason": ""}
                # 若分析器建議結束，不送 end_reason（避免矛盾）；否則送 reason
                if end_decision.get('action') == 'end':
                    last_end_reason = ""
                else:
                    last_end_reason = end_decision.get("reason", "")
                # 即使分析器建議結束，也強制繼續（達到最小句數）
                continue

            # 已達最小句數：呼叫分析器決定是否結束，但不再送 end_reason 給下一句
            end_decision = self.gpt.dialogue_handler.should_end_dialogue(
                dialogue_turns=dialogue_turns,
                current_topic=current_topic
            ) or {"action": "continue", "reason": ""}
            last_end_reason = ""  # 達到最小句數後不送 end_reason
            if end_decision.get('action') == 'end':
                break
        
        # 返回 (純對話回合, 情緒紀錄)
        return dialogue_turns, topic_emotion_records
    
    def _compose_multi_topic_dialogue_result(self, dialogue_topics: List[Dict], dialogue_context: Dict = None) -> Dict:
        """組合多主題對話結果"""
        all_participants = set()
        topics_info = []
        content_lines = []  # 純對話格式（"人名：對話"）
        total_turns = 0
        
        for topic_data in dialogue_topics:
            # 收集該主題的所有回合資訊（包含意圖和情緒紀錄）
            topic_turns_info = []
            for turn in topic_data['turns']:
                turn_info = {
                    'speaker': turn['speaker'],
                    'content': turn['content'],
                    'intent': turn.get('intent', '')  # 包含意圖
                }
                # 加入情緒紀錄（self_emotion 和 perceived_emotion）
                if 'self_emotion' in turn:
                    turn_info['self_emotion'] = turn['self_emotion']
                if 'perceived_emotion' in turn:
                    turn_info['perceived_emotion'] = turn['perceived_emotion']
                topic_turns_info.append(turn_info)

                # 生成純對話格式（不包含情緒紀錄）
                content_lines.append(f"{turn['speaker']}: {turn['content']}")

                all_participants.add(turn['speaker'])
                total_turns += 1

            topic_info = {
                'topic': topic_data['topic'],
                'turn_count': len(topic_data['turns']),
                'turns': topic_turns_info  # 包含完整回合資訊（含意圖和情緒紀錄）
            }
            topics_info.append(topic_info)
        
        return {
            'type': 'dialogue',
            'participants': list(all_participants),
            'content': content_lines,  # 純對話格式（"人名：對話"），不含情緒紀錄
            'topics': topics_info,  # 包含主題、回合資訊（含意圖）和情緒紀錄
            'dialogue_context': dialogue_context,
            'total_topics': len(dialogue_topics),
            'total_turns': total_turns
        }

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

        participants = []
        if len(dialogue_turns) >= 1:
            participants.append(dialogue_turns[0]['speaker'])
        if len(dialogue_turns) >= 2:
            participants.append(dialogue_turns[1]['speaker'])

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