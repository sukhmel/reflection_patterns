#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'sukhmel'

import cProfile as profile
from reflection import ReflectionPattern

game = ReflectionPattern(profile = True, base = (997, 1499))
profile.run('game.execute()')
