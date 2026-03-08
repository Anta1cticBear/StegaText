# StegaText

This repo contains the implementations of several linguistic steganography methods in paper "Near-imperceptible Neural Linguistic Steganography via Self-Adjusting Arithmetic Coding" published in EMNLP 2020.

## New: Prompt Injection Attack Extraction

We've added a tool to extract system prompt extraction attack phrases from red team datasets. The tool generates **100 English-only red team prompts** (25 per category). See `extract_prompt_injection_attacks.py` for details.

### Quick Start

```bash
# Generate example prompts (works offline)
python extract_prompt_injection_attacks.py --mode examples

# Download and extract from datasets (requires internet)
python extract_prompt_injection_attacks.py --mode download
```

The tool extracts and categorizes prompts into:
1. **Direct extraction attacks** (直接提取攻击): Direct commands to output system prompts
2. **Context ignoring jailbreak** (上下文忽略越狱): Role-playing to escape safety controls
3. **Cognitive deception** (认知欺骗): Inducing leakage in compliant contexts
4. **Encoding bypass strategies** (编码绕过策略): Using translation/encoding to bypass filters

Results are saved to `./prompt_injection_attacks/` directory. See the [extraction results README](./prompt_injection_attacks/README.md) for more details.

## Dependency

You need to install all dependent librarys in `requirements.txt` file. Besides, you need to download the `gpt2-medium` model (345M parameter) from [transformers library](https://huggingface.co/transformers/pretrained_models.html)

## Datasets

We put all four datasets mentioned in the paepr into the `datasets/` folder.


## Included Implementations

1. `block_baseline.py`: implementations of baseline method `Bin-LM` in the paper.
2. `huffman_baseline.py`: implementations of baseline method `RNN-Stega` in the paper.
3. `arithmetic_baseline.py`: implementations of baseline method `Arithmetic` in the paper.
4. `saac.py`: implementations of our proposed method `SAAC` in the paper.

## How to run

You can run all steganography methods in two modes: 

1. `run_single_end2end.py`: a script to run though the entire steganography pipeline (i.e., encryption -> encoding -> decoding -> decryption) on `one plaintext`.
2. `run_batch_encode.py`: a script to run the encryption+encoding steps on `a batch of plaintexts`.

Example commands are included in `run_all.sh`.

## Cite

```
@inproceedings{Shen2020SAAC,
  title={Near-imperceptible Neural Linguistic Steganography via Self-Adjusting Arithmetic Coding},
  author={Jiaming Shen and Heng Ji and Jiawei Han},
  booktitle={EMNLP},
  year={2020}
}
```
