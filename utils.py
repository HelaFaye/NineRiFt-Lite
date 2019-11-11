from threading import Thread
from kivy.logger import Logger
try:
    from kivymd.toast import toast
except:
    pass

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

    # TODO add option to only allow a single running instance
    def wrapped(*args, **kwargs):
        th = Thread(target=fn, args=args, kwargs=kwargs)
        th.start()
    return wrapped
