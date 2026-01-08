import threading
import time
import tkinter as tk
from pynput import keyboard
import pyperclip
from plyer import notification
import grapheme
from tkinter import ttk
from datetime import datetime

class ClipBoardCounter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("clipboard counter")
        self.root.geometry("600x150")
        self.root.iconify()

        self.notify_timeout = tk.IntVar(value=3) # デフォルト3秒
        self.notify_enabled = tk.BooleanVar(value=True) # 通知ON/OFF
        self.always_on_top = tk.BooleanVar(value=False)

        self.settings_window = None
        self.menubar = tk.Menu(self.root)

        # メニューバー
        self.setting_menu = tk.Menu(self.menubar, tearoff=0)
        self.setting_menu.add_command(label="設定", command=self.open_settings)
        self.setting_menu.add_separator() # 区切り線
        self.setting_menu.add_command(label="終了", command=self.on_closing)
        
        # メニューバーに登録
        self.menubar.add_cascade(label="設定", menu=self.setting_menu)
        
        # ルートウィンドウにメニューバーを適用
        self.root.config(menu=self.menubar)

        self.label = tk.Label(self.root, text="Ctrl+C を監視中...", font=("MS Gothic", 12))
        self.label.pack(expand=True)

        # --- GUI: 履歴リスト (Treeview) の設定 ---
        columns = ("time", "count", "preview")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        
        # 各カラムの見出しと幅
        self.tree.heading("time", text="時刻")
        self.tree.heading("count", text="文字数")
        self.tree.heading("preview", text="テキスト（先頭15文字）")
        
        self.tree.column("time", width=100, anchor="center")
        self.tree.column("count", width=60, anchor="center")
        self.tree.column("preview", width=300, anchor="w")
        
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

        # ホットキー監視設定
        self.hotkey = keyboard.GlobalHotKeys({
            '<ctrl>+c': self.on_copy
        })

        # 監視用スレッド生成
        self.monitor_thread = threading.Thread(target=self.hotkey.start, daemon=True)
        self.monitor_thread.start()

        # 終了処理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    def toggle_topmost(self):
        # 最前面表示の切り替え
        is_top = self.always_on_top.get()
        self.root.attributes("-topmost", is_top)
    def on_copy(self):
        # Ctrl+Cをフックした際の処理
        time.sleep(0.1)  # クリップボード更新待ち

        try:
            content = pyperclip.paste()
            if content and isinstance(content, str):
                # 文字数カウント（マルチバイト・絵文字対応）
                count = grapheme.length(content)
                # タイムスタンプ取得
                now = datetime.now().strftime("%H:%M:%S")
                # 先頭15文字（改行はスペースに置換して表示崩れを防ぐ）
                preview = content.replace("\n", " ")[:15]
                
                # GUIの更新と通知
                self.root.after(0, lambda: self.update_list(now, count, preview))
                self.show_balloon(count, preview)
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

    def show_balloon(self, count, text):
        # OSの通知（バルーン）を表示

        # タイムアウト値を取得
        try:
            current_timeout = self.notify_timeout.get()
        except:
            current_timeout = 3 # 入力が不正な場合のフォールバック
        # 冒頭15文字だけプレビュー表示
        preview = (text[:15] + '...') if len(text) > 15 else text
        notification.notify(
            title="clip board counter",
            message=f"{count} 文字\n内容: {preview}",
            app_name="clip board counter",
            timeout=current_timeout  # 3秒間表示
        )

    def on_closing(self):
        self.hotkey.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
    
    def open_settings(self):
        # 設定用のサブウィンドウを表示
        if self.settings_window is not None and tk.Toplevel.winfo_exists(self.settings_window):
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("設定")
        self.settings_window.geometry("300x250")
        self.settings_window.transient(self.root) 

        # 1. 通知のON/OFF
        chk_notify = tk.Checkbutton(self.settings_window, text="コピー時に通知を表示する", 
                                    variable=self.notify_enabled)
        chk_notify.pack(pady=5)

        # 常に最前面に表示する
        tk.Checkbutton(self.settings_window, text="常に最前面に表示する", 
                       variable=self.always_on_top,
                       command=self.toggle_topmost).pack(pady=5)

        # 2. タイムアウト時間の設定
        timeout_frame = tk.Frame(self.settings_window)
        timeout_frame.pack(pady=10)
        
        tk.Label(timeout_frame, text="通知の表示時間(秒):").pack(side="left")
        
        # 数値入力用のスピンボックス (1秒〜10秒まで)
        spin_timeout = tk.Spinbox(timeout_frame, from_=1, to=10, width=5, 
                                  textvariable=self.notify_timeout)
        spin_timeout.pack(side="left", padx=5)

        # 閉じるボタン
        close_btn = tk.Button(self.settings_window, text="閉じる", 
                              command=self.settings_window.destroy)
        close_btn.pack(side="bottom", pady=10)

if __name__ == "__main__":
    app = ClipBoardCounter()
    app.run()