# 定义一些常量
MTU = 1542  # 最大传输单元（字节）
sw_queue = 2  # 每个交换机的队列数量（两个队列，一个用于收，一个用于发）
NUM_ACTIONS = 2  # 每个交换机队列的动作数量（0：不发送/接收，1：发送/接收）
NUM_STATES = sw_queue # 状态空间大小（假设简单的状态表示，每个队列有两个状态：队列长度是否超过一半）
LEARNING_RATE = 0.1
DISCOUNT_FACTOR = 0.9
EPSILON = 0.1
BATCH_SIZE = 64  # 每次从经验回放缓冲区中采样的样本数量
TARGET_UPDATE_FREQ = 10  # 目标网络更新频率，每多少个episode更新一次目标网络
MEMORY_SIZE = 10000  # 经验回放缓冲区大小
GAMMA = 0.99  # 折扣因子，用于权衡未来奖励的重要性
NUM_EPISODES = 100 #训练轮次

# 网络参数
LINK_BANDWIDTH = 1000 * 1000 * 1000  # 链路带宽，1000 MB/s，转换为字节每秒
SLOT_LENGTH = 125 * 1000  # 时隙长度，125 μs，转换为纳秒
SWITCH_DELAY = 10 * 1000  # 交换机延迟，10 μs，转换为纳秒
CLOCK_ERROR = 0.1 * 1000  # 时钟误差，0.1 μs，转换为纳秒
CQF_QUEUE_LENGTH = 15000  # CQF队列长度，15000 B


# 网络拓扑相关参数（示例，根据实际情况调整）
NUM_SWITCHES = 5  # 交换机数量
NUM_QUEUES_PER_SWITCH = 4  # 每个交换机的队列数量

EPSILON_START = 1.0  # 初始的epsilon值，表示开始时较高的探索概率
EPSILON_END = 0.01  # 最终的epsilon值，表示经过训练后较低的探索概率
EPSILON_DECAY = 0.995  # epsilon的衰减率，用于逐渐降低探索概率