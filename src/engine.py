"""宠物技能学习系统"""
from dataclasses import dataclass

BASE_SLOTS = 4
MAX_SLOTS = 7
MAX_LEVEL = 10
FORGET_RETURN_RATE = 0.5
FRAGMENTS_PER_BOOK = 5
SLOT_UNLOCK_ITEM = "slot_key"

_QUALITY_BONUS = {"normal": 0.0, "rare": 0.05, "epic": 0.10, "legend": 0.15}


@dataclass
class PetSkill:
    sid: str
    name: str
    pet_type: str
    level: int
    locked: bool
    stat_type: str = ""
    invested_exp: int = 0
    invested_books: int = 0


@dataclass
class SkillDef:
    sid: str
    name: str
    pet_type: str = "any"
    stat_type: str = ""


class PetSkillSystem:
    def __init__(self):
        self.pet_skills = {}
        self.pet_type = {}
        self.skill_db = {}
        self.slot_count = {}
        self.intimacy = {}
        self.quality = {}

    def register_skill(self, sid, name, pet_type="any", stat_type=""):
        self.skill_db[sid] = SkillDef(sid, name, pet_type, stat_type)

    def _slots(self, pet_id):
        return self.slot_count.get(pet_id, BASE_SLOTS)

    # bug4 fix: 技能格可通过道具解锁，有上限
    def unlock_slot(self, pet_id, item):
        if item != SLOT_UNLOCK_ITEM:
            return False
        current = self._slots(pet_id)
        if current >= MAX_SLOTS:
            return False
        self.slot_count[pet_id] = current + 1
        return True

    def _type_compatible(self, pet_id, skill_def):
        pet_t = self.pet_type.get(pet_id)
        if pet_t is None or skill_def.pet_type in ("", "any"):
            return True
        return pet_t == skill_def.pet_type

    def learn(self, pet_id, skill_id, skill_book):
        skills = self.pet_skills.setdefault(pet_id, [])
        skill_def = self.skill_db.get(skill_id)
        # bug1 fix: 检查宠物类型/属性兼容性
        if skill_def is not None and not self._type_compatible(pet_id, skill_def):
            return False
        if any(s.sid == skill_id for s in skills):
            return False
        # bug6 fix: 同类型技能互斥，只能激活一个
        stat_type = skill_def.stat_type if skill_def else ""
        if stat_type and any(s.stat_type == stat_type for s in skills):
            return False
        new_skill = PetSkill(
            skill_id,
            skill_def.name if skill_def else skill_id,
            skill_def.pet_type if skill_def else "any",
            1,
            False,
            stat_type,
        )
        if len(skills) < self._slots(pet_id):
            skills.append(new_skill)
            return True
        # bug2 fix: 只覆盖未锁定的技能（等级最低者优先）
        candidates = [s for s in skills if not s.locked]
        if not candidates:
            return False
        victim = min(candidates, key=lambda s: s.level)
        skills[skills.index(victim)] = new_skill
        return True

    # bug3 fix: 升级需要技能经验 + 同名技能书（或技能碎片）
    def upgrade(self, pet_id, skill_id, exp, book=None, fragments=0):
        for s in self.pet_skills.get(pet_id, []):
            if s.sid == skill_id:
                if s.level >= MAX_LEVEL:
                    return False
                need_exp = s.level * 100
                if exp < need_exp:
                    return False
                if book != skill_id and fragments < FRAGMENTS_PER_BOOK:
                    return False
                s.level += 1
                s.invested_exp += need_exp
                s.invested_books += 1
                return True
        return False

    # bug5 fix: 触发概率综合技能等级 + 宠物亲密度 + 宠物品质
    def get_trigger_chance(self, pet_id, skill_id):
        for s in self.pet_skills.get(pet_id, []):
            if s.sid == skill_id:
                chance = 0.10
                chance += 0.02 * s.level
                chance += 0.0005 * max(0, min(100, self.intimacy.get(pet_id, 0)))
                chance += _QUALITY_BONUS.get(self.quality.get(pet_id, "normal"), 0.0)
                return min(0.95, chance)
        return 0.0

    def can_learn_duplicate(self, pet_id, stat_type):
        if not stat_type:
            return True
        return not any(
            s.stat_type == stat_type for s in self.pet_skills.get(pet_id, [])
        )

    # bug7 fix: 遗忘返还50%材料，需确认
    def forget(self, pet_id, skill_id, confirm=False):
        skills = self.pet_skills.get(pet_id, [])
        for s in skills:
            if s.sid == skill_id:
                if s.locked:
                    return {"ok": False, "reason": "locked"}
                if not confirm:
                    return {
                        "ok": False,
                        "confirm_required": True,
                        "message": "确认遗忘技能 {}？将返还50%材料".format(s.name),
                    }
                skills.remove(s)
                return {
                    "ok": True,
                    "returned_exp": int(s.invested_exp * FORGET_RETURN_RATE),
                    "returned_books": s.invested_books // 2,
                }
        return {"ok": False, "reason": "not_found"}
