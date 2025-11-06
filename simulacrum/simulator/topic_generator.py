import random
from typing import Dict, List, Optional, Set
from datetime import datetime
from .persona import Persona

class TopicGenerator:
    def __init__(self, gpt_interface):
        self.gpt = gpt_interface
        self.discussed_topics = []  # 追蹤已討論的主題
        
    def generate_topic_from_memories(
        self,
        personas: Dict[str, Persona],
        dialogue_context: Dict = None,
        recent_dialogue_turns: List[Dict] = None
    ) -> Optional[str]:
        """從記憶中生成對話主題
        
        Args:
            personas: 參與對話的角色字典
            current_date: 當前日期
            
        Returns:
            生成的主題字串，如果失敗則返回 None
        """
        # 收集所有角色的記憶
        all_memories = []
        for persona_name, persona in personas.items():
            persona_memories = persona.memory.get_all_memories()
            # 為每個記憶添加所屬角色資訊
            for memory in persona_memories:
                memory_with_owner = memory.copy() if isinstance(memory, dict) else memory
                if isinstance(memory_with_owner, dict):
                    memory_with_owner['owner'] = persona_name
                all_memories.append(memory_with_owner)
        
        if not all_memories:
            print("⚠️ 沒有找到任何記憶，使用預設主題")
            return "日常生活分享"
        
        # 由 GPT 從所有記憶中挑選與最近三句對話有關的記憶（直接選1條）
        selected_memories = self._select_memories_for_topic(all_memories, recent_dialogue_turns, limit=1)
        
        # 使用 GPT 生成主題
        topic = self._generate_topic_with_gpt(selected_memories, personas, dialogue_context)
        
        if topic:
            self.discussed_topics.append(topic)
            return topic
        else:
            # 如果生成失敗，使用備用主題
            print(f"⚠️ 主題生成失敗，使用備用主題")
            return self._generate_fallback_topic()
    

    def _select_memories_for_topic(self, all_memories: List[Dict], recent_dialogue_turns: List[Dict], limit: int = 5) -> List[Dict]:
        """挑選作為主題依據的記憶

        - 若有最近對話：用 GPT 從所有記憶挑與最近三句相關的1條
        - 若無最近對話：從所有記憶中隨機挑1條
        """
        if not recent_dialogue_turns:
            # 隨機挑選一條記憶，增加多樣性
            valid_memories = [m for m in all_memories if isinstance(m, dict)]
            if not valid_memories:
                return []

            selected = random.choice(valid_memories)
            # 確保有 owner 欄位
            if 'owner' not in selected:
                selected = selected.copy()
                selected['owner'] = selected.get('owner', 'unknown')

            return [{
                'description': selected.get('description', ''),
                'type': selected.get('type', ''),
                'owner': selected.get('owner', 'unknown')
            }]

        # 準備最近三句對話（忽略沒有 speaker/content 的輔助節點，如情緒紀錄 _meta 節點）
        safe_turns = [
            turn for turn in recent_dialogue_turns
            if isinstance(turn, dict) and 'speaker' in turn and 'content' in turn
        ]
        recent_lines = [f"{turn['speaker']}: {turn['content']}" for turn in safe_turns]
        # 若篩完後沒有可用對話，退回隨機記憶模式
        if not recent_lines:
            valid_memories = [m for m in all_memories if isinstance(m, dict)]
            if not valid_memories:
                return []
            selected = random.choice(valid_memories)
            if 'owner' not in selected:
                selected = selected.copy()
                selected['owner'] = selected.get('owner', 'unknown')
            return [{
                'description': selected.get('description', ''),
                'type': selected.get('type', ''),
                'owner': selected.get('owner', 'unknown')
            }]

        recent_text = "\n".join(recent_lines)

        # 準備記憶清單（只傳必要欄位，避免提示詞過長）
        memory_summaries = []
        for m in all_memories:  # 安全上限，避免過長
            if isinstance(m, dict):
                memory_summaries.append({
                    'description': m.get('description', '')
                })

        prompt = (
            f"請閱讀最近三句對話，以及提供的記憶清單，挑選{limit}條與這三句對話\n"
            "在主題、人物、事件、地點或關鍵概念上『有關聯』的記憶。\n\n"
            f"最近對話：\n{recent_text}\n\n"
            f"記憶清單：\n" + "\n".join([f"- {m['description']}" for m in memory_summaries]) + "\n\n"
            "【挑選指引】\n"
            "- 不需要完美匹配，可以選擇間接相關的記憶\n"
            "- 可以選擇背景故事、延伸話題或相關經驗\n"
            "- 優先選擇有趣、有討論價值的記憶\n"
            "- 如果沒有明顯相關的，可以選擇任何一條你覺得有趣的\n\n"
            "請直接返回選中的記憶描述文字：\n"
        )

        resp = self.gpt._call_gpt(prompt, 'topic_related_memory_selector', temperature=0.6)
        if not resp or not isinstance(resp, str):
            return []

        selected_memory = {
            'description': resp.strip(),
            'type': 'episodic',
            'owner': 'unknown'
        }
        return [selected_memory]
    
    def _generate_topic_with_gpt(
        self,
        selected_memories: List,
        personas: Dict[str, Persona],
        dialogue_context: Dict = None
    ) -> Optional[str]:
        """使用 GPT 生成對話主題"""
        
        # 準備記憶描述
        memory_descriptions = []
        for memory in selected_memories:
            if isinstance(memory, dict):
                owner = memory.get('owner', '未知')
                description = memory.get('description', '')
                memory_type = memory.get('type', '')
                memory_descriptions.append(f"[{owner}] {memory_type}: {description}")
        
        # 準備角色資訊
        persona_info = []
        for name, persona in personas.items():
            persona_info.append(f"{name}: {persona.innate}")
        
        # 準備已討論主題
        discussed_topics_str = "、".join(self.discussed_topics) if self.discussed_topics else "無"
        
        # 準備情境資訊
        context_info = ""
        if dialogue_context:
            context_info = (
                f"對話情境：{dialogue_context.get('description', '未知')}\n\n"
            )
        
        prompt = (
            f"請根據以下記憶和角色資訊，生成一個適合朋友日常聊天的主題：\n\n"
            f"參與角色：\n" + "\n".join(persona_info) + "\n\n"
            f"相關記憶：\n" + "\n".join(memory_descriptions) + "\n\n"
            f"已討論過的主題：{discussed_topics_str}\n\n"
            + context_info +
            f"請生成一個新的對話主題，要求：\n"
            f"1. 基於提供的記憶內容\n"
            f"2. 適合朋友間輕鬆聊天\n"
            f"3. 與已討論主題不同\n"
            f"4. 簡潔自然，像朋友會聊的話題\n"
            f"5. 避免過於正式或複雜的內容\n"
            f"6. 考慮當前對話情境的類別和描述\n\n"
            f"範例：\n"
            f"- 最近工作怎樣\n"
            f"- 看什麼電影\n"
            f"- 家裡還好嗎\n"
            f"- 最近有什麼趣事\n\n"
            f"避免的複雜範例：\n"
            f"- 暑假你打算怎麼安排教學或暑期班？會不會試著做短影片或IG直播教學？\n"
            f"- 最近有沒有學生說過讓你會心一笑的答案或趣事？\n\n"
            f"請以 JSON 格式返回：\n"
            f'{{\n'
            f'  "topic": "生成的主題"\n'
            f'}}\n'
        )
        
        response = self.gpt._call_gpt(prompt, 'topic_generator', temperature=0.8)
        
        if response and 'topic' in response:
            return response['topic']
        else:
            print("⚠️ GPT 主題生成失敗")
            return None
    
    
    def _generate_fallback_topic(self) -> str:
        """生成備用主題（當主要生成失敗時）"""
        fallback_topics = [
            "最近的生活變化",
            "對未來的想法",
            "印象深刻的經歷",
            "最近的感受",
            "生活中的小確幸",
            "遇到的挑戰",
            "學到的新事物",
            "對某件事的看法"
        ]
        
        # 選擇一個還沒討論過的備用主題
        available_topics = [topic for topic in fallback_topics if topic not in self.discussed_topics]
        
        if available_topics:
            selected_topic = random.choice(available_topics)
            self.discussed_topics.append(selected_topic)
            return selected_topic
        else:
            # 如果所有備用主題都用過了，重置討論歷史
            self.discussed_topics = []
            selected_topic = random.choice(fallback_topics)
            self.discussed_topics.append(selected_topic)
            return selected_topic
    
    def get_discussed_topics(self) -> List[str]:
        """獲取已討論的主題列表"""
        return self.discussed_topics.copy()
    
    def reset_discussed_topics(self):
        """重置已討論主題列表"""
        self.discussed_topics = []
