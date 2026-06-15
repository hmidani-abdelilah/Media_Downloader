import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES

class DnDApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

app = DnDApp()
app.geometry("400x250")

def handle_drop(event):
    # Clean formatting brackets around paths
    file_path = event.data.strip("{}")
    label.configure(text=f"Dropped:\n{file_path}")

# Target drop UI component
label = ctk.CTkLabel(app, text="Drop Files Here", fg_color="gray20", corner_radius=10)
label.pack(expand=True, fill="both", padx=30, pady=30)

# Register component target
label.drop_target_register(DND_FILES)
label.dnd_bind("<<Drop>>", handle_drop)

app.mainloop()
