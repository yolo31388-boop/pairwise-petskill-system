"""宠物技能学习系统"""
from dataclasses import dataclass

# 技能定义: skill_id -> 要求的宠物类型 / 属性类型(同类型互斥)
SKILL_DEFS = {
    "bite":       {"pet_type": "physical", "stat_type": "attack"},
    "claw":       {"pet_type": "physical", "stat_type": "attack"},
    "fireball":   {"pet_type": "magic",    "stat_type": "attack"},
    "heal":       {"pet_type": "magic",    "stat_type": "hp"},
    "iron_skin":  {"pet_type": "any",      "stat_type": "defense"},
    "war_cry":    {"pet_type": "any",      "stat_type": "attack"},
}

BASE_SLOTS = 4
MAX_SLOTS = 8
SLOT_UNLOCK_ITEM = "skill_slot_stone"
FRAGMENTS_PER_BOOK = 10
FORGET_REFUND_RATE = 0.5
QUALITY_BONUS = {"normal": 0.0, "rare": 0.03, "epic": 0.06, "legend": 0.10}


@dataclass
class PetSkill:
    sid: str
    name: str
    pet_type: str
    level: int
    locked: bool
    stat_type: str = ""
    exp: int = 0


class PetSkillSystem:
    def __init__(self):
        self.pet_skills = {}
        self.pet_type = {}
        self.slots = {}          # pet_id -> 已解锁技能格数
        self.intimacy = {}       # pet_id -> 亲密度 0-100
        self.quality = {}        # pet_id -> 品质
        self.books = {}          # pet_id -> {skill_id: 同名技能书数量}
        self.fragments = {}      # pet_id -> 碎片数量

    # ---- 内部辅助 ----
    def _slot_count(self, pet_id):
        return self.slots.get(pet_id, BASE_SLOTS)

    def _skill_def(self, skill_id):
        return SKILL_DEFS.get(skill_id, {"pet_type": "any", "stat_type": ""})

    def _skills(self, pet_id):
        return self.pet_skills.setdefault(pet_id, [])

    # ---- bug1 修复: 学习检查宠物类型 ----
    def learn(self, pet_id, skill_id, skill_book):
        sdef = self._skill_def(skill_id)
        ptype = self.pet_type.get(pet_id, "any")
        if sdef["pet_type"] not in ("any", ptype):
            return False  # 类型不兼容, 不能学

        skills = self._skills(pet_id)
        if any(s.sid == skill_id for s in skills):
            return False  # 已学过同名技能

        # bug6 修复: 同属性类型互斥, 只能激活一个
        if sdef["stat_type"] and any(
            s.stat_type == sdef["stat_type"] for s in skills
        ):
            return False

        new = PetSkill(skill_id, skill_id, sdef["pet_type"], 1, False,
                       sdef["stat_type"])
        if len(skills) < self._slot_count(pet_id):
            skills.append(new)
            return True

        # bug2 修复: 锁定技能受保护, 只覆盖第一个未锁定的
        for i, s in enumerate(skills):
            if not s.locked:
                skills[i] = new
                return True
        return False  # 全部锁定, 无法覆盖

    # ---- bug3 修复: 升级需要 经验 + 同名技能书(或碎片) ----
    def upgrade(self, pet_id, skill_id, exp):
        for s in self.pet_skills.get(pet_id, []):
            if s.sid == skill_id:
                need_exp = s.level * 100
                if exp < need_exp:
                    return False
                pet_books = self.books.setdefault(pet_id, {})
                if pet_books.get(skill_id, 0) >= 1:
                    pet_books[skill_id] -= 1
                elif self.fragments.get(pet_id, 0) >= FRAGMENTS_PER_BOOK:
                    self.fragments[pet_id] -= FRAGMENTS_PER_BOOK
                else:
                    return False  # 没有同名技能书或碎片
                s.level += 1
                s.exp += exp
                return True
        return False

    # ---- bug4 修复: 技能格可通过道具解锁, 有上限 ----
    def unlock_slot(self, pet_id, item):
        if item != SLOT_UNLOCK_ITEM:
            return False
        current = self._slot_count(pet_id)
        if current >= MAX_SLOTS:
            return False
        self.slots[pet_id] = current + 1
        return True

    # ---- bug5 修复: 触发概率 = 基础 + 等级 + 亲密度 + 品质 ----
    def get_trigger_chance(self, pet_id, skill_id):
        for s in self.pet_skills.get(pet_id, []):
            if s.sid == skill_id:
                chance = 0.10 + 0.04 * s.level
                chance += 0.002 * self.intimacy.get(pet_id, 0)
                chance += QUALITY_BONUS.get(self.quality.get(pet_id, "normal"), 0.0)
                return min(chance, 0.95)
        return 0.0

    # ---- bug6 修复: 同类型技能互斥 ----
    def can_learn_duplicate(self, pet_id, stat_type):
        return not any(
            s.stat_type == stat_type for s in self.pet_skills.get(pet_id, [])
        )

    # ---- bug7 修复: 遗忘返还 50% 材料, 需确认 ----
    def forget(self, pet_id, skill_id, confirm=False):
        if not confirm:
            return None  # 未确认, 返回提示
        skills = self.pet_skills.get(pet_id, [])
        for i, s in enumerate(skills):
            if s.sid == skill_id:
                if s.locked:
                    return None  # 锁定技能不能遗忘
                del skills[i]
                refund_exp = int(s.exp * FORGET_REFUND_RATE)
                refund_frag = int((s.level - 1) * FRAGMENTS_PER_BOOK
                                  * FORGET_REFUND_RATE)
                self.fragments[pet_id] = (
                    self.fragments.get(pet_id, 0) + refund_frag)
                return {"exp": refund_exp, "fragments": refund_frag}
        return None
