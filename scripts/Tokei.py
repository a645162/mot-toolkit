import os
import datetime

if __name__ == "__main__":
    print("MOT Toolkit")
    print("Author: Haomin Kong")
    print("https://github.com/a645162/mot-toolkit")

    # Get the current time
    now = datetime.datetime.now()
    format_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Current Time: {format_time}")

    try:
        ret = os.system("tokei")
        if ret != 0:
            print("Please install tokei by running 'cargo install tokei' in the terminal.")
    except Exception as e:
        print(f"Error: {e}")
