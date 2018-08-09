class Exporter:
    def name(self):
        pass
    
    def export(self, measurements, ts=None):
        pass
    
    def close(self):
        pass

    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.close()
        return False