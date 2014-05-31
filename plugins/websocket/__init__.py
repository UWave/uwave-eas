#!/usr/bin/env python

import __main__
import websocket

def send_alert(msg):
    try:
        ws = websocket.create_connection('wss://127.0.0.1:4444/primus')
        websock_msg = '{"type": "alert", "title": "EAS Alert", "link": "", "color": "%s", "message": "%s", "expires": %d}' % \
            (msg.webcolor(), msg.description(), msg.expires() * 1000)
        print 'Sending: ', websock_msg
        ws.send(websock_msg)
        ws.close()
    except:
        print "Unexpected error sending web alert:", sys.exc_info()[0]

__main__.alert_sent_hooks.append(send_alert)
