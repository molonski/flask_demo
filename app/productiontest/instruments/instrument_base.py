class InstrumentBase(object):

    def __init__(self):
        self.manufacturer = 'artiphon'
        self.attached = self._is_connected()

    def set_development_mode(self, val):
        pass

    def read(self, reading_name):
        return {''}

    def _is_connected(self):
        return False

    def __repr__(self):
        return '<{}: {} - connected: {}>'.format(self.manufacturer, self.name, self.attached)

