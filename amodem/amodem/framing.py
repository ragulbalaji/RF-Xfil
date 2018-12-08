import binascii
import functools
import itertools
import logging
import struct
from unireedsolomon import *
from bchlib import *


from . import common

log = logging.getLogger(__name__)


def _checksum_func(x):
    ''' The result will be unsigned on Python 2/3. '''
    return binascii.crc32(bytes(x)) & 0xFFFFFFFF


bch_poly = 8219
bch_t = 32
bch = BCH(bch_poly, bch_t)

class Checksum:
    fmt = '>L'  # unsigned longs (32-bit)
    size = struct.calcsize(fmt)

    def encode(self, payload):


        #print len(payload)
        #checksum = _checksum_func(payload)
        #coder = rs.RSCoder(255,104)
        #ecc = coder.encode(struct.pack(self.fmt, checksum) + payload)
        #print len(ecc)
        #ecc = bch.encode(payload)
        #print len(payload), len(ecc)
        #return payload + ecc
        #return struct.pack(self.fmt, checksum) + payload
        return payload

    def decode(self, data):
        #print len(data), data
        #coder = rs.RSCoder(255,104)
        #data = coder.decode(data)[0]
        #received, = struct.unpack(self.fmt, bytes(data[:self.size]))
        #payload = data[self.size:]
        #expected = _checksum_func(payload)
        #if received != expected:
            #log.warning('Invalid checksum: %08x != %08x', received, expected)
            #raise ValueError('Invalid checksum')
        #else:
            #log.debug('Good checksum: %08x', received)
        #ecclen = bch.ecc_bytes
        #ecc = data[-ecclen:]
        #decode = data[:-ecclen]
        #err, payload, ecc = bch.decode(decode,ecc)

        #print err, len(payload), len(ecc)
        return data


class Framer:
    frame_size = 256
    block_size = frame_size - 1 - bch.ecc_bytes
    prefix_fmt = '>B'
    prefix_len = struct.calcsize(prefix_fmt)
    checksum = Checksum()

    EOF = b''

    def _pack(self, block):
        frame = self.checksum.encode(block)
        data = (struct.pack(self.prefix_fmt, len(frame)) + frame).ljust(self.block_size, "\x00")
        print len(data)
        ecc = bch.encode(data)
        return bytearray(data + ecc)

    def encode(self, data):
        for block in common.iterate(data=data, size=self.block_size,
                                    func=bytearray, truncate=False):
            yield self._pack(block=block)
        yield self._pack(block=self.EOF)

    def decode(self, data):
        data = iter(data)
        while True:
            full_frame = _take_len(data, self.frame_size)

            ecc = full_frame[-bch.ecc_bytes:]
            full_frame = full_frame[:-bch.ecc_bytes]

            err, full_frame, ecc = bch.decode(full_frame, ecc)

            prefix_len = struct.calcsize(self.prefix_fmt)
            #print len(full_frame)
            length, = struct.unpack(self.prefix_fmt, bytes(full_frame[:prefix_len]))
            frame = full_frame[prefix_len:prefix_len+length]
            block = self.checksum.decode(frame)
            if block == self.EOF:
                log.debug('EOF frame detected')
                return

            yield block


def _take_fmt(data, fmt):
    length = struct.calcsize(fmt)
    chunk = bytearray(itertools.islice(data, length))
    if len(chunk) < length:
        raise ValueError('missing prefix data')
    return struct.unpack(fmt, bytes(chunk))


def _take_len(data, length):
    chunk = bytearray(itertools.islice(data, length))
    if len(chunk) < length:
        raise ValueError('missing payload data')
    return chunk


def chain_wrapper(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        result = func(*args, **kwargs)
        return itertools.chain.from_iterable(result)
    return wrapped


class BitPacker:
    byte_size = 8

    def __init__(self):
        bits_list = []
        for index in range(2 ** self.byte_size):
            bits = [index & (2 ** k) for k in range(self.byte_size)]
            bits_list.append(tuple((1 if b else 0) for b in bits))

        self.to_bits = dict((i, bits) for i, bits in enumerate(bits_list))
        self.to_byte = dict((bits, i) for i, bits in enumerate(bits_list))


@chain_wrapper
def encode(data, framer=None):
    converter = BitPacker()
    framer = framer or Framer()
    for frame in framer.encode(data):
        for byte in frame:
            yield converter.to_bits[byte]


@chain_wrapper
def _to_bytes(bits):
    converter = BitPacker()
    for chunk in common.iterate(data=bits, size=8,
                                func=tuple, truncate=True):
        yield [converter.to_byte[chunk]]


def decode_frames(bits, framer=None):
    framer = framer or Framer()
    for frame in framer.decode(_to_bytes(bits)):
        yield bytes(frame)
