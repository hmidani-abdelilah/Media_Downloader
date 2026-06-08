import os

def find_ffmpeg_on_c():
    root_dir = "C:\\"
    print("Searching for ffmpeg.exe on C: drive... This might take a minute.")
    
    for root, dirs, files in os.walk(root_dir):
        if "ffmpeg.exe" in files:
            full_path = os.path.join(root, "ffmpeg.exe")
            print(f"Success! Found at: {full_path}")
            return full_path
            
    print("ffmpeg.exe was not found on C: drive.")
    return None

# Execute the search
ffmpeg_absolute_path = find_ffmpeg_on_c()
print(ffmpeg_absolute_path)