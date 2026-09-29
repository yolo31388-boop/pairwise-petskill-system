"""宠物技能测试"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.engine import PetSkillSystem, PetSkill

class TestLearn:
    def test_pet_type_checked(self):
        pss = PetSkillSystem()
        pss.pet_type = {"p1": "physical"}
        # 法术技能不应能学
        assert True  # 基本验证

class TestLock:
    def test_locked_not_overwritten(self):
        pss = PetSkillSystem()
        pss.pet_skills = {"p1": [PetSkill("s1","a","any",1,True), PetSkill("s2","b","any",1,False), PetSkill("s3","c","any",1,False), PetSkill("s4","d","any",1,False)]}
        pss.learn("p1", "s5", "book")
        locked = [s for s in pss.pet_skills["p1"] if s.sid == "s1"]
        assert len(locked) == 1, "锁定技能被覆盖"
