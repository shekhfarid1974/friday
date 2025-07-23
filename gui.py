import tkinter as tk
from PIL import Image, ImageTk
import threading
import os  # ←← This was missing! Add it at the top

def start_gui():
    root = tk.Tk()
    root.title("F.R.I.D.A.Y.")
    root.geometry("400x500")
    root.configure(bg='black')

    label = tk.Label(root, text="F.R.I.D.A.Y.\nOnline", fg="#00ff00", bg="black", font=("Courier", 16))
    label.pack(pady=50)

    canvas = tk.Canvas(root, width=200, height=200, bg='black', highlightthickness=0)
    canvas.pack()

    # Draw glowing circle (like arc reactor)
    def animate():
        canvas.delete("all")
        x = 100
        y = 100
        r = 50
        canvas.create_oval(x-r, y-r, x+r, y+r, outline="#00ffff", width=4)
        canvas.create_oval(x-r//2, y-r//2, x+r//2, y+r//2, fill="#00ffff", outline="")
        root.after(500, lambda: canvas.create_oval(x-60, y-60, x+60, y+60, outline="#00ffff", width=1, stipple="gray50"))
        root.after(1000, animate)

    animate()

    # Start F.R.I.D.A.Y. backend in a new thread
    threading.Thread(target=lambda: os.system("python friday.py"), daemon=True).start()

    root.mainloop()

if __name__ == "__main__":
    start_gui()