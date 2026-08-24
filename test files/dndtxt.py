import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_TEXT

class LinkDnDApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        # Load the extension into CustomTkinter
        self.TkdndVersion = TkinterDnD._require(self)
        
        self.geometry("500x150")
        self.title("Link Drop Box")
        
        # Setup the CTkEntry widget
        self.entry_box = ctk.CTkEntry(self, width=400, placeholder_text="Drag a website URL here...")
        self.entry_box.pack(expand=True, padx=20, pady=20)
        
        # Access the underlying standard entry object
        native_entry = self.entry_box._entry
        native_entry.drop_target_register(DND_TEXT)
        native_entry.dnd_bind("<<Drop>>", self.drop_link)

    def drop_link(self, event):
        # Format the incoming text string
        url = event.data.strip("{} ")
        
        # Clear field and update text
        self.entry_box.delete(0, "end")
        self.entry_box.insert(0, url)

if __name__ == "__main__":
    app = LinkDnDApp()
    app.mainloop()
