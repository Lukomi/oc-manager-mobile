import os
import json
from kivy.app import App
from kivy.core.text import LabelBase
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image as KivyImage
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "oc_data.json")

FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts", "simhei.ttf")
try:
    LabelBase.register(name='Chinese', fn_regular=FONT_PATH)
except Exception as e:
    print("字体注册失败：", e)


# ========== 自动高度 Label ==========
class AutoLabel(Label):
    def __init__(self, **kwargs):
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('halign', 'left')
        kwargs.setdefault('valign', 'top')
        kwargs.setdefault('font_name', 'Chinese')
        super().__init__(**kwargs)
        self.bind(width=self._on_width)
        self.bind(texture_size=self._on_texture)

    def _on_width(self, *args):
        self.text_size = (self.width, None)

    def _on_texture(self, *args):
        try:
            h = float(self.texture_size[1]) + 20
        except Exception:
            h = 40
        self.height = h


# ========== 可点击的图片 ==========
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

        content = BoxLayout(orientation='vertical')
        big_img = KivyImage(source=fixed, allow_stretch=True, keep_ratio=True)
        content.add_widget(big_img)

        close_btn = Button(text="关闭", font_name='Chinese',
                           size_hint_y=None, height=60)
        content.add_widget(close_btn)

        popup = Popup(
            title=os.path.basename(fixed),
            title_font='Chinese',
            content=content,
            size_hint=(0.95, 0.95),
            auto_dismiss=True
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()


# ========== 长按按钮 ==========
class LongPressButton(Button):
    def __init__(self, on_long_press=None, **kwargs):
        super().__init__(**kwargs)
        self._lp_event = None
        self._lp_callback = on_long_press

    def on_press(self):
        super().on_press()
        if self._lp_callback:
            self._lp_event = Clock.schedule_once(
                lambda dt: self._lp_callback(self), 0.6
            )

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
        self.current_cat = "全部"
        self.load_data()
        self.build_ui()
        self.refresh_oc_list()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.all_data = json.load(f)
        else:
            self.all_data = []

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.all_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print("保存失败：", e)
            return False

    def get_categories(self):
        cats = ["全部", "未分类"]
        for oc in self.all_data:
            c = oc.get("category", "")
            if c and c not in cats:
                cats.append(c)
        return cats

    def build_ui(self):
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # 顶部：标题 + 新建按钮
        top = BoxLayout(size_hint_y=None, height=60, spacing=10)
        title = Label(
            text="OC 管理器",
            font_name='Chinese',
            font_size=22
        )
        top.add_widget(title)
        new_btn = Button(
            text="＋ 新建 OC",
            font_name='Chinese',
            font_size=14,
            size_hint_x=None,
            width=140
        )
        new_btn.bind(on_press=self.on_new_oc)
        top.add_widget(new_btn)
        root.add_widget(top)

        # 主体
        body = BoxLayout(orientation='horizontal', spacing=10)

        # 左侧分类
        left = BoxLayout(orientation='vertical', size_hint_x=0.32, spacing=5)
        left_title = Label(text="分类", font_name='Chinese',
                           font_size=16, size_hint_y=None, height=36)
        left.add_widget(left_title)

        self.cat_scroll = ScrollView()
        self.cat_list = BoxLayout(orientation='vertical',
                                  size_hint_y=None, spacing=5)
        self.cat_list.bind(minimum_height=self.cat_list.setter('height'))
        self.cat_scroll.add_widget(self.cat_list)
        left.add_widget(self.cat_scroll)

        # 右侧 OC 列表
        right = BoxLayout(orientation='vertical', spacing=5)
        self.oc_title = Label(text="全部", font_name='Chinese',
                              font_size=16, size_hint_y=None, height=36)
        right.add_widget(self.oc_title)

        # 提示文字
        hint = Label(
            text="点名字进详情，长按删除",
            font_name='Chinese',
            font_size=11,
            size_hint_y=None,
            height=22
        )
        right.add_widget(hint)

        oc_scroll = ScrollView()
        self.oc_list = BoxLayout(orientation='vertical',
                                 size_hint_y=None, spacing=5)
        self.oc_list.bind(minimum_height=self.oc_list.setter('height'))
        oc_scroll.add_widget(self.oc_list)
        right.add_widget(oc_scroll)

        body.add_widget(left)
        body.add_widget(right)
        root.add_widget(body)
        self.add_widget(root)

        self.refresh_category_list()

    def refresh_category_list(self):
        self.cat_list.clear_widgets()
        for cat in self.get_categories():
            btn = Button(text=cat, font_name='Chinese',
                         size_hint_y=None, height=50)
            btn.bind(on_press=lambda b, c=cat: self.on_category_click(c))
            self.cat_list.add_widget(btn)

    def on_category_click(self, cat):
        self.current_cat = cat
        self.oc_title.text = cat
        self.refresh_oc_list()

    def refresh_oc_list(self):
        self.oc_list.clear_widgets()
        for i, oc in enumerate(self.all_data):
            c = oc.get("category", "")
            if self.current_cat == "全部":
                m = True
            elif self.current_cat == "未分类":
                m = (c == "")
            else:
                m = (c == self.current_cat)
            if m:
                btn = LongPressButton(
                    text=oc.get("name", "未命名"),
                    font_name='Chinese',
                    size_hint_y=None,
                    height=60,
                    on_long_press=lambda inst, idx=i: self.on_delete_oc(idx)
                )
                btn.bind(on_press=lambda b, idx=i: self.on_oc_click(idx))
                self.oc_list.add_widget(btn)

    def on_oc_click(self, idx):
        # 短按：进详情
        # 但是长按也会触发 on_press，所以这里加一个延迟判断
        # 简单做法：如果长按的定时器还在，就不进详情
        # 为了简化，直接进详情，长按弹窗会盖在上面
        detail = self.manager.get_screen('detail')
        detail.show_oc(self.all_data[idx])
        self.manager.current = 'detail'

    # ---------- 新建 OC ----------
    def on_new_oc(self, instance):
        content = BoxLayout(orientation='vertical', padding=15, spacing=12)
        content.add_widget(Label(
            text="新建 OC",
            font_name='Chinese', font_size=16,
            size_hint_y=None, height=36
        ))
        content.add_widget(Label(
            text="名字：",
            font_name='Chinese', font_size=13,
            size_hint_y=None, height=24,
            halign='left'
        ))

        name_input = TextInput(
            font_name='Chinese', font_size=14,
            multiline=False, size_hint_y=None, height=50
        )
        content.add_widget(name_input)

        content.add_widget(Label(
            text="分类（可留空）：",
            font_name='Chinese', font_size=13,
            size_hint_y=None, height=24,
            halign='left'
        ))

        # 分类下拉用按钮选择
        cat_input = TextInput(
            font_name='Chinese', font_size=14,
            multiline=False, size_hint_y=None, height=50
        )
        cat_input.text = ""
        content.add_widget(cat_input)

        btn_row = BoxLayout(size_hint_y=None, height=50, spacing=10)
        ok_btn = Button(text="确定", font_name='Chinese')
        cancel_btn = Button(text="取消", font_name='Chinese')
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)

        popup = Popup(title="新建 OC", title_font='Chinese',
                      content=content, size_hint=(0.85, 0.75))

        def on_ok(inst):
            name = name_input.text.strip()
            if not name:
                return
            category = cat_input.text.strip()
            new_oc = {
                "name": name,
                "category": category,
                "other_names": "",
                "age": "",
                "gender": "",
                "appearance": "",
                "world": "",
                "image_groups": [],
                "custom_fields": [],
                "section_order": [],
                "children_map": {},
                "relations": []
            }
            self.all_data.append(new_oc)
            if self.save_data():
                popup.dismiss()
                self.refresh_oc_list()
                self.refresh_category_list()

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    # ---------- 删除 OC ----------
    def on_delete_oc(self, idx):
        name = self.all_data[idx].get("name", "未命名")

        content = BoxLayout(orientation='vertical', padding=15, spacing=15)
        content.add_widget(Label(
            text=f"确定删除「{name}」吗？",
            font_name='Chinese', font_size=16,
            size_hint_y=None, height=60
        ))
        content.add_widget(Label(
            text="此操作不可撤销",
            font_name='Chinese', font_size=12,
            size_hint_y=None, height=30
        ))

        btn_row = BoxLayout(size_hint_y=None, height=50, spacing=10)
        ok_btn = Button(text="删除", font_name='Chinese')
        cancel_btn = Button(text="取消", font_name='Chinese')
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)

        popup = Popup(title="删除 OC", title_font='Chinese',
                      content=content, size_hint=(0.8, 0.55))

        def on_ok(inst):
            self.all_data.pop(idx)
            if self.save_data():
                popup.dismiss()
                self.refresh_oc_list()
                self.refresh_category_list()

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()


# ========== 详情页 ==========
class DetailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_oc = None
        self.field_inputs = []
        self.name_label = None

    def make_input_row(self, label_text, value, multiline=False):
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=3)
        box.height = 150 if multiline else 90

        lbl = Label(
            text=f"【{label_text}】",
            font_name='Chinese',
            font_size=14,
            size_hint_y=None,
            height=28,
            halign='left',
            valign='middle'
        )
        lbl.bind(size=lbl.setter('text_size'))
        box.add_widget(lbl)

        ti = TextInput(
            text=str(value) if value else "",
            font_name='Chinese',
            font_size=14,
            multiline=multiline,
            size_hint_y=None,
            height=110 if multiline else 55
        )
        box.add_widget(ti)
        return box, ti

    def show_oc(self, oc):
        self.current_oc = oc
        self.field_inputs = []
        self.clear_widgets()

        root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        top = BoxLayout(size_hint_y=None, height=50, spacing=10)
        back_btn = Button(text="← 返回", font_name='Chinese', size_hint_x=0.25)
        back_btn.bind(on_press=self.go_back)
        top.add_widget(back_btn)

        self.name_label = Label(
            text=oc.get("name", "未命名"),
            font_name='Chinese',
            font_size=20
        )
        top.add_widget(self.name_label)

        save_btn = Button(text="保存", font_name='Chinese', size_hint_x=0.25)
        save_btn.bind(on_press=self.save_all)
        top.add_widget(save_btn)
        root.add_widget(top)

        scroll = ScrollView()
        info_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=12,
            padding=(10, 10)
        )
        info_box.bind(minimum_height=info_box.setter('height'))

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
            row, ti = self.make_input_row(label_text, oc.get(key, ""), multiline)
            info_box.add_widget(row)
            self.field_inputs.append(("builtin", key, ti))

        for idx, field in enumerate(oc.get("custom_fields", [])):
            if field.get("type") == "text":
                title = field.get("title", "")
                value = field.get("value", "")
                row, ti = self.make_input_row(title, value, True)
                info_box.add_widget(row)
                self.field_inputs.append(("custom", idx, ti))

        for idx, field in enumerate(oc.get("custom_fields", [])):
            if field.get("type") != "text":
                title = field.get("title", "")
                info_box.add_widget(AutoLabel(
                    text=f"【{title}】（图片条目，手机版暂不支持编辑）",
                    font_size=14
                ))

        # ===== 参考图片 =====
        info_box.add_widget(AutoLabel(text="【参考图片】", font_size=18))

        groups = oc.get("image_groups", [])
        if not groups:
            # 没有分组时显示占位
            info_box.add_widget(AutoLabel(
                text="（暂无参考图片分组，可在电脑版添加）",
                font_size=13
            ))
        else:
            for grp in groups:
                gname = grp.get("name", "未命名分组")
                ginfo = grp.get("info", "")
                gimages = grp.get("images", [])

                info_box.add_widget(AutoLabel(text=f"◆ {gname}", font_size=16))
                if ginfo:
                    info_box.add_widget(AutoLabel(text=ginfo, font_size=13))

                if gimages:
                    grid = GridLayout(cols=2, spacing=10,
                                      size_hint_y=None, padding=(5, 5))
                    grid.bind(minimum_height=grid.setter('height'))

                    for path in gimages:
                        fixed = path.replace("\\", "/")
                        if not os.path.exists(fixed):
                            grid.add_widget(Label(
                                text=f"找不到：{os.path.basename(fixed)}",
                                font_name='Chinese', font_size=12,
                                size_hint_y=None, height=100
                            ))
                            continue
                        try:
                            img = ClickableImage(
                                source=fixed,
                                full_path=path,
                                size_hint_y=None,
                                height=200,
                                allow_stretch=True,
                                keep_ratio=True
                            )
                            grid.add_widget(img)
                        except Exception:
                            grid.add_widget(Label(
                                text=f"无法显示：{os.path.basename(fixed)}",
                                font_name='Chinese', font_size=12,
                                size_hint_y=None, height=100
                            ))
                    info_box.add_widget(grid)

        # ===== 关系图 =====
        relations = oc.get("relations", [])
        info_box.add_widget(AutoLabel(text="【关系图】", font_size=18))

        if not relations:
            info_box.add_widget(AutoLabel(
                text="（暂无关系，点下方按钮添加）",
                font_size=13
            ))
        else:
            for idx, rel in enumerate(relations):
                target = rel.get("target", "")
                relation = rel.get("relation", "")
                story = rel.get("story", "")

                card = BoxLayout(
                    orientation='vertical',
                    size_hint_y=None,
                    spacing=4,
                    padding=(10, 8)
                )
                card.bind(minimum_height=card.setter('height'))

                # 第一行：目标 + 关系 + 删除按钮
                head_row = BoxLayout(size_hint_y=None, height=40, spacing=5)

                head_text = f"→ {target}"
                if relation:
                    head_text += f"（{relation}）"
                head_label = Label(
                    text=head_text, font_name='Chinese',
                    font_size=15, halign='left', valign='middle'
                )
                head_label.bind(size=head_label.setter('text_size'))
                head_row.add_widget(head_label)

                del_btn = Button(
                    text="删除", font_name='Chinese',
                    font_size=12,
                    size_hint_x=None, width=80
                )
                del_btn.bind(on_press=lambda b, i=idx: self.delete_relation(i))
                head_row.add_widget(del_btn)
                card.add_widget(head_row)

                # 故事
                if story:
                    card.add_widget(AutoLabel(text=story, font_size=13))

                info_box.add_widget(card)

        # 添加关系按钮
        add_rel_btn = Button(
            text="＋ 添加关系",
            font_name='Chinese',
            size_hint_y=None,
            height=50
        )
        add_rel_btn.bind(on_press=self.add_relation)
        info_box.add_widget(add_rel_btn)
                    
        btn_row = BoxLayout(size_hint_y=None, height=55, spacing=10)
        add_btn = Button(text="＋ 添加条目", font_name='Chinese')
        add_btn.bind(on_press=self.add_entry)
        del_btn = Button(text="－ 删除条目", font_name='Chinese')
        del_btn.bind(on_press=self.delete_entry)
        btn_row.add_widget(add_btn)
        btn_row.add_widget(del_btn)
        info_box.add_widget(btn_row)

        scroll.add_widget(info_box)
        root.add_widget(scroll)
        self.add_widget(root)

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
        content = BoxLayout(orientation='vertical', padding=15, spacing=15)
        content.add_widget(Label(
            text="选择要添加的条目类型",
            font_name='Chinese', font_size=16,
            size_hint_y=None, height=40
        ))
        text_btn = Button(text="文字信息", font_name='Chinese',
                          size_hint_y=None, height=60)
        image_btn = Button(text="图片信息", font_name='Chinese',
                           size_hint_y=None, height=60)
        content.add_widget(text_btn)
        content.add_widget(image_btn)

        popup = Popup(title="添加条目", title_font='Chinese',
                      content=content, size_hint=(0.8, 0.55))

        def choose_text(inst):
            popup.dismiss()
            self.ask_title_and_add("text")

        def choose_image(inst):
            popup.dismiss()
            self.ask_title_and_add("images")

        text_btn.bind(on_press=choose_text)
        image_btn.bind(on_press=choose_image)
        popup.open()

    def ask_title_and_add(self, field_type):
        content = BoxLayout(orientation='vertical', padding=15, spacing=15)
        content.add_widget(Label(
            text="请输入条目名称",
            font_name='Chinese', font_size=16,
            size_hint_y=None, height=40
        ))
        ti = TextInput(font_name='Chinese', font_size=14,
                       multiline=False, size_hint_y=None, height=50)
        content.add_widget(ti)

        btn_row = BoxLayout(size_hint_y=None, height=50, spacing=10)
        ok_btn = Button(text="确定", font_name='Chinese')
        cancel_btn = Button(text="取消", font_name='Chinese')
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)

        popup = Popup(title="添加条目", title_font='Chinese',
                      content=content, size_hint=(0.8, 0.5))

        def on_ok(inst):
            title = ti.text.strip()
            if not title:
                return
            for f in self.current_oc.get("custom_fields", []):
                if f.get("title") == title:
                    self.show_toast("这个名字已经存在")
                    return
            if field_type == "text":
                new_field = {"title": title, "type": "text", "value": ""}
            else:
                new_field = {"title": title, "type": "images", "value": []}
            self.current_oc.setdefault("custom_fields", []).append(new_field)
            popup.dismiss()
            self.save_to_file()
            self.show_oc(self.current_oc)
            self.show_toast(f"已添加「{title}」")

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def delete_entry(self, instance):
        fields = self.current_oc.get("custom_fields", [])
        if not fields:
            self.show_toast("没有可删除的条目")
            return

        content = BoxLayout(orientation='vertical', padding=10, spacing=5)
        content.add_widget(Label(
            text="选择要删除的条目",
            font_name='Chinese', font_size=16,
            size_hint_y=None, height=40
        ))

        scroll = ScrollView()
        list_box = BoxLayout(orientation='vertical',
                             size_hint_y=None, spacing=5)
        list_box.bind(minimum_height=list_box.setter('height'))
        scroll.add_widget(list_box)
        content.add_widget(scroll)

        popup = Popup(title="删除条目", title_font='Chinese',
                      content=content, size_hint=(0.85, 0.75))

        def make_del(idx, title):
            def do_del(inst):
                self.current_oc["custom_fields"].pop(idx)
                popup.dismiss()
                self.save_to_file()
                self.show_oc(self.current_oc)
                self.show_toast(f"已删除「{title}」")
            return do_del

        for i, f in enumerate(fields):
            title = f.get("title", "未命名")
            btn = Button(text=title, font_name='Chinese',
                         size_hint_y=None, height=55)
            btn.bind(on_press=make_del(i, title))
            list_box.add_widget(btn)

        cancel_btn = Button(text="取消", font_name='Chinese',
                            size_hint_y=None, height=50)
        cancel_btn.bind(on_press=popup.dismiss)
        content.add_widget(cancel_btn)
        popup.open()

    def show_toast(self, text):
        popup = Popup(
            title="",
            title_size=0,
            separator_height=0,
            content=Label(text=text, font_name='Chinese', font_size=16),
            size_hint=(None, None),
            size=(220, 100),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.2)

    # ---------- 添加关系 ----------
    def add_relation(self, instance):
        oc = self.current_oc
        # 从所有 OC 里拿候选名字（排除自己）
        home = self.manager.get_screen('home')
        candidates = [
            o.get("name", "") for o in home.all_data
            if o.get("name") and o.get("name") != oc.get("name")
        ]

        content = BoxLayout(orientation='vertical', padding=15, spacing=12)

        # 目标角色
        content.add_widget(Label(
            text="目标角色：", font_name='Chinese', font_size=14,
            size_hint_y=None, height=28, halign='left'
        ))

        # 候选按钮列表（可滚动）
        cand_scroll = ScrollView(size_hint_y=None, height=140)
        cand_box = BoxLayout(orientation='vertical',
                             size_hint_y=None, spacing=4)
        cand_box.bind(minimum_height=cand_box.setter('height'))

        target_holder = {"value": ""}
        target_label = Label(
            text="（未选择）", font_name='Chinese', font_size=13,
            size_hint_y=None, height=28, halign='left'
        )
        target_label.bind(size=target_label.setter('text_size'))

        def make_pick(name):
            def pick(inst):
                target_holder["value"] = name
                target_label.text = f"已选：{name}"
            return pick

        if not candidates:
            cand_box.add_widget(Label(
                text="（没有其他 OC 可供选择）",
                font_name='Chinese', font_size=12,
                size_hint_y=None, height=40
            ))
        else:
            for name in candidates:
                btn = Button(text=name, font_name='Chinese',
                             size_hint_y=None, height=44)
                btn.bind(on_press=make_pick(name))
                cand_box.add_widget(btn)

        cand_scroll.add_widget(cand_box)
        content.add_widget(cand_scroll)
        content.add_widget(target_label)

        # 关系
        content.add_widget(Label(
            text="关系：", font_name='Chinese', font_size=14,
            size_hint_y=None, height=28, halign='left'
        ))
        rel_input = TextInput(
            font_name='Chinese', font_size=14,
            multiline=False, size_hint_y=None, height=46
        )
        content.add_widget(rel_input)

        # 故事
        content.add_widget(Label(
            text="故事：", font_name='Chinese', font_size=14,
            size_hint_y=None, height=28, halign='left'
        ))
        story_input = TextInput(
            font_name='Chinese', font_size=13,
            multiline=True, size_hint_y=None, height=90
        )
        content.add_widget(story_input)

        # 按钮
        btn_row = BoxLayout(size_hint_y=None, height=50, spacing=10)
        ok_btn = Button(text="确定", font_name='Chinese')
        cancel_btn = Button(text="取消", font_name='Chinese')
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)

        popup = Popup(title="添加关系", title_font='Chinese',
                      content=content, size_hint=(0.9, 0.9))

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
                "target": target,
                "relation": relation,
                "story": story
            })
            popup.dismiss()
            self.save_to_file()
            self.show_oc(oc)
            self.show_toast("已添加关系")

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    # ---------- 删除关系 ----------
    def delete_relation(self, idx):
        oc = self.current_oc
        rels = oc.get("relations", [])
        if idx < 0 or idx >= len(rels):
            return
        rel = rels[idx]
        target = rel.get("target", "")

        content = BoxLayout(orientation='vertical', padding=15, spacing=15)
        content.add_widget(Label(
            text=f"确定删除和「{target}」的关系吗？",
            font_name='Chinese', font_size=15,
            size_hint_y=None, height=60
        ))

        btn_row = BoxLayout(size_hint_y=None, height=50, spacing=10)
        ok_btn = Button(text="删除", font_name='Chinese')
        cancel_btn = Button(text="取消", font_name='Chinese')
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)

        popup = Popup(title="删除关系", title_font='Chinese',
                      content=content, size_hint=(0.8, 0.5))

        def on_ok(inst):
            rels.pop(idx)
            popup.dismiss()
            self.save_to_file()
            self.show_oc(oc)
            self.show_toast("已删除关系")

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def go_back(self, instance):
        self.manager.current = 'home'


# ========== App ==========
class OCApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(DetailScreen(name='detail'))
        return sm


if __name__ == "__main__":
    OCApp().run()
