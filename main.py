#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
TODO:
 * clickable input interface
 * GUI to interact with user
 * rewriting flood
 * color picker
 * refactor mouse_click and keyboard_click
"""

__author__ = 'sukhmel'

import sys
import pygame

class reflection_pattern:

    def __init__(self):
        """
        initialize pygame and reset everything to defaults
        """
        pygame.init()

        self.step = 0
        self.base = (0, 0) #(64, 33)
        self.scale = (20, 20)
        self.size = (0, 0)

        self.fore_color = (0, 0, 0)
        self.click_color = 0
        self.back_color = (255, 255, 255)
        self.mouse_position = (-1, -1)

        self.palette = [(240,   0,   0),
                        (  1,   1,   1),
                        (255, 255,   0),
                        (255,   0, 255),
                        (0,   255, 255),
                        (200, 200,   0),
                        (200,   0, 200),
                        (  0, 200, 200),
                        (  0,   0, 254),
                        (  0, 254,   0),
                        (190, 190, 190)]

        self.proceed = True
        self.data = [] # [ [1(\),0( ),-1(/)], line color, top color, bottom color, is rendered flag

        self.pattern_step = 0
        self.position = (0, 0)
        self.direction = [1, 1]
        self.pattern = [] #1, 1, 0, 1, 1, 1, 0 # 1, 1, 0, 1, 0, 0
        self.window = pygame.display.set_mode(self.size)

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
            self.data = [[[0, self.fore_color, self.back_color, self.back_color, False]
                            for y in range(self.base[1])]
                            for x in range(self.base[0])]
            self.pattern_step = 0
            self.position = (0, 0)
            self.direction = [1, 1]
            self.pattern = [1, 1, 0, 1, 0]
        else:
            for y in range(self.base[1]):
                for x in range(self.base[0]):
                    self.data[x][y][4] = False;

        self.size = (self.base[0]*self.scale[0], self.base[1]*self.scale[1])
        self.window = pygame.display.set_mode(self.size)
        self.set_caption()
        field = pygame.Surface(pygame.display.get_surface().get_size())
        field = field.convert()
        field.fill(self.back_color)
        pygame.display.get_surface().blit(field, (0, 0))
        pygame.display.flip()
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
                    self.mouseclick(event.pos, self.back_color)

    def execute(self):
        """
        start main loop for events and rendering
        """
        while 1:
            self.user_input(pygame.event.get())
            if self.step > 0:
                pygame.time.wait( self.step )
            if self.proceed:
                pos = self.advance()
                if self.step > 0:
                    self.paint(pos, True)
            if not self.proceed:
                self.paint()

    def advance(self):
        """
        calculate next state of the field depending on current
        :return: changed data's position. paint should be later called on this position
        """
        value = self.direction[0]*self.direction[1]
        color = self.fore_color
        if isinstance(self.pattern[self.pattern_step], tuple):
            color = self.pattern[self.pattern_step]
        elif not self.pattern[self.pattern_step]:
            value = 0

        # field data:      at given coordinates, [1(\)0( )-1(/)], line,  top,           bottom, already rendered
        self.data[self.position[0]][self.position[1]] = [value, color, self.back_color, self.back_color, False]
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

                upper_points = [(points[0][0] + value, points[0][1]),
                               (),
                               (points[1][0], points[1][1] - 1)]
                lower_points = [(points[0][0], points[0][1] + 1),
                                (),
                                (points[1][0] - value, points[1][1])]

                if value == 1:
                    upper_points[1] = corners[1]
                    lower_points[1] = corners[2]
                else:
                    upper_points[1] = corners[0]
                    lower_points[1] = corners[2]

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
        if self.mouse_position != pos or \
            color != pygame.display.get_surface().get_at(pos):
            if color is None:
                color = self.palette[self.click_color]
            field = self.flood(pos, color)
            self.mouse_position = pos
            pygame.display.get_surface().blit(field, (0,0))
            pygame.display.flip()

    def flood(self, pos, color):
        """
        TODO incomplete
        flood fill with chosen color
        :param pos:   data coordinates of starting point
        :param color: color to fill with
        :return:      modified screen that was used for painting
        """
        queue = set()
        data = (pos[0] % self.scale[0], pos[1] % self.scale[1])
        value = self.data[int(data[0]/self.scale[0])][int(data[1]/self.scale[1])]
        top = 0 < data[0] - value*data[1] < sum(self.scale)/2
        queue.add((pos[0], pos[1], top)
        screen = pygame.display.get_surface()
        ref_color = screen.get_at(pos)
        """
        for logic of calculating adjacent positions: see doc folder
        could've been done clearer, I guess 
        """
        if ref_color != self.fore_color:
            screen.set_at(pos, color)
            if ref_color != color:
                while 1:
                    try:
                        point = queue.pop()
                    except KeyError:
                        break
                    else:
                        adjacent = [(point[0] - 1, point[1]),
                                    (point[0] + 1, point[1]),
                                    (point[0], point[1] - 1),
                                    (point[0], point[1] + 1)]
                        for i in range(4):
                            try:
                                if screen.get_at(adjacent[i]) == ref_color:
                                    queue.add(adjacent[i])
                                    screen.set_at(adjacent[i], color)
                            except IndexError:
                                pass
        return screen

    def change_click_color(self, delta):
        self.click_color = (self.click_color + delta) % len(self.palette)
        self.set_caption()

    def set_caption(self):
        pygame.display.set_caption(
            '%i x %i ' % self.base + '@ (%i, %i) ' % self.scale
            + ', color is (%i, %i, %i)' % self.palette[self.click_color])

if __name__ == "__main__":
    game = reflection_pattern();
    game.execute()
