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
    spacebar to pause auto colouring
    
usage:
    game = ReflectionPattern(...)
    game.execute()
"""

__author__ = 'sukhmel'

import sys
import pygame
import colorsys

pygame.init()
pygame.key.set_repeat(500, 200)

class ReflectionPattern:

    EVENT_EXIT    = pygame.USEREVENT
    EVENT_EXEC    = pygame.USEREVENT + 1
    EVENT_RESET   = pygame.USEREVENT + 2
    EVENT_SCALE   = pygame.USEREVENT + 3
    EVENT_TIMEOUT = pygame.USEREVENT + 4

    def __init__(self
                 , base             = (21,19)
                 , scale            = (5,5)
                 , pattern          = (True, True, None, True, False)
                 , auto_color       = False
                 , paint_auto_steps = False
                 , fps          = 0
                 , start_position   = (0,0)
                 , start_direction  = (1, 1)
                 , start_step       = 0
                 , profile          = False
                 , profile_string   = None
    ):
        """
        initialize internals and reset everything to defaults or passed values
        :param base:            size of field in terms of cells. Will be multiplied by scale
        :param scale:           scale of dimensions separately
        :param pattern:         pattern of line to emerge. None or False is a blank space, True is foreground color,
                                anything convertible to int is color number in palette, (r, g, b) is RGB color value
        :param auto_color:      automatically color field parts based on size or other parameters
        :param paint_auto_steps: repaint after each step of auto colouring
        :param fps:             approximate desired frames per second in field redraw.
        :param start_position:  initial cell
        :param start_direction: initial direction
        :param start_step:      initial index inside of pattern
        :param profile:         close after first complete calculation of the field. Useful for profiling advance()
        :param profile_string:  executed as "self.[profile_string]" to automatically profile interaction
        """
        self.paint_auto_steps = paint_auto_steps
        self.profile_string = profile_string
        self.in_direction = start_direction
        self.in_position = start_position
        self.in_step    = start_step
        self.fps    = fps
        self.base       = base
        self.pattern    = pattern
        self.profile    = profile
        self.auto_color = auto_color
        self.color_shown = True
        self.delta_resize = 1
        if isinstance(scale, int):
            self.scale  = (scale, scale)
        else:
            self.scale  = scale

        # following values will be set within reset() call
        self.direction  = 0
        self.position   = 0
        self.patt_step  = 0

        self.palette    = [(0, 0, 0)]
        self.auto_palette = []

        val_range = 1
        sat_range = 4
        hue_range = 50
        for s in range(sat_range - 1, -1, -1 ):
            for v in range(val_range):
                for h in range(hue_range):
                    color = colorsys.hsv_to_rgb((h+1)/hue_range,
                                                (s+1)/sat_range,
                                                (v+1)/val_range)
                    color = tuple([int(c*255) for c in color])
                    self.palette.append(color)
                    if s == max(sat_range - 2, 1):
                        self.auto_palette.append(color)

        self.palette.append((255, 255, 255))

        self.fore_color  = 0
        self.click_color = 105 % len(self.palette)
        self.back_color  = -1

        self.color_picker_height = 8
        self.color_picker_rows   = sat_range
        self.proceed = True
        self.draw    = True

        self.uncoloured = set() # uncoloured points
        self.buffer     = set()
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

            self.data = []  # list comprehension is used to correctly fill an array with copies, not references
            self.data = [[[0,                               # line type: 0 - no line, 1 is \, -1 is /
                           self.get_color(self.fore_color), # line color
                           self.get_color(self.back_color),   # upper color
                           self.get_color(self.back_color),   # lower color
                           False]                           # is rendered
                            for y in range(self.base[1])]
                            for x in range(self.base[0])]

            self.uncoloured = set()
            for x in range(self.base[0]):
                for y in range(self.base[1]):
                    for z in (2, 3):
                        self.uncoloured.add((x, y, z))


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
        rows = (self.color_shown and [1] or [self.color_picker_rows])[0]
        pygame.display.set_mode((self.size[0], self.size[1] + self.color_picker_height * rows))
        field = pygame.Surface(pygame.display.get_surface().get_size())
        field = field.convert()
        field.fill(self.get_color(self.back_color))
        pygame.display.get_surface().blit(field, (0, 0))
        pygame.display.flip()
        self.set_caption()
        self.repaint()
        self.paint_color_picker(picker = not self.color_shown)

    def key_press(self, event):
        queue = []
        mod = pygame.key.get_mods()

        if mod & pygame.KMOD_ALT:
            delta = 5
        elif mod & pygame.KMOD_CTRL:
            delta = 10
        elif mod & pygame.KMOD_SHIFT:
            delta = 50
        else:
            delta = 1

        base = None
        if event.key == pygame.K_LEFT:
            base = (max(1, self.base[0] - delta), self.base[1])
        if event.key == pygame.K_RIGHT:
            base = (self.base[0] + delta, self.base[1])
        if event.key == pygame.K_UP:
            base = (self.base[0], max(1, self.base[1] - delta))
        if event.key == pygame.K_DOWN:
            base = (self.base[0], self.base[1] + delta)
        if base is not None:
            queue.append(pygame.event.Event(self.EVENT_RESET, {'base': base}))

        scale = None
        if event.unicode == "+" or event.unicode == "]":
            scale = (self.scale[0] + 1, self.scale[1] + 1)
        if event.unicode == "-" or event.unicode == "[":
            if self.scale[0] > 1 and self.scale[1] > 1:
                scale = (self.scale[0] - 1, self.scale[1] - 1)
        if scale is not None:
            queue.append(pygame.event.Event(self.EVENT_SCALE, {'scale': scale}))

        if event.key == pygame.K_SPACE:
            self.uncoloured, self.buffer = self.buffer, self.uncoloured

        fps = None
        if event.unicode == "<":
            fps = max([0, self.fps - delta])
        if event.unicode == ">":
            fps = self.fps + delta
        if fps is not None:
            queue.append(pygame.event.Event(self.EVENT_TIMEOUT, {'fps': fps}))

        return queue

    def user_input(self, events):
        """
        process input events
        :param events:
        """
        actions = []
        for event in events:

            if  (event.type == pygame.QUIT) or \
                (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                actions += [pygame.event.Event(self.EVENT_EXIT, {})]

            if event.type is pygame.KEYDOWN:
                actions += self.key_press(event)

            if  event.type == pygame.MOUSEBUTTONUP:
                actions += self.mouse_click(event)

            if event.type == self.EVENT_EXEC:
                actions += [event]

        return actions

    def execute(self):
        """
        start main loop for events and rendering
        """
        while 1:
            actions = self.user_input(pygame.event.get())

            for event in actions:
                if event.type is self.EVENT_RESET:
                    print(event.base)#self.reset(event.base) RESET IS THE PROBLEM. IT DESTROYS KBD STATE

            if self.proceed:
                pos = self.advance()
                if self.fps > 0:
                    self.paint(pos, True)

            if not self.proceed:
                if self.draw:
                    self.paint()
                    self.draw = False

                if not (self.auto_color and self.automatic_colouring(self.paint_auto_steps)):
                    pygame.time.wait(100)

            pygame.time.Clock().tick(self.fps)

    def get_color(self, index, palette = None):
        """
        get color from given palette
        :param index: None or False gives None color, True gives foreground color, anything convertible to int takes
                      color by index from palette, any kind of container of length 3 gives (r, g, b) as RGB color value
        :param palette: palette to take color from. Takes from self.palette if None or unspecified
        :return: color tuple in RGB format: (r, g, b)
        """
        if palette is None:
            palette = self.palette

        try:
            if len(index) == 1:
                color = self.get_color(index[0], palette)
            elif len(index) == 3:
                color = index
            else:
                raise ValueError('Pattern element must be container of length 3, bool, None or int-convertible. '
                                 'Can not convert ' + str(index))
        except TypeError:
            if index is None or index is False:
                color = None
            elif index is True:
                color = self.get_color(self.fore_color, self.palette)
            else:
                if not isinstance(index, int):
                    index = int(index)
                color = palette[index % len(palette)]

        return color

    def advance(self):
        """
        calculate next state of the field depending on current
        :return: changed data's position. paint should be later called on this position
        """
        color = self.get_color(self.pattern[self.patt_step])

        if color is None:
            value = 0
        else:
            value = self.direction[0]*self.direction[1]

        # field data:      at given coordinates, [1(\)0( )-1(/)], line,  top,           bottom, already rendered
        self.data[self.position[0]][self.position[1]] = [value, color,
                                                         self.get_color(self.back_color),
                                                         self.get_color(self.back_color), False]
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
                if self.profile_string is not None:
                    pygame.event.post(pygame.event.Event(self.EVENT_EXEC, {'do': self.profile_string}))

                pygame.event.post(pygame.event.Event(pygame.QUIT))

        temp = self.position
        self.position = new_position
        return temp

    def repaint(self, force = False):
        """
        paint whole field
        :param force: repaint all parts of field
        :return: new value to be applied to self.draw
        """
        field = None
        draw  = True
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
            draw = False
        return draw

    def automatic_colouring(self, repaint = False):
        result = True
        try:
            point = self.uncoloured.pop()
        except KeyError:
            result = False
        else:
            self.flood(point=point, auto=True)

        if repaint or not result:
            self.repaint()

        return result

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

        if picker:
            rows = self.color_picker_rows
        else:
            rows = 1
        size = (self.size[0], self.size[1] + self.color_picker_height * rows)
        if pygame.display.get_surface().get_size() != size:
            pygame.display.set_mode(size)

        pick_box = pygame.Surface((self.size[0], self.color_picker_height * rows)).convert()

        if picker:
            length = len(palette)-2
            width = (pick_box.get_size()[0] - self.color_picker_height/2) * \
                    self.color_picker_rows / len(palette)
            columns = length/rows
            bw_width = max(self.color_picker_height + 1, width)
            pygame.draw.rect(pick_box,
                             self.get_color(0, palette),
                             pygame.Rect(
                                 pick_box.get_size()[0] - bw_width,
                                 0,
                                 bw_width + 1,
                                 self.color_picker_height * rows/2))
            pygame.draw.rect(pick_box,
                             self.get_color(-1, palette),
                             pygame.Rect(
                                 pick_box.get_size()[0] - bw_width,
                                 self.color_picker_height * rows/2,
                                 bw_width + 1,
                                 self.color_picker_height * rows/2))
            for index in range(length):
                pygame.draw.rect(pick_box,
                                 self.get_color(index + 1, palette),
                                 pygame.Rect(
                                     (index % columns) * width,
                                     self.color_picker_height * divmod(index, columns)[0],
                                     width + 1,
                                     self.color_picker_height))
        else:
            pygame.draw.rect(pick_box, self.get_color(self.click_color), pick_box.get_rect())

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
        process mouse click event.
        :param event:
        :return:
        """
        if event.button == 4:
            self.change_click_color(+1)
        if event.button == 5:
            self.change_click_color(-1)
        if event.button == 1 or event.button == 3:
            color = (event.button == 1 and
                     [self.get_color(self.click_color)] or
                     [self.get_color(self.back_color)])[0]

            if event.pos[1] < self.size[1]:
                if not self.draw:
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

    def flood(self, pos = None, color = None, point = None, auto = False):
        """
        flood fill with chosen color
        :param pos:   data coordinates of starting point
        :param color: color to fill with
        :return:      modified screen that was used for painting
        """
        if not auto and color is None:
            raise TypeError('Color must be specified unless auto-painting is done')

        if pos is None and point is None:
            raise TypeError('Either on-screen coordinates or field point coordinates must be specified')

        if point is None:
            place = (int(pos[0]/self.scale[0]) % self.size[0], int(pos[1]/self.scale[1]) % self.size[1])
            value = (self.data[place[0]][place[1]][0] == -1 and [-1] or [1])[0]
            # top's value is index of corresponding color in data; 2 is top, 3 is bottom
            top = ((0 < pos[0] % self.scale[0] - value*(pos[1] % self.scale[1]) < sum(self.scale)/2) and [2] or [3])[0]
            point = tuple(place) + (top, )

        screen = pygame.display.get_surface()

        #for logic of calculating adjacent positions: see doc folder
        #could've been done clearer, I guess
        if (self.data[point[0]][point[1]][point[2]] != color and color is not None) \
            or (auto and self.data[point[0]][point[1]][point[2]] == self.get_color(self.back_color)):
            area = self.get_contiguous_area(point, auto)
            if auto:
                color = self.get_color(int(len(area)/2), self.auto_palette)
            for position in area:
                self.data[position[0]][position[1]][position[2]] = color
                self.data[position[0]][position[1]][4] = False

        return screen

    def get_contiguous_area(self, pos, mark_as_coloured = False):
        queue = set()
        result = set()
        queue.add(pos)
        result.add(pos)
        while 1:
                try:
                    point = queue.pop()
                except KeyError:
                    break
                else:
                    for direction in ['h', 'v', 's']:
                        try:
                            temp = self.get_adjacent_to(point, direction)
                            if temp not in result:
                                queue.add(temp)
                                result.add(temp)
                        except IndexError:
                            pass
        if mark_as_coloured:
            self.uncoloured = self.uncoloured - result

        return result

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
            + ', color is (%i, %i, %i) ' %  self.get_color(self.click_color) + '#%i' % self.click_color)

if __name__ == "__main__":
    game = ReflectionPattern(auto_color=True, base=(81, 79), scale=6, fps=0, paint_auto_steps=True)
    game.execute()
# 123 119
# 19  21
# 317 182
# 225 113
