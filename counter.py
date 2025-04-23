import tkinter as tk

class CounterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Counter")
        
        # Set fullscreen mode
        self.root.attributes('-fullscreen', True)
        
        # Set black background
        self.root.configure(bg="black")
        
        # Create a frame to center the counter
        self.main_frame = tk.Frame(self.root, bg="black")
        self.main_frame.pack(expand=True, fill="both")
        
        # Create a label to display the counter
        self.counter_label = tk.Label(
            self.main_frame, 
            font=("Arial", 120, "bold"),
            text="1", 
            fg="white", 
            bg="black",
            anchor="center"
        )
        self.counter_label.pack(expand=True, fill="both")
        
        # Add escape key binding to exit fullscreen
        self.root.bind("<Escape>", self.end_fullscreen)
        
        # Initialize counter value
        self.count = 1
        
        # Call method to update the counter
        self.update_counter()
    
    def end_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", False)
        return "break"
        
    def update_counter(self):
        # Update the counter value
        self.counter_label.config(text=str(self.count))
        
        # Increment the counter
        self.count += 1
        
        # Call this method again after 1 second (1000ms)
        self.root.after(1000, self.update_counter)

if __name__ == "__main__":
    # Create the Tkinter window
    root = tk.Tk()
    
    # Create the counter app
    app = CounterApp(root)
    
    # Start the Tkinter main loop
    root.mainloop()
