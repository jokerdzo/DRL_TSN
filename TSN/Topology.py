#网络拓扑结构

#线性拓扑
def linearTopology(switch_type, num_switches):
    switches = [switch_type(i) for i in range(num_switches)]
    for i in range(num_switches - 1):
        switches[i].set_next_switch(switches[i + 1])
        switches[i + 1].hop_count = switches[i].hop_count + 1  # 更新跳数
    return switches

#环形拓扑

#星型拓扑