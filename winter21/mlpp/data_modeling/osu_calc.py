def compute_acc(score):
    c50, c100, c300, cmiss = score['count50'], score['count100'], score['count300'], score['countmiss']
    return (c50 / 6 + c100 / 3 + c300) / (c50 + c100 + c300 + cmiss)
