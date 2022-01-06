import numpy as np
import weakref
import contextlib

class Variable:
    def __init__(self, data, name=None):
        __array_priority__ = 200
        if data is not None:
            if not isinstance(data, np.ndarray):
                raise TypeError('{} is not supported'.format(type(data)))

        self.data = data
        self.grad = None
        self.name = name
        self.creator = None
        self.generation = 0

    def set_creator(self, func):
        self.creator = func
        self.generation = func.generation + 1

    def backward(self, retain_grad=False):
        if self.grad is None:
            self.grad = np.ones_like(self.data)

        funcs = []
        seen_set = set()
        def add_func(f):
          if f not in seen_set:
            funcs.append(f)
            seen_set.add(f)
            funcs.sort(key=lambda x: x.generation)
        
        add_func(self.creator)

        funcs = [self.creator]
        while funcs:
            f = funcs.pop()
            # gys = [output.grad for output in f.outputs]
            gys = [output().grad for output in f.outputs]
            gxs = f.backward(*gys)
            if not isinstance(gxs, tuple):
                gxs = (gxs,)

            for x, gx in zip(f.inputs, gxs):
              if x.grad is None:
                x.grad = gx
              else:
                x.grad = x.grad + gx

              if x.creator is not None:
                #funcs.append(x.creator)
                add_func(x.creator)
            if not retain_grad:
              for y in f.outputs:
                y().grad = None
      
    def cleargrad(self):
      self.grad = None  

    @property
    def shape(self):
      return self.data.shape

    @property
    def ndim(self):
      return self.data.ndim
    
    @property
    def size(self):
      return self.data.size
    
    @property
    def dtype(size):
      return self.data.dtype
    
    def __len__(self):
      return len(self.data)

    def __repr__(self):
      if self.data is None:
        return 'variable(None)'
      p = str(self.data).replace('\n', '\n' + ' '*9)
      return 'variable(' + p + ')'


def as_array(x):
    if np.isscalar(x):
        return np.array(x)
    return x


class Function:
    def __call__(self, *inputs):
        inputs = [as_variable(x) for x in inputs]

        xs = [x.data for x in inputs]
        ys = self.forward(*xs)
        if not isinstance(ys, tuple):
            ys = (ys,)
        outputs = [Variable(as_array(y)) for y in ys]

        if Config.enable_backprop:
          self.generation = max([x.generation for x in inputs])
          for output in outputs:
              output.set_creator(self)
          self.inputs = inputs
          self.outputs = [weakref.ref(output) for output in outputs]
          return outputs if len(outputs) > 1 else outputs[0]

    def forward(self, xs):
        raise NotImplementedError()

    def backward(self, gys):
        raise NotImplementedError()

class Config:
  enable_backprop = True

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


class Add(Function):
    def forward(self, x0, x1):
        y = x0 + x1
        return y

    def backward(self, gy):
        return gy, gy


def add(x0, x1):
  x1 = as_array(x1)
  return Add()(x0, x1)


class Mul(Function):
  def forward(self, x0, x1):
    y = x0 * x1
    return y

  def backward(self, gy):
    x0, x1 = self.inputs[0].data, self.inputs[1].data
    return gy*x1, gy*x0

def mul(x0, x1):
  x1 = as_array(x1)
  return Mul()(x0, x1)


class Neg(Function):
  def forward(self, x):
    return -x

  def backward(self, gy):
    return -y

def neg(x):
  return Neg()(x)

@contextlib.contextmanager
def using_config(name, value):
  old_value = getattr(Config, name)
  setattr(Config, name, value)
  try:
    yield
  finally:
    setattr(Config, name, old_value)

def no_grad():
  return using_config('enable_backprop', False)

def as_variable(obj):
  if isinstance(obj, Variable):
    return obj
  return Variable(obj)
  
Variable.__add__ = add
Variable.__radd__ = add
Variable.__mul__ = mul
Variable.__rmul__ = mul