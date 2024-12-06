QUEUE_LENGTH = 15000  # CQF队列长度（字节）

# class CQFQueue:
#     def __init__(self):
#         self.send_queue = []
#         self.receive_queue = []
#         self.total_send_size = 0
#         self.total_receive_size = 0
#
#     def enqueue(self, frame):
#         if self.total_receive_size + frame.size <= QUEUE_LENGTH:
#             self.receive_queue.append(frame)
#             self.total_receive_size += frame.size
#             return True
#         return False
#
#     def dequeue_send(self):
#         if self.send_queue:
#             frame = self.send_queue.pop(0)
#             self.total_send_size -= frame.size
#             return frame
#         return None
#
#     def enqueue_send(self, frame):
#         if self.total_send_size + frame.size <= QUEUE_LENGTH:
#             self.send_queue.append(frame)
#             self.total_send_size += frame.size
#             return True
#         return False
#
#     def dequeue_receive(self):
#         if self.receive_queue:
#             frame = self.receive_queue.pop(0)
#             self.total_receive_size -= frame.size
#             return frame
#         return None

# CQF队列类
class CQFQueue:
    def __init__(self):
        self.frames = []
        self.total_size = 0

    def enqueue(self, frame):
        if self.total_size + frame.size <= QUEUE_LENGTH:
            self.frames.append(frame)
            self.total_size += frame.size
            return True
        return False

    def dequeue(self):
        if self.frames:
            frame = self.frames.pop(0)
            self.total_size -= frame.size
            return frame
        return None