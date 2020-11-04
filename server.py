import binascii
import socket
import struct
import sys
import hashlib
import random
import time

UDP_IP = '127.0.0.1'
UDP_PORT = 5123


# 소켓 생성
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP,UDP_PORT))

responseSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("서버 준비 완료...\n")

# 패킷 해석
unpacker = struct.Struct("I I 8s 32s")
rData = struct.Struct('I I 32s')

#서버 딜레이랑 Loss 프린틍
def Network_Delay():
    if True and random.choice([0,1,0]) == 1: #여기서 1이면 딜레이 있는거라고 판단
        time.sleep(.01)
        print("딜레이 발생")
    else:
        print("패킷 보냄")

def Network_Loss():
    if True and random.choice([0,1,1,0]) == 1: #1이면 데이터 로스 발생 이라고 가정
        print("loss 발생")
        return(1)
    else:
        return(0)

#checksum 오류 발생
def Packet_Checksum_Corrupter(rcvpkt):
    if True and random.choice([0,1,0,1]) == 1:
        return(b'Corrupt!')
    else:
        return (rcvpkt)

#rpkt생성
def make_rpkt(ACK, SEQ, chkSum):
    chkSum_ToByte = chkSum.encode()
    # ACK/NAK 패킷 생성해서 보내기
    values = (rcvpkt[0], SEQ, chkSum_ToByte)
    sndpkt = rData.pack(*values)
    return sndpkt

# 첵섬 오류 수
Checksum_Error = 0
# 연결 계속 유지 해야 하므로 while 반복문으로 구성
while True:
    print("---------------------------------------------------------------")
    responseSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    data, addr = sock.recvfrom(1024)

    rcvpkt = unpacker.unpack(data)

    #정상적인 패킷 데이터 수신하고 서버에 띄움
    print("패킷 정상 수신완료")
    print(rcvpkt[0], rcvpkt[1], rcvpkt[2], rcvpkt[3])
    SEQ = rcvpkt[1]   #0은 ACK자리

    if rcvpkt[3] != 500:
        print("정상수신완료\n")
        if rcvpkt[1] == 1:
            SEQ = 0
        else:
            SEQ = 1

        #checksum 생성
        chkSum = str(random.random())  # 원랜 여기서 만들지 않겠지만.. 과제를 위해 여기서 만들었어요.
        sndpkt = make_rpkt(rcvpkt[0], SEQ, chkSum)

        #랜덤으로 딜레이 발생시키기
        Network_Delay()
        Network_Loss()
        responseSocket.sendto(sndpkt ,(UDP_IP, 7841))
        responseSocket.close()

    else:

        print("첵섬 오류 발생 재전송 요청")

        if rcvpkt[0] == 1:
            ACK = 0
        else:
            ACK = 1

        # 패킷 생성
        responseVal = (rcvpkt[0], SEQ, chkSum)
        UDP_Packet = rData.pack(*responseVal)
        Network_Delay()
        Network_Loss()
        responseSocket.sendto(UDP_Packet,(UDP_IP,7841))
        responseSocket.close()

        print("ACK 보내는중")

