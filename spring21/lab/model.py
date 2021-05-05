import torch
from torch import nn

class Siamese(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(7, 16, 5), # 16@46
            nn.ReLU(),
            nn.MaxPool1d(2), #16@24
        )
        
        self.liner = nn.Sequential(
            nn.Linear(368, 120),
            nn.ReLU(),
            nn.Linear(120, 1),
        )
        
        self.out = nn.Sigmoid()
    
    def forward_one(self, x):
        x = self.conv(x)
        x = x.view(x.size()[0], -1)
        x = self.liner(x)
        return x
    
    def forward(self, x1, x2):
        out1 = self.forward_one(x1)
        out2 = self.forward_one(x2)
        
        return self.out(out1 - out2)