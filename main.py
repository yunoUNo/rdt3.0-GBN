import socket
import random
import time
import _thread


#각종 변수
error = 0
fail_error = 100   # 실패시에 수신할 시퀀스 넘버 입니다.
filename = 'yuno.txt'
TIMEOUT_ERROR = 0
running = 0   # 총 패킷 보낸 횟수
pkt_No = 0
# 소켓 생성
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock.bind(("127.0.0.1", 7841))

# 스레드 변수

mutex = _thread.allocate_lock()

## ip랑 포트넘버 자꾸 틀리게 작성하게 되길래 그냥 저장해놨어요 안씁니다 안까먹으려고 한거에요!
MyIP = "127.0.0.1"
MyPort = 5123

# SEQ, ACK
SEQ = 0
ACK = 0

# timer에 쓰이는 변수
time_interval = 0.001#random.uniform(0.008,0.012) # 유니폼분포로 생성
start_time = time.time()
stop_time =start_time + time_interval
num = 0
result = 0
sleeptime = 0.09   #대기시간

#GBN 변수들
send_base = 0
pkt_array = []
error_seq = 0
send_window = 4 + send_base

#-------------------------packet-----------------------------------------------------------#
def make_pkt(SEQ, data = b''):   # checksum은 패킷에 포함 안 시키고 랜덤으로 발생시켜서 오류 잡아낼겁니다.
    print("패킷 생성중...")
    seq_bytes = SEQ.to_bytes(4, byteorder='little', signed=True)
    return seq_bytes + data

def make_falsePkt(fail_error, data = b''):
    print("오류 패킷 생성중...")
    seq_bytes = fail_error.to_bytes(4, byteorder='little', signed = True)
    return seq_bytes + data

def make_windowPkt():
    return b''

def extract(rcvpkt):
    seq_num = int.from_bytes(rcvpkt[0:4], byteorder = 'little', signed = True)
    return seq_num, rcvpkt[4:]
#------------------------------------------------------------------------------------------#

#-------------------------UDT--------------------------------------------------------------#
def udp_send(sndpkt,sock):   #여기서 loss와 biterror를 검출 합니다.
    sock.sendto(sndpkt, (MyIP,MyPort))
    return

def udp_rcv(sock):
    rcvpkt, addr = sock.recvfrom(5016)
    return rcvpkt, addr
#------------------------------------------------------------------------------------------#

#--------------------------rdt-------------------------------------------------------------#
def rdt_send(data, sock):
    global error, SEQ, mutex, TIMEOUT_ERROR, running, sndpkt, pkt_No

    # Receiver Thread
    _thread.start_new_thread(rdt_rcv,(sock,sndpkt ))
    # 실험을 위한 fileopen
    try:
        file = open(filename, 'rb')
    except IOError:
        print('파일 오픈 오류... 뭐가 문제지?', filename)
        return

    while True:
        mutex.acquire()
        num = random.randint(1, 1000)   # 오류 발생률 1/1000
        data = file.read(100)
        pkt_No += 1
        if not data:
            break
        #-------------------------------------패킷 보내는 부분-------------------------------------#
        if num == 100:
            sndpkt = make_falsePkt(fail_error, data)  # seqNum을 100 으로 했기 때문에 정상 수신이 되지 않음.
            print("Loss 발생 상황!")
            error += 1
            running += 1
            udp_send(sndpkt, sock)

        else:  # 정상적으로 수신될 때 정상 패킷 생성 합니다.
            sndpkt = make_pkt(SEQ, data)  # 정상 패킷 만들때는 제대로된 SEQ와 makepkt함수 사용.
            print(" 정상 패킷 생성 완료 정상 수신...",SEQ)
            running += 1
            udp_send(sndpkt, sock)

        # timer 시작해서 보내기
        if result == 0:
            start_timer()
            print("timer 재는중")
        # -------------------------------------ACK 받을 때 까지 wait----------------------------------#
        while result != 0 and not timeout(time_interval):
            mutex.release()
            print("ACK 기다리는중...")
            time.sleep(sleeptime)
            mutex.acquire()

        if timeout(time_interval):
            print("Timeout...재전송 합니다")
            TIMEOUT_ERROR += 1
            running += 1
            stop_timer()
            udp_send(sndpkt,sock)
        mutex.release()

    print("error: ", error)
    print("TIMEOUT: ", TIMEOUT_ERROR)
    print("패킷 만든 수: ", pkt_No)

def rdt_rcv(sock, sndpkt):   #sndpkt를 넣은 이유는 오류 났을때 이전에 생성한 sndpkt를 저장해 놓기 위함입니다.
    global mutex,SEQ

    while True:
        rcvpkt, _ = udp_rcv(sock)
        ack, _ = extract(rcvpkt)
    # 서버 스레드 시작
        print('\nACK 받음: ', ack)
        print("\n")
        if( ack == SEQ):
            mutex.acquire()
            print("정상 수신 완료.")
            if SEQ == 0:
                SEQ += 1
            else:
                SEQ -= 1
            stop_timer()
            print("---------------------------------------------")
            mutex.release()
        else:
            mutex.acquire()
            print("잘못된게 왔네용")
            udp_send(sndpkt,sock)
            print("재전송 했습니다.")
            mutex.release()

#------------------------------------------------------------------------------------------#

#--------------------------------timer-----------------------------------------------------#
def start_timer():
    global result
    result = time.time()

def stop_timer():
    global result
    result = 0

def timeout(time_interval):
    global result
    if result == 0:
        return False
    else:
        return time.time() - result >= time_interval
#------------------------------------------------------------------------------------------#

#-------------------------------------gbn_rdt,rcv------------------------------------------#
def gbn_rdt_send(filename, sock):
    global error, SEQ, mutex, send_base, pkt_array, TIMEOUT_ERROR, running, error_seq, send_window

    try:
        file = open(filename, 'rb')
    except IOError:
        print("파일 오픈 오류 발생: ", filename)
        return

    # pacets을 우선 패킷 버퍼에 전부 넣어놓습니다.

    SEQ = 0
    while True:
        data = file.read(100)
        if not data:
            break

        sndpkt = make_pkt(SEQ, data)
        pkt_array.append(sndpkt)
        SEQ += 1

    print("패킷 수", len(pkt_array))
    window_size = 50
    next_seq = 0   # 처음이 0번 패킷

    #리시버 스레드 시작
    _thread.start_new_thread(gbn_rdt_rcv, (sock, ))

    while send_base < len(pkt_array):
        mutex.acquire()

        for i in range(send_base, send_base + send_window):
            num = random.randint(1, 1000)

            #가짜기 때문에 시퀀스넘버가 증가하지도 않고 여기서부터 ACK가 오지 않기 때문에 다음에 이것이 send_base가 될겁니다.
            if num == 999:
                print("에러 발생 에러 패킷 보냅니다..")
                error += 1
                udp_send(pkt_array[next_seq+1], sock)   # 패킷 번호를 하나 높여서 보냅니다.
                error_seq = next_seq
            else:
                print("정상 패킷 보내는중", next_seq)
                print("next_seq", next_seq)
                udp_send(pkt_array[next_seq], sock)
                next_seq += 1

        # timer 시작해서 보내기
        if result == 0:
            start_timer()
            print("timer 재는중")
            # -------------------------------------ACK 받을 때 까지 wait----------------------------------#
        while result != 0 and not timeout(time_interval):
            mutex.release()
            print("ACK 기다리는중...")
            time.sleep(sleeptime)   # 패킷을 보내는 사이의 시간 rtt는 아닌데..
            mutex.acquire()

        if timeout(time_interval):
            print("Timeout...재전송 합니다")
            TIMEOUT_ERROR += 1
            running += 1
            stop_timer()
            next_seq = send_base

        else:
            print("윈도우 이동!")
            window_size += send_window   # ack 받은 만큼 옆으로 이동.

        mutex.release()
    print("error: ", error)
    udp_send(make_windowPkt(), sock, ("127.0.0.1", 5123))   # 빈 윈도우 채우는거 sendwindow 아닙니다.
    print("빈패킷 보냄...")
    file.close()


def gbn_rdt_rcv(sock):
    global send_base, mutex

    while True:
        rcvpkt, _ = udp_rcv(sock)
        ack, _ = extract(rcvpkt)

        #정상 수신 일 때
        print("ACK 받음...", ack)
        if (ack >= send_base):
            mutex.acquire()
            send_base = ack + 1   #베이스를 정상으로 받은 ack에서 1 올립니다.
            stop_timer()
            mutex.release()

        #비정상 수신 일 때
        else:
            mutex.acquire()
            print("잘못된 ACK 받음")
            send_base = ack
            stop_timer()
            mutex.release()


'''------------rdt3.0실행-------------------
sndpkt = make_pkt(SEQ,b'yuno')
rdt_send(filename, sock)
----------------------------------------'''

'''GBN 실행---------------------------
gbn_rdt_send(filename,sock)
-----------------------------------'''

#---------------------------------------
filename = "yuno.txt"
gbn_rdt_send(filename,sock)
sock.close()
