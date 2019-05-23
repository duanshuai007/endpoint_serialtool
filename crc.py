
def InverUint8(dat):
    temp = 0
    for i in range(8):
        if dat & (1 << i) > 0:
            shift_bit = 7 - i
            temp |= 1 << shift_bit
    return temp

def InverUint16(dat):
    temp = 0
    for i in range(16):
        if dat & (1 << i) > 0:
            shift_bit = 15 - i
            temp |= 1 << shift_bit
    return temp

#head len id[2] cmd identify[4]
#a5   0c  09 00 01  01 02 03 04
def calc_senddata(str_list):
    if len(str_list) != 9:
        return 0

    #print(str_list)
    wCRCin = 0x0000
    wCPoly = 0x8005
    wChar = 0
    pos = 0
    while True:
        wChar = str_list[pos]
        #print 'wChar1:%s'%hex(wChar)
        wChar = InverUint8(wChar)
        wChar = wChar << 8
        #print 'wChar2:%s'%hex(wChar)
        wCRCin = wCRCin^wChar
        #print 'wCRCin1:%s'%hex(wCRCin)
        for i in range(8):
            if (wCRCin & 0x8000) > 0:
                wCRCin = wCRCin << 1
                wCRCin = wCRCin ^ wCPoly
            else:
                wCRCin = wCRCin << 1
        #print 'wCRCin2:%s'%hex(wCRCin)
        pos = pos + 1
        if pos >= 9:
            break
    wCRCin = InverUint16(wCRCin)
    return wCRCin

if __name__ == '__main__': 
    str = [0xa5,0x0c,0x90,0x00,0x01,0x01,0x02,0x03,0x04]
    print(calc_senddata(str))