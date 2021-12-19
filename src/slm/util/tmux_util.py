import libtmux
import time

server = libtmux.Server()
session = server.find_where({"session_name": "login"})
if session is None:
    session = server.new_session(session_name="login")

M_WINDOW_INDEX_DICT = {}


def new_pane_in_window(window_name):
    """
    Select or create a window by name, then create and return a new pane.

    :window_name: name of a window
    :returns: a new pane

    """
    window = session.find_where({"window_name": window_name})
    pane = None
    if window is None:
        window = session.new_window(window_name=window_name)
        pane = window.panes[0]
    else:
        window.select_window()
        pane = window.split_window()
    return pane


def new_tiled_panes(window_name_prefix, amount):
    """
    Create new windows with the same prefix, each window will
    split into nine panes at most.

    :window_name_prefix: window name prefix of these panes
    :amount: total number of panes to be created
    :returns: panes

    """
    max_amount_in_a_window = 9
    number_of_windows = int((amount - 1) / max_amount_in_a_window) + 1
    index = M_WINDOW_INDEX_DICT.get(window_name_prefix)
    if index is None:
        index = 0
        M_WINDOW_INDEX_DICT[window_name_prefix] = index
    M_WINDOW_INDEX_DICT[window_name_prefix] = index + number_of_windows
    count = 0
    panes = []
    while count < number_of_windows:
        window_name = "%s-%d" % (window_name_prefix, index + count)
        window = session.find_where({"window_name": window_name})
        if window is not None:
            window.kill_window()
        window = session.new_window(window_name=window_name)
        # calculte number of panes
        amount_in_this_window = min(
            amount - count * max_amount_in_a_window, max_amount_in_a_window
        )
        for idx in range(0, amount_in_this_window - 1):
            window.split_window()
            # adjust tile after split in case of not enough space
            window.select_layout("tiled")
        panes.extend(window.panes)
        count += 1
    return panes


def wait_until(pane, prompt, timeout):
    outs = pane.cmd("capture-pane", "-p").stdout
    if len(outs) < 1:
        out = ""
    else:
        out = outs[-1].strip()
    total = 0
    while not out.endswith(prompt):
        time.sleep(0.1)
        total += 0.1
        if total > timeout:
            return False
        outs = pane.cmd("capture-pane", "-p").stdout
        if len(outs) < 1:
            out = ""
        else:
            out = outs[-1].strip()
    return True


def wait_until_any(pane, prompts, timeout):
    outs = pane.cmd("capture-pane", "-p").stdout
    if len(outs) < 1:
        out = ""
    else:
        out = outs[-1].strip()
    total = 0
    while True:
        for prompt in prompts:
            if prompt is None:
                continue
            if out.endswith(prompt):
                return prompt
        time.sleep(0.1)
        total += 0.1
        if total > timeout:
            return None
        outs = pane.cmd("capture-pane", "-p").stdout
        if len(outs) < 1:
            out = ""
        else:
            out = outs[-1].strip()
