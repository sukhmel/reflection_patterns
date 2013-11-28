#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
controls:
    + or ] increases scale
    - or [ decreases scale
    > increases time delay
    < decreases time delay
    mousewheel scrolls through colors to fill
    left mousebutton fills with current color
    right mousebutton fills with background color
    arrow keys change field size
    
usage:
    game = ReflectionPattern(...)
    game.execute()
"""

__author__ = 'sukhmel'

import sys
import pygame

pygame.init()

class ReflectionPattern:

    def __init__(self
                 , base             = (21,19)
                 , scale            = (5,5)
                 , pattern          = [(48,), (48,), 0, (13,), 0]
                 , step             = 0
                 , start_position   = (0,0)
                 , start_direction  = [1, 1]
                 , start_step       = 0
                 , profile          = False
    ):
        """
        initialize internals and reset everything to defaults or passed values
        :param base:            size of field in terms of cells. Will be multiplied by scale
        :param scale:           scale of dimensions separately
        :param pattern:         pattern of line to emerge. 0 is blank space, 1 is foreground colors,
                                (i,) is color number i in palette, (r, g, b) is RGB color value
        :param step:            amount of milliseconds used in call to pygame.tyme.wait() before each
                                field redraw. Real slowdown differs because of drawing speed.
        :param start_position:  initial cell
        :param start_direction: initial direction
        :param start_step:      initial index inside of pattern
        :param profile:         close after first complete calculation of the field. Useful for profiling advance()
        """
        self.in_direction = start_direction
        self.in_position = start_position
        self.in_step    = start_step
        self.step       = step
        self.base       = base
        self.scale      = scale
        self.pattern    = pattern
        self.profile    = profile

        # following values will be set within reset() call
        self.direction  = 0
        self.position   = 0
        self.patt_step  = 0
        self.color_shown= 0

        self.palette    = []
        color_values = (0, 50, 100, 200, 255)
        for r in color_values:
            for g in color_values:
                for b in color_values:
                    self.palette.append((r, g, b))

        self.fore_color  = 0
        self.click_color = 105
        self.back_color  = -1

        self.color_picker_height = 10
        self.color_picker_rows   = len(color_values)
        self.proceed = True
        self.draw    = True
        self.data = [] # [ [1(\),0( ),-1(/)], line color, top color, bottom color, is rendered flag

        self.size = (1, 1)
        self.reset(force = True)

    def reset(self, new_base = None, force = False):
        """
        reset field parameters, restart calculating if necessary, otherwise continue
        set all data[4] to False, so that they are rendered
        :param new_base: size of field without respect to scaling
        """
        if self.base != new_base or force:
            if new_base is not None:
                self.base = new_base
            self.proceed = True
            self.data = [[[0,                               # line type: 0 - no line, 1 is \, -1 is /
                           self.palette[self.fore_color],   # line color
                           self.palette[self.back_color],   # upper color
                           self.palette[self.back_color],   # lower color
                           False]                           # is rendered
                            for y in range(self.base[1])]
                            for x in range(self.base[0])]
            self.direction  = list(self.in_direction)
            self.position   = self.in_position
            self.patt_step  = self.in_step
        else:
            for y in range(self.base[1]):
                for x in range(self.base[0]):
                    self.data[x][y][4] = False

        self.draw = True
        self.size = (self.base[0]*self.scale[0],
                     self.base[1]*self.scale[1])
        pygame.display.set_mode((self.size[0], self.size[1] + self.color_picker_height))
        field = pygame.Surface(pygame.display.get_surface().get_size())
        field = field.convert()
        field.fill(self.back_color)
        pygame.display.get_surface().blit(field, (0, 0))
        pygame.display.flip()
        self.set_caption()
        self.repaint()
        self.color_shown = self.paint_color_picker(picker = False)

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
                self.mouse_click(event)

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
        if isinstance(self.pattern[self.patt_step], tuple):
            if len(self.pattern[self.patt_step]) == 1:
                color = self.palette[self.pattern[self.patt_step][0]]
            else:
                color = self.pattern[self.patt_step]

        elif not self.pattern[self.patt_step]:
            value = 0

        # field data:      at given coordinates, [1(\)0( )-1(/)], line,  top,           bottom, already rendered
        self.data[self.position[0]][self.position[1]] = [value, color,
                                                         self.palette[self.back_color],
                                                         self.palette[self.back_color], False]
        self.patt_step = (self.patt_step + 1) % len(self.pattern)

        new_position = list(self.position)
        for i in range(2):
            if self.position[i] + self.direction[i] > self.base[i] - 1 or \
                     self.position[i] + self.direction[i] < 0:
                self.direction[i] *= -1
            else:
                new_position[i] = self.position[i] + self.direction[i]

        if new_position == self.position:
            self.proceed = False # so that we will stop instead of travelling backwards
            if self.profile:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

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

    def paint_color_picker(self, picker = True, palette = None):
        """
        paint color chooser or current click color
        :param picker:  true if chooser should be shown
        :param palette: color palette to draw, self.palette by default
        :return: true if color is displayed, false if picker is displayed
        """
        if palette is None:
            palette = self.palette

        screen = pygame.Surface.convert(pygame.display.get_surface())
        resized = False

        if picker:
            rows = self.color_picker_rows
        else:
            rows = 1
        size = (self.size[0], self.size[1] + self.color_picker_height * rows)
        if pygame.display.get_surface().get_size() != size:
            pygame.display.set_mode(size)
            resized = True

        pick_box = pygame.Surface((self.size[0], self.color_picker_height * rows)).convert()

        if picker:
            width = pick_box.get_size()[0] * \
                    self.color_picker_rows / len(palette)
            columns = len(palette)/self.color_picker_rows
            for index in range(len(self.palette)):
                pygame.draw.rect(pick_box,
                                 palette[index],
                                 pygame.Rect(
                                     (index % columns) * width,
                                     self.color_picker_height * divmod(index, columns)[0],
                                     width + 1,
                                     self.color_picker_height))
        else:
            pygame.draw.rect(pick_box, palette[self.click_color], pick_box.get_rect())

        pygame.display.get_surface().blit(screen, (0, 0))
        pygame.display.get_surface().blit(pick_box, (0, self.size[1]))

        pygame.display.flip()
        return not picker

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
                    pygame.display.get_surface().blit(field, corners[0],
                                                      pygame.Rect(corners[0],
                                                          (corners[3][0] - corners[0][0],
                                                           corners[3][1] - corners[0][1])))
                    pygame.display.flip()

        return field

    def mouse_click(self, event):
        """
        process mouse click event. Should take event as parameter
        :param pos:
        :param color:
        :return:
        """
        if event.button == 4:
            self.change_click_color(+1)
        if event.button == 5:
            self.change_click_color(-1)
        if event.button == 1 or event.button == 3:
            color = (event.button == 1 and
                     [self.palette[self.click_color]] or
                     [self.palette[self.back_color]])[0]

            if event.pos[1] < self.size[1]:
                if color is None:
                    color = self.palette[self.click_color]

                self.flood(event.pos, color)
                self.repaint()
            else:
                if not self.color_shown:
                    self.change_click_color(index =
                        self.palette.index(pygame.display.get_surface().get_at(event.pos)[:-1]))
                else:
                    self.color_shown = self.paint_color_picker(picker = self.color_shown)

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
        data_point = self.data[place[0]][place[1]]
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

    def change_click_color(self, delta = 0, index = None):
        if index is None:
            self.click_color = (self.click_color + delta) % len(self.palette)
        else:
            self.click_color = index
        self.set_caption()
        self.color_shown = self.paint_color_picker(False)

    def set_caption(self):
        pygame.display.set_caption(
            '%i x %i ' % self.base + '@ (%i, %i) ' % self.scale
            + ', color is (%i, %i, %i) ' %  self.palette[self.click_color] + '#%i' % self.click_color)

if __name__ == "__main__":
    game = ReflectionPattern()
    game.execute()
