#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
TODO:
 * clickable input interface
 * GUI to interact with user
 * refactor mouse_click and keyboard_click
"""

__author__ = 'sukhmel'

import sys
import pygame

class ReflectionPattern:

    def __init__(self):
        """
        initialize pygame and reset everything to defaults
        """
        pygame.init()

        self.step = 0
        self.base = (0, 0) #(64, 33)
        self.scale = (20, 20)
        self.size = (0, 0)

        self.palette = []
        color_values = (0, 50, 100, 150, 200, 255)
        for r in color_values:
            for g in color_values:
                for b in color_values:
                    self.palette.append((r, g, b))

        self.fore_color  = 0
        self.click_color = 3
        self.back_color  = len(self.palette) - 1

        self.colorpicker = 20
        
        self.proceed = True
        self.draw    = True
        self.data = [] # [ [1(\),0( ),-1(/)], line color, top color, bottom color, is rendered flag

        self.pattern_step = 0
        self.position = (0, 0)
        self.direction = [1, 1]
        self.pattern = [] #1, 1, 0, 1, 1, 1, 0 # 1, 1, 0, 1, 0, 0
        self.window = 0

        self.reset((19, 21))

    def reset(self, new_base):
        """
        reset field parameters, restart calculating if necessary, otherwise continue
        set all data[4] to False, so that they are rendered
        :param new_base: size of field without respect to scaling
        """
        if self.base != new_base:
            self.proceed = True
            self.base = new_base
            self.data = [[[0,                               # line type: 0 - no line, 1 is \, -1 is /
                           self.palette[self.fore_color],   # line color
                           self.palette[self.back_color],   # upper color
                           self.palette[self.back_color],   # lower color
                           False]                           # is rendered
                            for y in range(self.base[1])]
                            for x in range(self.base[0])]
            self.pattern_step = 0
            self.position = (0, 0)
            self.direction = [1, 1]
            self.pattern = [1, 1, 0, 1, 0]
        else:
            for y in range(self.base[1]):
                for x in range(self.base[0]):
                    self.data[x][y][4] = False

        self.draw = True
        self.size = (self.base[0]*self.scale[0], self.base[1]*self.scale[1] + self.colorpicker)
        self.window = pygame.display.set_mode(self.size)
        self.set_caption()
        self.repaint()

    def user_input(self, events):
        """
        process input events
        :param events:
        """
        for event in events:
            if  (event.type == pygame.QUIT) or \
                (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                delta = 1
                if event.mod == 64:
                    delta = 100
                if event.mod == 256:
                    delta = 10
                if event.mod == 1:
                    delta = 50

                if event.key == pygame.K_LEFT:
                    self.reset((max(1, self.base[0] - delta), self.base[1]))
                if event.key == pygame.K_RIGHT:
                    self.reset((self.base[0] + delta, self.base[1]))
                if event.key == pygame.K_UP:
                    self.reset((self.base[0], max(1, self.base[1] - delta)))
                if event.key == pygame.K_DOWN:
                    self.reset((self.base[0], self.base[1] + delta))
                if event.key == pygame.K_KP_PLUS or event.unicode == "]":
                    self.scale = (self.scale[0] + 1, self.scale[1] + 1)
                    self.reset(self.base)
                if event.key == pygame.K_KP_MINUS or event.unicode == "[":
                    if self.scale[0] > 1 and self.scale[1] > 1:
                        self.scale = (self.scale[0] - 1, self.scale[1] - 1)
                        self.reset(self.base)
                if event.unicode == "<":
                    self.step -= 10
                    self.step = max([0, self.step])
                if event.unicode == ">":
                    self.step += 10
                    self.step = min([500, self.step])

            if  event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouseclick(event.pos)
                if event.button == 4:
                    self.change_click_color(+1)
                if event.button == 5:
                    self.change_click_color(-1)
                if event.button == 3:
                    self.mouseclick(event.pos, self.palette[self.back_color])

    def execute(self):
        """
        start main loop for events and rendering
        """
        while 1:
            self.user_input(pygame.event.get())
            if self.draw:
                pygame.display.get_surface().blit(self.paint_colorpicker(), (0,0))
                pygame.display.flip()

            if self.step > 0:
                pygame.time.wait( self.step )

            if self.proceed:
                pos = self.advance()
                if self.step > 0:
                    self.paint(pos, True)
            if not self.proceed:
                if self.draw:
                    self.paint()
                else:
                    pygame.time.wait(100)

    def advance(self):
        """
        calculate next state of the field depending on current
        :return: changed data's position. paint should be later called on this position
        """
        value = self.direction[0]*self.direction[1]
        color = self.palette[self.fore_color]
        if isinstance(self.pattern[self.pattern_step], tuple):
            if len(self.pattern[self.pattern_step]) == 1:
                color = self.palette[self.pattern[self.pattern_step][0]]
            else:
                color = self.pattern[self.pattern_step]

        elif not self.pattern[self.pattern_step]:
            value = 0

        # field data:      at given coordinates, [1(\)0( )-1(/)], line,  top,           bottom, already rendered
        self.data[self.position[0]][self.position[1]] = [value, color, self.palette[self.back_color], self.palette[self.back_color], False]
        self.pattern_step = (self.pattern_step + 1) % len(self.pattern)

        new_position = list(self.position)
        for i in range(2):
            if self.position[i] + self.direction[i] > self.base[i] - 1 or \
                     self.position[i] + self.direction[i] < 0:
                self.direction[i] *= -1
            else:
                new_position[i] = self.position[i] + self.direction[i]

        if new_position == self.position:
            self.proceed = False # so that we will stop instead of travelling backwards

        temp = self.position
        self.position = new_position
        return temp

    def repaint(self, force = False):
        """
        paint whole field
        :param force: repaint all parts of field
        """
        field = None
        if force:   #dedicated cycle to improve performance
            for x in range(len(self.data)):
                for y in range(len(self.data[x])):
                    self.data[x][y][4] = False
        for x in range(len(self.data)):
            for y in range(len(self.data[x])):
                field = self.paint((x, y), False, field)
        if field is not None:
            pygame.display.get_surface().blit(field, (0,0))
            pygame.display.flip()
        else:
            self.draw = False

    def paint_colorpicker(self, palette = None):
        if palette is None:
            palette = self.palette

        screen = pygame.display.get_surface()
        width = self.size[0]/len(palette)
        for index in range(len(self.palette)):
            pygame.draw.rect(screen,
                             palette[index],
                             pygame.Rect(
                                 index*width,
                                 self.size[1] - self.colorpicker,
                                 width + 1,
                                 self.colorpicker))
        return screen

    def paint(self, pos = None, flip = True, field = None):
        """
        paint one part of field
        :param pos:   data coordinates
        :param flip:  display field after painting
        :param field: screen to paint or None for current screen
        :return:      modified screen used for painting
        """
        if pos is None:
            self.repaint()
        else:
            if self.data[pos[0]][pos[1]] is not None and not self.data[pos[0]][pos[1]][4]:
                self.draw = True
                if field is None:
                    field = pygame.display.get_surface()
                value = self.data[pos[0]][pos[1]][0]
                x = (pos[0]*self.scale[0],
                     pos[0]*self.scale[0] + self.scale[0] - 1)
                y = (pos[1]*self.scale[1],
                     pos[1]*self.scale[1] + self.scale[1] - 1)
                corners = ((x[0], y[0]),
                           (x[1], y[0]),
                           (x[0], y[1]),
                           (x[1], y[1]))
                if value == 1:
                    points = [corners[0],
                              corners[3]]
                else:
                    points = [corners[1],
                              corners[2]]

                upper_points = [(points[0][0], points[0][1]),
                               (),
                               (points[1][0], points[1][1])]
                lower_points = [(points[0][0], points[0][1]),
                                (),
                                (points[1][0], points[1][1])]

                if value == 1:
                    upper_points[1] = corners[1]
                    lower_points[1] = corners[2]
                else:
                    upper_points[1] = corners[0]
                    lower_points[1] = corners[3]

                pygame.draw.polygon(field, self.data[pos[0]][pos[1]][2], upper_points)
                pygame.draw.polygon(field, self.data[pos[0]][pos[1]][3], lower_points)

                if self.data[pos[0]][pos[1]][0] != 0:
                    pygame.draw.line(field, self.data[pos[0]][pos[1]][1], points[0], points[1])

                self.data[pos[0]][pos[1]][4] = True

                if flip:
                    pygame.display.get_surface().blit(field, (0,0))
                    pygame.display.flip()

        return field

    def mouseclick(self, pos, color = None):
        """
        process mouse click event. Should take event as parameter
        :param pos:
        :param color:
        :return:
        """
        if pos[1] < self.base[1]*self.scale[1]:
            if color is None:
                if isinstance(self.click_color, int):
                    color = self.palette[self.click_color]
                else:
                    color = self.click_color

            self.flood(pos, color)
            self.repaint()
        else:
            self.click_color = pygame.display.get_surface().get_at(pos)[:-1]
            self.set_caption()

    def get_adjacent_to(self, pos, direction):
        """
        get adjacent field cell position, including top/bottom index
        :raises IndexError: if adjacent position is outside of the field or top is not connected with bottom
        :param pos:  current cell index
        :param direction: 's' - inside cell, 'h' - horizontal, 'v' - vertical
        :return:     (x, y, top)
        """
        result = [pos[0], pos[1], -1]

        # we go to bottom of upper cell if we are on top, or to top of lower cell otherwise
        if direction is 'v':
            delta = (pos[2] == 2 and [-1] or [+1])[0]
            result[1] += delta
            result[2]  = int((5 - delta)/2)

        # if top and bottom are connected, we go to other part of same cell
        if direction is 's':
            if self.data[pos[0]][pos[1]][0] == 0:
                result[2] = 5 - pos[2]
            else:
                raise IndexError

        # we go to different directions depending on current line state
        if direction is 'h':
            value = (self.data[pos[0]][pos[1]][0] == -1 and [-1] or [1])[0]
            step = (pos[2] == 2 and [value] or [-value])[0]
            adj_value = (self.data[pos[0] + step][pos[1]][0] == -1 and [-1] or [1])[0]
            result[0] += step
            result[2] = (adj_value == step and [3] or [2])[0]

        # check for boundaries. Will throw IndexError if not correct
        if -1 < result[0] < self.base[0] and -1 < result[1] < self.base[1]:
            return tuple(result)
        else:
            raise IndexError

    def flood(self, pos, color):
        """
        TODO incomplete
        flood fill with chosen color
        :param pos:   data coordinates of starting point
        :param color: color to fill with
        :return:      modified screen that was used for painting
        """
        queue = set()
        place = (int(pos[0]/self.scale[0]), int(pos[1]/self.scale[1]))
        data_point = self.data[int(place[0]/self.scale[0])][int(place[1]/self.scale[1])]
        value = (data_point[0] == -1 and [-1] or [1])[0]
        # top's value is index of corresponding color in data; 2 is top, 3 is bottom
        top = ((0 < pos[0] % self.scale[0] - value*(pos[1] % self.scale[1]) < sum(self.scale)/2) and [2] or [3])[0]
        ref_color = data_point[top]
        queue.add((place[0], place[1], top))
        screen = pygame.display.get_surface()

        #for logic of calculating adjacent positions: see doc folder
        #could've been done clearer, I guess
        if ref_color != color:
            self.data[place[0]][place[1]][top]  = color
            self.data[place[0]][place[1]][4]    = False
            while 1:
                try:
                    point = queue.pop()
                except KeyError:
                    break
                else:
                    for i in ['h', 'v', 's']:
                        try:
                            temp = self.get_adjacent_to(point, i)
                            if self.data[temp[0]][temp[1]][temp[2]] == ref_color:
                                queue.add(temp)
                                self.data[temp[0]][temp[1]][temp[2]] = color
                                self.data[temp[0]][temp[1]][4] = False
                        except IndexError:
                            pass
        return screen

    def change_click_color(self, delta):
        self.click_color = (self.click_color + delta) % len(self.palette)
        self.set_caption()

    def set_caption(self):
        pygame.display.set_caption(
            '%i x %i ' % self.base + '@ (%i, %i) ' % self.scale
            + ', color is (%i, %i, %i)' %
            (isinstance(self.click_color, int) and
                [self.palette[self.click_color]] or [self.click_color])[0])

if __name__ == "__main__":
    game = ReflectionPattern();
    game.execute()
