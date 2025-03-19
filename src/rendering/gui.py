import pygame

# Colors
COLOR_WHITE = (255,255,255)
COLOR_BLACK = (0,0,0)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_CYAN = (0, 255, 255)
COLOR_MAGENTA = (255, 0, 255)
COLOR_ORANGE = (255, 165, 0)
COLOR_PURPLE = (128, 0, 128)
COLOR_BROWN = (139, 69, 19)
COLOR_PINK = (255, 192, 203)
COLOR_LIGHT_BLUE = (173, 216, 230)
COLOR_DARK_BLUE = (0, 0, 139)
COLOR_LIGHT_GREEN = (144, 238, 144)
COLOR_DARK_GREEN = (0, 100, 0)
COLOR_BEIGE = (245, 245, 220)
COLOR_TEAL = (0, 128, 128)
COLOR_GOLD = (255, 215, 0)
COLOR_SILVER = (192, 192, 192)
COLOR_MAROON = (128, 0, 0)
COLOR_NAVY = (0, 0, 128)
COLOR_TURQUOISE = (64, 224, 208)
COLOR_LAVENDER = (230, 230, 250)
COLOR_INDIGO = (75, 0, 130)

if False:
    COLOR_TITLE = COLOR_PINK
    COLOR_CONTENT = COLOR_GREEN
    COLOR_SCROLLBAR = COLOR_LIGHT_BLUE
    COLOR_SCROLL = COLOR_BLUE
    COLOR_TEXT = COLOR_BLACK
    COLOR_BORDER = COLOR_ORANGE
    COLOR_BG = COLOR_WHITE
    COLOR_EXTRAS = COLOR_CYAN
    COLOR_BUTTON = COLOR_MAROON
else:
    COLOR_TITLE = (20, 20, 20)
    COLOR_CONTENT = (30, 30, 30)
    COLOR_SCROLLBAR = (30, 30, 30)
    COLOR_SCROLL = (200, 50, 50)
    COLOR_TEXT = (255, 255, 255)
    COLOR_BORDER = (50, 50, 50)
    COLOR_BG = (60, 60, 60)
    COLOR_EXTRAS = COLOR_SILVER
    COLOR_BUTTON = COLOR_MAROON


def clamp(val, min_val, max_val):
    return min(max_val, max(val, min_val))

def map_value(x, x1, x2, y1, y2):
    return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

def absolute_rect(main_rect, relative_rect):
    return pygame.Rect(main_rect.x+relative_rect.x,
                       main_rect.y+relative_rect.y,
                       relative_rect.width,
                       relative_rect.height)

class Button:
    def __init__(self, text, y):
        self.text = text
        self.y = y
        self.clicked = False
        self.clickable = True
        self.rect = None

    def __repr__(self):
        return f"Text: {self.text}, y: {self.y}"


class Window:
    def __init__(self, x, y, width, height, title, font, screen):
        self.font = font
        self.title = title
        self.screen = screen
        self.font_height = self.font.get_height()
        self.font_width = font.render(" ", True, (0,0,0)).get_width()

        self.texts = []
        self.buttons = []

        self.current_y = 0

        self.dragging = False
        self.resizing = False
        self.docking = False
        self.dock_area = 0
        #0-up, 1-down, 2-left, 3-right

        self.scrollbar_width = 10
        self.scrollbar_position = 0
        self.scrollbar_height = 100
        self.scrollbar_dragging = False
        self.scrollbar_draggable = True

        self.active = False

        self.recalc(x, y, width, height)

    def __repr__(self):
        return f"Texts: {len(self.texts)}, buttons: {len(self.buttons)}, y: {self.current_y}"

    def draw(self):
        if self.active:
            pygame.draw.rect(self.screen, COLOR_BORDER, absolute_rect(self.main_rect, self.border_rect))
        #pygame.draw.rect(self.screen, COLOR_RED, self.main_rect)
        pygame.draw.rect(self.screen, COLOR_SCROLLBAR, absolute_rect(self.main_rect, self.scrollbar_bg_rect))
        pygame.draw.rect(self.screen, COLOR_TITLE, absolute_rect(self.main_rect, self.title_rect))
        if self.scrollbar_draggable == True:
            pygame.draw.rect(self.screen, COLOR_SCROLL, absolute_rect(self.main_rect, self.scroll))
        if not self.docking:
            pygame.draw.rect(self.screen, COLOR_EXTRAS, absolute_rect(self.main_rect, self.resize_rect))
        else:
            if self.dock_area == 0:
                pygame.draw.rect(self.screen, COLOR_EXTRAS, self.resize_down_rect)
            elif self.dock_area == 1:
                pygame.draw.rect(self.screen, COLOR_EXTRAS, self.resize_up_rect)
            elif self.dock_area == 2:
                pygame.draw.rect(self.screen, COLOR_EXTRAS, self.resize_right_rect)
            elif self.dock_area == 3:
                pygame.draw.rect(self.screen, COLOR_EXTRAS, self.resize_left_rect)

        pygame.draw.rect(self.screen, COLOR_CONTENT, absolute_rect(self.main_rect, self.content_rect))

        self.font.set_bold(False)
        self.font.set_italic(False)
        self.font.set_underline(False)

        buffer = int((self.content_rect.height) / self.font_height)
        num_lines = 0
        if len(self.texts) != 0:
            num_lines = self.texts[-1][0]
        if len(self.buttons) != 0:
            num_lines = max(num_lines, self.buttons[-1].y)
        num_lines += 1

        if num_lines <= buffer:
            self.scrollbar_draggable = False
        else:
            self.scrollbar_draggable = True
            self.scrollbar_height = buffer / num_lines * (self.scrollbar_bg_rect.height)

        percent_scroll = self.scrollbar_position / (self.scrollbar_bg_rect.height - self.scrollbar_height)
        font_render = self.font.render(f"{self.title}", True, COLOR_TEXT)
        title_rect_abs = absolute_rect(self.main_rect, self.title_rect)
        self.screen.blit(font_render, (title_rect_abs.x+self.font_width, title_rect_abs.y))

        prev_y = 0
        x = 0
        y_offset = 0
        val = map_value(percent_scroll, 0, 1, buffer, num_lines)
        start_line = int(val - buffer)
        end_line = start_line + buffer - 1
        skip_y = -1
        for y,text,color,bold,italic,underline in self.texts:
            if y == skip_y:
                continue
            if y < start_line:
                y_offset = start_line
                continue
            if y > end_line:
                break
            if y != prev_y:
                x = 0
            prev_y = y
            self.font.set_bold(bold)
            self.font.set_italic(italic)
            self.font.set_underline(underline)
            font_render = self.font.render(text, True, color)
            # if x + font_render.get_width() > self.content_rect.width:
            #     skip_y = y
            #     continue
            content_rect_abs = absolute_rect(self.main_rect, self.content_rect)
            self.screen.blit(font_render, (content_rect_abs.x + x + self.font_width, content_rect_abs.y + (y-y_offset) * self.font_height))
            x += font_render.get_width()# + self.font_width

        self.font.set_bold(False)
        self.font.set_italic(False)
        self.font.set_underline(False)

        p = 2
        for button in self.buttons:
            button_rect = pygame.Rect(self.content_rect.width*0.1, button.y * self.font_height + p, self.content_rect.width*0.8, self.font_height-2*p)
            y = button.y
            if y < start_line:
                y_offset = start_line
                button.clickable = False
                continue
            if y > end_line:
                button.clickable = False
                continue
            button.clickable = True
            button_rect.y = self.content_rect.y + (y-y_offset) * self.font_height + p
            button.rect = button_rect
            pygame.draw.rect(self.screen, COLOR_BUTTON, absolute_rect(self.main_rect, button_rect))
            font_render = self.font.render(button.text, True, COLOR_TEXT)
            content_rect_abs = absolute_rect(self.main_rect, self.content_rect)
            self.screen.blit(font_render, (content_rect_abs.x + content_rect_abs.width/2-font_render.get_width()/2, content_rect_abs.y + (y-y_offset) * self.font_height))

        if self.dragging:
            pygame.draw.rect(self.screen, COLOR_EXTRAS, self.dock_right_rect)
            pygame.draw.rect(self.screen, COLOR_EXTRAS, self.dock_left_rect)
            pygame.draw.rect(self.screen, COLOR_EXTRAS, self.dock_up_rect)
            pygame.draw.rect(self.screen, COLOR_EXTRAS, self.dock_down_rect)

    def handle_event(self, event):
        if not self.active:
            return
        self.handle_resize(event)
        self.handle_scroll(event)
        self.handle_drag(event)
        self.handle_buttons(event)

    def handle_scroll(self, event):
        if self.scrollbar_draggable == False or self.resizing:
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            scroll_rect = absolute_rect(self.main_rect, self.scroll)
            if scroll_rect.collidepoint(event.pos):
                self.scrollbar_dragging = True
                mouse_x, mouse_y = event.pos
                self.mouse_scroll_offset = mouse_y - (self.main_rect.y + self.scrollbar_position)
        elif event.type == pygame.MOUSEMOTION:
            if self.scrollbar_dragging:
                mouse_x, mouse_y = event.pos
                new_position = mouse_y - self.mouse_scroll_offset - self.main_rect.y
                self.scrollbar_position = clamp(new_position, 0, self.scrollbar_bg_rect.height-self.scrollbar_height)
                self.recalc(self.main_rect.x, self.main_rect.y, self.main_rect.width, self.main_rect.height)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.scrollbar_dragging = False

    def handle_drag(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            title_rect = absolute_rect(self.main_rect, self.title_rect)
            if title_rect.collidepoint(event.pos):
                if self.docking:
                    mouse_x, mouse_y = event.pos
                    self.recalc(mouse_x-self.font_height/2, mouse_y-self.font_height/2, self.prev_rect.width, self.prev_rect.height)
                    self.docking = False
                self.dragging = True
                mouse_x, mouse_y = event.pos
                self.mouse_drag_offset_x = mouse_x - self.main_rect.x
                self.mouse_drag_offset_y = mouse_y - self.main_rect.y
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mouse_x, mouse_y = event.pos
                new_position_x = mouse_x - self.mouse_drag_offset_x
                new_position_y = mouse_y - self.mouse_drag_offset_y
                self.recalc(new_position_x, new_position_y, self.main_rect.width, self.main_rect.height)
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging:
                self.prev_rect = self.main_rect.copy()
                if self.dock_right_rect.collidepoint(event.pos):
                    self.dock(3)
                elif self.dock_left_rect.collidepoint(event.pos):
                    self.dock(2)
                elif self.dock_up_rect.collidepoint(event.pos):
                    self.dock(0)
                elif self.dock_down_rect.collidepoint(event.pos):
                    self.dock(1)
                self.dragging = False

    def dock(self, area, offset=0):
        self.docking = True
        self.dock_area = area
        if offset == -1:
            width = self.window_size[0] / 10
            height = self.window_size[1] / 10
        else:
            width = offset
            height = offset
        self.window_size = pygame.display.get_window_size()
        if area == 3:
            self.recalc(self.window_size[0]-width, 0, width, self.window_size[1])
        elif area == 2:
            self.recalc(0, 0, width, self.window_size[1])
        elif area == 0:
            self.recalc(0, 0, self.window_size[0], height)
        elif area == 1:
            self.recalc(0, self.window_size[1]-height, self.window_size[0], height)

    def handle_resize(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            if self.docking:
                if self.dock_area == 1:
                    if self.resize_up_rect.collidepoint(event.pos):
                        self.mouse_resize_up_offset_y = mouse_y -(self.resize_up_rect.y+self.resize_up_rect.height)
                        self.resizing = True
                elif self.dock_area == 0:
                    if self.resize_down_rect.collidepoint(event.pos):
                        self.mouse_resize_down_offset_y = mouse_y -self.main_rect.height
                        self.resizing = True
                elif self.dock_area == 2:
                    if self.resize_right_rect.collidepoint(event.pos):
                        self.mouse_resize_right_offset_x = mouse_x -self.main_rect.width
                        self.resizing = True
                elif self.dock_area == 3:
                    if self.resize_left_rect.collidepoint(event.pos):
                        self.mouse_resize_left_offset_x = mouse_x - (self.resize_left_rect.x+self.resize_left_rect.width)
                        self.resizing = True
            else:
                resize_rect = absolute_rect(self.main_rect, self.resize_rect)
                if resize_rect.collidepoint(event.pos):
                    self.resizing = True
                    mouse_x, mouse_y = event.pos
                    self.mouse_resize_offset_x = mouse_x - self.main_rect.width
                    self.mouse_resize_offset_y = mouse_y -self.main_rect.height
        elif event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = event.pos
            if self.docking:
                if self.dock_area == 1 and self.resizing:
                    new_height = self.window_size[1] - (mouse_y - self.mouse_resize_up_offset_y)
                    self.recalc(self.main_rect.x, self.window_size[1]-new_height, self.main_rect.width, new_height)
                elif self.dock_area == 0 and self.resizing:
                    new_height = mouse_y - self.mouse_resize_down_offset_y
                    self.recalc(self.main_rect.x, self.main_rect.y, self.main_rect.width, new_height)
                elif self.dock_area == 2 and self.resizing:
                    new_width = mouse_x - self.mouse_resize_right_offset_x
                    self.recalc(self.main_rect.x, self.main_rect.y, new_width, self.main_rect.height)
                elif self.dock_area == 3 and self.resizing:
                    new_width = self.window_size[0] - (mouse_x - self.mouse_resize_left_offset_x)
                    self.recalc(self.window_size[0]-new_width, self.main_rect.y, new_width, self.main_rect.height)
            else:
                if self.resizing:
                    mouse_x, mouse_y = event.pos
                    new_width = mouse_x - self.mouse_resize_offset_x
                    new_height = mouse_y - self.mouse_resize_offset_y
                    self.recalc(self.main_rect.x, self.main_rect.y, new_width, new_height)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.resizing = False

    def handle_buttons(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, button in enumerate(self.buttons):
                button_rect = absolute_rect(self.main_rect, button.rect)
                if button_rect.collidepoint(event.pos):
                    button.clicked = True
                    break

    def recalc(self, pos_x, pos_y, width, height):
        self.window_size = pygame.display.get_window_size()
        width = clamp(width, 100 ,self.window_size[0])
        height = clamp(height, 100, self.window_size[1])
        pos_x = clamp(pos_x, 0, self.window_size[0]-width)
        pos_y = clamp(pos_y, 0, self.window_size[1]-height)
        self.main_rect = pygame.Rect(pos_x, pos_y, width, height)
        border_thickness = 2
        self.border_rect = pygame.Rect(-border_thickness, -border_thickness, width+2*border_thickness, height+2*border_thickness)
        self.content_rect = pygame.Rect(0, self.font_height, width-self.scrollbar_width, height-self.font_height)
        self.scrollbar_bg_rect = pygame.Rect(width-self.scrollbar_width, self.font_height, self.scrollbar_width, height-self.font_height)
        self.title_rect = pygame.Rect(0, 0, width, self.font_height)
        pad = self.scrollbar_width/2
        big_pad = 20*pad
        self.resize_rect = pygame.Rect(self.main_rect.width - pad, self.main_rect.height - pad, pad, pad)
        self.scroll = pygame.Rect(self.scrollbar_bg_rect.x, self.scrollbar_bg_rect.y + self.scrollbar_position, self.scrollbar_width, self.scrollbar_height)

        self.dock_right_rect = pygame.Rect(self.window_size[0] - pad, self.window_size[1]/2-big_pad/2, pad, big_pad)
        self.dock_left_rect = pygame.Rect(0, self.window_size[1]/2-big_pad/2, pad, big_pad)
        self.dock_up_rect = pygame.Rect(self.window_size[0]/2 - big_pad/2, 0, big_pad, pad)
        self.dock_down_rect = pygame.Rect(self.window_size[0]/2 - big_pad/2, self.window_size[1]-pad, big_pad, pad)

        self.resize_down_rect = pygame.Rect(self.main_rect.width/2 - big_pad/2, self.main_rect.height, big_pad, pad)
        self.resize_up_rect = pygame.Rect(self.main_rect.width/2 - big_pad/2, self.main_rect.y-pad, big_pad, pad)
        self.resize_left_rect = pygame.Rect(self.main_rect.x-pad, self.main_rect.height/2-big_pad/2, pad, big_pad)
        self.resize_right_rect = pygame.Rect(self.main_rect.width, self.main_rect.height/2-big_pad/2, pad, big_pad)


class GUI:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font

        self.windows = []
        self.current_window = None
        self.sameline = False

    def handle_active(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                for window in reversed(self.windows):  # Check top-most first
                    if window.main_rect.collidepoint(event.pos):
                        self.windows.remove(window)  # Remove from current position
                        self.windows.append(window)  # Move to top (last in list)
                        window.active = True
                        # Deactivate other windows
                        for w in self.windows:
                            if w != window:
                                w.active = False
                        break  # Stop after first match

    def handle_event(self, event):
        self.handle_active(event)
        for window in self.windows:
            window.handle_event(event)

    def begin_window(self, x, y, width, height, title, dock_area=-1, dock_offset=0):
        for window in self.windows:
            if window.title == title:
                self.current_window = window
                self.current_window.texts.clear()
                self.current_window.current_y = 0
                return
        self.current_window = Window(x,y,width,height,title,self.font,self.screen)
        self.current_window.prev_rect = self.current_window.main_rect
        if dock_area != -1:
            self.current_window.dock(dock_area, dock_offset)

    def end_window(self):
        if not self.current_window:
            return
        for window in self.windows:
            if window.title == self.current_window.title:
                return
        self.windows.append(self.current_window)
        self.current_window = None

    def same_line(self):
        self.sameline = True
        if self.current_window:
            self.current_window.current_y -= 1

    def add_text(self, text, bold=False, italic=False, underline=False):
        self.add_text_with_color(text, COLOR_TEXT, bold, italic, underline)

    def add_text_with_color(self, text, color, bold=False, italic=False, underline=False):
        if not self.current_window:
            return
        exist = False
        # for t in self.current_window.texts:
        #     if t[1] == text and t[0] == self.current_window.current_y:
        #         exist = True
        if not exist:
            data = (self.current_window.current_y, text, color, bold, italic, underline)
            self.current_window.texts.append(data)
            # words = text.split(" ")
            # for word in words:
            #     data = (self.current_window.current_y, word, color, bold, italic, underline)
            #     self.current_window.texts.append(data)
            self.current_window.current_y += 1
        self.sameline = False

    def add_button(self, text):
        if not self.current_window:
            return False
        exist = False
        y = self.current_window.current_y
        for b in self.current_window.buttons:
            if b.text == text:
                button = b
                exist = True
        if not exist:
            self.current_window.buttons.append(Button(text, y))
            button = self.current_window.buttons[-1]
        self.current_window.current_y += 1
        if button.clicked:
            button.clicked = False
            return True
        return False

    def draw(self):
        for window in self.windows:
            window.draw()