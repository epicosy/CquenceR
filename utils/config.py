#!/usr/bin/env python3

from os.path import dirname, abspath
from pathlib import Path

from utils.data_objects import DataPaths, Configuration, ONMTArguments

ROOT_DIR = dirname(dirname(abspath(__file__)))

ONMT_ARGS = {'preprocess': {
        'src_seq_length': 1010,
        'tgt_seq_length': 200,
        'src_vocab_size': 1000,
        'tgt_vocab_size': 1000,
        'dynamic_dict': True,
        'share_vocab': True
    },
    'train': {
        'model': {
            'lstm': {
                'encoder_type': 'brnn',
                'enc_layers': 2,
                'decoder_type': 'rnn',
                'dec_layers': 2,
                'rnn_size': 256,
                'global_attention': 'general',
                'bridge': True,
                'copy_attn': True,
                'reuse_copy_attn': True,
            },
            'transformer': {
                'encoder_type': 'transformer',
                'decoder_type': 'transformer',
                'layers': 6,
                'rnn_size': 256,
                'transformer_ff': 2048,
                'heads': 8,
                'position_encoding': True,
                'max_generator_batches': 2,
                'dropout': 0.1,
                'batch_type': 'tokens',
                'normalization': 'tokens',
                'accum_count': 2,
                'optim': 'adam',
                'adam_beta2': 0.998,
                'decay_method': 'noam',
                'learning_rate': 2,
                'max_grad_norm': 0,
                'param_init': 0,
                'param_init_glorot': True,
                'label_smoothing': 0.1,
            }
        },
        'batch_size': 32,
        'word_vec_size': 256,
        'train_steps': 2000,
        'valid_steps': 50,
        'early_stopping': 10,
        'world_size': 1,
        'save_checkpoint_steps': 1000
    },
    'translate': {
        'beam_size': 50,
        'n_best': 50,
        'dynamic_dict': True,
        'replace_unk': True
    }
}

data_path = Path(ROOT_DIR) / Path("data")
data_paths = DataPaths(root=data_path,
                       raw=data_path / Path("raw"),
                       processed=data_path / Path("processed"),
                       input=data_path / Path("input"),
                       model=data_path / Path("model"))

onmt_args = ONMTArguments(preprocess=ONMT_ARGS['preprocess'], train=ONMT_ARGS['train'], translate=ONMT_ARGS['translate'])
configuration = Configuration(root=Path(ROOT_DIR),
                              data_paths=data_paths,
                              onmt_args=onmt_args,
                              trunc_limit=200)
