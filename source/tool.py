import json
import logging
import os
from abc import abstractmethod

import pygame as pg
from pygame.locals import *

from . import constants as c

logger = logging.getLogger('main')

# 状态机 抽象基类
class State:
    def __init__(self):
        self.start_time = 0
        self.current_time = 0
        self.done = False   # false 代表未做完
        self.next = None    # 表示这个状态退出后要转到的下一个状态
        self.persist = {}   # 在状态间转换时需要传递的数据

    # 当从其他状态进入这个状态时，需要进行的初始化操作
    @abstractmethod
    def startup(self, current_time: int, persist: dict):
        # 前面加了@abstractmethod表示抽象基类中必须要重新定义的method（method是对象和函数的结合）
        pass

    # 当从这个状态退出时，需要进行的清除操作
    def cleanup(self):
        self.done = False
        return self.persist

    # 在这个状态运行时进行的更新操作
    @abstractmethod
    def update(self, surface: pg.Surface, keys, current_time: int):
        # 前面加了@abstractmethod表示抽象基类中必须要重新定义的method
        pass

    # 工具：范围判断函数，用于判断点击
    def inArea(self, rect: pg.Rect, x: int, y: int):
        if rect.x <= x <= rect.right and rect.y <= y <= rect.bottom:
            return True
        else:
            return False

    # 工具：用户数据保存函数
    def saveUserData(self):
        with open(c.USERDATA_PATH, 'w', encoding='utf-8') as f:
            userdata = {}
            for i in self.game_info:
                if i in c.INIT_USERDATA:
                    userdata[i] = self.game_info[i]
            data_to_save = json.dumps(userdata, sort_keys=True, indent=4)
            f.write(data_to_save)


# 进行游戏控制 循环 事件响应
class Control:
    def __init__(self):
        self.screen = pg.display.get_surface()
        self.done = False
        self.clock = pg.time.Clock()    # 创建一个对象来帮助跟踪时间
        self.keys = pg.key.get_pressed()
        self.mouse_pos = None
        self.mouse_click = [
            False,
            False,
        ]  # value:[left mouse click, right mouse click]
        self.current_time = 0.0
        self.state_dict = {}
        self.state_name = None
        self.state = None
        try:
            # 存在存档即导入
            # 先自动修复读写权限(Python权限规则和Unix不一样，420表示unix的644，Windows自动忽略不支持项)
            os.chmod(c.USERDATA_PATH, 420)
            with open(c.USERDATA_PATH, encoding='utf-8') as f:
                userdata = json.load(f)
        except FileNotFoundError:
            self.setupUserData()
        except json.JSONDecodeError:
            logger.warning('用户存档解码错误！程序将新建初始存档！\n')
            self.setupUserData()
        else:   # 没有引发异常才执行
            self.game_info = {}
            # 导入数据，保证了可运行性，但是放弃了数据向后兼容性，即假如某些变量在以后改名，在导入时可能会被重置
            need_to_rewrite = False
            for key in c.INIT_USERDATA:
                if key in userdata:
                    self.game_info[key] = userdata[key]
                else:
                    self.game_info[key] = c.INIT_USERDATA[key]
                    need_to_rewrite = True
            if need_to_rewrite:
                with open(c.USERDATA_PATH, 'w', encoding='utf-8') as f:
                    savedata = json.dumps(
                        self.game_info, sort_keys=True, indent=4
                    )
                    f.write(savedata)
        # 存档内不包含即时游戏时间信息，需要新建
        self.game_info[c.CURRENT_TIME] = 0

        # 50为目前的基础帧率，乘以倍率即是游戏帧率
        self.fps = 50 * self.game_info[c.GAME_RATE]

    def setupUserData(self):
        if not os.path.exists(os.path.dirname(c.USERDATA_PATH)):
            os.makedirs(os.path.dirname(c.USERDATA_PATH))
        with open(c.USERDATA_PATH, 'w', encoding='utf-8') as f:
            savedata = json.dumps(c.INIT_USERDATA, sort_keys=True, indent=4)
            f.write(savedata)
        self.game_info = c.INIT_USERDATA.copy()   # 内部全是不可变对象，浅拷贝即可

    def setup_states(self, state_dict: dict, start_state):
        self.state_dict = state_dict
        self.state_name = start_state
        self.state = self.state_dict[self.state_name]
        self.state.startup(self.current_time, self.game_info)

    def update(self):
        # 自 pygame_init() 调用以来的毫秒数 * 游戏速度倍率，即游戏时间
        self.current_time = pg.time.get_ticks() * self.game_info[c.GAME_RATE]

        if self.state.done:
            self.flip_state()

        self.state.update(
            self.screen, self.current_time, self.mouse_pos, self.mouse_click
        )
        self.mouse_pos = None
        self.mouse_click[0] = False
        self.mouse_click[1] = False

    # 状态转移
    def flip_state(self):
        if self.state.next == c.EXIT:
            pg.quit()
            os._exit(0)
        self.state_name = self.state.next
        persist = self.state.cleanup()
        self.state = self.state_dict[self.state_name]
        self.state.startup(self.current_time, persist)

    def event_loop(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.done = True
            elif event.type == pg.KEYDOWN:
                self.keys = pg.key.get_pressed()
                if event.key == pg.K_f:
                    pg.display.set_mode(
                        c.SCREEN_SIZE, pg.HWSURFACE | pg.FULLSCREEN
                    )
                elif event.key == pg.K_u:
                    pg.display.set_mode(c.SCREEN_SIZE)
            elif event.type == pg.KEYUP:
                self.keys = pg.key.get_pressed()
            elif event.type == pg.MOUSEBUTTONDOWN:
                self.mouse_pos = pg.mouse.get_pos()
                (
                    self.mouse_click[0],
                    _,
                    self.mouse_click[1],
                ) = pg.mouse.get_pressed()
                logger.debug(
                    '点击位置: (%s, %s) 左右键点击情况: %s',
                    self.mouse_pos[0],
                    self.mouse_pos[1],
                    self.mouse_click,
                )

    def draw_fps(self):
        fps_text = get_font(14).render(
            f'FPS: {self.clock.get_fps():.1f}', True, c.WHITE, c.BLACK
        )
        self.screen.blit(fps_text, (5, 5))

    def run(self):
        while not self.done:
            self.event_loop()
            self.update()
            if c.SHOW_FPS:
                self.draw_fps()
            pg.display.update()
            self.clock.tick(self.fps)


def get_image(
    sheet: pg.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    colorkey: tuple[int] = c.BLACK,
    scale: int = 1,
) -> pg.Surface:
    # 不保留alpha通道的图片导入
    image = pg.Surface([width, height])
    rect = image.get_rect()

    image.blit(sheet, (0, 0), (x, y, width, height))
    if colorkey:
        image.set_colorkey(colorkey)
    if scale != 1:
        image = pg.transform.scale(
            image, (int(rect.width * scale), int(rect.height * scale))
        )
    return image


def get_image_alpha(
    sheet: pg.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    colorkey: tuple[int] = c.BLACK,
    scale: int = 1,
) -> pg.Surface:
    # 保留alpha通道的图片导入
    image = pg.Surface([width, height], SRCALPHA)
    rect = image.get_rect()

    image.blit(sheet, (0, 0), (x, y, width, height))
    image.set_colorkey(colorkey)
    if scale != 1:
        image = pg.transform.scale(
            image, (int(rect.width * scale), int(rect.height * scale))
        )
    return image


_FONTS: dict[tuple[int, bool], pg.font.Font] = {}


def get_font(size: int, bold: bool = False) -> pg.font.Font:
    key = (size, bold)
    if key not in _FONTS:
        font = pg.font.Font(c.FONT_PATH, size)
        font.bold = bold
        _FONTS[key] = font
    return _FONTS[key]


def load_image_frames(
    directory: str, image_name: str, colorkey: tuple[int], accept: tuple[str]
) -> list[pg.Surface]:
    frame_list = []
    tmp = {}
    # image_name is "Peashooter", pic name is "Peashooter_1", get the index 1
    index_start = len(image_name) + 1
    frame_num = 0
    for pic in os.listdir(directory):
        name, ext = os.path.splitext(pic)
        if ext.lower() in accept:
            index = int(name[index_start:])
            img = pg.image.load(os.path.join(directory, pic))
            if img.get_alpha():
                img = img.convert_alpha()
            else:
                img = img.convert()
                img.set_colorkey(colorkey)
            tmp[index] = img
            frame_num += 1

    for i in range(frame_num):  # 这里注意编号必须连续，否则会出错
        frame_list.append(tmp[i])
    return frame_list


# colorkeys 是设置图像中的某个颜色值为透明,这里用来消除白边
def load_all_gfx(
    directory: str,
    colorkey: tuple[int] = c.WHITE,
    accept: tuple[str] = ('.png', '.jpg', '.bmp', '.gif', '.webp'),
) -> dict[str : pg.Surface]:
    graphics = {}
    for name1 in os.listdir(directory):
        # subfolders under the folder resources\graphics
        dir1 = os.path.join(directory, name1)
        if os.path.isdir(dir1):
            for name2 in os.listdir(dir1):
                dir2 = os.path.join(dir1, name2)
                if os.path.isdir(dir2):
                    # e.g. subfolders under the folder resources\graphics\Zombies
                    for name3 in os.listdir(dir2):
                        dir3 = os.path.join(dir2, name3)
                        # e.g. subfolders or pics under the folder resources\graphics\Zombies\ConeheadZombie
                        if os.path.isdir(dir3):
                            # e.g. it"s the folder resources\graphics\Zombies\ConeheadZombie\ConeheadZombieAttack
                            image_name, _ = os.path.splitext(name3)
                            graphics[image_name] = load_image_frames(
                                dir3, image_name, colorkey, accept
                            )
                        else:
                            # e.g. pics under the folder resources\graphics\Plants\Peashooter
                            image_name, _ = os.path.splitext(name2)
                            graphics[image_name] = load_image_frames(
                                dir2, image_name, colorkey, accept
                            )
                            break
                else:
                    # e.g. pics under the folder resources\graphics\Screen
                    name, ext = os.path.splitext(name2)
                    if ext.lower() in accept:
                        img = pg.image.load(dir2)
                        if img.get_alpha():
                            img = img.convert_alpha()
                        else:
                            img = img.convert()
                            img.set_colorkey(colorkey)
                        graphics[name] = img
    return graphics


def _scan_gfx_index(
    directory: str,
    accept: tuple[str] = ('.png', '.jpg', '.bmp', '.gif', '.webp'),
) -> dict[str, tuple]:
    index = {}
    if not os.path.isdir(directory):
        return index
    for name1 in os.listdir(directory):
        dir1 = os.path.join(directory, name1)
        if os.path.isdir(dir1):
            for name2 in os.listdir(dir1):
                dir2 = os.path.join(dir1, name2)
                if os.path.isdir(dir2):
                    for name3 in os.listdir(dir2):
                        dir3 = os.path.join(dir2, name3)
                        if os.path.isdir(dir3):
                            image_name, _ = os.path.splitext(name3)
                            index[image_name] = ('frames', dir3, image_name)
                        else:
                            image_name, _ = os.path.splitext(name2)
                            index[image_name] = ('frames', dir2, image_name)
                            break
                else:
                    name, ext = os.path.splitext(name2)
                    if ext.lower() in accept:
                        index[name] = ('image', dir2)
    return index


class GfxDict:
    def __init__(self, directory: str):
        self._directory = directory
        self._cache: dict[str, object] = {}
        self._index: dict[str, tuple] | None = None

    def _ensure_index(self):
        if self._index is None:
            self._index = _scan_gfx_index(self._directory)

    def _load(self, name: str):
        self._ensure_index()
        if name not in self._index:
            raise KeyError(name)
        entry = self._index[name]
        if entry[0] == 'frames':
            _, directory, image_name = entry
            self._cache[name] = load_image_frames(
                directory, image_name, c.WHITE, ('.png', '.jpg', '.bmp', '.gif', '.webp')
            )
        else:
            _, path = entry
            img = pg.image.load(path)
            if img.get_alpha():
                img = img.convert_alpha()
            else:
                img = img.convert()
                img.set_colorkey(c.WHITE)
            self._cache[name] = img

    def __getitem__(self, name: str):
        if name not in self._cache:
            self._load(name)
        return self._cache[name]

    def get(self, name: str, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def preload_names(self, names):
        for name in names:
            if name not in self._cache:
                try:
                    self._load(name)
                except KeyError:
                    pass

    def preload_category(self, category: str):
        self._ensure_index()
        category_path = os.path.join(self._directory, category)
        for name, entry in self._index.items():
            path = entry[1]
            if path.startswith(category_path):
                self.preload_names([name])


def preload_menu_gfx():
    for category in ('Screen',):
        GFX.preload_category(category)
    GFX.preload_names(
        [
            c.MAIN_MENU_IMAGE,
            c.OPTION_ADVENTURE,
            c.LITTLEGAME_BUTTON,
            c.EXIT,
            c.OPTION_BUTTON,
            c.HELP,
            c.TROPHY_SUNFLOWER,
            c.BIG_MENU,
            c.UNIVERSAL_BUTTON,
            c.SOUND_VOLUME_BUTTON,
        ]
    )
    for i in range(2):
        GFX.preload_names(
            [
                f'{c.OPTION_ADVENTURE}_{i}',
                f'{c.LITTLEGAME_BUTTON}_{i}',
                f'{c.EXIT}_{i}',
                f'{c.OPTION_BUTTON}_{i}',
                f'{c.HELP}_{i}',
            ]
        )


def preload_level_gfx(map_data: dict | None = None):
    GFX.preload_names(
        [
            c.BACKGROUND_NAME,
            c.LITTLE_MENU,
            c.SHOVEL,
            c.SHOVEL_BOX,
            c.CAR,
            c.BOOM_IMAGE,
            c.HUGE_WAVE_APPROCHING,
            c.LEVEL_PROGRESS_BAR,
            c.LEVEL_PROGRESS_ZOMBIE_HEAD,
            c.LEVEL_PROGRESS_FLAG,
            c.SUN,
        ]
    )
    if map_data is not None:
        GFX.preload_names([c.BACKGROUND_NAME])


pg.display.set_caption(c.ORIGINAL_CAPTION)  # 设置标题
SCREEN = pg.display.set_mode(c.SCREEN_SIZE, pg.SCALED)   # 设置初始屏幕
pg.mixer.set_num_channels(64)
if os.path.exists(
    c.ORIGINAL_LOGO
):    # 设置窗口图标，仅对非Nuitka时生效，Nuitka不需要包括额外的图标文件，自动跳过这一过程即可
    pg.display.set_icon(pg.image.load(c.ORIGINAL_LOGO))

GFX = GfxDict(c.PATH_IMG_DIR)
preload_menu_gfx()
