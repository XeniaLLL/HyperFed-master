import os
import os.path
import argparse
from collections import Counter

import numpy as np
import torch.utils.data
from sklearn.model_selection import train_test_split

from utils.dataset_utils import save_file, split_with_strategy


def vision_dataset_ndarray(dataset_type, root: str, transform):
    train_set = dataset_type(
        root=root,
        train=True,
        transform=transform
    )
    test_set = dataset_type(
        root=root,
        train=False,
        transform=transform
    )
    train_data, train_labels = next(iter(torch.utils.data.DataLoader(train_set, batch_size=len(train_set))))
    train_data = train_data.numpy()
    train_labels = train_labels.numpy()
    test_data, test_labels= next(iter(torch.utils.data.DataLoader(test_set, batch_size=len(test_set))))
    test_data = test_data.numpy()
    test_labels = test_labels.numpy()
    all_data = np.concatenate([train_data, test_data])
    all_labels = np.concatenate([train_labels, test_labels])
    return all_data, all_labels


def parse_cmd_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir_path', required=True, help="Directory of the dataset")
    parser.add_argument('--n_clients', type=int, required=True, help='Number of clients')
    parser.add_argument(
        '--strategy',
        required=True,
        choices=['label', 'dirichlet', 'dirichlet_quantity', 'uniform'],
        help="1) label: Each client will contains 'n_class_per_client' classes. \n"
             "2) dirichlet: The distribution of each class is generated by Dirichlet distributions.\n"
             "3) dirichlet_quantity: The number of samples per client is generated by Dirichlet distributions.\n"
             "4) uniform: Split uniformly.\n"
             "*Tips: If you want each client to have the same label distribution, "
             "use 'label' strategy with 'n_class_per_client' set as the number of class of the dataset"
    )
    parser.add_argument('--test_ratio', type=float, required=True)
    parser.add_argument(
        '--alpha',
        type=float,
        help="Required by 'dirichlet' and 'dirichlet_quantity' splitting. "
             "Parameter of Dirichlet distributions."
    )
    parser.add_argument(
        '--min_size',
        type=int,
        default=1,
        help="Parameter of 'dirichlet' and 'dirichlet_quantity' splitting, default value is 1. "
             "The number of samples per client will be greater than or equal to 'min_size'."
    )
    parser.add_argument(
        '--n_class_per_client',
        type=int,
        help="Required by 'label' splitting. "
             "Each client will contains 'n_class_per_client' classes."
    )
    args = parser.parse_args()
    return args


def main_template(args, data: np.ndarray, labels: np.ndarray):
    clients = split_with_strategy(
        data,
        labels,
        n_clients=args.n_clients,
        strategy=args.strategy,
        alpha=args.alpha,
        min_size=args.min_size,
        n_class_per_client=args.n_class_per_client
    )
    train_data = []
    test_data = []
    for client_data, client_labels in clients:
        (client_train_data,
         client_test_data,
         client_train_labels,
         client_test_labels) = train_test_split(client_data, client_labels, test_size=args.test_ratio)
        train_data.append({'x': client_train_data, 'y': client_train_labels})
        test_data.append({'x': client_test_data, 'y': client_test_labels})
    os.makedirs(os.path.join(args.dir_path, 'train'), exist_ok=True)
    os.makedirs(os.path.join(args.dir_path, 'test'), exist_ok=True)
    save_file(
        config_path=os.path.join(args.dir_path, 'config.json'),
        train_path=os.path.join(args.dir_path, 'train'),
        test_path=os.path.join(args.dir_path, 'test'),
        train_data=train_data,
        test_data=test_data,
        num_clients=args.n_clients,
        num_classes=10, 
        statistic=[list(Counter(labels.tolist()).items()) for _, labels in clients],
        partition=args.strategy,
        alpha=args.alpha
    )
