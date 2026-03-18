"""Tests for Beatcoach."""
from src.core import Beatcoach
def test_init(): assert Beatcoach().get_stats()["ops"] == 0
def test_op(): c = Beatcoach(); c.process(x=1); assert c.get_stats()["ops"] == 1
def test_multi(): c = Beatcoach(); [c.process() for _ in range(5)]; assert c.get_stats()["ops"] == 5
def test_reset(): c = Beatcoach(); c.process(); c.reset(); assert c.get_stats()["ops"] == 0
def test_service_name(): c = Beatcoach(); r = c.process(); assert r["service"] == "beatcoach"
