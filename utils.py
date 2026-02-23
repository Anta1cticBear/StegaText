import torch
import numpy as np
import bitarray

from transformers import AutoModelForCausalLM, AutoTokenizer


class ModelWrapper:
    """Wrapper to make modern HF models return (logits, past) tuples like old GPT2."""
    def __init__(self, model):
        self.model = model

    def __call__(self, input_ids, past=None):
        outputs = self.model(input_ids, past_key_values=past, use_cache=True)
        return outputs.logits, outputs.past_key_values

    def to(self, device):
        self.model.to(device)
        return self

    def eval(self):
        self.model.eval()
        return self


def limit_past(past):
    if past is None:
        return past
    # DynamicCache: trim each layer's keys/values to keep the last 1022 tokens
    for layer in past.layers:
        layer.keys = layer.keys[:, :, -1022:, :]
        layer.values = layer.values[:, :, -1022:, :]
    return past

def kl(q, logq, logp):
    res = q*(logq-logp)/0.69315
    res[q==0] = 0
    return res.sum().item() # in bits

def entropy(q, logq):
    res = q*logq/0.69315
    res[q==0] = 0
    return -res.sum().item() # in bits

# e.g. [0, 1, 1, 1] looks like 1110=14
def bits2int(bits):
    res = 0
    for i, bit in enumerate(bits):
        res += bit*(2**i)
    return res

# LSB -> MSB
def int2bits(inp, num_bits):
    if num_bits == 0:
        return []
    strlist = ('{0:0%db}'%num_bits).format(inp)
    return [int(strval) for strval in reversed(strlist)]

def is_sent_finish(token_idx, enc):
    token = enc.decoder[token_idx]
    return '.' in token or '!' in token or '?' in token

def num_same_from_beg(bits1, bits2):
    assert len(bits1) == len(bits2)
    for i in range(len(bits1)):
        if bits1[i] != bits2[i]:
            break

    return i

def encode_context(raw_text, enc):
    context_tokens = [enc.eos_token_id] + enc.encode(raw_text)
    return context_tokens

def get_model(seed=1234, model_name='Qwen/Qwen3-0.6B', device_id="0"):
    np.random.seed(seed)
    torch.random.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    device = torch.device(f"cuda:{device_id}" if torch.cuda.is_available() else "cpu")

    enc = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

    # Add encoder/decoder dicts for compatibility with GPT2-style code throughout
    # the codebase (e.g., enc.encoder[token_str], enc.decoder[token_id]).
    # These attributes are added directly to the tokenizer instance for simplicity,
    # as they are used pervasively in encode/decode functions across all modules.
    vocab = enc.get_vocab()
    enc.encoder = vocab
    enc.decoder = {v: k for k, v in vocab.items()}

    # Wrap encode to not add special tokens by default (matching GPT2 behavior).
    # The original GPT2Tokenizer.encode() did not add special tokens, and the
    # steganography algorithms rely on this for correct bit encoding/decoding.
    _original_encode = enc.encode
    def _encode_no_special(text, **kwargs):
        kwargs.setdefault('add_special_tokens', False)
        return _original_encode(text, **kwargs)
    enc.encode = _encode_no_special

    raw_model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)
    model = ModelWrapper(raw_model)
    model.to(device)
    model.eval()

    return enc, model, device

enc32_itoc = ['\0', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '.', ',', "'", '!', ' ']
enc32_ctoi = {k: v for v, k in enumerate(enc32_itoc)}
def enc32(text):
    bits = []
    for c in text:
        bits.extend(int2bits(enc32_ctoi[c], 5))
    return bits

def dec32(bits):
    text = ''
    for i in range(0, len(bits), 5):
        c = enc32_itoc[bits2int(bits[i:i+5])]
        if c == '\0':
            break
        text += c
    return text

# message should be bit string
# encoded should be text string
def expansion_ratio(message, encoded):
    message_bits = len(message)
    encoded_ba = bitarray.bitarray()
    encoded_ba.frombytes(encoded.encode('utf-8'))
    encoded_bits = len(encoded_ba.tolist())
    return encoded_bits/message_bits

def get_output_file_name(args):
    dataset_path = args["dataset_path"]
    encryption_method = args["encrypt"]
    steganography_method = args["encode"]
    if steganography_method in ["bins", "huffman"]:
        block_size = args["block_size"]
        output_name = f"{dataset_path}/results_{encryption_method}_{steganography_method}_block_{block_size}.json"
    elif steganography_method == "patient-huffman":
        block_size = args["block_size"]
        epsilon = args["epsilon"]
        output_name = f"{dataset_path}/results_{encryption_method}_{steganography_method}_block_{block_size}_epsilon_{epsilon}.json"
    elif steganography_method == "arithmetic":
        precision = args["precision"]
        temp = args["temp"]
        topK = args["topK"]
        output_name = f"{dataset_path}/results_{encryption_method}_{steganography_method}_precision_{precision}_temp_{temp}_topK_{topK}.json"
    elif steganography_method == "saac":
        precision = args["precision"]
        temp = args["temp"]
        delta = args["delta"]
        output_name = f"{dataset_path}/results_{encryption_method}_{steganography_method}_precision_{precision}_temp_{temp}_delta_{delta}.json"
    else:
        output_name = ""
    return output_name
