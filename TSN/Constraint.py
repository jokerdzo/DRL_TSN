from TSN.parameter import *

# 用于计算最大时隙（max_slot）的函数，求最大公约数
def gcd(numbers):
    if len(numbers) == 1:
        return numbers[0]
    else:
        a = numbers[0]
        b = gcd(numbers[1:])
        while b!= 0:
            a, b = b, a % b
        return a

def check_frame_offset_constraint(frame, slot):
    """检查帧偏移约束"""
    if frame.offset < frame.release_time / slot or \
       frame.offset > (frame.deadline / slot - frame.length - frame.link_delay / slot):
        return False
    return True

def check_slot_constraint(frames):
    """检查时隙约束"""
    max_slot = gcd([f.period for f in frames])
    min_slot = (CQF_QUEUE_LENGTH * MTU / LINK_BANDWIDTH + SWITCH_DELAY + frames[0].link_delay + CLOCK_ERROR)
    for frame in frames:
        if not (min_slot <= frame.offset <= max_slot and frame.offset % min_slot == 0):
            return False
    return True

def check_receiving_window_constraint(frame, hop_count):
    """检查接收窗口约束"""
    rx_slot = frame.offset / SLOT_LENGTH + hop_count
    max_rx = (rx_slot + 1) * SLOT_LENGTH + CLOCK_ERROR
    min_rx = rx_slot * SLOT_LENGTH - CLOCK_ERROR
    if not (min_rx <= frame.offset <= max_rx):
        return False
    return True

def check_queue_resource_constraint(switch, frame):
    """检查队列资源约束"""
    queue = switch.queues[frame.qid]
    if queue.total_size + frame.size > CQF_QUEUE_LENGTH:
        return False
    return True

def check_end_to_end_delay_constraint(frame):
    """检查端到端延迟约束"""
    end_to_end_delay = frame.destination_node.receive_time - frame.source_node.send_time
    if end_to_end_delay > frame.max_end_to_end_delay:
        return False
    return True