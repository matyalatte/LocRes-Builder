import os, json

def mkdir(dir):
    os.makedirs(dir, exist_ok=True)

def get_ext(file):
    return file.split('.')[-1]

def get_size(file):
    pos=file.tell()
    file.seek(0,2)
    size=file.tell()
    file.seek(pos)
    return size

def check(actual, expected, f=None, msg='Parse failed. This is unexpected error.'):
    if actual!=expected:
        if f is not None:
            print('offset: {}'.format(f.tell()))
        print('actual: {}'.format(actual))
        print('expected: {}'.format(expected))
        raise RuntimeError(msg)

def read_uint32(file):
    bin=file.read(4)
    return int.from_bytes(bin, "little")

def read_uint16(file):
    bin=file.read(2)
    return int.from_bytes(bin, "little")

def read_uint8(file):
    bin=file.read(1)
    return int.from_bytes(bin, "little")

def read_int32(file):
    bin=file.read(4)
    return int.from_bytes(bin, "little", signed=True)

def read_str(file):
    num = read_int32(file)
    if num==0:
        return None

    utf16=num<0
    if num<0:
        num=-num
    string = file.read((num-1)*(1+utf16)).decode("utf-16-le"*utf16 + "ascii"*(not utf16))
    file.seek(1+utf16,1)
    return string

def read_str_array(file, len=None):
    return read_array(file, read_str, len=len)

def read_array(file, read_func, len=None):
    if len is None:
        len = read_uint32(file)
    ary=[read_func(file) for i in range(len)]
    return ary

def write_uint8(file, n):
    bin = n.to_bytes(1, byteorder="little")
    file.write(bin)

def write_uint32(file, n):
    bin = n.to_bytes(4, byteorder="little")
    file.write(bin)

def write_int32(file, n):
    bin = n.to_bytes(4, byteorder="little", signed=True)
    file.write(bin)

def write_str(file, s):
    num = len(s)+1
    utf16=not s.isascii()
    write_int32(file, num*(1- 2* utf16))
    str_byte = s.encode("utf-16-le"*utf16+"ascii"*(not utf16))
    file.write(str_byte + b'\x00'*(1+utf16))

def write_str_array(file, strings, with_length=False):
    if with_length:
        write_uint32(file, len(strings))
    for s in strings:
        write_str(file, s)
    

def write_array(file, ary, with_length=False):
    if with_length:
        write_uint32(file, len(ary))
    for a in ary:
        a.write(file)

def load_json(file):
    with open(file, 'r', encoding='utf-8') as f:
        j = json.load(f)
    return j

def save_json(file, j):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(j, f, indent=4, ensure_ascii=False)


def compare_files(file1,file2):
    f1=open(file1, 'rb')
    f2=open(file2, 'rb')
    print('Comparing {} and {}...'.format(file1, file2))

    f1_size=get_size(f1)
    f2_size=get_size(f2)
    
    size=min(f1_size, f2_size)
    i=0
    f1_bin=f1.read()
    f2_bin=f2.read()
    f1.close()
    f2.close()

    if f1_size==f2_size and f1_bin==f2_bin:
        print('Same data!')
        return

    i=-1
    for b1, b2 in zip(f1_bin, f2_bin):
        i+=1
        if b1!=b2:
            break
    raise RuntimeError('Not same :{}'.format(i))

def compare(path1, path2, ext=None, rec=0):
    if (not os.path.exists(path1)) or (not os.path.exists(path2)):
        print(path1)
        print(path2)
        raise RuntimeError('File not found.')
    if os.path.isfile(path1)!=os.path.isfile(path2):
        raise RuntimeError('Not the same.')
    if os.path.isfile(path1):
        if ext is not None:
            if get_ext(path1) not in ext:
                return
        compare_files(path1, path2)
        return

    if rec==0:
        return
    rec-=1
    for f in os.listdir(path1):
        p1 = os.path.join(path1, f)
        p2 = os.path.join(path2, f)
        compare(p1, p2, ext=ext, rec=rec)
        