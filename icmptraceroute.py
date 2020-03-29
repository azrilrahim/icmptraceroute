#!/usr/bin/python
#
# icmptraceroute.py 
# Copyright (C) 2020. Azril Rahim All Right Reserved
#
# Email:    azrilazam@gmail.com
# LinkedIn: https://www.linkedin.com/in/azril-rahim-93540a19/
# GitHub:   https://github.com/azrilrahim
#
# A complete article write up of this code can be found at GitHub
# https: https://github.com/azrilrahim/icmptraceroute
#  
# This code is to demonstrate the principle of trace using ICMP method
# This usage of this code:
#
# default: icmptraceroute.py <host name>
# option: -m <number> [number of hops. default is 30]
#
# This code is freely available and distributed under GNU Public License V3.0
#
# Revision 1: March 30 2020
#   :new code upload
#


import os
import struct
import socket
from ctypes import Structure
from ctypes import c_ubyte,c_ushort,c_uint32
import sys
import time


if (sys.platform == "win32") :
    DEFAULTTIMER = time.clock
else:
    DEFAULTTIMER = time.time


#IP Class
#This is to process IP Header Information
class IP(Structure):
    _fields_ = [
        ("version", c_ubyte,4),
        ("headerLength", c_ubyte,4), 
        ("tos", c_ubyte),
        ("packetLength", c_ushort),
        ("id", c_ushort),
        ("offset", c_ushort),
        ("ttl", c_ubyte),
        ("protocol", c_ubyte),
        ("checksum", c_ushort),
        ("srcIP", c_uint32),
        ("dstIP", c_uint32)
    ]
   
    def __new__(self,socket_buffer):
        return self.from_buffer_copy(socket_buffer)
    
    def __init__(self,socket_buffer=None):
        
        #this is the hop address that reply the ping
        self.TTL_ADDRESS = socket.inet_ntoa(struct.pack("<L", self.srcIP))
#end of class IP

#ICMP Class
#This is to process ICMP Header Information
class ICMP(Structure):
    _fields_ = [
        ("type", c_ubyte),
        ("code", c_ubyte),
        ("checksum", c_ushort),
        ("unused", c_ushort),
        ("next_hop_mtu", c_ushort)
    ]

    def __new__ (self,socket_buffer):
        return self.from_buffer_copy(socket_buffer)

    def __init__ (self,socket_buffer):
        pass
#End of class ICMP

#Ping function
def ping(pingSock,icmpSock,ttl_count, dest_host, port):
    
    global DEFAULTTIMER
    ipHeader = None
    icmpHeader = None
    sentTime = 0
    recievedTime = 0
    transitTime = 0

    #start the ping
    sentTime = DEFAULTTIMER()

    pingSock.setsockopt(socket.SOL_IP,socket.IP_TTL,ttl_count)
    try:
        pingSock.sendto("",(dest_host,port))
        response = icmpSock.recvfrom(512)[0]
    except socket.error as err:
        if err.errno == 35:
            print ("%d\t%15s" % (ttl_count, "***"))
            return 2 #filtered
        else:
            return 4 #network error

    recievedTime = DEFAULTTIMER()
    transitTime = int((recievedTime - sentTime) * 1000) #convert to ms

    #process the IP HEADER    
    ipHeader = IP(response[0:20])

    #Process the ICMP Header
    icmpHeader = ICMP(response[20:32])

    #display ping result
    print ("%d\t%15s     %dms" % (ttl_count,ipHeader.TTL_ADDRESS, transitTime))
    if icmpHeader.type == 11 :
        return 11 #continue
    return 0 #reach its destination

#End of PING function

#Trace route funtion
def traceroute(dest_host,port,max_hop):

    destHostName = None
    destHostAddr = None

    ttl_count = 1
    timeOut = struct.pack("ll", 5, 0) #5 seconds socket time out

    #get the hostname and hostaddr
    try:
        destHostName = dest_host
        destHostAddr = socket.gethostbyname(destHostName)
    except:
        try:
            destHostAddr = dest_host
            destHostName = socket.gethostbyaddr(destHostAddr)
        except:
            print("Error: %s is an invalid destination name\n" % dest_host)
            sys.exit(3)

    #create the socket handler
    icmpSock = socket.socket(socket.AF_INET, socket.SOCK_RAW,socket.IPPROTO_ICMP)
    icmpSock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVTIMEO,timeOut)

    #set ping socket into UDP mode instead of TCP
    pingSock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)

    #we need to bind the recieving icmp sock
    icmpSock.bind(("",port))
    ttl_count = 1

    print ("\nTracing Route for %s [%s] for maximum %d hop(s):" % (destHostName,destHostAddr, max_hop))
    print ("Hop\t%15s     Transit Time\n" % ("Routing address"))
    while True:
        status = ping(pingSock,icmpSock,ttl_count,destHostAddr,port)
        if (status == 0):
            print("\nPacket reached %s after %d hop(s)\n" % (dest_host,ttl_count))
            break
        
        if (status == 4):
            #network error
            print (" Error: Network Problem.Unable To Proceed\n")
            break

        if (ttl_count >= max_hop):
            print("\nPacket does not reached %s after %d hop(s)\n" % (dest_host,ttl_count))
            break
        #Add the TTL count by 1 so we can move to next HOP
        ttl_count = ttl_count + 1

    pingSock.close()
#End of Traceroute function

#The main function
def main (argv):

    #standard variable declaration
    dest_host = None
    max_hop = 30
    port = 33434
    arg = 0
    argMax = len(argv)
    try:
        while True:
            if (arg >= argMax):
                break

            if (argv[arg] == "-m"):
                #print ("%d: %s" % (arg, argv[arg]))
                #print ("%d: %s" % (arg+1, argv[arg+1]))    
                max_hop = int (argv[arg+1])
                arg = arg + 2
                continue
            else:
                dest_host = argv[arg]
                arg = arg + 1
                continue

            if (argv[arg] == "-b"):
                #print ("%d: %s" % (arg, argv[arg]))
                #print ("%d: %s" % (arg+1, argv[arg+1]))   
                max_hop = int (argv[arg+1])
                arg = arg + 2
                continue
            else:
                dest_host = argv[arg]
                arg = arg + 1
                continue

            arg = arg + 1
    except:
        print("Error: invalid or missing value for %s" % argv[arg])
        sys.exit(2)

    #let do the traceroute
    traceroute(dest_host,port,max_hop)

#End of main function


#The main
if __name__ == "__main__":
    main(sys.argv[1:])
