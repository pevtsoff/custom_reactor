import socket, selectors


class Reactor:
    def __init__(
        self,
        socket=socket.socket(),
    ):
        self.sock = socket
        self.sock.bind(("localhost", 1234))
        self.sock.listen(100)
        self.sock.setblocking(False)
        self.mask = ""
        self.list = []
        self.sync_demultiplexer = selectors.DefaultSelector()  # it has method select
        self.register_handler(
            self.sock,
            selectors.EVENT_READ,
            AcceptEventHandler(reactor=self).handle_event,
        )

    def register_handler(self, connection, event_type, event_handler):
        self.sync_demultiplexer.register(connection, event_type, event_handler)

    def remove_handler(self, connection):
        self.sync_demultiplexer.unregister(connection)

    def handle_events(self):
        # main reactor loop
        while True:
            events = self.sync_demultiplexer.select()
            for handle, mask in events:
                handle_event_callback = handle.data
                handle_event_callback(handle.fileobj, mask)


class EventHandler:
    def __init__(self, reactor):
        self.reactor = reactor

    def handle_event(self):
        raise NotImplemented


class AcceptEventHandler(EventHandler):
    def __init__(self, reactor):
        print("initializing Accept Event handler")
        super().__init__(reactor)

    def handle_event(self, socket, mask):
        conn, addr = self.reactor.sock.accept()
        print("accepted", conn.__str__(), "from", addr)
        conn.setblocking(False)
        self.reactor.register_handler(
            conn,
            selectors.EVENT_READ,
            ReadEventHandler(self.reactor, conn).handle_event,
        )


class ReadEventHandler(EventHandler):
    def __init__(self, reactor, connection):
        print("initializing Read Event handler")
        super().__init__(reactor)
        self.conn = connection

    def handle_event(self, socket, mask):
        try:
            data = self.conn.recv(1000)
            if data:
                print("echoing back:", repr(data), "to", self.conn)
                self.conn.send(data)
            else:
                print("closing", self.conn.__str__())
                self.reactor.remove_handler(self.conn)
                self.conn.close()

        except Exception as e:
            print("Connection closed:", self.conn, e)


if __name__ == "__main__":
    reactor = Reactor()
    reactor.handle_events()
