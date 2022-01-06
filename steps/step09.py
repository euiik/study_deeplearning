import numpy as np

class Variable:
  def __init__(self, data):
    if data != None:
      if not isinstance(data, np.ndarray):
        raise TypeError(f'{type(data)}은 지원하지 않습니다.')

    self.data = data
    self.grad = None
    self.creator = None

  def set_creator(self, func):
    self.creator = func

  def backward(self):
    if self.grad == None:
      self.grad = np.ones_like(self.data)

    funcs = [self.creator]
    while funcs:
      f = funcs.pop()
      x, y = f.input, f.output
      x.grad = f.backward(y.grad)

      if x.creator != None:
        funcs.append(x.creator)


class Function:
  def __call__(self, input):
    x = input.data
    y = self.forward(x)

    output = Variable(as_array(y))
    output.set_creator(self)

    self.input = input
    self.output = output

    return output

  def forward(self, x):
    raise NotImplementedError()

  def backward(self, gy):
    raise NotImplementedError()


class Square(Function):
  def forward(self, x):
    y = x ** 2
    return y
  
  def backward(self, gy):
    x = self.input.data
    gx = 2 * x * gy
    return gx


class Exp(Function):
  def forward(self, x):
    y = np.exp(x)
    return y

  def backward(self, gy):
    x = self.input.data
    gx = np.exp(x) * gy
    return gx

def square(x):
  f = Square()
  return f(x)

def exp(x):
  f = Exp()
  return f(x)

def as_array(x):
  if np.isscalar(x):
    return np.array(x)
  return x