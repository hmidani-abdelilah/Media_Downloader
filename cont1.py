import os
import customtkinter as ctk

# Set the theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ShutdownApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup to mimic a standard messagebox popup
        self.title("System Shutdown")
        self.geometry("400x180")
        self.resizable(False, False)
        
        # Keep on top of all other windows
        self.attributes("-topmost", True)

        self.time_left = 30

        # Title/Message Label
        self.label_msg = ctk.CTkLabel(
            self, 
            text=f"Your PC will shut down automatically in {self.time_left} seconds.", 
            font=("Arial", 14),
            wraplength=350
        )
        self.label_msg.pack(pady=(40, 20), padx=20)

        # Cancel Button
        self.btn_cancel = ctk.CTkButton(
            self, 
            text="Cancel Shutdown", 
            width=150,
            command=self.cancel_shutdown
        )
        self.btn_cancel.pack(pady=(10, 20))

        # Start the loop
        self.update_countdown()

    def update_countdown(self):
        if self.time_left > 0:
            # Update the label text safely
            self.label_msg.configure(
                text=f"Your PC will shut down automatically in {self.time_left} seconds."
            )
            self.time_left -= 1
            # Call again in 1 second
            self.after(1000, self.update_countdown)
        else:
            self.label_msg.configure(text="Shutting down now...")
            self.execute_shutdown()

    def execute_shutdown(self):
        #os.system("shutdown /s /t 0")
        print("Shutdown command executed (simulated).")  # For testing purposes
        self.destroy()

    def cancel_shutdown(self):
        self.destroy()

if __name__ == "__main__":
    app = ShutdownApp()
    app.mainloop()