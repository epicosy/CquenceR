# CquenceR
Automatic Program Repair tool based on Sequence-to-Sequence Learning.

###### The current version patches one-line single-file vulnerabilities.

The tool is based and extends to C programs the original technique called (SequenceR)[https://github.com/KTH/chai].

## Prerequisites

* [Python (=>3.7)](https://www.python.org/)

### Python Dependencies
* [OpenNMT (=>1.1.1)](https://github.com/OpenNMT/OpenNMT-py)


## Baseline

The baseline usage involves three operations: preprocess, train and repair.

The script ```CquenceR/init.sh``` checks python version, sets PYTHONPATH, installs OpenNMT and executes the preprocess and train operations.

### Preprocess
This operation tokenizes, truncates and transforms the dataset into the input to train the model.
The truncation limit can be changed in the ```CquenceR/config.py``` file.

``` console
$ ./CquenceR.py preprocess -split train_val --src_path 'src_path' --out_path 'out_path'
```

### Train
This operation trains a model from the previous preprocessed dataset files. 
The GPU is not used during training. Uncomment the "'gpu_ranks': 0" line in the ```CquenceR/config.py``` file. 
Make sure you export CUDA_VISIBLE_DEVICES=0.
Check more about GPU usage in the [OpenNMT docs](https://opennmt.net/OpenNMT-py/).

``` console
$ ./CquenceR.py train
```

### Repair
This operation uses the model previously generated to predict fixes and applies them to the source code.
Make sure you supply the absolute paths.
The default compiler command must contain the keyword __SOURCE_NAME__, which is replaced with the patched files generated.
The default test command must contain the keyword __TEST_NAME__, which is replaced with the test names. These have the format "p#" and "n#" where # is the number of the test case and p is for positive test cases and n is for negative test cases.
The test that don't pass must raise an error code.

``` console
$ ./CquenceR.py repair --working_dir /tmp/Barcoder/ --src_path Barcoder/src/main.c --vuln_line 176 --compile_script "cb_repair.py compile -wd /tmp/Barcoder -cn Barcoder -if /tmp/Barcoder/Barcoder/src/main.c -ffs __SOURCE_NAME__ -v" --test_script "/home/epicosy/thesis/implementation/repair/SecureThemAll/benchmark/cb-repair/src/cb_repair.py test -wd /tmp/Barcoder -cn Barcoder -tn __TEST_NAME__ -v -ef -np" --pos_tests 10 --neg_tests 1
```

## Dataset

Dataset contains one line patches from various projects. Check [PatchBundle](https://github.com/epicosy/PatchBundle) for more information and details about the dataset.