import threading
import time
import os
import json
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from pynput import keyboard
import win32clipboard # 要: pip install pywin32
import grapheme
from plyer import notification

CONFIG_FILE = "config.json"

class ClipBoardCounter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("clipboard counter")
        self.root.geometry("600x300")
        self.root.iconify()

        self.notify_timeout = tk.IntVar(value=3) # デフォルト3秒
        self.notify_enabled = tk.BooleanVar(value=True) # 通知ON/OFF
        self.always_on_top = tk.BooleanVar(value=False)
        
        # 設定の読み込み
        self.load_config()

        self.settings_window = None

        # メニューバー
        self.menubar = tk.Menu(self.root)
        self.setting_menu = tk.Menu(self.menubar, tearoff=0)
        self.setting_menu.add_command(label="設定", command=self.open_settings)
        self.setting_menu.add_separator() # 区切り線
        self.setting_menu.add_command(label="終了", command=self.on_closing)
        
        # メニューバーに登録
        self.menubar.add_cascade(label="設定", menu=self.setting_menu)
        
        # ルートウィンドウにメニューバーを適用
        self.root.config(menu=self.menubar)

        self.label = tk.Label(self.root, text="Ctrl+C を監視中...", font=("MS Gothic", 12))
        self.label.pack(pady=5)

        # 履歴リスト
        columns = ("time", "count", "preview")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        self.tree.heading("time", text="時刻")
        self.tree.heading("count", text="文字数/サイズ")
        self.tree.heading("preview", text="内容プレビュー")
        self.tree.column("time", width=100, anchor="center")
        self.tree.column("count", width=120, anchor="center")
        self.tree.column("preview", width=300, anchor="w")
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

        # ホットキー監視（別スレッド）
        self.hotkey = keyboard.GlobalHotKeys({'<ctrl>+c': self.on_copy})
        self.monitor_thread = threading.Thread(target=self.hotkey.start, daemon=True)
        self.monitor_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # 設定の保存・読み込み
    def save_config(self):
        config = {
            "notify_enabled": self.notify_enabled.get(),
            "notify_timeout": self.notify_timeout.get(),
            "always_on_top": self.always_on_top.get()
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.notify_enabled.set(config.get("notify_enabled", True))
                    self.notify_timeout.set(config.get("notify_timeout", 3))
                    self.always_on_top.set(config.get("always_on_top", False))
                    # 最前面設定を反映
                    self.toggle_topmost()
            except Exception as e:
                print(f"Config Load Error: {e}")

    def toggle_topmost(self):
        # 最前面表示の切り替え
        is_top = self.always_on_top.get()
        self.root.attributes("-topmost", is_top)

    def format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"

    def on_copy(self):
        # Ctrl+Cをフックした際の処理
        time.sleep(0.1)  # クリップボード更新待ち
        try:
            win32clipboard.OpenClipboard()
            # ファイルコピーの判定
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
                files = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
                win32clipboard.CloseClipboard()
                
                total_size = sum(os.path.getsize(f) for f in files if os.path.exists(f))
                size_str = self.format_size(total_size)
                msg = f"📁 {len(files)}個のファイル (計 {size_str})"
                
                self.root.after(0, lambda: self.update_list(datetime.now().strftime("%H:%M:%S"), "-", msg))
                self.show_balloon("ファイルコピー", msg)

            # テキストコピーの判定
            elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                content = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                
                count = grapheme.length(content)
                preview = content.replace("\n", " ")[:15]
                
                self.root.after(0, lambda: self.update_list(datetime.now().strftime("%H:%M:%S"), count, preview))
                self.show_balloon(f"{count} 文字", preview)
            else:
                win32clipboard.CloseClipboard()
        except Exception as e:
            print(f"Error: {e}")

    def update_list(self, timestamp, count, preview):
        # メイン画面のリストを更新
        # 新しいデータを先頭に挿入
        self.tree.insert("", 0, values=(timestamp, count, preview))
        
        # 10件を超えたら古いもの（一番下）を削除
        items = self.tree.get_children()
        if len(items) > 10:
            self.tree.delete(items[-1])

    def show_balloon(self, title_text, msg):
        # OSの通知（バルーン）を表示

        if not self.notify_enabled.get():
            return
        notification.notify(
            title=title_text,
            message=msg,
            app_name="ClipCounter",
            timeout=self.notify_timeout.get()
        )

    def open_settings(self):
        if self.settings_window is not None and tk.Toplevel.winfo_exists(self.settings_window):
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("設定")
        self.settings_window.geometry("300x250")
        self.settings_window.transient(self.root)
        
        tk.Checkbutton(self.settings_window, text="コピー時に通知を表示する", variable=self.notify_enabled).pack(anchor="w", padx=40)
        
        tk.Checkbutton(self.settings_window, text="常に最前面に表示", variable=self.always_on_top, 
                       command=self.toggle_topmost).pack(anchor="w", padx=40)

        frame = tk.Frame(self.settings_window)
        frame.pack(pady=15)
        tk.Label(frame, text="通知秒数:").pack(side="left")
        tk.Spinbox(frame, from_=1, to=10, width=5, textvariable=self.notify_timeout).pack(side="left", padx=5)

        tk.Button(self.settings_window, text="保存して閉じる", command=self.close_and_save).pack(side="bottom", pady=10)

    def close_and_save(self):
        self.save_config()
        self.settings_window.destroy()

    def on_closing(self):
        self.save_config() # 終了時にも念のため保存
        self.hotkey.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ClipBoardCounter()
    app.run()