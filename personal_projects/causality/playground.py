import numpy as np

class UniformDistribution(object):
    '''
    https://levelup.gitconnected.com/understanding-uniform-distribution-and-cracking-the-data-science-interview-a8404166330d
    '''
    def __init__(self, a, b) -> None:
        super().__init__()
        self.a = a
        self.b = b

    def sample(self, x):
        if self.a <= x <= self.b:
            return 1
        else:
            return 0

    def pdf(self, x):
        if self.a <= x <= self.b:
            return 1/(self.b - self.a)
        else:
            return 0

    def pdf_indicator(self, x):
        return (self.indicator_a(x)*self.indicator_b(x))/(self.b-self.a)

    def cdf(self, x):
        if x < self.a:
            return 0
        elif self.a <= x <= self.b:
            return (x - self.a)/(self.b - self.a)

    def indicator_a(self, x):
        if x < self.a:
            return 0
        else:
            return 1

    def indicator_b(self, x):
        if x > self.b:
            return 0
        else:
            return 1

    def likelihood(self, X):
        n = len(X)
        return (1/(self.b - self.a)**n)*np.prod([self.indicator_a(x)*self.indicator_b(x) for x in X])

    def mle(self, X):
        self.a = np.min(X)
        self.b = np.max(X)
        return self.a, self.b

if __name__ == "__main__":
    # Say we have X ~ Uniform(-1, 1) and Y = X². What is the covariance of X and Y?
    # The covariance of two uniform distributions
    print('main')
    uni = UniformDistribution(1,2)
    # res = uni.mle([1,1,3,4,11])
    # print(res)
    print(uni.pdf(1))