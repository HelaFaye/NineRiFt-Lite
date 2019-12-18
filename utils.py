from threading import Thread
from kivy.logger import Logger
try:
    from kivymd.toast import toast
except:
    pass

th = Thread()

# toast or print
def tprint(msg):
    Logger.info('tprint: %s' % (msg,))
    try:
        toast(msg)
    except:
        pass

def sidethread(fn):
    """
    Essentially reverse of @mainthread kivy decorator - runs function/method in
    a separate thread
    """
    def wrapped(*args, **kwargs):
        global th
        if not th.is_alive():
            th = Thread(target=fn, args=args, kwargs=kwargs)
            th.start()
        else:
            tprint('sidethread is already active')
    return wrapped

def specialthread(fn):
    """
    Essentially reverse of @mainthread kivy decorator - runs function/method in
    a separate thread
    """
    def wrapped(*args, **kwargs):
        th1 = Thread(target=fn, args=args, kwargs=kwargs)
        th1.start()

    return wrapped
