#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'sukhmel'

import cProfile as profile
from reflection import ReflectionPattern

game = ReflectionPattern(profile=True, profile_string="flood((100, 100),(255,0,0))", base=(816, 499), scale=(2, 2), pattern=[1,0])
profile.run('game.execute()')
