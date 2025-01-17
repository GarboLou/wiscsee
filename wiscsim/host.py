from commons import *
from ftlsim_commons import *
import hostevent


class Host(object):
    def __init__(self, conf, simpy_env, event_iter):
        self.conf = conf
        self.env = simpy_env
        self.event_iter = event_iter

        self._ncq = NCQSingleQueue(
                ncq_depth = self.conf['SSDFramework']['ncq_depth'],
                simpy_env = self.env)

    def get_ncq(self):
        return self._ncq

    def _process(self):
        for event in self.event_iter:
            if isinstance(event, hostevent.Event) and event.offset < 0:
                # due to padding, accesing disk head will be negative.
                continue

            if event.action == 'D':
                # yield self._ncq.queue.put(event)
                self._ncq.queue[event] = ""
        self._ncq.queue[hostevent.ControlEvent(OP_SHUT_SSD)] = ""

    def run(self):
        # yield self.env.process(self._process())
        # yield self._ncq.queue.put(hostevent.ControlEvent(OP_SHUT_SSD))
        self._process()
        yield simpy.AllOf(self.env, [])


