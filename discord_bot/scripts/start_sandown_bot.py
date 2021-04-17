import time, os

def setup_tmux():
    try:
        os.system('tmux send-keys -t mcserver:1.1 "tmux split-window -h" ENTER')
        print("Split lower pane horizontally.")
    except:
        print("Error splitting window.")
    
    try:
        os.system('tmux send-keys -t mcserver:1.2 "sandownbot" ENTER')
        print("Started sandown bot.")
    except:
        print("Error starting sandown bot.")

    time.sleep(1)

if __name__ == '__main__':
    setup_tmux()
