import os
import customtkinter as ctk

# Set the theme and color options
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ShutdownCountdownApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("System Shutdown Warning")
        self.geometry("400x200")
        self.resizable(False, False)
        
        # Keep the window on top of other applications
        self.attributes("-topmost", True)

        # Remaining time variable
        self.time_left = 30

        # UI Elements
        self.label_msg = ctk.CTkLabel(
            self, 
            text="Your PC will shut down automatically in:", 
            font=("Arial", 16)
        )
        self.label_msg.pack(pady=(20, 5))

        self.label_timer = ctk.CTkLabel(
            self, 
            text=f"{self.time_left} seconds", 
            font=("Arial", 28, "bold"), 
            text_color="#FF4444"  # Alert red color
        )
        self.label_timer.pack(pady=10)

        self.btn_cancel = ctk.CTkButton(
            self, 
            text="Cancel Shutdown", 
            fg_color="#333333", 
            hover_color="#555555",
            command=self.cancel_shutdown
        )
        self.btn_cancel.pack(pady=(10, 20))

        # Start the countdown loop
        self.update_countdown()

    def update_countdown(self):
        if self.time_left > 0:
            self.label_timer.configure(text=f"{self.time_left} seconds")
            self.time_left -= 1
            # Call this method again after 1000ms (1 second)
            self.after(1000, self.update_countdown)
        else:
            self.label_timer.configure(text="Shutting down...")
            self.execute_shutdown()

    def execute_shutdown(self):
        # Windows shutdown command: /s (shutdown), /t 0 (immediately)
        #os.system("shutdown /s /t 0")
        print("Shutdown command executed (simulated).")  # For testing purposes
        self.destroy()

    def cancel_shutdown(self):
        # Standard window close if aborted
        self.destroy()

if __name__ == "__main__":
    app = ShutdownCountdownApp()
    app.mainloop()