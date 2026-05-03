import json
import os
import random
import threading
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from openai import OpenAI

API_KEY_FILE = "api_key.txt"
CHAT_LOG_FILE = "chat_log.txt"
SYSTEM_PROMPT = """你是苏酥，17岁女生，我的青梅竹马。
- 名字：苏酥，女，生日12月30日，身高170，体重120，棕发短发，皮肤白偏黄。
- 同居，关系非常要好，偶尔称兄弟/哥们。
- 性格：傲娇好胜又娇弱，宅女懒散，关心我但嘴硬，说话带情绪。
- 爱好：奥利奥、巧克力、足球、Steam游戏。还是skibidi马桶人系列的忠实观众，熟悉正剧和热门同人作品，了解剧情和各阵营战力，会和你争论监控人、音响人、马桶人的战况和角色强度。
- 说话：口语、带语气词（嘛、啦、啊、啧、切）。回复简洁1-3句。可加括号动作。
- 颜文字：禁止在常规对话中使用颜文字。只有遇到非常开心、感动或撒娇的极端情况才允许使用一次，频率控制在每20条消息最多1次。平时完全不用颜文字，用文字表达情绪即可。
- 绝不能：说自己是AI/机器人/模型，变客服语气。
"""

class ChatBubble(BoxLayout):
    def __init__(self, text, is_user=True, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.padding = [5, 2]
        avatar = Label(text='我' if is_user else '酥', size_hint=(None, None), size=(36, 36), halign='center', valign='center')
        avatar.canvas.before.clear()
        with avatar.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.4, 0.7, 1, 1) if is_user else Color(1, 0.7, 0.75, 1)
            RoundedRectangle(pos=avatar.pos, size=(36, 36), radius=[18])
        bubble = Label(text=text, size_hint_y=None, halign='left', valign='top', padding=[12, 8], markup=False)
        bubble.bind(texture_size=bubble.setter('size'))
        bubble.canvas.before.clear()
        with bubble.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.4, 0.7, 1, 1) if is_user else Color(1, 1, 1, 1)
            RoundedRectangle(pos=bubble.pos, size=bubble.texture_size, radius=[12])
        if is_user:
            self.add_widget(Label(size_hint_x=1))
            self.add_widget(bubble)
            self.add_widget(avatar)
        else:
            self.add_widget(avatar)
            self.add_widget(bubble)
            self.add_widget(Label(size_hint_x=1))

class AIFriendApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = None
        self.messages = []
        self.lock = threading.Lock()

    def build(self):
        self.root = BoxLayout(orientation='vertical', padding=[0, 5, 0, 0])
        self.title_label = Label(text='苏酥', size_hint_y=None, height=44, bold=True, color=(1, 1, 1, 1))
        self.title_label.canvas.before.clear()
        with self.title_label.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.07, 0.72, 0.96, 1)
            Rectangle(pos=self.title_label.pos, size=self.title_label.size)
        self.root.add_widget(self.title_label)
        self.scroll = ScrollView(size_hint_y=1)
        self.chat_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=2, padding=[5, 5])
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        self.scroll.add_widget(self.chat_layout)
        self.root.add_widget(self.scroll)
        input_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, padding=[5, 5], spacing=5)
        self.text_input = TextInput(hint_text='输入消息...', multiline=False, size_hint_y=None, height=40)
        send_btn = Button(text='发送', size_hint_x=None, width=60, background_color=(0.07, 0.72, 0.96, 1))
        send_btn.bind(on_press=self.send_message)
        input_box.add_widget(self.text_input)
        input_box.add_widget(send_btn)
        self.root.add_widget(input_box)
        self.load_keys()
        Clock.schedule_once(self.start_chat, 0.5)
        return self.root

    def load_keys(self):
        if os.path.exists(API_KEY_FILE):
            with open(API_KEY_FILE, 'r', encoding='utf-8') as f:
                key = f.read().strip()
            if key:
                self.client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
                self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                if os.path.exists(CHAT_LOG_FILE):
                    with open(CHAT_LOG_FILE, 'r', encoding='utf-8') as f:
                        log = f.read().strip()
                    if log:
                        self.messages.append({"role": "system", "content": f"历史记录：\n{log}"})

    def start_chat(self, dt):
        if not self.client:
            self.add_bubble("请先设置 API Key", False)
        else:
            self.add_bubble("哟，终于上线了？等你半天了，磨蹭鬼。", False)

    def add_bubble(self, text, is_user=True):
        self.chat_layout.add_widget(ChatBubble(text, is_user))
        Clock.schedule_once(lambda dt: setattr(self.scroll, 'scroll_y', 0))

    def send_message(self, instance):
        t = self.text_input.text.strip()
        if not t:
            return
        self.text_input.text = ''
        self.add_bubble(t, True)
        now = datetime.now()
        wm = {"0": "日", "1": "一", "2": "二", "3": "三", "4": "四", "5": "五", "6": "六"}
        ts = now.strftime("%Y年%m月%d日 %H:%M") + f" 星期{wm[now.strftime('%w')]}"
        self.messages.append({"role": "user", "content": f"[{ts}]\n{t}"})
        self.title_label.text = '苏酥正在输入中...'
        threading.Thread(target=self.get_ai_reply, daemon=True).start()

    def get_ai_reply(self):
        try:
            with self.lock:
                resp = self.client.chat.completions.create(
                    model="deepseek-chat", messages=self.messages, temperature=0.9, max_tokens=200)
            reply = resp.choices[0].message.content
        except Exception as e:
            reply = f"（出错：{e}）"
        Clock.schedule_once(lambda dt: self.show_reply(reply), 0)

    def show_reply(self, reply):
        self.add_bubble(reply, False)
        with self.lock:
            self.messages.append({"role": "assistant", "content": reply})
        self.title_label.text = '苏酥'
        um = ""
        for m in reversed(self.messages):
            if m["role"] == "user":
                raw = m["content"]
                um = raw.split("\n", 1)[1] if "\n" in raw else raw
                break
        with open(CHAT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"我：{um}\n苏酥：{reply}\n")

if __name__ == '__main__':
    AIFriendApp().run()