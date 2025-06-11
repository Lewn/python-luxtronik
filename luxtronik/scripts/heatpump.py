# -*- coding: utf-8 -*-
"""
@author: lloopik
"""

import socket
import xml.etree.ElementTree as ET

handshake = b"""\
GET / HTTP/1.1
Host: 192.168.6.157:8214
Sec-WebSocket-Version: 13
Sec-WebSocket-Protocol: Lux_WS
Sec-WebSocket-Key: ZZ+cWMQ/7pOM47nXyH58+w==
Upgrade: websocket

""".replace(b'\n',b'\r\n')

HOST = "192.168.6.157"
PORT = 8214

def send(s, message):
    print(" --> \n" + message)
    message = message.encode('utf-8')
    s.sendall(bytes([0x81, len(message)]) + message)
    print("\n\n")

def receive(s):
    frame = s.recv(2)

    assert frame[0] == 0x81, "Type not supported"
    assert frame[1] & 128 == 0, "Mask not supported"
    length = frame[1] & 127
    assert length < 127, "Super long messages not supported"
    if length == 126:
        frame += s.recv(2)
        length = (frame[2] << 8) + frame[3]

    res = b""
    while length > 0:
        buf = s.recv(min(length, 1024))
        length -= len(buf)
        res += buf
    res = res.decode('utf-8')
    print(" <-- \n" + res + "\n\n")
    return res

def dump_websocket(ip, port = PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST,PORT))
        print(handshake.decode())
        s.sendall(handshake)
        s.settimeout(1)
        data = s.recv(1024)
        print(data.decode())
        assert b"HTTP/1.1 101 Switching Protocols" in data, "Could not open websocket"

        send(s, "LOGIN;999999")
        data = receive(s)

        tree = ET.fromstring(data)

        for ch in tree:
            if ch.find('readOnly') is not None:
                continue

            navid = ch.attrib['id']

            print("=== Retrieving: ", ch.find('name').text)

            send(s, "GET;" + navid)
            receive(s)

if __name__ == '__main__':
    dump_websocket(HOST)
