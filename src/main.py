import threading
import time
import tkinter as tk
from pynput import keyboard
import pyperclip
from plyer import notification
import grapheme

class CopyMonitorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("clipboard counter")
        self.root.geometry("300x150")
        self.root.iconify()

        self.label = tk.Label(self.root, text="Ctrl+C を監視中...", font=("MS Gothic", 12))
        self.label.pack(expand=True)

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
        # Ctrl+Cが押された時に実行

        # クリップボードを書き換えるまでの待機
        time.sleep(0.1)
        try:
            # テキストを取得
            content = pyperclip.paste()
            if content and isinstance(content, str):
                count = grapheme.length(content)
                self.show_balloon(count, content)
                self.root.after(0, lambda: self.label.config(text=f"前回：{count}文字"))
        except Exception as e:
            print(f"エラーが発生しました: {e}")

    def show_balloon(self, count, text):
        # OSの通知（バルーン）を表示"

        # 冒頭15文字だけプレビュー表示
        preview = (text[:15] + '...') if len(text) > 15 else text
        notification.notify(
            title="clip board counter",
            message=f"{count} 文字\n内容: {preview}",
            app_name="Copy Monitor",
            timeout=3  # 3秒間表示
        )

    def on_closing(self):
        self.hotkey.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = CopyMonitorApp()
    app.run()