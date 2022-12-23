## Adrian Vrouwenvelder
## December 1, 2022

class Broker(object):
    def __init__(self, name='broker'):
        self._name = name
        self._subscribers = []

    def attach(self, subscriber):
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)

    def detach(self, subscriber):
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)

    def route(self, msg:object, topic:str):
        for subscriber in self._subscribers:
            if topic in subscriber.topics:
                subscriber.sub(msg)


class Publisher(object):
    def __init__(self, name: str, broker):
        self._name = name
        self._broker = broker

    def pub(self, msg: object, topic: str):
        print (f'{self._name} publishing "{msg}" to topic {topic}')
        self._broker.route(msg, topic)

    def __str__(self):
        return f"{self._name}"


class Subscriber(object):
    def __init__(self, name: str, broker, topics):
        self._name = name
        broker.attach(self)
        self._topics = topics

    #override
    def sub(self, msg):
        print (f'Subscriber: {self._name} got message: "{msg}"')

    @property
    def topics(self):
        return self._topics

    def __str__(self):
        return f"{self._name}@{self._topics}"


def test():
    broker = Broker()

    p1 = Publisher('p1', broker)
    p2 = Publisher('p2', broker)

    s1 = Subscriber('s1', broker, topics=['A'])
    s2 = Subscriber('s2', broker, topics=['A', 'B'])

    p1.pub('hello p1-A', topic='A')
    p1.pub('hello p1-B', topic='B') # Not propagated. S1 is not interested in topic B.
    p2.pub('hello p2-A', topic='A')
    p2.pub('hello p2-B', topic='B')


if __name__ == '__main__':
    test()

