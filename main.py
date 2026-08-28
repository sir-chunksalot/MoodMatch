import os
import threading
import tkinter as tk
from collections import defaultdict
from tkinter import messagebox, simpledialog, ttk

import httpx
from dotenv import load_dotenv

load_dotenv()

# Main window setup
root = tk.Tk()
root.title("MoodMatch")
root.geometry("500x400")

#------------------------------------------------------
#Logic
categories = ["Default"]
songs = defaultdict(list)


def add_new_category():
    # Opens the input prompt popup window
    user_response = simpledialog.askstring("Input Needed", "Enter name of new category:")
    
    # Handle the response
    if user_response:
        categories.append(user_response)
        dropdown['values'] = categories
        messagebox.showinfo("Success!","Category successfully added")
    else:
        messagebox.showinfo("Result", "You cancelled the prompt.")
        
def remove_category():
    # Opens the input prompt popup window
    user_response = simpledialog.askstring("Input Needed", "Enter name of the target category:")
    
    # Handle the response
    if categories.__contains__(user_response):
        categories.remove(user_response)
        dropdown['values'] = categories
        messagebox.showinfo("Success!","Category successfully removed")
    else:
        messagebox.showinfo("Result", "Category not found")

def submit_songs():
    user_input = entry_box.get()
    if(user_input):
        songs[dropdown.get()].append(user_input)
        print("songs:", songs)
        entry_box.delete(0, tk.END)
        
def accept_song():
    AI_output = output_box.get("1.0", "3.0")
    if(AI_output):
        songs[dropdown.get()].append(AI_output)
        print("songs:", songs)
        output_box.delete(0, tk.END)


def format_song_library():
    lines = []
    for category, titles in songs.items():
        if not titles:
            continue
        lines.append(f"{category}:")
        for title in titles:
            lines.append(f"  - {title}")
    return "\n".join(lines)


def show_output(text):
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, text)


def recommend_matching_song():
    library = format_song_library()
    if not library:
        messagebox.showinfo("MoodMatch", "Add some songs first.")
        return

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        messagebox.showerror(
            "Missing API key",
            "Set GEMINI_API_KEY in a .env file or as an environment variable.",
        )
        return

    show_output("Analyzing vibe...")
    match_btn.config(state="disabled")

    def run():
        try:
            result = call_gemini(api_key, library)
        except httpx.HTTPStatusError as exc:
            result = f"Could not get a recommendation ({exc.response.status_code}):\n{exc.response.text}"
        except Exception as exc:
            result = f"Could not get a recommendation:\n{exc}"
        root.after(0, lambda: finish_recommendation(result))

    threading.Thread(target=run, daemon=True).start()


def finish_recommendation(result):
    match_btn.config(state="normal")
    show_output(result)


def call_gemini(api_key, library):
    response = httpx.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent",
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        json={
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "You recommend music. Given the user's songs (grouped by category), "
                            "infer the shared vibe, energy, genre, and mood. Recommend exactly one "
                            "real song that matches that vibe and is not already in their list. "
                            "Reply with three lines: Song: <title>, Artist: <name>, Why: <one or two sentences>."
                        )
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": f"Here are the user's songs grouped by category:\n\n{library}"
                        }
                    ],
                }
            ],
            "generationConfig": {"temperature": 0.8},
        },
        timeout=30.0,
    )
    response.raise_for_status()
    parts = response.json()["candidates"][0]["content"]["parts"]
    return "".join(part.get("text", "") for part in parts).strip()
        


#-------------------------------------------------------
#UI

# Top frame for dropdown and button
top_frame = tk.Frame(root)
top_frame.pack(anchor="nw", padx=10, pady=10)

# Dropdown menu
dropdown_var = tk.StringVar()
dropdown = ttk.Combobox(top_frame, textvariable=dropdown_var, values=categories, width=15)
dropdown.current(0)
dropdown.pack(side="left", padx=5)

# Add category button
add_btn = tk.Button(top_frame, text="Add", command=add_new_category)
add_btn.pack(side="left", padx=5)

# remove category button
add_btn = tk.Button(top_frame, text="Remove", command=remove_category)
add_btn.pack(side="left", padx=5)

# Entry frame for title and input box
entry_frame = tk.Frame(root)
entry_frame.pack(fill="x", padx=15, pady=10)

# Entry title label
entry_label = tk.Label(entry_frame, text="Input Title:")
entry_label.pack(anchor="w")

# Entry box
entry_box = tk.Entry(entry_frame)
entry_box.pack(fill="x", pady=5)

# Add submit button
add_btn = tk.Button(entry_frame, text="Submit", command=submit_songs)
add_btn.pack(side="left", padx=5)

match_btn = tk.Button(entry_frame, text="Match Vibe", command=recommend_matching_song)
match_btn.pack(side="left", padx=5)

# Output frame
output_frame = tk.Frame(root)
output_frame.pack(fill="both", expand=True, padx=15, pady=10)

# Output title label
output_label = tk.Label(output_frame, text="Output:")
output_label.pack(anchor="w")

# Output box (Text widget for multi-line support)
output_box = tk.Text(output_frame, height=10)
output_box.pack(fill="both", expand=True, pady=5)

# Add save button
add_btn = tk.Button(output_frame, text="Save Song", command=accept_song)
add_btn.pack(side="left", padx=5)



# Start application
root.mainloop()
