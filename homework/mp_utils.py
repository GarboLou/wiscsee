from commons import *
from wiscsim.hostevent import *
import math
import sys
import datetime as dt

DEBUG = True
def log_msg(*msg):
    '''
    Log a message with the current time stamp.
    '''
    msg = [str(_) for _ in msg]
    if DEBUG:
        print"[%s] %s" % ((dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), " ".join(msg))

    sys.stdout.flush()

def split_lpns(offset, size):
    page_size = 4096.0
    lpns = [lpn for lpn in range(int(math.floor(offset/page_size)), int(math.ceil((offset+size)/page_size)))]

    return lpns

def parse_events(filename, start_lineno=0, lineno=float('inf'), format="MSR"):
    log_msg("parsing %s with %s format" % (filename, format))
    # Dict<Format, Tuple<size_scale, time_scale, delimeter>>
    format_config = {"MSR" : (1, 100, ","), "blktrace" : (512, 1000**3, " "), "systor" : (1, 1000**3, ","), "normal" : (1, 1000, " "), "FIU" : (512, 1, " "), "Financial" : (1, 1000**3, ",", 512)}
    size_scale = format_config[format][0]
    offset_scale = size_scale
    time_scale = format_config[format][1]
    delimeter = format_config[format][2]
    if len(format_config[format]) > 3:
        offset_scale = format_config[format][3]

    events = []
    with open(filename) as fp:
        t_start = None
        last_t = 0
        active_events = 0
        exist_lpns = dict()
        warm_up_writes = []
        for i, raw in enumerate(fp):
            if i < start_lineno:
                continue
            # parse trace
            line = raw.strip().split(delimeter)
            if format == "MSR":
                t, p, d, mode, offset, size, t0 = line
                t, d, offset, size, t0 = int(t), int(d), int(offset), int(size), int(t0)
            if format == "normal":
                t, d, offset, size, mode = line
                t, d, offset, size, mode = int(t), int(d), int(offset), int(size), int(mode)
            elif format == "blktrace":
                line = filter(lambda _: _ != '', line)
                raise NotImplementedError
            elif format == "systor":
                if i == 0:
                    continue
                t, t0, mode, d, offset, size = line
                if t0 == "":
                    t0 = 0.0
                t, d, offset, size, t0 = float(t), int(d), int(offset), int(size), float(t0)
            elif format == "Financial":
                app, offset, size, mode, t = line
                if int(app)!=0:
                    continue
                t, offset, size = float(t), int(offset), int(size)
            elif format == "FIU":
                t, pid, proc, offset, size, mode, _, d, _ = line
                t, offset, size = float(t), int(offset), int(size)

            # shift timestamp
            if not t_start:
                t_start = t
            t -= t_start

            # scale trace
            offset *= offset_scale
            size *= size_scale
            t = int(t*time_scale)
            if size == 0:
                continue

            if mode in ["Read", "R", 0, 'r']:
                op = OP_READ
                should_warm_up = False
                for lpn in split_lpns(offset, size):
                    if lpn not in exist_lpns:
                        should_warm_up = True
                        exist_lpns[lpn] = None
                if should_warm_up:
                    warm_up_writes += [Event(512, 0, OP_WRITE, offset, size, timestamp=0)]
            elif mode in ["Write", "W", 1, 'w']:
                op = OP_WRITE
                for lpn in split_lpns(offset, size):
                    exist_lpns[lpn] = None

            # create event
            if t < last_t:
                continue
            # events += [ControlEvent(OP_SLEEP, arg1=t - last_t)]
            events += [Event(512, 0, op, offset, size, timestamp=t)]
            active_events += 1
            last_t = t

            # termination
            if i > lineno:
                break

            if (i-start_lineno) % 1000000 == 0:
                log_msg("parsed %d lines" % i)

        log_msg("parsed %d lines" % i)

    events = [ControlEvent(OP_ENABLE_RECORDER)] + warm_up_writes + events

    log_msg("Total warm-up events %d" % len(warm_up_writes))
    log_msg("Total active events %d" % active_events)
    return events
