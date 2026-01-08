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

    def on_copy(self):
        """Ctrl+Cをフックした際の処理"""
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
        """メイン画面のリストを更新（最新が一番上）"""
        # 新しいデータを先頭に挿入
        self.tree.insert("", 0, values=(timestamp, count, preview))
        
        # 10件を超えたら古いもの（一番下）を削除
        items = self.tree.get_children()
        if len(items) > 10:
            self.tree.delete(items[-1])

    def show_balloon(self, count, text):
        # OSの通知（バルーン）を表示"

        # 冒頭15文字だけプレビュー表示
        preview = (text[:15] + '...') if len(text) > 15 else text
        notification.notify(
            title="clip board counter",
            message=f"{count} 文字\n内容: {preview}",
            app_name="clip board counter",
            timeout=3  # 3秒間表示
        )

    def on_closing(self):
        self.hotkey.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ClipBoardCounter()
    app.run()