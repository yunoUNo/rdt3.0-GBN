import socket


# 각종 변수
error = 0  # error
fail_error = 100  # 실패시에 수신할 시퀀스 넘버 입니다.

# 소켓 생성
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", 5123))

# SEQ, ACK
SEQ = 0
ACK = 0

# timer에 쓰이는 변수
start_time = 0
stop_time = -1
time_interval = 0.09


# -------------------------packet-----------------------------------------------------------#
def make_pkt(SEQ):  # receiver는 SEQ만 보내면 댑니다. chksum은 sender와 똑같은 방법으로 검출
    print("r패킷 생성중...")
    seq_bytes = SEQ.to_bytes(4, byteorder='little', signed=True)
    return seq_bytes


def make_falsePkt(fail_error):
    print("r오류 패킷 생성중...")
    seq_bytes = fail_error.to_bytes(4, byteorder='little', signed=True)
    return seq_bytes


def extract(rcvpkt):
    seq = int.from_bytes(rcvpkt[0:4], byteorder='little', signed=True)
    return seq, rcvpkt[4:]


# ------------------------------------------------------------------------------------------#

# -------------------------UDT--------------------------------------------------------------#
def udp_send(sndpkt, sock, addr):  # 여기서 loss와 biterror를 검출 합니다.
    sock.sendto(sndpkt, addr)
    return


def udp_rcv(sock):
    rcvpkt, addr = sock.recvfrom(5016)
    return rcvpkt, addr


# ------------------------------------------------------------------------------------------#

# ----------------------------------------rdt-----------------------------------------------#
def rdt_rcv(filename, sock):
    global error
    collect = 0
    try:
        file = open(filename, 'wb')
        print("파일 오픈 완료")
    except IOError:
        print("파일 왜 또 안열려 ㅠㅠ..: ", filename)
        return

    while True:
        rcvpkt, addr = udp_rcv(sock)
        if not rcvpkt:
            print("전송 끝 종료합니다...")
            break
        rSEQ, data = extract(rcvpkt)
        print("패킷 수신 완료: ", rSEQ)

        # ACK 보내는부분
        if rSEQ == 100:
            print("Error가 왔네용")
            print("Error 잘못된 ACK를 보냅니당.", rSEQ)
            error += 1
            sndpkt = make_falsePkt(fail_error)
            udp_send(sndpkt, sock, addr)

        elif rSEQ == collect:
            print("정상 수신완료.")
            print("진짜 제대로된 패킷 ACK보냅니당.", rSEQ)
            sndpkt = make_pkt(rSEQ)
            file.write(data)
            udp_send(sndpkt, sock, addr)

            if collect == 0:
                collect += 1
            else:
                collect -= 1
    file.close()


# ------------------------------------------------------------------------------------------#

# --------------------------------------gbn_rdt---------------------------------------------#
def gbn_rdt_rcv(filename, sock):
    global error
    correct = 0
    try:
        file = open(filename, 'wb')
        print("파일 오픈 완료")
    except IOError:
        print("파일 오픈 오류: ", filename)
        return

    while True:
        rcvpkt, addr = udp_rcv(sock)
        if not rcvpkt:
            print("전송 받은 패킷이 없습니다...\n 시스템종료")
            break
        rSEQ, data = extract(rcvpkt)
        print("패킷 수신 완료: ", rSEQ)

        # ACK 보내기
        if rSEQ == correct:  # 한번 오류를 받기 시작하면 뒤에도 계속 오류 입니다. sr이랑 다르게 구현함.
            print("정상 수신 완료")
            print("ACK를 sender 에게 보내는중", correct)
            sndpkt = make_pkt(correct)
            udp_send(sndpkt, sock, addr)
            correct += 1
            file.write(data)
        else:
            print("비정상 수신")
            print("비정상 ACK를 sender 에게 보내는중", rSEQ)
            sndpkt = make_pkt(rSEQ)
            udp_send(sndpkt, sock, addr)


# ----------------------------------------------------------------------------------#
filename = "yuno.txt"
'''--------------rdt실행-------------
rdt_rcv(filename, sock)
----------------------------------'''

'''--------------gbn실행-------------
gbn_rdt_rcv(filename, sock)
----------------------------------'''
gbn_rdt_rcv(filename, sock)
sock.close()
