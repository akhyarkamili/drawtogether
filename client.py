from twisted.internet import reactor
from twisted.internet.protocol import Factory, Protocol
from twisted.internet.protocol import ClientCreator

class Greeter(Protocol):
    def sendMessage(self, msg):
        self.transport.write("MESSAGE %s\n" % msg)

class GreeterFactory(Factory):
    def buildProtocol(self, addr):
        return Greeter()

def gotProtocol(p):
    print "reached"
    p.sendMessage("Hello")
    reactor.callLater(5, p.sendMessage, "This is sent in a second")
    reactor.callLater(2, p.transport.loseConnection)

creator = ClientCreator(reactor, Greeter)
d = creator.connectTCP("localhost", 15112)
d2 = 
d.addCallback(gotProtocol)
reactor.run()

print 'hello'