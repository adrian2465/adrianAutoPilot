## Adrian Vrouwenvelder
## December 1, 2022

class Observer:
  def __init__(self, observable):
    observable.subscribe(self)

  def notify(self, observable, *args, **kwargs):
    print('Got', args, kwargs, 'From', observable)


class Observable:
  def __init__(self):
    self._observers = []

  def subscribe(self, observer):
    self._observers.append(observer)

  def notify_observers(self, *args, **kwargs):
    for obs in self._observers:
      obs.notify(self, *args, **kwargs)

  def unsubscribe(self,observer):
    self._observers.remove(observer)

# For testing/demonstration
if __name__=="__main__":
  # Initializing the subject
  subject = Observable()

  # Initializing twp observers with the subject object
  observer1 = Observer(subject)
  observer2 = Observer(subject)
  
  # The following message will be notified to 2 observers
  subject.notify_observers('This is the 1st broadcast', kw='From the Observer')
  subject.unsubscribe(observer2)

  # The following message will be notified to just 1 observer since
  # the observer has been unsubscribed
  subject.notify_observers('This is the 2nd broadcast', kw='From the Observer')


