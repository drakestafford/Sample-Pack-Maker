import os

def list_wavs(folder_path):
    print("Files found:")
    for file in os.listdir(folder_path):
        if file.lower().endswith(".wav"):
            print(file)

if __name__ == "__main__":
    folder = input("Drag your folder of WAV files here: ").strip()
    folder = folder.replace("\\ ", " ")
    list_wavs(folder)
