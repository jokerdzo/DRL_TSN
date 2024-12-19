from CQFQueue import CQFQueue
from Frame import *
from network.DQN import DQNAgent
from parameter import *
from utils import *

import random
import time
import z3  # 导入Z3求解器库，用于SMT算法

# 交换机类,用于SMT和Tabu的求解
class Switch:
    def __init__(self, switch_id):
        self.switch_id = switch_id
        self.queues = [[] for _ in range(sw_queue)]

    def enqueue_frame(self, frame):
        queue = self.queues[frame.qid]
        queue.append(frame)

    def dequeue_frame(self, queue_id):
        queue = self.queues[queue_id]
        if queue:
            return queue.pop(0)
        return None

    def is_queue_empty(self):
        return all(len(queue) == 0 for queue in self.queues)

    def smt_scheduling(self, frames):
        # 使用Z3求解器进行SMT调度
        solver = z3.Solver()

        # 为每个帧的发送时间创建变量
        send_times = []
        for frame in frames:
            send_time = z3.Int(f"send_time_{frame.flow_id}")
            send_times.append(send_time)
            # 添加约束：发送时间在帧的偏移量和截止时间之间
            solver.add(frame.offset <= send_time, send_time <= frame.deadline - frame.size / LINK_BANDWIDTH)

        # 检查约束是否可满足
        if solver.check() == z3.sat:
            model = solver.model()
            for frame, send_time in zip(frames, send_times):
                frame.offset = model[send_time].as_long()
                self.enqueue_frame(frame)
            return True
        return False

    def tabu_search_scheduling(self, frames, tabu_list_size=10, max_iterations=100):
        current_solution = [queue.copy() for queue in self.queues]
        for frame in frames:
            current_solution[frame.qid].append(frame)

        best_solution = current_solution.copy()
        tabu_list = []

        for _ in range(max_iterations):
            neighbor_solutions = self.generate_neighbor_solutions(current_solution)
            # 评估邻居解（这里只是一个简单的评估，实际需要根据约束和目标函数进行更准确的评估）
            best_neighbor, best_neighbor_value = self.evaluate_neighbors(neighbor_solutions, tabu_list)

            if best_neighbor is None:
                break

            current_solution = best_neighbor
            tabu_list.append(best_neighbor)
            if len(tabu_list) > tabu_list_size:
                tabu_list.pop(0)

            if self.evaluate_solution(current_solution) < self.evaluate_solution(best_solution):
                best_solution = current_solution.copy()

        # 根据最佳解进行调度
        for queue_id in range(sw_queue):
            self.queues[queue_id] = best_solution[queue_id]

        return True

    def generate_neighbor_solutions(self, solution):
        neighbor_solutions = []
        for queue_id in range(sw_queue):
            for i in range(len(solution[queue_id])):
                for j in range(len(solution[queue_id])):
                    if i!= j:
                        neighbor_solution = [queue.copy() for queue in solution]
                        neighbor_solution[queue_id][i], neighbor_solution[queue_id][j] = neighbor_solution[queue_id][j], neighbor_solution[queue_id][i]
                        neighbor_solutions.append(neighbor_solution)
        return neighbor_solutions

    def evaluate_neighbors(self, neighbor_solutions, tabu_list):
        best_neighbor = None
        best_neighbor_value = float('inf')
        for neighbor in neighbor_solutions:
            value = self.evaluate_solution(neighbor)
            if value < best_neighbor_value and neighbor not in tabu_list:
                best_neighbor = neighbor
                best_neighbor_value = value
        return best_neighbor, best_neighbor_value

    def evaluate_solution(self, solution):
        total_delay = 0
        for queue in solution:
            for frame in queue:
                # 假设简单计算延迟为偏移量加上链路延迟
                total_delay += frame.offset + frame.link_delay
        return total_delay

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
                # if frame and frame.offset <= current_time:
                if frame:
                    # 检查约束
                    # if self.check_all_constraints(frame):
                        print(f"Switch {self.switch_id}: Sending frame {frame.flow_id} from queue {queue_id} to Switch {self.next_switch.switch_id} at time {current_time}")
                        self.next_switch.receive_frame(frame, current_time)
                    # else:
                    #     print(f"Switch {self.switch_id}: Frame {frame.flow_id} violates constraints at time {current_time}")
                # elif frame:
                #     print(f"Switch {self.switch_id}: Frame {frame.flow_id} in queue {queue_id} not ready for sending at time {current_time}")
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

    def check_all_constraints(self, frame):
        return (self.check_frame_offset_constraint(frame) and
                self.check_slot_constraint(frame) and
                self.check_receiving_window_constraint(frame) and
                self.check_queue_resource_constraint(frame) and
                self.check_end_to_end_delay_constraint(frame))

    def check_frame_offset_constraint(self, frame):
        # 帧偏移约束检查
        if frame.offset < frame.release_time / SLOT_LENGTH or frame.offset > frame.deadline / SLOT_LENGTH - frame.size / LINK_BANDWIDTH - self.next_switch.hop_count * SWITCH_DELAY / SLOT_LENGTH:
            return False
        return True

    def check_slot_constraint(self, frame):
        # 时隙约束检查
        max_slot = gcd([f.period for f in frames])
        min_slot = (CQF_QUEUE_LENGTH * MTU / LINK_BANDWIDTH + SWITCH_DELAY + frames[0].link_delay + CLOCK_ERROR)
        if not (min_slot <= frame.offset <= max_slot and frame.offset % min_slot == 0):
            return False
        return True

    def check_receiving_window_constraint(self, frame):
        # 接收窗口约束检查
        rx_slot = frame.offset / SLOT_LENGTH + self.hop_count
        max_rx = (rx_slot + 1) * SLOT_LENGTH + CLOCK_ERROR
        min_rx = rx_slot * SLOT_LENGTH - CLOCK_ERROR
        if not (min_rx <= frame.offset <= max_rx):
            return False
        return True

    def check_queue_resource_constraint(self, frame):
        # 队列资源约束检查
        queue = self.queues[frame.qid]
        total_frame_size = 0
        for f in queue.frames:
            total_frame_size += f.size
        total_frame_size += frame.size
        return total_frame_size <= CQF_QUEUE_LENGTH

    def check_end_to_end_delay_constraint(self, frame):
        # 端到端延迟约束检查
        end_to_end_delay = current_time - frame.release_time + self.hop_count * SWITCH_DELAY
        if end_to_end_delay > frame.max_end_to_end_delay:
            return False
        return True


# 测试函数
if __name__ == "__main__":
    num_flows = 10

    switches_smt = [Switch(i) for i in range(NUM_SWITCHES)]
    switches_tabu = [Switch(i) for i in range(NUM_SWITCHES)]

    switches = [TSNSwitch(i) for i in range(NUM_SWITCHES)]
    for i in range(NUM_SWITCHES - 1):
        switches[i].set_next_switch(switches[i + 1])
        switches[i + 1].hop_count = switches[i].hop_count + 1  # 更新跳数

    frames = generate_frames(num_flows, NUM_SWITCHES)
    for frame in frames:
        switches[frame.source_switch].schedule_frame(frame)

    # 测试SMT算法
    start_time = time.time()
    for switch in switches_smt:
        success = switch.smt_scheduling(frames)
        if not success:
            print("SMT scheduling failed.")
    end_time = time.time()
    print(f"SMT scheduling successful. Time cost: {end_time - start_time} seconds.")

    # 测试Tabu算法
    start_time = time.time()
    for switch in switches_tabu:
        success = switch.tabu_search_scheduling(frames)
        if not success:
            print("Tabu search scheduling failed.")
    end_time = time.time()
    print(f"Tabu search scheduling successful. Time cost: {end_time - start_time} seconds.")

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