


class Square(Function):
    def forward(self, x):
        y = x ** 2
        return y
    def backward(self, gy):
        x = self.inputs[0].data
        gx = 2 * x * gy
        return gx

def square(x):
    f = Square()
    return f(x)
