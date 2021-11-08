import time, os

def start_tmux():
    """Starts detached Tmux session, with 2 panes, named 'sess'."""

    os.system('tmux new -d -s sess')
    os.system('tmux send-keys -t sess:1.0 "tmux split-window -v" ENTER')
    time.sleep(.5)
    os.system('tmux send-keys -t sess:1.0 "tmux new-window" ENTER')
    time.sleep(.5)
    os.system('tmux send-keys -t sess:2.0 "tmux split-window -v" ENTER')
    time.sleep(1)


def setup_tmux():
    os.system('tmux send-keys -t sess:1.1 "sandownbot" ENTER')

if __name__ == '__main__':
    start_tmux()
    setup_tmux()
