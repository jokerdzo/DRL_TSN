from parameter import *
import random

class Frame:
    def __init__(self, flow_id, period, size, qid, offset, source_switch, destination_switch, release_time, deadline, link_delay, max_end_to_end_delay, hop_count=0):
        self.flow_id = flow_id
        self.period = period
        self.size = size
        self.qid = qid
        self.offset = offset
        self.source_switch = source_switch
        self.destination_switch = destination_switch
        self.release_time = release_time
        self.deadline = deadline
        self.link_delay = link_delay
        self.max_end_to_end_delay = max_end_to_end_delay
        self.hop_count = hop_count

# 生成测试帧
def generate_frames(num_flows, num_switches):
    frames = []
    for i in range(num_flows):
        period = random.choice([800 * 1000, 1600 * 1000, 3200 * 1000])  # 随机选择周期，转换为纳秒
        size = random.randint(100, MTU)
        qid = random.randint(0, sw_queue - 1)
        offset = random.randint(0, period)  # 随机生成偏移量，在合理范围内
        source_switch = random.randint(0, num_switches - 2)
        destination_switch = random.randint(source_switch + 1, num_switches - 1)
        release_time = random.randint(0, period)  # 随机生成帧释放时间
        deadline = release_time + period  # 设置期限为释放时间加上周期
        link_delay = random.randint(0, 10000)  # 随机生成链路延迟
        max_end_to_end_delay = random.randint(100000, 1000000)  # 随机生成最大端到端延迟
        hop_count = 0  # 初始化跳数为0
        frames.append(Frame(i, period, size, qid, offset, source_switch, destination_switch, release_time, deadline, link_delay, max_end_to_end_delay, hop_count))
    return frames