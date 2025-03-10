import torch
import torch.nn as nn
import random
from TSN.parameter import *
import os
import numpy as np

# DQN网络结构
class DQN(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(state_dim, 128)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(128, action_dim)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x

# DQN智能体类
class DQNAgent:
    def __init__(self, state_dim, action_dim):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.policy_net = DQN(state_dim, action_dim)
        self.target_net = DQN(state_dim, action_dim)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        self.optimizer = torch.optim.Adam(self.policy_net.parameters(), lr=LEARNING_RATE)
        self.memory = []
        self.position = 0
        self.epsilon = EPSILON_START

    def remember(self, state, action, reward, next_state, done):
        if len(self.memory) < MEMORY_SIZE:
            self.memory.append(None)
        self.memory[self.position] = (state, action, reward, next_state, done)
        self.position = (self.position + 1) % MEMORY_SIZE

    def act(self, state):
        if random.random() < self.get_epsilon():
            return random.randrange(self.action_dim)
        state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0).view(1, -1)
        with torch.no_grad():
            q_values = self.policy_net(state_tensor)
        return torch.argmax(q_values).item()

    def get_epsilon(self):
        return self.epsilon

    def replay(self):
        if len(self.memory) < BATCH_SIZE:
            return
        batch = random.sample(self.memory, BATCH_SIZE)
        states, actions, rewards, next_states, dones = zip(*batch)
        states = torch.tensor(states, dtype=torch.float32)
        actions = torch.tensor(actions, dtype=torch.long).unsqueeze(1)
        rewards = torch.tensor(rewards, dtype=torch.float32).unsqueeze(1)
        next_states = torch.tensor(next_states, dtype=torch.float32)
        dones = torch.tensor(dones, dtype=torch.float32).unsqueeze(1)

        q_values = self.policy_net(states).gather(1, actions)
        next_q_values = self.target_net(next_states).max(1)[0].unsqueeze(1)
        expected_q_values = rewards + GAMMA * next_q_values * (1 - dones)

        loss = nn.MSELoss()(q_values, expected_q_values)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def update_target_network(self):
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def decay_epsilon(self):
        self.epsilon = max(EPSILON_END, self.epsilon * EPSILON_DECAY)

    def save_model(self, file_path):
        torch.save(self.policy_net.state_dict(), file_path)

    def load_model(self, file_path):
        if os.path.exists(file_path):
            self.policy_net.load_state_dict(torch.load(file_path))
            self.target_net.load_state_dict(self.policy_net.state_dict())
            print(f"Loaded model from {file_path}")
        else:
            print(f"Model file {file_path} not found.")