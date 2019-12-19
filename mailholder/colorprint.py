class ColorPrint():

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.front = '\x1b[1;%sm' % (self.kwargs['c'])
        self.back = '\x1b[0m'
        self.values = []
        for x in args:
            self.values.append(self.front + str(x) + self.back)
        return print(*self.values)

    def __repr__(self, *args, **kwargs):
        return print(*self.values)

cprint = ColorPrint()

bold = lambda *x: cprint(*x, c=30)
red = lambda *x: cprint(*x, c=31)
green = lambda *x: cprint(*x, c=32)
yellow = lambda *x: cprint(*x, c=33)
blue = lambda *x: cprint(*x, c=34)
purple = lambda *x: cprint(*x, c=35)
turquoise = lambda *x: cprint(*x, c=36)
gray = lambda *x: cprint(*x, c=37)
italic = lambda *x: cprint(*x, c=3)

