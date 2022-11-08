from machine import Pin, PWM, Timer
import network
import usocket as socket
import _thread
import struct

moteur_1 = Pin(12, Pin.OUT)
moteur_2 = Pin(14, Pin.OUT)
moteur_1_pwm = PWM(moteur_1)
moteur_2_pwm = PWM(moteur_2)

azimuth = 0
update_engine = 0
timer = Timer(-1)
def timer_handler(timer):
    global update_engine
    update_engine = 1
timer.init(period = 10, mode = Timer.PERIODIC, callback = timer_handler)

# Connect to wifi
ssid = 'PPI-IMTNE'
password = 'PPI2022SN'
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)
while station.isconnected() == False:
    pass
print('Connection successful')
print(station.ifconfig())

# Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 4747))
server.listen(5)

def listen():
    global azimuth
    while True:
        print('Waiting for connection')
        conn, addr = server.accept()
        print('Got a connection from %s' % str(addr))
        while True:
            data = bytearray()
            error = False
            while len(data) < 4:
                request = conn.recv(4 - len(data))
                if not request:
                    error = True
                    break
                data += request
            if error:
                break
            azimuth = struct.unpack("f", data)[0]
            #print(azimuth)
        azimuth = 0
        
_thread.start_new_thread(listen, ())

while True:
    if update_engine:
        update_engine = 0
        
        duty = int(min(4000 * abs(azimuth), 1023))
        print(azimuth)
        if azimuth > 0:
            moteur_1_pwm.duty(duty)
            moteur_2_pwm.duty(0)
        else:
            moteur_1_pwm.duty(0)
            moteur_2_pwm.duty(duty)