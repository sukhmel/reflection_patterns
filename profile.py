#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'sukhmel'

import cProfile as profile
from main import ReflectionPattern

starts = (
    {
        'profile'            : True
        , 'base'             : (21,19)
        , 'scale'            : (5,5)
        , 'pattern'          : (True, True, None, True, False)
        , 'auto_color'       : False
        , 'paint_auto_steps' : False
        , 'timeout'          : 0
        , 'start_position'   : (0,0)
        , 'start_direction'  : (1, 1)
        , 'start_step'       : 0
        , 'profile_string'   : None
    },  # all values default except for profile

    {
        'profile' : True
        , 'profile_string' : "self.flood((100, 100),(255,0,0))"
        , 'base'           : (816, 499)
        , 'scale'          : (2, 2)
        , 'pattern'        : [1, 0]
    }, # flood speed test

    {
        'profile' : True
        , 'base'             : (816, 499)
        , 'scale'            : (2, 2)
        , 'pattern'          : [True, True, None]
        , 'auto_color'       : True
    },

    {
        'profile' : True
        , 'base'             : (816, 499)
        , 'scale'            : (2, 2)
        , 'pattern'          : [True, True, None]
        , 'auto_color'       : True
        , 'paint_auto_steps' : True
    } # same starts with different values of 'paint_auto_step'

)

for param in starts:
    game = ReflectionPattern(**param)
    profile.run('game.execute()')