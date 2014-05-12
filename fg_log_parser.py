#!/usr/local/bin/python2.7
""" Fortigate Log Parser

Usage: fg_log_parser.py
  fg_log_parser.py (-f <logfile> | --file <logfile>)

Options:
    -h --help   Show this message.
    --version  shows version information
"""
__author__ = 'olivier'

import shlex
from docopt import docopt
import os.path


def read_fg_firewall_log(logfile):
    """
    Reads fortigate firewall log line.
    Returns a list with dictionaries per line
    """
    KVDELIM = '='  # key and value deliminator
    try:
        fh = open(logfile, "r")
    except Exception, e:
        print "Error: file %s not readable" % (logfile)
        print e.message
        quit(2)

    loglist = []

    for line in fh:
        # lines are splited with shlex to recognise embeded substrings
        # such as key="valword1 valword2"
        keyvalues = {}
        for field in shlex.split(line):
            key, value = field.split(KVDELIM)
            keyvalues[key] = value
        loglist.append(keyvalues)
        keyvalues = {}
    fh.close()
    return loglist


def get_ips(loglist, source=True, dest=False):
    """
    returns list of either source or destination ip adresses
    """
    iplist = []
    if source:
        IPTYPE = 'srcip'
    elif dest:
        IPTYPE = 'dstip'

    for item in loglist:
        iplist.append(item[IPTYPE])
    return iplist


def translate_protonr(protocolnr):
    """
    Translates port nr as names.
    Example: 6 should return "TCP"
    """
    if int(protocolnr) == 1:
        return "ICMP"   # icmp has protonr 1
    elif int(protocolnr) == 6:
        return "TCP"    # tcp has protonr 6
    elif int(protocolnr) == 17:
        return "UDP"    # udp has protonr 17
    else:
        return protocolnr


def get_communication_matrix(parsedlog):
    """
    calculates a communication matrix
    from fortigate logs
    """
    # sets contain no duplicate values
    srclist = set(get_ips(parsedlog, source=True))

    matrix = {}
    """
    for loop creates a dictionary with multiple levels
    l1: srcips (source ips)
        l2: dstips (destination ips)
            l3: dstport (destination port number)
                l4: proto (protocoll number)
                    l5: occurence count
    """
    for src in srclist:
        if src in matrix:
            pass
        else:
            matrix[src] = {}
        for logline in parsedlog:
            if logline['srcip'] == src:
                dstip = logline['dstip']
                dstport = logline['dstport']
                proto = translate_protonr(logline['proto'])
                # sentbyte = logline['sentbyte'] # not used now
                # rcvdbyte = logline['rcvdbyte'] # not used now
                if dstip not in matrix[src]:
                    matrix[src][dstip] = {}
                    if dstport not in matrix[src][dstip]:
                        matrix[src][dstip][dstport] = {}
                        if proto not in matrix[src][dstip][dstport]:
                            matrix[src][dstip][dstport][proto] = 1
                elif proto in matrix[src][dstip][dstport]:
                    matrix[src][dstip][dstport][proto] += 1
    return matrix


def print_communication_matrix(matrix, indent=0):
    """
    prints the communication matrix in a nice format
    """
    # pprint(matrix)
    # json.dumps(matrix, sort_keys=True, indent=4)
    for key, value in matrix.iteritems():
        print '\t' * indent + str(key)
        if isinstance(value, dict):
            print_communication_matrix(value, indent+1)
        else:
            print '\t' * (indent+1) + str(value)
    return None


def main():
    """
    main function
    """
    # gets arguments from docopt
    arguments = docopt(__doc__)
    arguments = docopt(__doc__, version='Fortigate Log Parser 0.1')
    # assigns docopt argument to logfile
    logfile = arguments['<logfile>']

    if logfile is None:
        print __doc__
        quit(2)

    # parse fortigate log
    parsedlog = read_fg_firewall_log(logfile)
    matrix = get_communication_matrix(parsedlog)
    print_communication_matrix(matrix)

if __name__ == "__main__":
    main()
