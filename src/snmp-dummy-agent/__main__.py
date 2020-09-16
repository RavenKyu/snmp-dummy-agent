##########################################################################################
from pysnmp.entity import engine, config
from pysnmp import debug
from pysnmp.entity.rfc3413 import cmdrsp, context, ntforg
from pysnmp.carrier.asynsock.dgram import udp
from pysnmp.smi import builder

import threading
import collections
import time

# can be useful
# debug.setLogger(debug.Debug('all'))

##########################################################################################
MibObject = collections.namedtuple('MibObject', ['mibName',
                                                 'objectType', 'valueGetFunc', 'valueSetFunc'])


##########################################################################################
class CustomMib(object):
    """Stores the data we want to serve.
    """

    # =====================================================================================
    def __init__(self):
        self._lock = threading.RLock()
        self._test_count = 0

    # =====================================================================================
    def getTestDescription(self):
        return "My Description [%s]" % self._test_count

    # =====================================================================================
    def getTestCount(self):
        with self._lock:
            return self._test_count

    # =====================================================================================
    def setTestCount(self, value):
        with self._lock:
            self._test_count = value


##########################################################################################
def createVariable(SuperClass, getValue, setValue, *args):
    """This is going to create a instance variable that we can export.
    getValue is a function to call to retreive the value of the scalar
    """

    # =====================================================================================
    class Var(SuperClass):
        def readGet(self, name, *args):
            # print "	Getting var..."
            return name, self.syntax.clone(getValue())

        # =====================================================================================
        def writeTest(self, name, *args):
            # print " Testing var..."
            pass

        # =====================================================================================
        def writeCommit(self, name, val, *args):
            # print " Setting var..."
            setValue(val)

    return Var(*args)


##########################################################################################
class SNMPAgent(object):
    """Implements an Agent that serves the custom MIB and
    can send a trap.
    """

    # =====================================================================================
    def __init__(self, mibObjects):
        """
        mibObjects - a list of MibObject tuples that this agent
        will serve
        """
        # each SNMP-based application has an engine
        self._snmpEngine = engine.SnmpEngine()

        # open a UDP socket to listen for snmp requests
        config.addSocketTransport(self._snmpEngine, udp.domainName,
                                  udp.UdpTransport().openServerMode(('', 161)))

        # add a v2 user with the community string public
        config.addV1System(self._snmpEngine, "my-read-area", "public")
        config.addV1System(self._snmpEngine, 'my-write-area', 'private')

        # let anyone accessing 'public' read anything in the subtree below,
        # which is the enterprises subtree that we defined our MIB to be in
        config.addVacmUser(self._snmpEngine, 2, "my-read-area", "noAuthNoPriv",
                           readSubTree=(1, 3, 6, 1, 4, 1))

        # Allow full MIB access for this user / securityModels at VACM
        config.addVacmUser(self._snmpEngine, 2, 'my-write-area', 'noAuthNoPriv',
                           readSubTree=(1, 3, 6, 1, 4, 1), writeSubTree=(1, 3, 6, 1, 4, 1))

        # each app has one or more contexts
        self._snmpContext = context.SnmpContext(self._snmpEngine)

        # the builder is used to load mibs. tell it to look in the
        # current directory for our new MIB. We'll also use it to
        # export our symbols later
        mibBuilder = self._snmpContext.getMibInstrum().getMibBuilder()
        mibSources = mibBuilder.getMibSources() + (builder.DirMibSource('.'),) + (
        builder.DirMibSource('/root/.pysnmp/mibs'),)
        mibBuilder.setMibSources(*mibSources)

        # our variables will subclass this since we only have scalar types
        # can't load this type directly, need to import it
        MibScalarInstance, = mibBuilder.importSymbols('SNMPv2-SMI',
                                                      'MibScalarInstance')
        # export our custom mib
        for mibObject in mibObjects:
            nextVar, = mibBuilder.importSymbols(mibObject.mibName,
                                                mibObject.objectType)
            instance = createVariable(MibScalarInstance,
                                      mibObject.valueGetFunc,
                                      mibObject.valueSetFunc,
                                      nextVar.name, (0,),
                                      nextVar.syntax)
            # need to export as <var name>Instance
            instanceDict = {str(nextVar.name) + "Instance": instance}
            mibBuilder.exportSymbols(mibObject.mibName,
                                     **instanceDict)

        # tell pysnmp to respotd to get, getnext, and getbulk
        cmdrsp.GetCommandResponder(self._snmpEngine, self._snmpContext)
        cmdrsp.SetCommandResponder(self._snmpEngine, self._snmpContext)
        cmdrsp.NextCommandResponder(self._snmpEngine, self._snmpContext)
        cmdrsp.BulkCommandResponder(self._snmpEngine, self._snmpContext)

    # =====================================================================================
    def setTrapReceiver(self, host, community):
        """Send traps to the host using community string community
        """
        config.addV1System(self._snmpEngine, 'nms-area', community)
        config.addVacmUser(self._snmpEngine, 2, 'nms-area', 'noAuthNoPriv',
                           notifySubTree=(1, 3, 6, 1, 4, 1))
        config.addTargetParams(self._snmpEngine,
                               'nms-creds', 'nms-area', 'noAuthNoPriv', 1)
        config.addTargetAddr(self._snmpEngine, 'my-nms', udp.domainName,
                             (host, 162), 'nms-creds',
                             tagList='all-my-managers')
        # set last parameter to 'notification' to have it send
        # informs rather than unacknowledged traps
        config.addNotificationTarget(
            self._snmpEngine, 'test-notification', 'my-filter',
            'all-my-managers', 'trap')

    # =====================================================================================
    def sendTrap(self):
        print("Sending trap")
        ntfOrg = ntforg.NotificationOriginator(self._snmpContext)
        errorIndication = ntfOrg.sendNotification(
            self._snmpEngine,
            'test-notification',
            ('MY-MIB', 'testTrap'),
            ())

    # =====================================================================================
    def serve_forever(self):
        print("Starting agent")
        self._snmpEngine.transportDispatcher.jobStarted(1)
        try:
            self._snmpEngine.transportDispatcher.runDispatcher()
        except:
            self._snmpEngine.transportDispatcher.closeDispatcher()
            raise


##########################################################################################
class Worker(threading.Thread):
    """Just to demonstrate updating the MIB
    and sending traps
    """

    def __init__(self, agent, mib):
        threading.Thread.__init__(self)
        self._agent = agent
        self._mib = mib
        self.setDaemon(True)

    def run(self):
        while True:
            time.sleep(3)
            customMib.setTestCount(customMib.getTestCount() + 1)
            agent.sendTrap()


##########################################################################################
if __name__ == '__main__':
    customMib = CustomMib()
    objects = [MibObject('MY-MIB', 'testDescription', customMib.getTestDescription, ''),
               MibObject('MY-MIB', 'testCount',
                         customMib.getTestCount, customMib.setTestCount), ]
    # MibObject('MY-MIB', 'ledControl', customMib.getTestCount, '')]
    agent = SNMPAgent(objects)
    agent.setTrapReceiver('192.168.189.138', 'traps')
    # Worker(agent, customMib).start()
    try:
        agent.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down")