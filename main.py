import os
import json
import shutil
import datetime
from kivy.app import App
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image as KivyImage
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior
from kivy.utils import platform, get_color_from_hex

if platform == 'android':
    from android.storage import app_storage_path, primary_external_storage_path
    from android.permissions import request_permissions, Permission
    try:
        request_permissions([Permission.READ_EXTERNAL_STORAGE,
                              Permission.WRITE_EXTERNAL_STORAGE,
                              Permission.READ_MEDIA_IMAGES])
    except Exception as e:
        print("权限请求失败：", e)
    DATA_DIR = app_storage_path()
    try:
        BACKUP_ROOT_DEFAULT = os.path.join(primary_external_storage_path(),
                                            "OCManager_Backup")
    except Exception:
        BACKUP_ROOT_DEFAULT = os.path.join(DATA_DIR, "backups")
    # 用于扫描导入文件的候选目录
    SEARCH_DIRS = [
        "/storage/emulated/0/Download",
        "/storage/emulated/0/Documents",
        "/storage/emulated/0",
        "/sdcard/Download",
        "/sdcard/Documents",
    ]
else:
    DATA_DIR = os.path.dirname(os.path.abspath(__file__))
    BACKUP_ROOT_DEFAULT = os.path.join(DATA_DIR, "backups")
    SEARCH_DIRS = [DATA_DIR]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DATA_DIR, "oc_data.json")
CATEGORIES_FILE = os.path.join(DATA_DIR, "categories.json")
CONFIG_FILE = os.path.join(DATA_DIR, "app_config.json")

FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts", "simhei.ttf")
try:
    LabelBase.register(name='Chinese', fn_regular=FONT_PATH)
except Exception as e:
    print("字体注册失败：", e)


# ===== 读取/保存用户配置（备份路径等） =====
def load_app_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_app_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("保存配置失败：", e)


APP_CFG = load_app_config()
BACKUP_ROOT = APP_CFG.get("backup_root", BACKUP_ROOT_DEFAULT)


# ===== 配色 =====
C_PRIMARY       = get_color_from_hex("#4A90E2")
C_PRIMARY_DARK  = get_color_from_hex("#357ABD")
C_PRIMARY_LIGHT = get_color_from_hex("#E8F1FB")
C_SUCCESS       = get_color_from_hex("#52C41A")
C_SUCCESS_DARK  = get_color_from_hex("#3FA213")
C_DANGER        = get_color_from_hex("#FF4D4F")
C_DANGER_DARK   = get_color_from_hex("#D9363E")
C_BG            = get_color_from_hex("#F5F7FA")
C_CARD          = get_color_from_hex("#FFFFFF")
C_BORDER        = get_color_from_hex("#E4E7ED")
C_TEXT          = get_color_from_hex("#303133")
C_TEXT_SUB      = get_color_from_hex("#606266")
C_TEXT_LIGHT    = get_color_from_hex("#909399")
C_SIDEBAR       = get_color_from_hex("#EEF1F5")
C_SIDEBAR_HOVER = get_color_from_hex("#DDE3EB")

Window.clearcolor = C_BG
Window.softinput_mode = 'pan'  # 键盘弹出时整个页面平移


# ===== 统一弹窗（居中偏上） =====
def make_popup(title, content, size_hint=(0.85, 0.5)):
    return Popup(
        title=title,
        title_font='Chinese',
        title_size=sp(14),
        content=content,
        size_hint=size_hint,
        background_color=C_BG,
        pos_hint={'center_x': 0.5, 'center_y': 0.55},
        auto_dismiss=False,
    )


# ========== 圆角卡片容器 ==========
class CardBox(BoxLayout):
    def __init__(self, bg=C_CARD, radius=10, **kwargs):
        super().__init__(**kwargs)
        self._radius = dp(radius)
        with self.canvas.before:
            self._color = Color(*bg)
            self._rect = RoundedRectangle(
                radius=[self._radius], pos=self.pos, size=self.size)
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


# ========== 圆角按钮 ==========
class RoundedButton(Button):
    def __init__(self, bg_color=C_PRIMARY, text_color=(1, 1, 1, 1),
                 radius=8, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.color = text_color
        self.font_name = 'Chinese'
        self._bg = bg_color
        self._radius = dp(radius)
        with self.canvas.before:
            self._color = Color(*bg_color)
            self._rect = RoundedRectangle(
                radius=[self._radius], pos=self.pos, size=self.size)
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def set_bg(self, color):
        self._bg = color
        self._color.rgba = color


def btn_primary(text, **kw):
    return RoundedButton(text=text, bg_color=C_PRIMARY, **kw)


def btn_success(text, **kw):
    return RoundedButton(text=text, bg_color=C_SUCCESS, **kw)


def btn_danger(text, **kw):
    return RoundedButton(text=text, bg_color=C_DANGER, **kw)


def btn_ghost(text, **kw):
    return RoundedButton(text=text, bg_color=C_CARD,
                         text_color=C_TEXT, **kw)


def btn_light(text, **kw):
    return RoundedButton(text=text, bg_color=C_SIDEBAR,
                         text_color=C_TEXT, **kw)


# ========== 圆角输入框 ==========
class RoundedInput(TextInput):
    def __init__(self, radius=6, **kwargs):
        super().__init__(**kwargs)
        self.font_name = 'Chinese'
        self.background_normal = ''
        self.background_active = ''
        self.background_color = (0, 0, 0, 0)
        self.foreground_color = C_TEXT
        self.cursor_color = C_PRIMARY
        self.padding = [dp(8), dp(8), dp(8), dp(8)]
        self._radius = dp(radius)
        with self.canvas.before:
            self._border_color = Color(*C_BORDER)
            self._border_rect = RoundedRectangle(
                radius=[self._radius], pos=self.pos, size=self.size)
            self._bg_color = Color(*C_CARD)
            self._bg_rect = RoundedRectangle(
                radius=[self._radius],
                pos=(self.x + dp(1), self.y + dp(1)),
                size=(self.width - dp(2), self.height - dp(2)))
        self.bind(pos=self._update, size=self._update,
                  focus=self._on_focus)

    def _update(self, *args):
        self._border_rect.pos = self.pos
        self._border_rect.size = self.size
        self._bg_rect.pos = (self.x + dp(1), self.y + dp(1))
        self._bg_rect.size = (self.width - dp(2), self.height - dp(2))

    def _on_focus(self, instance, value):
        if value:
            self._border_color.rgba = C_PRIMARY
        else:
            self._border_color.rgba = C_BORDER


# ========== 自动高度 Label ==========
class AutoLabel(Label):
    def __init__(self, **kwargs):
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('halign', 'left')
        kwargs.setdefault('valign', 'top')
        kwargs.setdefault('font_name', 'Chinese')
        if 'font_size' not in kwargs:
            kwargs['font_size'] = sp(15)
        super().__init__(**kwargs)
        self.bind(width=self._on_width)
        self.bind(texture_size=self._on_texture)

    def _on_width(self, *args):
        self.text_size = (self.width, None)

    def _on_texture(self, *args):
        try:
            h = float(self.texture_size[1]) + dp(10)
        except Exception:
            h = dp(30)
        self.height = h


# ========== 可点击图片 ==========
class ClickableImage(ButtonBehavior, KivyImage):
    def __init__(self, full_path=None, **kwargs):
        super().__init__(**kwargs)
        self.full_path = full_path

    def on_press(self):
        if not self.full_path:
            return
        fixed = self.full_path.replace("\\", "/")
        if not os.path.exists(fixed):
            return
        content = BoxLayout(orientation='vertical', padding=dp(6),
                            spacing=dp(6))
        content.add_widget(KivyImage(source=fixed, allow_stretch=True,
                                      keep_ratio=True))
        close_btn = btn_primary("关闭", font_size=sp(15),
                                size_hint_y=None, height=dp(46))
        content.add_widget(close_btn)
        popup = make_popup(os.path.basename(fixed), content,
                           size_hint=(0.95, 0.95))
        popup.auto_dismiss = True
        close_btn.bind(on_press=popup.dismiss)
        popup.open()


# ========== 长按按钮 ==========
class LongPressButton(RoundedButton):
    def __init__(self, on_long_press=None, **kwargs):
        super().__init__(**kwargs)
        self._lp_event = None
        self._lp_callback = on_long_press

    def on_press(self):
        super().on_press()
        if self._lp_callback:
            self._lp_event = Clock.schedule_once(
                lambda dt: self._lp_callback(self), 0.6)

    def on_release(self):
        super().on_release()
        if self._lp_event:
            self._lp_event.cancel()
            self._lp_event = None


# ========== 主页 ==========
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.all_data = []
        self.categories = []
        self.current_cat = "全部"
        self.load_data()
        self.load_categories()
        self.build_ui()
        self.refresh_oc_list()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.all_data = json.load(f)
            except Exception:
                self.all_data = []
        else:
            self.all_data = []

    def load_categories(self):
        if os.path.exists(CATEGORIES_FILE):
            try:
                with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
                    self.categories = json.load(f)
            except Exception:
                self.categories = []
        else:
            self.categories = []

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.all_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print("保存失败：", e)
            return False

    def save_categories(self):
        try:
            with open(CATEGORIES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.categories, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print("保存分类失败：", e)
            return False

    def get_categories(self):
        cats = ["全部", "未分类"]
        for c in self.categories:
            if c and c not in cats:
                cats.append(c)
        for oc in self.all_data:
            c = oc.get("category", "")
            if c and c not in cats:
                cats.append(c)
        return cats

    def build_ui(self):
        outer = BoxLayout(orientation='vertical',
                          padding=dp(8), spacing=dp(8))

        top_card = CardBox(size_hint_y=None, height=dp(56),
                           padding=(dp(10), dp(8)))
        top_row = BoxLayout(spacing=dp(6))
        title = Label(text="OC 管理器", font_name='Chinese',
                      font_size=sp(18), bold=True, color=C_TEXT,
                      halign='left', valign='middle')
        title.bind(size=title.setter('text_size'))
        top_row.add_widget(title)

        menu_btn = RoundedButton(text="☰", bg_color=C_SIDEBAR,
                                  text_color=C_TEXT, font_size=sp(18),
                                  size_hint_x=None, width=dp(40))
        menu_btn.bind(on_press=self.open_main_menu)
        top_row.add_widget(menu_btn)

        new_btn = btn_primary("＋ 新建", font_size=sp(13),
                              size_hint_x=None, width=dp(80))
        new_btn.bind(on_press=self.on_new_oc)
        top_row.add_widget(new_btn)
        top_card.add_widget(top_row)
        outer.add_widget(top_card)

        body = BoxLayout(orientation='horizontal', spacing=dp(8))

        left_card = CardBox(size_hint_x=0.34, padding=dp(8), spacing=dp(6),
                            orientation='vertical')
        cat_title = Label(text="分类", font_name='Chinese',
                          font_size=sp(14), bold=True, color=C_TEXT,
                          size_hint_y=None, height=dp(28))
        left_card.add_widget(cat_title)

        self.cat_scroll = ScrollView(do_scroll_x=False,
                                      bar_width=dp(3),
                                      scroll_type=['bars', 'content'])
        self.cat_list = BoxLayout(orientation='vertical',
                                  size_hint_y=None, spacing=dp(4))
        self.cat_list.bind(minimum_height=self.cat_list.setter('height'))
        self.cat_scroll.add_widget(self.cat_list)
        left_card.add_widget(self.cat_scroll)

        add_cat_btn = btn_ghost("＋ 添加分类", font_size=sp(12),
                                size_hint_y=None, height=dp(40))
        add_cat_btn.bind(on_press=self.on_new_category)
        left_card.add_widget(add_cat_btn)

        body.add_widget(left_card)

        right_card = CardBox(padding=dp(8), spacing=dp(6),
                             orientation='vertical')
        self.oc_title = Label(text="全部", font_name='Chinese',
                              font_size=sp(14), bold=True, color=C_TEXT,
                              size_hint_y=None, height=dp(28))
        right_card.add_widget(self.oc_title)
        hint = Label(text="点名字进详情，长按删除",
                     font_name='Chinese', font_size=sp(10),
                     color=C_TEXT_LIGHT,
                     size_hint_y=None, height=dp(18))
        right_card.add_widget(hint)

        oc_scroll = ScrollView(do_scroll_x=False,
                               bar_width=dp(3),
                               scroll_type=['bars', 'content'])
        self.oc_list = BoxLayout(orientation='vertical',
                                 size_hint_y=None, spacing=dp(4))
        self.oc_list.bind(minimum_height=self.oc_list.setter('height'))
        oc_scroll.add_widget(self.oc_list)
        right_card.add_widget(oc_scroll)

        body.add_widget(right_card)
        outer.add_widget(body)
        self.add_widget(outer)
        self.refresh_category_list()

    def refresh_category_list(self):
        self.cat_list.clear_widgets()
        for cat in self.get_categories():
            is_special = cat in ("全部", "未分类")
            is_active = (cat == self.current_cat)

            if is_active:
                bg = C_PRIMARY
                fg = (1, 1, 1, 1)
            else:
                bg = C_PRIMARY_LIGHT if is_special else C_SIDEBAR
                fg = C_TEXT

            if is_special:
                btn = RoundedButton(text=cat, bg_color=bg, text_color=fg,
                                     font_size=sp(13),
                                     size_hint_y=None, height=dp(44))
            else:
                btn = LongPressButton(text=cat, bg_color=bg, text_color=fg,
                                       font_size=sp(13),
                                       size_hint_y=None, height=dp(44),
                                       on_long_press=lambda inst, c=cat:
                                       self.on_delete_category(c))
            btn.bind(on_press=lambda b, c=cat: self.on_category_click(c))
            self.cat_list.add_widget(btn)

    def on_category_click(self, cat):
        self.current_cat = cat
        self.oc_title.text = cat
        self.refresh_category_list()
        self.refresh_oc_list()

    def refresh_oc_list(self):
        self.oc_list.clear_widgets()
        for i, oc in enumerate(self.all_data):
            c = oc.get("category", "")
            if self.current_cat == "全部":
                m = True
            elif self.current_cat == "未分类":
                m = (c == "" or c not in self.get_categories())
            else:
                m = (c == self.current_cat)
            if m:
                btn = LongPressButton(
                    text=oc.get("name", "未命名"),
                    bg_color=C_PRIMARY_LIGHT, text_color=C_TEXT,
                    font_size=sp(14),
                    size_hint_y=None, height=dp(50),
                    on_long_press=lambda inst, idx=i: self.on_delete_oc(idx))
                btn.bind(on_press=lambda b, idx=i: self.on_oc_click(idx))
                self.oc_list.add_widget(btn)

    def on_oc_click(self, idx):
        detail = self.manager.get_screen('detail')
        detail.show_oc(self.all_data[idx])
        self.manager.current = 'detail'

    # ---------- 新建分类 ----------
    def on_new_category(self, instance):
        content = CardBox(orientation='vertical',
                          padding=dp(12), spacing=dp(10))
        content.add_widget(Label(text="新建分类", font_name='Chinese',
                                 font_size=sp(15), bold=True, color=C_TEXT,
                                 size_hint_y=None, height=dp(32)))
        name_input = RoundedInput(multiline=False,
                                   size_hint_y=None, height=dp(46))
        content.add_widget(name_input)

        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        ok_btn = btn_primary("确定", font_size=sp(14))
        cancel_btn = btn_light("取消", font_size=sp(14))
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)

        popup = make_popup("新建分类", content, size_hint=(0.85, 0.45))

        def on_ok(inst):
            name = name_input.text.strip()
            if not name:
                return
            if name in ("全部", "未分类"):
                self.show_toast("这是保留名")
                return
            if name in self.categories:
                self.show_toast("分类已存在")
                return
            self.categories.append(name)
            self.save_categories()
            popup.dismiss()
            self.refresh_category_list()
            self.show_toast(f"已添加：{name}")

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    # ---------- 删除分类 ----------
    def on_delete_category(self, cat):
        content = CardBox(orientation='vertical',
                          padding=dp(12), spacing=dp(10))
        content.add_widget(Label(text=f"删除分类「{cat}」？",
                                 font_name='Chinese', font_size=sp(15),
                                 bold=True, color=C_TEXT,
                                 size_hint_y=None, height=dp(40)))
        content.add_widget(Label(text="该分类下的 OC 会变成未分类",
                                 font_name='Chinese', font_size=sp(11),
                                 color=C_TEXT_SUB,
                                 size_hint_y=None, height=dp(28)))
        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        ok_btn = btn_danger("删除", font_size=sp(14))
        cancel_btn = btn_light("取消", font_size=sp(14))
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)

        popup = make_popup("删除分类", content, size_hint=(0.85, 0.45))

        def on_ok(inst):
            for oc in self.all_data:
                if oc.get("category") == cat:
                    oc["category"] = ""
            if cat in self.categories:
                self.categories.remove(cat)
            self.save_categories()
            self.save_data()
            popup.dismiss()
            self.current_cat = "全部"
            self.refresh_category_list()
            self.refresh_oc_list()
            self.show_toast(f"已删除：{cat}")

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    # ---------- 新建 OC ----------
    def on_new_oc(self, instance):
        content = CardBox(orientation='vertical',
                          padding=dp(12), spacing=dp(8))
        content.add_widget(Label(text="新建 OC", font_name='Chinese',
                                 font_size=sp(16), bold=True, color=C_TEXT,
                                 size_hint_y=None, height=dp(32)))
        content.add_widget(Label(text="名字：", font_name='Chinese',
                                 font_size=sp(13), color=C_TEXT_SUB,
                                 size_hint_y=None, height=dp(24),
                                 halign='left'))
        name_input = RoundedInput(multiline=False,
                                   size_hint_y=None, height=dp(46))
        content.add_widget(name_input)
        content.add_widget(Label(text="分类（可留空）：", font_name='Chinese',
                                 font_size=sp(13), color=C_TEXT_SUB,
                                 size_hint_y=None, height=dp(24),
                                 halign='left'))
        default_cat = "" if self.current_cat in ("全部", "未分类") else self.current_cat
        cat_input = RoundedInput(multiline=False,
                                  size_hint_y=None, height=dp(46),
                                  text=default_cat)
        content.add_widget(cat_input)
        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        ok_btn = btn_primary("确定", font_size=sp(14))
        cancel_btn = btn_light("取消", font_size=sp(14))
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)

        popup = make_popup("新建 OC", content, size_hint=(0.9, 0.65))

        def on_ok(inst):
            name = name_input.text.strip()
            if not name:
                return
            category = cat_input.text.strip()
            new_oc = {
                "name": name, "category": category,
                "other_names": "", "age": "", "gender": "",
                "appearance": "", "world": "",
                "image_groups": [], "custom_fields": [],
                "section_order": [], "children_map": {}, "relations": []
            }
            self.all_data.append(new_oc)
            if self.save_data():
                popup.dismiss()
                self.refresh_oc_list()
                self.refresh_category_list()

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def on_delete_oc(self, idx):
        name = self.all_data[idx].get("name", "未命名")
        content = CardBox(orientation='vertical',
                          padding=dp(12), spacing=dp(10))
        content.add_widget(Label(text=f"确定删除「{name}」吗？",
                                 font_name='Chinese', font_size=sp(15),
                                 bold=True, color=C_TEXT,
                                 size_hint_y=None, height=dp(50)))
        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        ok_btn = btn_danger("删除", font_size=sp(14))
        cancel_btn = btn_light("取消", font_size=sp(14))
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)
        popup = make_popup("删除 OC", content, size_hint=(0.85, 0.45))

        def on_ok(inst):
            self.all_data.pop(idx)
            if self.save_data():
                popup.dismiss()
                self.refresh_oc_list()
                self.refresh_category_list()

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    # ---------- 主菜单 ----------
    def open_main_menu(self, instance):
        content = CardBox(orientation='vertical',
                          padding=dp(12), spacing=dp(10))
        content.add_widget(Label(text="菜单", font_name='Chinese',
                                 font_size=sp(15), bold=True, color=C_TEXT,
                                 size_hint_y=None, height=dp(32)))

        backup_btn = btn_primary("备份数据", font_size=sp(14),
                                  size_hint_y=None, height=dp(48))
        content.add_widget(backup_btn)

        set_path_btn = btn_ghost("设置备份路径", font_size=sp(13),
                                  size_hint_y=None, height=dp(44))
        content.add_widget(set_path_btn)

        import_btn = btn_success("导入数据", font_size=sp(14),
                                  size_hint_y=None, height=dp(48))
        content.add_widget(import_btn)

        close_btn = btn_light("关闭", font_size=sp(13),
                               size_hint_y=None, height=dp(42))
        content.add_widget(close_btn)

        popup = make_popup("菜单", content, size_hint=(0.85, 0.65))

        close_btn.bind(on_press=popup.dismiss)
        backup_btn.bind(on_press=lambda x: (popup.dismiss(),
                                             self.backup_data(None)))
        set_path_btn.bind(on_press=lambda x: (popup.dismiss(),
                                               self.set_backup_path(None)))
        import_btn.bind(on_press=lambda x: (popup.dismiss(),
                                             self.import_data(None)))
        popup.open()

    # ---------- 设置备份路径 ----------
    def set_backup_path(self, instance):
        content = CardBox(orientation='vertical',
                          padding=dp(12), spacing=dp(10))
        content.add_widget(Label(text="备份存储路径",
                                 font_name='Chinese', font_size=sp(15),
                                 bold=True, color=C_TEXT,
                                 size_hint_y=None, height=dp(28)))
        content.add_widget(Label(
            text="留空则用默认路径。\n推荐：/storage/emulated/0/OCManager_Backup",
            font_name='Chinese', font_size=sp(10),
            color=C_TEXT_LIGHT,
            size_hint_y=None, height=dp(44)))
        path_input = RoundedInput(multiline=False,
                                   size_hint_y=None, height=dp(46),
                                   text=BACKUP_ROOT)
        content.add_widget(path_input)

        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        ok_btn = btn_primary("确定", font_size=sp(14))
        cancel_btn = btn_light("取消", font_size=sp(14))
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)

        popup = make_popup("设置备份路径", content, size_hint=(0.9, 0.55))

        def on_ok(inst):
            global BACKUP_ROOT
            new_path = path_input.text.strip()
            if not new_path:
                new_path = BACKUP_ROOT_DEFAULT
            try:
                os.makedirs(new_path, exist_ok=True)
            except Exception as e:
                self.show_toast(f"路径无效：{e}")
                return
            BACKUP_ROOT = new_path
            APP_CFG["backup_root"] = new_path
            save_app_config(APP_CFG)
            popup.dismiss()
            self.show_toast(f"已设置：\n{new_path}")

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    # ---------- 备份数据 ----------
    def backup_data(self, instance):
        try:
            os.makedirs(BACKUP_ROOT, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(BACKUP_ROOT, f"OC备份_{ts}")
            os.makedirs(backup_dir, exist_ok=True)

            if os.path.exists(DATA_FILE):
                shutil.copy2(DATA_FILE,
                             os.path.join(backup_dir, "oc_data.json"))
            if os.path.exists(CATEGORIES_FILE):
                shutil.copy2(CATEGORIES_FILE,
                             os.path.join(backup_dir, "categories.json"))

            self.show_toast(f"已备份到：\n{backup_dir}")
        except Exception as e:
            self.show_toast(f"备份失败：{e}")

    # ---------- 导入数据（扫描常见目录） ----------
    def import_data(self, instance):
        found = []
        search_dirs = list(SEARCH_DIRS)
        # 加上备份目录
        if os.path.exists(BACKUP_ROOT):
            search_dirs.append(BACKUP_ROOT)

        for base in search_dirs:
            if not os.path.exists(base):
                continue
            try:
                for root, dirs, files in os.walk(base):
                    # 限制搜索深度，避免太慢
                    depth = root[len(base):].count(os.sep)
                    if depth > 3:
                        dirs[:] = []
                        continue
                    for f in files:
                        if f == "oc_data.json":
                            full = os.path.join(root, f)
                            if full not in found:
                                found.append(full)
            except Exception:
                continue

        if not found:
            self.show_toast("未找到 oc_data.json\n请放到手机的 下载 或 Documents 文件夹")
            return

        content = CardBox(orientation='vertical',
                          padding=dp(12), spacing=dp(8))
        content.add_widget(Label(text="选择要导入的文件",
                                 font_name='Chinese', font_size=sp(15),
                                 bold=True, color=C_TEXT,
                                 size_hint_y=None, height=dp(32)))
        scroll = ScrollView(do_scroll_x=False)
        list_box = BoxLayout(orientation='vertical',
                             size_hint_y=None, spacing=dp(4))
        list_box.bind(minimum_height=list_box.setter('height'))
        scroll.add_widget(list_box)
        content.add_widget(scroll)

        popup = make_popup("导入数据", content, size_hint=(0.95, 0.75))

        def make_pick(path):
            def pick(inst):
                popup.dismiss()
                self.confirm_import(path)
            return pick

        for path in found:
            # 显示相对路径的尾部，太长不好看
            display = path
            if len(display) > 50:
                display = "..." + display[-50:]
            btn = btn_light(display, font_size=sp(11),
                            size_hint_y=None, height=dp(52))
            btn.bind(on_press=make_pick(path))
            list_box.add_widget(btn)

        cancel_btn = btn_light("取消", font_size=sp(13),
                                size_hint_y=None, height=dp(42))
        cancel_btn.bind(on_press=popup.dismiss)
        content.add_widget(cancel_btn)
        popup.open()

    def confirm_import(self, src_path):
        content = CardBox(orientation='vertical',
                          padding=dp(12), spacing=dp(10))
        content.add_widget(Label(
            text=f"导入：\n{os.path.basename(src_path)}？",
            font_name='Chinese', font_size=sp(14),
            bold=True, color=C_TEXT,
            size_hint_y=None, height=dp(60)))
        content.add_widget(Label(
            text="当前数据会被覆盖，且无法撤销",
            font_name='Chinese', font_size=sp(11),
            color=C_DANGER,
            size_hint_y=None, height=dp(28)))

        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        ok_btn = btn_danger("导入", font_size=sp(14))
        cancel_btn = btn_light("取消", font_size=sp(14))
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)

        popup = make_popup("导入数据", content, size_hint=(0.9, 0.45))

        def on_ok(inst):
            popup.dismiss()
            self.do_import(src_path)

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def do_import(self, src_path):
        try:
            with open(src_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                self.show_toast("文件格式不对")
                return

            shutil.copy2(src_path, DATA_FILE)

            cat_src = os.path.join(os.path.dirname(src_path),
                                    "categories.json")
            if os.path.exists(cat_src):
                shutil.copy2(cat_src, CATEGORIES_FILE)

            self.load_data()
            self.load_categories()
            self.current_cat = "全部"
            self.oc_title.text = "全部"
            self.refresh_category_list()
            self.refresh_oc_list()

            self.show_toast("导入成功")
        except json.JSONDecodeError:
            self.show_toast("不是合法 JSON")
        except Exception as e:
            self.show_toast(f"导入失败：{e}")

    def show_toast(self, text):
        content = BoxLayout()
        content.add_widget(Label(text=text, font_name='Chinese',
                                 font_size=sp(13), color=C_TEXT))
        popup = Popup(title="", title_size=0, separator_height=0,
                      content=content,
                      size_hint=(None, None), size=(dp(280), dp(120)),
                      auto_dismiss=True, background_color=C_CARD,
                      pos_hint={'center_x': 0.5, 'center_y': 0.6})
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2.0)


# ========== 详情页 ==========
class DetailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_oc = None
        self.field_inputs = []
        self.section_widgets = {}
        self.scroll_view = None
        self.info_box = None
        self.sidebar = None
        self.sidebar_open = False
        self._sidebar_w = dp(240)
        self._edge_start = None

    def make_input_row(self, label_text, value, multiline=False):
        card = CardBox(orientation='vertical',
                       size_hint_y=None, spacing=dp(4),
                       padding=(dp(10), dp(8)))
        card.height = dp(170) if multiline else dp(105)

        lbl = Label(text=label_text, font_name='Chinese',
                    font_size=sp(13), bold=True, color=C_TEXT,
                    size_hint_y=None, height=dp(22),
                    halign='left', valign='middle')
        lbl.bind(size=lbl.setter('text_size'))
        card.add_widget(lbl)

        ti = RoundedInput(text=str(value) if value else "",
                          font_size=sp(14), multiline=multiline,
                          size_hint_y=None,
                          height=dp(120) if multiline else dp(52))
        card.add_widget(ti)
        return card, ti

    def show_oc(self, oc):
        self.current_oc = oc
        self.field_inputs = []
        self.section_widgets = {}
        self.sidebar_open = False
        self.clear_widgets()

        root = FloatLayout()

        main = BoxLayout(orientation='vertical',
                         padding=dp(8), spacing=dp(8),
                         size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})

        top_card = CardBox(size_hint_y=None, height=dp(52),
                           padding=(dp(8), dp(6)))
        top = BoxLayout(spacing=dp(6))

        menu_btn = RoundedButton(text="☰", bg_color=C_SIDEBAR,
                                  text_color=C_TEXT, font_size=sp(18),
                                  size_hint_x=None, width=dp(44))
        menu_btn.bind(on_press=lambda x: self.toggle_sidebar())
        top.add_widget(menu_btn)

        back_btn = RoundedButton(text="←", bg_color=C_SIDEBAR,
                                  text_color=C_TEXT, font_size=sp(16),
                                  size_hint_x=None, width=dp(44))
        back_btn.bind(on_press=self.go_back)
        top.add_widget(back_btn)

        self.name_label = Label(text=oc.get("name", "未命名"),
                                font_name='Chinese', font_size=sp(15),
                                bold=True, color=C_TEXT)
        top.add_widget(self.name_label)

        save_btn = btn_primary("保存", font_size=sp(13),
                                size_hint_x=None, width=dp(64))
        save_btn.bind(on_press=self.save_all)
        top.add_widget(save_btn)
        top_card.add_widget(top)
        main.add_widget(top_card)

        scroll = ScrollView(do_scroll_x=False,
                            bar_width=dp(3),
                            scroll_type=['bars', 'content'])
        self.scroll_view = scroll
        info_box = BoxLayout(orientation='vertical', size_hint_y=None,
                             spacing=dp(8), padding=(0, dp(4)))
        info_box.bind(minimum_height=info_box.setter('height'))
        self.info_box = info_box

        self._build_sections(info_box, oc)

        scroll.add_widget(info_box)
        main.add_widget(scroll)
        root.add_widget(main)

        self.sidebar = self._build_sidebar(oc)
        self.sidebar.x = -self._sidebar_w
        root.add_widget(self.sidebar)

        self.add_widget(root)

    def _build_sections(self, info_box, oc):
        fields = [
            ("名字", "name", False),
            ("分类", "category", False),
            ("其他名字", "other_names", False),
            ("年龄", "age", False),
            ("性别", "gender", False),
            ("样貌描述/锚点", "appearance", True),
            ("所属世界观", "world", True),
        ]
        for label_text, key, multiline in fields:
            card, ti = self.make_input_row(label_text, oc.get(key, ""),
                                            multiline)
            info_box.add_widget(card)
            self.field_inputs.append(("builtin", key, ti))
            self.section_widgets[label_text] = card

        children_map = oc.get("children_map", {})
        for idx, field in enumerate(oc.get("custom_fields", [])):
            if field.get("type") == "text":
                title = field.get("title", "")
                card, ti = self.make_input_row(title, field.get("value", ""),
                                               True)
                info_box.add_widget(card)
                self.field_inputs.append(("custom", idx, ti))
                self.section_widgets[title] = card

                for c in children_map.get(title, []):
                    ctitle = c.get("title", "")
                    if c.get("type") == "text":
                        sub_card = CardBox(orientation='vertical',
                                            size_hint_y=None,
                                            spacing=dp(3),
                                            padding=(dp(10), dp(6)))
                        sub_card.height = dp(90)
                        s_lbl = Label(text="▸ " + ctitle,
                                       font_name='Chinese', font_size=sp(12),
                                       bold=True, color=C_PRIMARY_DARK,
                                       size_hint_y=None, height=dp(20),
                                       halign='left')
                        s_lbl.bind(size=s_lbl.setter('text_size'))
                        sub_card.add_widget(s_lbl)
                        cval = c.get("value", "")
                        s_val = Label(text=str(cval) if cval else "（空）",
                                       font_name='Chinese', font_size=sp(12),
                                       color=C_TEXT_SUB,
                                       size_hint_y=None, height=dp(50),
                                       halign='left', valign='top')
                        s_val.bind(size=s_val.setter('text_size'))
                        sub_card.add_widget(s_val)
                        info_box.add_widget(sub_card)
                        self.section_widgets[ctitle] = sub_card

        for field in oc.get("custom_fields", []):
            if field.get("type") != "text":
                title = field.get("title", "")
                lbl_card = CardBox(size_hint_y=None, height=dp(56),
                                    padding=(dp(10), dp(8)))
                lbl_card.add_widget(Label(
                    text=f"【{title}】（图片条目）",
                    font_name='Chinese', font_size=sp(13),
                    color=C_TEXT, halign='left'))
                info_box.add_widget(lbl_card)
                self.section_widgets[title] = lbl_card

        ref_card = CardBox(orientation='vertical',
                            size_hint_y=None, spacing=dp(8),
                            padding=(dp(10), dp(10)))
        ref_card.bind(minimum_height=ref_card.setter('height'))
        ref_title = Label(text="参考图片", font_name='Chinese',
                          font_size=sp(15), bold=True, color=C_TEXT,
                          size_hint_y=None, height=dp(26),
                          halign='left')
        ref_title.bind(size=ref_title.setter('text_size'))
        ref_card.add_widget(ref_title)
        self.section_widgets["参考图片"] = ref_card

        groups = oc.get("image_groups", [])
        if not groups:
            ref_card.add_widget(Label(text="（暂无分组）",
                                       font_name='Chinese', font_size=sp(12),
                                       color=C_TEXT_LIGHT,
                                       size_hint_y=None, height=dp(28)))
        else:
            for grp in groups:
                gname = grp.get("name", "")
                ginfo = grp.get("info", "")
                gimages = grp.get("images", [])

                g_lbl = Label(text="◆ " + gname, font_name='Chinese',
                              font_size=sp(14), bold=True,
                              color=C_PRIMARY_DARK,
                              size_hint_y=None, height=dp(26),
                              halign='left')
                g_lbl.bind(size=g_lbl.setter('text_size'))
                ref_card.add_widget(g_lbl)
                self.section_widgets[gname] = ref_card

                if ginfo:
                    info_lbl = Label(text=ginfo, font_name='Chinese',
                                     font_size=sp(12), color=C_TEXT_SUB,
                                     size_hint_y=None,
                                     halign='left', valign='top')
                    info_lbl.bind(width=lambda i, w: setattr(i, 'text_size', (w, None)))
                    info_lbl.bind(texture_size=lambda i, ts: setattr(i, 'height', ts[1] + dp(6)))
                    ref_card.add_widget(info_lbl)

                if gimages:
                    grid = GridLayout(cols=2, spacing=dp(6),
                                      size_hint_y=None,
                                      padding=(0, dp(4)))
                    grid.bind(minimum_height=grid.setter('height'))
                    for path in gimages:
                        fixed = path.replace("\\", "/")
                        if not os.path.exists(fixed):
                            grid.add_widget(Label(
                                text=f"找不到：{os.path.basename(fixed)}",
                                font_name='Chinese', font_size=sp(11),
                                color=C_DANGER,
                                size_hint_y=None, height=dp(80)))
                            continue
                        try:
                            grid.add_widget(ClickableImage(
                                source=fixed, full_path=path,
                                size_hint_y=None, height=dp(160),
                                allow_stretch=True, keep_ratio=True))
                        except Exception:
                            grid.add_widget(Label(text="无法显示",
                                                   font_name='Chinese',
                                                   font_size=sp(11),
                                                   color=C_DANGER,
                                                   size_hint_y=None,
                                                   height=dp(80)))
                    ref_card.add_widget(grid)
        info_box.add_widget(ref_card)

        rel_card = CardBox(orientation='vertical',
                            size_hint_y=None, spacing=dp(8),
                            padding=(dp(10), dp(10)))
        rel_card.bind(minimum_height=rel_card.setter('height'))
        rel_title = Label(text="关系图", font_name='Chinese',
                          font_size=sp(15), bold=True, color=C_TEXT,
                          size_hint_y=None, height=dp(26),
                          halign='left')
        rel_title.bind(size=rel_title.setter('text_size'))
        rel_card.add_widget(rel_title)
        self.section_widgets["关系图"] = rel_card

        relations = oc.get("relations", [])
        if not relations:
            rel_card.add_widget(Label(text="（暂无关系）",
                                       font_name='Chinese', font_size=sp(12),
                                       color=C_TEXT_LIGHT,
                                       size_hint_y=None, height=dp(28)))
        else:
            for idx, rel in enumerate(relations):
                target = rel.get("target", "")
                relation = rel.get("relation", "")
                story = rel.get("story", "")

                item = CardBox(orientation='vertical',
                                bg=C_PRIMARY_LIGHT, radius=6,
                                size_hint_y=None, spacing=dp(3),
                                padding=(dp(10), dp(8)))
                item.bind(minimum_height=item.setter('height'))

                head_row = BoxLayout(size_hint_y=None, height=dp(34),
                                     spacing=dp(4))
                head_text = f"→ {target}"
                if relation:
                    head_text += f"（{relation}）"
                head_label = Label(text=head_text, font_name='Chinese',
                                   font_size=sp(13), bold=True,
                                   color=C_PRIMARY_DARK,
                                   halign='left', valign='middle')
                head_label.bind(size=head_label.setter('text_size'))
                head_row.add_widget(head_label)

                del_btn = btn_danger("删除", font_size=sp(11),
                                      size_hint_x=None, width=dp(56),
                                      size_hint_y=None, height=dp(30))
                del_btn.bind(on_press=lambda b, i=idx: self.delete_relation(i))
                head_row.add_widget(del_btn)
                item.add_widget(head_row)

                if story:
                    s_lbl = Label(text=story, font_name='Chinese',
                                  font_size=sp(12), color=C_TEXT,
                                  size_hint_y=None,
                                  halign='left', valign='top')
                    s_lbl.bind(width=lambda i, w: setattr(i, 'text_size', (w, None)))
                    s_lbl.bind(texture_size=lambda i, ts: setattr(i, 'height', ts[1] + dp(4)))
                    item.add_widget(s_lbl)

                rel_card.add_widget(item)

        add_rel_btn = btn_ghost("＋ 添加关系", font_size=sp(13),
                                 size_hint_y=None, height=dp(42))
        add_rel_btn.bind(on_press=self.add_relation)
        rel_card.add_widget(add_rel_btn)
        info_box.add_widget(rel_card)

    def _build_sidebar(self, oc):
        sb = BoxLayout(orientation='vertical',
                       size_hint=(None, 1),
                       width=self._sidebar_w,
                       pos_hint={'x': 0, 'y': 0},
                       padding=dp(8), spacing=dp(8))
        with sb.canvas.before:
            Color(*C_CARD)
            bg_rect = RoundedRectangle(radius=[0], pos=sb.pos, size=sb.size)
        def update_bg(*args):
            bg_rect.pos = sb.pos
            bg_rect.size = sb.size
        sb.bind(pos=update_bg, size=update_bg)

        sb.add_widget(Label(text="导航", font_name='Chinese',
                            font_size=sp(15), bold=True, color=C_TEXT,
                            size_hint_y=None, height=dp(32)))

        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True,
                            bar_width=dp(4),
                            scroll_type=['bars', 'content'],
                            bar_color=(0.5, 0.5, 0.5, 0.6))
        inner = BoxLayout(orientation='vertical', size_hint_y=None,
                          spacing=dp(4))
        inner.bind(minimum_height=inner.setter('height'))

        def make_item(text, target, is_sub=False):
            if is_sub:
                b = btn_light(text, font_size=sp(12),
                              size_hint_y=None, height=dp(40))
            else:
                b = RoundedButton(text=text, bg_color=C_SIDEBAR,
                                   text_color=C_TEXT,
                                   font_size=sp(13),
                                   size_hint_y=None, height=dp(46))
            b.halign = 'left'
            b.bind(size=b.setter('text_size'))
            b.bind(on_press=lambda inst, t=target: self._on_sidebar_click(t))
            return b

        builtin = ["名字", "分类", "其他名字", "年龄", "性别",
                   "样貌描述/锚点", "所属世界观"]
        for t in builtin:
            inner.add_widget(make_item(t, t))

        for field in oc.get("custom_fields", []):
            if field.get("type") == "text":
                title = field.get("title", "")
                inner.add_widget(make_item(title, title))

                for c in oc.get("children_map", {}).get(title, []):
                    if c.get("type") == "text":
                        ct = c.get("title", "")
                        inner.add_widget(make_item("▸ " + ct, ct, is_sub=True))

        inner.add_widget(make_item("参考图片", "参考图片"))
        for grp in oc.get("image_groups", []):
            gname = grp.get("name", "")
            if gname:
                inner.add_widget(make_item("◆ " + gname, gname, is_sub=True))

        inner.add_widget(make_item("关系图", "关系图"))

        scroll.add_widget(inner)
        sb.add_widget(scroll)

        action_box = BoxLayout(size_hint_y=None, height=dp(96),
                                orientation='vertical', spacing=dp(4))
        add_btn = btn_primary("＋ 添加条目", font_size=sp(13),
                              size_hint_y=None, height=dp(44))
        add_btn.bind(on_press=self._sidebar_add_entry)
        action_box.add_widget(add_btn)

        del_btn = btn_danger("－ 删除条目", font_size=sp(13),
                             size_hint_y=None, height=dp(44))
        del_btn.bind(on_press=self._sidebar_delete_entry)
        action_box.add_widget(del_btn)
        sb.add_widget(action_box)

        close_btn = btn_light("关闭", font_size=sp(13),
                               size_hint_y=None, height=dp(40))
        close_btn.bind(on_press=lambda x: self.close_sidebar())
        sb.add_widget(close_btn)

        return sb

    def _sidebar_add_entry(self, instance):
        self.close_sidebar()
        Clock.schedule_once(lambda dt: self.add_entry(None), 0.2)

    def _sidebar_delete_entry(self, instance):
        self.close_sidebar()
        Clock.schedule_once(lambda dt: self.delete_entry(None), 0.2)

    def _on_sidebar_click(self, title):
        widget = self.section_widgets.get(title)
        if widget is None:
            for k, w in self.section_widgets.items():
                if k.strip() == title.strip():
                    widget = w
                    break
        if widget and self.scroll_view:
            self.close_sidebar()
            Clock.schedule_once(
                lambda dt: self.scroll_view.scroll_to(widget,
                                                       padding=dp(10),
                                                       animate=True),
                0.25)
        else:
            self.show_toast(f"找不到：{title}")

    def toggle_sidebar(self):
        if self.sidebar_open:
            self.close_sidebar()
        else:
            self.open_sidebar()

    def open_sidebar(self):
        if not self.sidebar or self.sidebar_open:
            return
        self.sidebar_open = True
        Animation(x=0, duration=0.2).start(self.sidebar)

    def close_sidebar(self):
        if not self.sidebar or not self.sidebar_open:
            return
        self.sidebar_open = False
        Animation(x=-self._sidebar_w, duration=0.2).start(self.sidebar)

    def on_touch_down(self, touch):
        if self.sidebar_open and self.sidebar:
            if not self.sidebar.collide_point(*touch.pos):
                self.close_sidebar()
                return True
        if (not self.sidebar_open and
            touch.x < dp(20) and
            touch.y > dp(40) and
            touch.y < self.height - dp(40)):
            self._edge_start = (touch.x, touch.y)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._edge_start:
            sx, sy = self._edge_start
            dx = touch.x - sx
            dy = touch.y - sy
            if dx > dp(30) and abs(dx) > abs(dy):
                self.open_sidebar()
                self._edge_start = None
                return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        self._edge_start = None
        return super().on_touch_up(touch)

    def save_all(self, instance):
        if not self.current_oc:
            return
        for kind, key, ti in self.field_inputs:
            if kind == "builtin":
                self.current_oc[key] = ti.text
            elif kind == "custom":
                self.current_oc["custom_fields"][key]["value"] = ti.text
        if self.save_to_file():
            self.name_label.text = self.current_oc.get("name", "未命名")
            self.show_toast("已保存")

    def save_to_file(self):
        try:
            home = self.manager.get_screen('home')
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(home.all_data, f, ensure_ascii=False, indent=2)
            home.refresh_oc_list()
            home.refresh_category_list()
            return True
        except Exception as e:
            self.show_toast(f"保存失败：{e}")
            return False

    def add_entry(self, instance):
        content = CardBox(orientation='vertical',
                          padding=dp(12), spacing=dp(10))
        content.add_widget(Label(text="添加条目类型", font_name='Chinese',
                                 font_size=sp(15), bold=True, color=C_TEXT,
                                 size_hint_y=None, height=dp(32)))
        b1 = btn_primary("文字信息", font_size=sp(14),
                          size_hint_y=None, height=dp(48))
        b2 = btn_primary("图片信息", font_size=sp(14),
                          size_hint_y=None, height=dp(48))
        content.add_widget(b1)
        content.add_widget(b2)
        popup = make_popup("添加条目", content, size_hint=(0.85, 0.5))

        def choose_text(inst):
            popup.dismiss()
            self.ask_parent_and_add("text")

        def choose_image(inst):
            popup.dismiss()
            self.ask_parent_and_add("images")

        b1.bind(on_press=choose_text)
        b2.bind(on_press=choose_image)
        popup.open()

    def ask_parent_and_add(self, field_type):
        oc = self.current_oc
        parents = [f.get("title", "") for f in oc.get("custom_fields", [])
                   if f.get("type") == "text"]

        content = CardBox(orientation='vertical',
                          padding=dp(12), spacing=dp(8))
        content.add_widget(Label(text="加到哪个条目下？", font_name='Chinese',
                                 font_size=sp(14), bold=True, color=C_TEXT,
                                 size_hint_y=None, height=dp(28)))
        scroll = ScrollView(do_scroll_x=False)
        list_box = BoxLayout(orientation='vertical',
                             size_hint_y=None, spacing=dp(4))
        list_box.bind(minimum_height=list_box.setter('height'))
        scroll.add_widget(list_box)
        content.add_widget(scroll)
        popup = make_popup("选择父条目", content, size_hint=(0.9, 0.75))

        top_btn = btn_ghost("（作为顶层条目）", font_size=sp(13),
                             size_hint_y=None, height=dp(46))
        def pick_top(inst):
            popup.dismiss()
            self.do_add_field(None, field_type)
        top_btn.bind(on_press=pick_top)
        list_box.add_widget(top_btn)

        for p in parents:
            btn = btn_light(p, font_size=sp(13),
                            size_hint_y=None, height=dp(46))
            def make_pick(parent_name):
                def pick(inst):
                    popup.dismiss()
                    self.do_add_field(parent_name, field_type)
                return pick
            btn.bind(on_press=make_pick(p))
            list_box.add_widget(btn)

        cancel_btn = btn_light("取消", font_size=sp(13),
                                size_hint_y=None, height=dp(42))
        cancel_btn.bind(on_press=popup.dismiss)
        content.add_widget(cancel_btn)
        popup.open()

    def do_add_field(self, parent_name, field_type):
        content = CardBox(orientation='vertical',
                          padding=dp(12), spacing=dp(10))
        content.add_widget(Label(text="请输入条目名称",
                                 font_name='Chinese', font_size=sp(15),
                                 bold=True, color=C_TEXT,
                                 size_hint_y=None, height=dp(32)))
        ti = RoundedInput(multiline=False,
                           size_hint_y=None, height=dp(46))
        content.add_widget(ti)
        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        ok_btn = btn_primary("确定", font_size=sp(14))
        cancel_btn = btn_light("取消", font_size=sp(14))
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)
        popup = make_popup("添加条目", content, size_hint=(0.85, 0.45))

        def on_ok(inst):
            title = ti.text.strip()
            if not title:
                return
            if field_type == "text":
                new_field = {"title": title, "type": "text", "value": ""}
            else:
                new_field = {"title": title, "type": "images", "value": []}
            oc = self.current_oc
            if parent_name is None:
                oc.setdefault("custom_fields", []).append(new_field)
            else:
                oc.setdefault("children_map", {})
                if parent_name not in oc["children_map"]:
                    oc["children_map"][parent_name] = []
                oc["children_map"][parent_name].append(new_field)
            popup.dismiss()
            self.save_to_file()
            self.show_oc(oc)
            self.show_toast(f"已添加「{title}」")

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def delete_entry(self, instance):
        oc = self.current_oc
        options = []
        for i, f in enumerate(oc.get("custom_fields", [])):
            options.append((f.get("title", "未命名"), ("parent", i, None)))
        for parent_name, children in oc.get("children_map", {}).items():
            for j, c in enumerate(children):
                options.append((f"    {parent_name} ▸ {c.get('title', '')}",
                                ("child", parent_name, j)))
        if not options:
            self.show_toast("没有可删除的条目")
            return

        content = CardBox(orientation='vertical',
                          padding=dp(12), spacing=dp(6))
        content.add_widget(Label(text="选择要删除的条目",
                                 font_name='Chinese', font_size=sp(15),
                                 bold=True, color=C_TEXT,
                                 size_hint_y=None, height=dp(32)))
        scroll = ScrollView(do_scroll_x=False)
        list_box = BoxLayout(orientation='vertical',
                             size_hint_y=None, spacing=dp(4))
        list_box.bind(minimum_height=list_box.setter('height'))
        scroll.add_widget(list_box)
        content.add_widget(scroll)
        popup = make_popup("删除条目", content, size_hint=(0.9, 0.75))

        def make_del(meta, title):
            def do_del(inst):
                kind = meta[0]
                if kind == "parent":
                    oc["custom_fields"].pop(meta[1])
                elif kind == "child":
                    pname = meta[1]
                    idx = meta[2]
                    oc["children_map"][pname].pop(idx)
                    if not oc["children_map"][pname]:
                        del oc["children_map"][pname]
                popup.dismiss()
                self.save_to_file()
                self.show_oc(oc)
                self.show_toast(f"已删除「{title}」")
            return do_del

        for title, meta in options:
            btn = btn_danger(title, font_size=sp(13),
                             size_hint_y=None, height=dp(46))
            btn.bind(on_press=make_del(meta, title))
            list_box.add_widget(btn)

        cancel_btn = btn_light("取消", font_size=sp(13),
                                size_hint_y=None, height=dp(42))
        cancel_btn.bind(on_press=popup.dismiss)
        content.add_widget(cancel_btn)
        popup.open()

    def add_relation(self, instance):
        oc = self.current_oc
        home = self.manager.get_screen('home')
        candidates = [o.get("name", "") for o in home.all_data
                      if o.get("name") and o.get("name") != oc.get("name")]
        content = CardBox(orientation='vertical',
                          padding=dp(12), spacing=dp(8))
        content.add_widget(Label(text="目标角色：", font_name='Chinese',
                                 font_size=sp(13), bold=True, color=C_TEXT_SUB,
                                 size_hint_y=None, height=dp(24),
                                 halign='left'))
        cand_scroll = ScrollView(size_hint_y=None, height=dp(120),
                                  do_scroll_x=False)
        cand_box = BoxLayout(orientation='vertical',
                             size_hint_y=None, spacing=dp(4))
        cand_box.bind(minimum_height=cand_box.setter('height'))
        target_holder = {"value": ""}
        target_label = Label(text="（未选择）", font_name='Chinese',
                             font_size=sp(12), color=C_TEXT_SUB,
                             size_hint_y=None, height=dp(24),
                             halign='left')
        target_label.bind(size=target_label.setter('text_size'))

        def make_pick(name):
            def pick(inst):
                target_holder["value"] = name
                target_label.text = f"已选：{name}"
            return pick

        if not candidates:
            cand_box.add_widget(Label(text="（没有其他 OC）",
                                      font_name='Chinese', font_size=sp(11),
                                      color=C_TEXT_LIGHT,
                                      size_hint_y=None, height=dp(36)))
        else:
            for name in candidates:
                btn = btn_light(name, font_size=sp(13),
                                size_hint_y=None, height=dp(40))
                btn.bind(on_press=make_pick(name))
                cand_box.add_widget(btn)
        cand_scroll.add_widget(cand_box)
        content.add_widget(cand_scroll)
        content.add_widget(target_label)

        content.add_widget(Label(text="关系：", font_name='Chinese',
                                 font_size=sp(13), bold=True, color=C_TEXT_SUB,
                                 size_hint_y=None, height=dp(24),
                                 halign='left'))
        rel_input = RoundedInput(multiline=False,
                                  size_hint_y=None, height=dp(44))
        content.add_widget(rel_input)

        content.add_widget(Label(text="故事：", font_name='Chinese',
                                 font_size=sp(13), bold=True, color=C_TEXT_SUB,
                                 size_hint_y=None, height=dp(24),
                                 halign='left'))
        story_input = RoundedInput(multiline=True,
                                    size_hint_y=None, height=dp(80))
        content.add_widget(story_input)

        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        ok_btn = btn_primary("确定", font_size=sp(14))
        cancel_btn = btn_light("取消", font_size=sp(14))
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)
        popup = make_popup("添加关系", content, size_hint=(0.95, 0.9))

        def on_ok(inst):
            target = target_holder["value"].strip()
            relation = rel_input.text.strip()
            story = story_input.text.strip()
            if not target:
                self.show_toast("请选择目标角色")
                return
            if not relation:
                self.show_toast("请填写关系")
                return
            oc.setdefault("relations", []).append({
                "target": target, "relation": relation, "story": story})
            popup.dismiss()
            self.save_to_file()
            self.show_oc(oc)
            self.show_toast("已添加关系")

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def delete_relation(self, idx):
        oc = self.current_oc
        rels = oc.get("relations", [])
        if idx < 0 or idx >= len(rels):
            return
        target = rels[idx].get("target", "")
        content = CardBox(orientation='vertical',
                          padding=dp(12), spacing=dp(10))
        content.add_widget(Label(text=f"删除和「{target}」的关系？",
                                 font_name='Chinese', font_size=sp(14),
                                 bold=True, color=C_TEXT,
                                 size_hint_y=None, height=dp(50)))
        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        ok_btn = btn_danger("删除", font_size=sp(14))
        cancel_btn = btn_light("取消", font_size=sp(14))
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)
        popup = make_popup("删除关系", content, size_hint=(0.85, 0.45))

        def on_ok(inst):
            rels.pop(idx)
            popup.dismiss()
            self.save_to_file()
            self.show_oc(oc)
            self.show_toast("已删除关系")

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def show_toast(self, text):
        content = BoxLayout()
        content.add_widget(Label(text=text, font_name='Chinese',
                                 font_size=sp(13), color=C_TEXT))
        popup = Popup(title="", title_size=0, separator_height=0,
                      content=content,
                      size_hint=(None, None), size=(dp(280), dp(120)),
                      auto_dismiss=True, background_color=C_CARD,
                      pos_hint={'center_x': 0.5, 'center_y': 0.6})
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2.0)

    def go_back(self, instance):
        self.manager.current = 'home'


# ========== App ==========
class OCApp(App):
    def build(self):
        if platform == 'android':
            root = BoxLayout(orientation='vertical',
                             padding=(0, dp(30), 0, 0))
        else:
            root = BoxLayout(orientation='vertical')

        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(DetailScreen(name='detail'))
        root.add_widget(sm)
        return root


if __name__ == "__main__":
    OCApp().run()