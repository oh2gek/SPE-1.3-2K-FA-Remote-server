# SPE amplifiers remote control server by OH2GEK
# This python program communicates with SPE Expert amplifiers via USB or RS-232 serial port
# and creates Websocket server to communicate with different clients.
# I have been tested it with Web client and ESP8266 based device.
# By default server is listening port :8888 for clients. Project is built and tested with
# Raspberry Pi 2. Python version 2.7.13. Also you need python-serial and Tornado version 4.5.3.
#  (sudo apt-get install python-serial && sudo python -m pip install tornado==4.5.3)
# For some reason I did't get it work with Tornado version 5.x
#
# I also have been running web server on same raspi (Lighttpd or apache) to run web client.
# Copy content in WEB folder to your web server root folder and change in index.html code from
# ( ws = new WebSocket("ws://YOUR.SERVER.IP:8888/ws") to match your server IP/name setup.
#
#
import struct
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import tornado.gen
import time
import thread
import serial
import json
from tornado import gen
from tornado.ioloop import IOLoop
ser = serial.Serial('/dev/ttyUSB0', 115200) #Serial port setup
print (":::Server Started:::")
json_last_time = " "
user_connected = False
setup_operate = False
setup_antenna = False
setup_input = False
setup_tune = False
setup_gain = False
con_trig=False
time_for_tx = True;
def server_task(out_q_2, in_w_1):
 class WSHandler(tornado.websocket.WebSocketHandler):
  def check_origin(self, origin):
    return True

  def simple_init(self):
        self.last = time.time()
        self.stop = False

  def open(self):
    global user_connected
    global con_trig
    global tx_speed
    con_trig=True
    user_connected = True
    self.simple_init()
    self.loop = tornado.ioloop.PeriodicCallback(self.check_ten_seconds, 200, io_loop=tornado.ioloop.IOLoop.instance())
    self.loop.start()
    ser.close()
    ser.open()
    print 'New user connected...'

  def on_message(self, message):
    global setup_operate
    global setup_antenna
    global setup_input
    global setup_tune
    global setup_gain
    if message == "oper":
     setup_operate = True
    elif message == "antenna":
     setup_antenna = True
    elif message == "input":
     setup_input = True
    elif message == "gain":
     setup_gain = True
    elif message == "tune":
     setup_tune = True

  def on_close(self):
    global user_connected
    user_connected = False
    self.loop.stop()
    ser.close()
    print 'Connection was closed...'

  def check_ten_seconds(self):
    global json_stream
    global json_last_time
    global con_trig
    global time_for_tx
    if (json_stream != json_last_time or time.time() > self.last + 15 or con_trig == True):
     con_trig=False
     time_for_tx = True
     self.last = time.time()
     json_last_time = json_stream
     self.write_message(json_stream)

 application = tornado.web.Application([
  (r'/ws', WSHandler),
 ])

 if __name__ == "__main__":
  http_server = tornado.httpserver.HTTPServer(application,max_body_size=128)
  http_server.listen(8888) #Port to listen for clients
  tornado.ioloop.IOLoop.instance().start()


def serial_task(in_q, out_w):
 global json_stream
 global user_connected
 global setup_operate
 global setup_antenna
 global setup_input
 global setup_tune
 global setup_gain
 global time_for_tx
 global tx_speed
 timeout = time.time() + 5
 data = []
 tx = 1
 ser.close()
 ser.open()
 ser.flushInput()
 request   = "\x55\x55\x55\x01\x90\x90"
 comoper  = "\x55\x55\x55\x01\x0D\x0D"
 comant   = "\x55\x55\x55\x01\x04\x04"
 cominput = "\x55\x55\x55\x01\x01\x01"
 comtune  = "\x55\x55\x55\x01\x09\x09"
 comgain  = "\x55\x55\x55\x01\x0b\x0b"
 ser.write(request)
 json_stream = " "
 while 1:
     try:
        if ser.isOpen and setup_operate and  ser.inWaiting() < 1:
         setup_operate = False
         ser.write(comoper)
         ser.write(request)
         print "Toggel operate"
        if ser.isOpen and setup_antenna and  ser.inWaiting() < 1:
         setup_antenna = False
         ser.write(comant)
         ser.write(request)
         print "Toggel antenna"
        if ser.isOpen and setup_input and  ser.inWaiting() < 1:
         setup_input = False
         ser.write(cominput)
         ser.write(request)
         print "Toggel input"
        if ser.isOpen and setup_tune and  ser.inWaiting() < 1:
         setup_tune = False
         ser.write(comtune)
         ser.write(request)
         print "Set Tune"
        if ser.isOpen and setup_gain and  ser.inWaiting() < 1:
         setup_gain = False
         ser.write(comgain)
         ser.write(request)
         print "Toggel gain"

	if ser.isOpen():
         test = 0
         if ser.inWaiting() > 0:
          result = ser.readline()
          data = result.split(",")
	  if len(data) == 22:
           if data[21]=="\r\n":
	    if data[2] =="O":
	     op_status = "Oper"
	    elif data[2] =="S":
	     op_status = "Stby"

            if data[3] =="R":
             tx_status = "RX"
            elif data[3] =="T":
             tx_status = "TX"

	    if data[6] =="00":
             band = "160m"
            elif data[6] =="01":
             band = "80m"
 	    elif data[6] =="02":
             band = "60m"
	    elif data[6] =="03":
             band = "40m"
	    elif data[6] =="04":
             band = "30m"
	    elif data[6] =="05":
             band = "20m"
	    elif data[6] =="06":
             band = "17m"
	    elif data[6] =="07":
             band = "15m"
	    elif data[6] =="08":
             band = "12m"
	    elif data[6] =="09":
             band = "10m"
	    elif data[6] =="10":
             band = "6m"
	    elif data[6] =="11":
             band = "4m"



	    if data[18] =="M":
             warn = "ALARM AMPLIFIER"
            elif data[18] =="A":
             warn = "NO SELECTED ANTENNA"
            elif data[18] =="S":
             warn = "SWR ANTENNA"
            elif data[18] =="B":
             warn = "NO VALID BAND"
            elif data[18] =="P":
             warn = "POWER LIMIT EXCEEDED"
            elif data[18] =="O":
             warn = "OVERHEATING"
            elif data[18] =="Y":
             warn = "ATU NOT AVAILABLE"
            elif data[18] =="W":
             warn = "TUNING WITH NO POWER"
            elif data[18] =="K":
             warn = "ATU BYPASSED"
            elif data[18] =="R":
             warn = "POWER SWITCH HELD BY REMOTE"
            elif data[18] =="T":
             warn = "COMBINER OVERHEATING"
	    elif data[18] =="C":
             warn = "COMBINER FAULT"
            elif data[18] =="N":
             warn = " "

	    if data[19] =="S":
             error = "SWR EXCEEDING LIMITS"
            elif data[19] =="A":
             error = "AMPLIFIER PROTECTION"
            elif data[19] =="D":
             error = "INPUT OVERDRIVING"
            elif data[19] =="H":
             error = "EXCESS OVERHEATING"
            elif data[19] =="C":
             error = "COMBINER FAULT"
            elif data[19] =="N":
             error = " "

            json_stream =json.dumps({"op_status":op_status,"tx_status":tx_status,"input":data[5],"band":band,"tx_antenna":data[7],"p_level":data[9],"p_out":data[10],"swr":data[11],"voltage":data[13],"drain":data[14],"pa_temp":data[15],"warnings":warn,"error":error,"aswr":data[12]})
          #Uncommet to see parsed data from amplifier...
	  # print 'ping'
          # print ("Operating status: "+data[2])
          # print ("TX status: "+data[3])
          # print ("Mem: "+data[4])
          # print ("Input: "+data[5])
          # print ("Band: "+data[6])
          # print ("TX antenna: "+data[7])
          # print ("RX antenna: "+data[8])
          # print ("Level: "+data[9])
          # print ("Power out: "+data[10])
          # print ("TSWR: 1:"+data[11])
          # print ("ASWR: 1:"+data[12])
          # print ("Voltage: "+data[13])
          # print ("Drain: "+data[14])
          # print ("PA temp: "+data[15])
          # print ("Warnings: "+data[18])
          # print ("Errors: "+data[19])
            data = []
            tx=0
            timeout = time.time() + 1



	 if ser.inWaiting() < 1 and tx == 0 and (tx_status == "TX" or op_status == "Oper") :
          if ser.isOpen() == True:
           ser.write(request)
           time_for_tx  = False
          tx=1
         if ser.inWaiting() < 1 and tx == 0 and time_for_tx == True and tx_status == "RX":
          if ser.isOpen() == True:
	   ser.write(request)
	   time_for_tx  = False
          tx=1
         if  time.time() > timeout and ser.isOpen() == True:
            timeout = time.time() + 1
            tx=1
            ser.write(request)
         test = test - 1
	if user_connected == True and ser.isOpen() == False:
         ser.close()
         ser.open()
         ser.flushInput()
         ser.write(request)
	 timeout = time.time() + 1
         print("COM open for user...")

        if user_connected == False and ser.isOpen() == True:
         ser.close()
         print("COM closed...")
     except:
	print 'Oho!'

try:
   thread.start_new_thread( server_task, (1, 1, ) )
   thread.start_new_thread( serial_task, (1, 1, ) )
except:
   print "Error: unable to start thread"

while 1:
   pass

