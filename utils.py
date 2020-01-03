from threading import Thread
from kivy.logger import Logger
try:
    from kivymd.toast import toast
except:
    pass

th0 = Thread()
th1 = Thread()

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
    a separate thread but, only if sidethread isn't already running
    """
    def wrapped(*args, **kwargs):
        global th0
        if th0.is_alive() == False:
            th0 = Thread(target=fn, args=args, kwargs=kwargs)
            th0.start()
        else:
            tprint('sidethread is already active')

    return wrapped

def specialthread(fn):
    """
    Essentially reverse of @mainthread kivy decorator - runs function/method in
    a separate thread
    """
    def wrapped(*args, **kwargs):
        global th1
        th1 = Thread(target=fn, args=args, kwargs=kwargs)
        th1.start()

    return wrapped
