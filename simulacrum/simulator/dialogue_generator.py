from typing import Dict, List, Optional
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
        interaction_count = random.randint(1, 1)
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
        
        # 隨機決定第一個說話者
        starts_with_main = random.choice([True, False])
        
        # 初始化當前話題
        current_topic = self.gpt.dialogue_handler.select_conversation_topic(
            speaker=main_persona,
            listener=secondary_persona,
            context=context,
            dialogue_history=dialogue_turns
        )
        
        while not is_dialogue_complete:
            # 決定當前說話者和聆聽者
            speaker_is_main = starts_with_main if len(dialogue_turns) % 2 == 0 else not starts_with_main
            speaker = main_persona if speaker_is_main else secondary_persona
            listener = secondary_persona if speaker_is_main else main_persona
            
            # 生成說話意圖
            intent = self.gpt.dialogue_handler.generate_speaking_intent(
                speaker=speaker,
                listener=listener,
                context=context,
                speaker_is_main=speaker_is_main,
                dialogue_history=dialogue_turns,
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
                dialogue_history=dialogue_turns,
                current_topic=current_topic
            )
            
            if not content:
                break
                
            # 記錄這句對話
            dialogue_turns.append({
                "speaker": speaker.name,
                "content": content
            })

            print(f"dialogue_turns: {len(dialogue_turns)}")
            
            # 檢查對話是否應該結束或變更話題
            dialogue_status = self.gpt.dialogue_handler.should_end_dialogue(
                dialogue_turns=dialogue_turns,
                context=context
            )
            
            if dialogue_status["action"] == "end":
                is_dialogue_complete = True
            elif dialogue_status["action"] == "change_topic":
                # 生成新話題
                current_topic = self.gpt.dialogue_handler.select_conversation_topic(
                    speaker=speaker,
                    listener=listener,
                    context=context,
                    dialogue_history=dialogue_turns
                )
        
        if dialogue_turns:
            return self._compose_dialogue_result(dialogue_turns, context)
        return None
        
    def _compose_dialogue_result(self, dialogue_turns: List, context: Dict) -> Dict:
        """組合完整對話結果"""
        content = [f"{turn['speaker']}: {turn['content']}" for turn in dialogue_turns]
        
        participants = [dialogue_turns[0]['speaker'], dialogue_turns[1]['speaker']]
        
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
            'keywords': keywords,
            'poignancy': poignancy,
            'context': context
        }