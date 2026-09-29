"""宠物技能学习 - 带7个bug"""
from dataclasses import dataclass, field
import random

@dataclass
class PetSkill:
    sid: str
    name: str
    pet_type: str
    level: int
    locked: bool

class PetSkillSystem:
    def __init__(self):
        self.pet_skills = {}
        self.pet_type = {}

    def learn(self, pet_id, skill_id, skill_book):
        # bug1: 不看宠物类型
        if pet_id not in self.pet_skills:
            self.pet_skills[pet_id] = []
        # bug2: 随机覆盖
        if len(self.pet_skills[pet_id]) >= 4:
            idx = random.randint(0, 3)
            self.pet_skills[pet_id][idx] = PetSkill(skill_id, skill_id, "any", 1, False)
        else:
            self.pet_skills[pet_id].append(PetSkill(skill_id, skill_id, "any", 1, False))
        return True

    def upgrade(self, pet_id, skill_id, exp):
        # bug3: 只需经验
        for s in self.pet_skills.get(pet_id, []):
            if s.sid == skill_id:
                s.level += 1
                return True
        return False

    def get_trigger_chance(self, pet_id, skill_id):
        # bug5: 固定概率
        return 0.3

    def can_learn_duplicate(self, pet_id, stat_type):
        # bug6: 可重复
        return True
