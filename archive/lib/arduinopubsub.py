## Adrian Vrouwenvelder
## December 1, 2022

from pubsub import Publisher, Broker, Subscriber

_arduino_topic = 'serial_input'
_broker = Broker("Arduino")

class ArduinoPublisher(Publisher):
    def __init__(self):
        super().__init__(name = 'ArduinoPublisher', broker = _broker)
    def pub(self, msg): 
        super().pub(msg = msg, topic = _arduino_topic)
    
class ArduinoSubscriber(Subscriber):
    def __init__(self, name = "ArduinoSubscriber"):
        super().__init__(name = name, broker = _broker, topics = [ _arduino_topic ])


def test():
    p = ArduinoPublisher()
    s1 = ArduinoSubscriber('s1')
    s2 = ArduinoSubscriber('s2')
    p.pub('Hello Brain et.al.')

if __name__ == '__main__':
    test()

