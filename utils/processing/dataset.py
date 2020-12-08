from sklearn.model_selection import train_test_split
from pandas import DataFrame

SPLIT_RATIOS = (0.85, 0.1, 0.05)


def train_val_test_split(dataset: DataFrame, shuffle: bool = True) -> dict:
    train, test = train_test_split(dataset, test_size=1 - SPLIT_RATIOS[0], shuffle=shuffle)
    k = SPLIT_RATIOS[2] / (SPLIT_RATIOS[1] + SPLIT_RATIOS[2])
    val, test = train_test_split(test, test_size=k, shuffle=shuffle)

    train = train.reset_index(drop=True)
    val = val.reset_index(drop=True)
    test = test.reset_index(drop=True)

    print(f"Train size: {len(train)}; Val size: {len(val)}; Test size: {len(test)}")

    return {'train': train, 'test': test, 'val': val}


def train_val_split(dataset: DataFrame, shuffle: bool = True) -> dict:
    train, val = train_test_split(dataset, test_size=SPLIT_RATIOS[2], shuffle=shuffle)

    train = train.reset_index(drop=True)
    val = val.reset_index(drop=True)

    print(f"Train size: {len(train)}; Val size: {len(val)};")

    return {'train': train, 'val': val}
