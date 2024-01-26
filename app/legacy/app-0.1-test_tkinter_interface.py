import customtkinter as ctk
import tkinter as tk

def on_button_click():
    label.configure(text="Volim te!")

# Initialize the main window
root = ctk.CTk()
root.title("CustomTkinter Interface")

# Create a custom label
label = ctk.CTkLabel(root, text="Bok Dora!")
label.pack(pady=10)

# Create a custom button
button = ctk.CTkButton(root, text="Pritisni me bebo", command=on_button_click)
button.pack(pady=10)

# Start the application
root.mainloop()