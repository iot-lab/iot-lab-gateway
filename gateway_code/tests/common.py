
class PopenMock(object):
    """
    Dummy Popen implementation for testing
    """
    out = None
    err = None
    returncode = None
    args = None

    def __init__(self, args, stdout, stderr):
        self.returncode = None
        type(self).args = args

    def communicate(self):
        self.returncode = type(self).returncode
        out = type(self).out
        err = type(self).err
        return out, err

    @classmethod
    def setup(cls, out=None, err=None, returncode=None):
        cls.out = out
        cls.err = err
        cls.returncode = returncode

