from CQFQueue import CQFQueue
from Frame import *
from network.DQN import DQNAgent
from parameter import *
from Constraint import *

# TSN交换机类
class TSNSwitch:
    def __init__(self, switch_id):
        self.switch_id = switch_id
        self.queues = [CQFQueue() for _ in range(sw_queue)]
        self.next_switch = None
        self.agent = DQNAgent(state_dim=NUM_STATES, action_dim=NUM_ACTIONS)
        self.hop_count = 0  # 初始化跳数，在拓扑构建时更新

    def set_next_switch(self, next_switch):
        self.next_switch = next_switch

    def schedule_frame(self, frame):
        if frame.source_switch == self.switch_id:
            queue_id = frame.qid
            return self.queues[queue_id].enqueue(frame)
        return False

    def send_frames(self, current_time):
        for queue_id, queue in enumerate(self.queues):
            state = self.get_state(queue_id)
            action = self.agent.act(state)
            if action == 1:
                frame = queue.dequeue()
                if frame and frame.offset <= current_time:
                    # 检查约束
                    print(f"Switch {self.switch_id}: Sending frame {frame.flow_id} from queue {queue_id} to Switch {self.next_switch.switch_id} at time {current_time}")
                    self.next_switch.receive_frame(frame, current_time)
                elif frame:
                    print(f"Switch {self.switch_id}: Frame {frame.flow_id} in queue {queue_id} not ready for sending at time {current_time}")
            else:
                print(f"Switch {self.switch_id}: Not sending from queue {queue_id} at time {current_time}")
            next_state = self.get_state(queue_id)
            reward = self.get_reward(queue_id)
            done = all(queue.total_size == 0 for queue in self.queues)
            self.agent.remember(state, action, reward, next_state, done)
            self.agent.replay()
            self.agent.decay_epsilon()

    def receive_frame(self, frame, current_time):
        if frame.destination_switch == self.switch_id:
            print(f"Switch {self.switch_id}: Received frame {frame.flow_id} at time {current_time}")
        else:
            queue_id = frame.qid
            self.queues[queue_id].enqueue(frame)
            # 更新接收帧的交换机跳数
            frame.hop_count += 1

    def get_state(self, queue_id):
        state = []
        for q in self.queues:
            if q.total_size > CQF_QUEUE_LENGTH / 2:
                state.append(1)
            else:
                state.append(0)
        return state

    def get_reward(self, queue_id):
        queue = self.queues[queue_id]
        if queue.total_size > CQF_QUEUE_LENGTH / 2:
            return -1
        return 1


# 测试函数
if __name__ == "__main__":
    num_flows = 10
    num_switches = 5

    switches = [TSNSwitch(i) for i in range(num_switches)]
    for i in range(num_switches - 1):
        switches[i].set_next_switch(switches[i + 1])
        switches[i + 1].hop_count = switches[i].hop_count + 1  # 更新跳数

    frames = generate_frames(num_flows, num_switches)
    for frame in frames:
        switches[frame.source_switch].schedule_frame(frame)

    current_time = 0
    for episode in range(NUM_EPISODES):
        print(f"Episode {episode + 1}")
        for switch in switches:
            switch.send_frames(current_time)
        current_time += SLOT_LENGTH
        if all(queue.total_size == 0 for switch in switches for queue in switch.queues):
            break
        if episode % TARGET_UPDATE_FREQ == 0:
            for switch in switches:
                switch.agent.update_target_network()