import itertools
import logging
import time
import numpy as np

from . import send as _send
from . import recv as _recv
from . import framing, common, stream, detect, sampling

log = logging.getLogger(__name__)

def send_bytes(config, data, dst, gain=1.0):
    sender = _send.Sender(dst, config=config, gain=gain)
    Fs = config.Fs

    # pre-padding audio with silence (priming the audio sending queue)
    sender.write(np.zeros(int(Fs * config.silence_start)))

    sender.start()

    training_duration = sender.offset
    log.info('Sending %.3f seconds of training audio', training_duration / Fs)


    bits = framing.encode(data)
    log.info('Starting modulation')
    sender.modulate(bits=bits)

    data_duration = sender.offset - training_duration
    #log.info('Sent %.3f kB @ %.3f seconds',
    #         reader.total / 1e3, data_duration / Fs)

    # post-padding audio with silence
    sender.write(np.zeros(int(Fs * config.silence_stop)))
    return True

def send(config, src, dst, gain=1.0):

    #reader = stream.Reader(src, eof=True)
    #data = itertools.chain.from_iterable(reader)
    while True:
        data = src.read(203*5)

        if len(data) == 0:
            break

        send_bytes(config, data, dst, gain)
    send_bytes(config, "", dst, gain)
#    send_bytes(config, "", dst, gain)
    return True

'''
    sender = _send.Sender(dst, config=config, gain=gain)
    Fs = config.Fs

    # pre-padding audio with silence (priming the audio sending queue)
    sender.write(np.zeros(int(Fs * config.silence_start)))

    sender.start()

    training_duration = sender.offset
    log.info('Sending %.3f seconds of training audio', training_duration / Fs)

    reader = stream.Reader(src, eof=True)
    data = itertools.chain.from_iterable(reader)
    bits = framing.encode(data)
    log.info('Starting modulation')
    sender.modulate(bits=bits)

    data_duration = sender.offset - training_duration
    log.info('Sent %.3f kB @ %.3f seconds',
             reader.total / 1e3, data_duration / Fs)

    # post-padding audio with silence
    sender.write(np.zeros(int(Fs * config.silence_stop)))
    return True
'''

def recv(config, src, dst, dump_audio=None, pylab=None):
    while True:
        if recv_segment(config,src,dst,dump_audio,pylab) == 0:
            break

def recv_segment(config, src, dst, dump_audio=None, pylab=None):
    if dump_audio:
        src = stream.Dumper(src, dump_audio)
    reader = stream.Reader(src, data_type=common.loads)
    signal = itertools.chain.from_iterable(reader)

    log.debug('Skipping %.3f seconds', config.skip_start)
    common.take(signal, int(config.skip_start * config.Fs))

    pylab = pylab or common.Dummy()
    detector = detect.Detector(config=config, pylab=pylab)
    receiver = _recv.Receiver(config=config, pylab=pylab)
    try:
        freq_error = 9999999
        while freq_error > 1000:
            log.info('Waiting for carrier tone: %.1f kHz', config.Fc / 1e3)
            signal, amplitude, freq_error = detector.run(signal)

            freq = 1 / (1.0 + freq_error)  # receiver's compensated frequency
            freq_error = (freq - 1) * 1e6
            log.debug('Frequency correction: %.3f ppm', (freq - 1) * 1e6)

            gain = 1.0 / amplitude
            log.debug('Gain correction: %.3f', gain)

        sampler = sampling.Sampler(signal, sampling.defaultInterpolator,
                                   freq=freq)
        return receiver.run(sampler, gain=1.0/amplitude, output=dst)
    except BaseException:
        log.exception('Decoding failed')
        return False
    finally:
        dst.flush()
        receiver.report()
