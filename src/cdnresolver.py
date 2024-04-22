# cdnresolver.py - Contains CDNResolver, for use in dnsserver script

# +-----------+
# |  Imports  |
# +-----------+
import socket
from dnslib import DNSRecord, QTYPE, RCODE, RR
from dnslib.server import DNSServer, DNSHandler, BaseResolver, DNSLogger

# +-------------+
# |  Constants  |
# +-------------+
EDGE_CONFIG = open('.config/http.config', 'r')
EDGE_HOSTS  = EDGE_CONFIG.readlines() 
EDGE_CONFIG.close()
N_EDGES = len(EDGE_HOSTS)



# +----------------+
# |  CDN Resolver  |
# +----------------+
class CDNResolver(BaseResolver):
    # -- Constructor --
    # > Creates a CDN Resolver, that plugs into a DNS Server 
    #   and resolves only A queries to name
    # > Uses round-robin approach to distribute queries among
    #   edge servers specified in EDGE_SERVERS
    def __init__(self, name):
        # Arguments for superclass
        self.timeout = 60 
        self.strip_aaaa = False

        self.name = name
        # Get all IPs for edge servers
        self.EDGE_ADDRS = []
        for host in EDGE_HOSTS:
            self.EDGE_ADDRS.append(socket.gethostbyname(host))

        # Current index into EDGE_ADDRS (for round-robin)
        self.edge_index = 0

    # -- Resolve --
    # > Resolves a DNS request 
    def resolve(self, request, handler):
        # Generate a reply to the request
        qname = request.q.qname 
        qtype = QTYPE[request.q.qtype]
        reply = request.reply()

        # Only resolve A queries for self.name 
        if self.name in str(qname):
            rr_to_add = RR.fromZone(f'{self.name} 60 A {self.EDGE_ADDRS[self.edge_index]}')
            reply.add_answer(*rr_to_add)
            self.edge_index = (self.edge_index + 1) % N_EDGES   # Round-robin
        
        # Return reply
        return reply 
