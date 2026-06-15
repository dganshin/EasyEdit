from copy import deepcopy
from functools import partial
import inspect
import random
import time
from typing import Any, Dict, List, Tuple
from peft import get_peft_model, AdaLoraConfig, TaskType, get_peft_model_state_dict, set_peft_model_state_dict, LoraConfig
import torch
from tqdm import tqdm
from torch.utils.data import DataLoader, Dataset, Sampler
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoProcessor

from .lora_hparams import LoRAHyperParams
from .lora_multimodal_hparams import LoRAMultimodalHyperParams


def apply_lora_to_model(
        model: AutoModelForCausalLM,
        tok: AutoTokenizer,
        requests: List[Dict],
        hparams: LoRAHyperParams,
        copy=False,
        return_orig_weights=False,
        keep_original_weight=False,
        **kwargs: Any,
) -> Tuple[AutoModelForCausalLM, Dict[str, Any]]:
    """
    Returns a model with the desired changes.
    :param copy: If true, will preserve the original model while creating a new one to edit.
        Note that you are responsible for deallocating the new model's memory to avoid leaks.
    :return: (1) the updated model, (2) the weights that changed
    """
    weights_copy = {}
    if copy:
        model = deepcopy(model)

    edited_model, train_stats = execute_lora(model, tok, requests, hparams, keep_original_weight)

    return edited_model, {"weights": weights_copy, "train_stats": train_stats}


def execute_lora(
        model: AutoModelForCausalLM,
        tok: AutoTokenizer,
        requests: List[Dict],
        hparams: LoRAHyperParams,
        keep_original_weight=False,
        **kwargs: Any,
) -> Dict[str, Tuple[torch.Tensor]]:
    """
    Executes the Lora update algorithm for the specified update at the specified layer
    Invariant: model at beginning of function == model at end of function
    """
    model.config.use_cache = False
    model.supports_gradient_checkpointing = True  #
    if getattr(hparams, "use_gradient_checkpointing", True):
        model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    if hparams.lora_type == "lora":
        Config = LoraConfig
    elif hparams.lora_type == "adalora":
        Config = AdaLoraConfig
    else:
        raise NotImplementedError
    if not keep_original_weight and hasattr(model,'peft_config'):
        peft_model = model
    else:
        peft_config = Config(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=hparams.rank,
            lora_alpha=hparams.lora_alpha, lora_dropout=hparams.lora_dropout,
            layers_to_transform=hparams.layers if len(hparams.layers) > 0 else None,
            target_modules=hparams.target_modules
        )
        peft_model = get_peft_model(model, peft_config)

    peft_model.is_parallelizable = True
    peft_model.model_parallel = True
    if hasattr(peft_model, 'print_trainable_parameters'):
        peft_model.print_trainable_parameters()
    requests = deepcopy(requests)
    preview_limit = min(5, len(requests))
    for idx, request in enumerate(requests):
        if '{}' in request['prompt']:
            request['prompt'] = request['prompt'].format(request['subject'])
        if idx < preview_limit:
            print(
                f"Executing LoRA algo for: "
                f"[{request['prompt']}] -> [{request['target_new']}]"
            )
    if len(requests) > preview_limit:
        print(f"... skipped {len(requests) - preview_limit} additional requests in preview")
    device = torch.device(f'cuda:{hparams.device}')
    texts = [r["prompt"] for r in requests]
    targets = [r["target_new"] for r in requests]

    adam_kwargs = {
        "lr": hparams.lr,
        "weight_decay": hparams.weight_decay,
        "eps": getattr(hparams, "adam_eps", 1e-8),
    }
    if device.type == "cuda" and "fused" in inspect.signature(torch.optim.Adam).parameters:
        adam_kwargs["fused"] = True
    opt = torch.optim.Adam(
        peft_model.parameters(),
        **adam_kwargs,
    )
    train_loader, dataset_stats = build_lora_dataloader(requests, tok, hparams)
    benchmark_steps = max(0, int(getattr(hparams, "benchmark_steps", 0)))
    log_interval = max(1, int(getattr(hparams, "log_interval", 10)))
    autocast_dtype = resolve_autocast_dtype(peft_model)
    loss_meter = AverageMeter()
    global_step = 0
    total_step_time = 0.0
    total_samples = 0
    total_tokens = 0
    total_target_tokens = 0
    total_padding_tokens = 0
    max_memory_allocated = 0
    stop_after_benchmark = False

    for it in range(hparams.num_steps):
        loss_meter.reset()
        progress = tqdm(
            train_loader,
            total=len(train_loader),
            desc=f"LoRA Epoch {it + 1}/{hparams.num_steps}",
            leave=False,
        )
        for batch_idx, batch in enumerate(progress, start=1):
            opt.zero_grad(set_to_none=True)
            input_ids = batch["input_ids"].to(device, non_blocking=getattr(hparams, "pin_memory", True))
            attention_mask = batch["attention_mask"].to(device, non_blocking=getattr(hparams, "pin_memory", True))
            labels = batch["labels"].to(device, non_blocking=getattr(hparams, "pin_memory", True))
            bs = input_ids.shape[0]
            step_tokens = int(attention_mask.sum().item())
            step_target_tokens = int((labels != -100).sum().item())
            step_padding_tokens = int((attention_mask.numel() - attention_mask.sum().item()))
            step_start = time.perf_counter()
            with torch.autocast(device_type="cuda", dtype=autocast_dtype, enabled=autocast_dtype is not None):
                pred = peft_model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                loss = pred.loss
            if not torch.isfinite(loss):
                raise RuntimeError(
                    f"LoRA training encountered non-finite loss: {loss.item()}. "
                    f"Try lowering lr / batch_size / rank, or enabling stronger gradient clipping."
                )
            loss.backward()
            max_grad_norm = getattr(hparams, "max_grad_norm", 0.0)
            if max_grad_norm and max_grad_norm > 0:
                torch.nn.utils.clip_grad_norm_(peft_model.parameters(), max_grad_norm)
            opt.step()

            step_time = time.perf_counter() - step_start
            global_step += 1
            total_step_time += step_time
            total_samples += bs
            total_tokens += step_tokens
            total_target_tokens += step_target_tokens
            total_padding_tokens += step_padding_tokens
            if device.type == "cuda":
                max_memory_allocated = max(max_memory_allocated, torch.cuda.max_memory_allocated(device))

            loss_meter.update(loss.item(), n=bs)
            if batch_idx % log_interval == 0 or batch_idx == len(train_loader):
                current_tokens_per_sec = step_tokens / max(step_time, 1e-8)
                progress.set_postfix(
                    loss=f"{loss.item():.4f}",
                    avg=f"{loss_meter.avg:.4f}",
                    tok_s=f"{current_tokens_per_sec:.0f}",
                )
            if benchmark_steps and global_step >= benchmark_steps:
                stop_after_benchmark = True
                break
        progress.close()
        print(f"LoRA Epoch {it + 1}/{hparams.num_steps} avg_loss={loss_meter.avg:.6f}")
        if stop_after_benchmark:
            break

    avg_step_time = total_step_time / max(global_step, 1)
    train_stats = {
        "num_steps_completed": global_step,
        "avg_step_time_sec": avg_step_time,
        "samples_per_sec": total_samples / max(total_step_time, 1e-8),
        "tokens_per_sec": total_tokens / max(total_step_time, 1e-8),
        "target_tokens_per_sec": total_target_tokens / max(total_step_time, 1e-8),
        "padding_ratio": total_padding_tokens / max(total_tokens + total_padding_tokens, 1),
        "max_gpu_memory_gb": max_memory_allocated / (1024 ** 3),
        "benchmark_steps": benchmark_steps,
        "stopped_after_benchmark": stop_after_benchmark,
        "dataset_stats": dataset_stats,
    }
    return peft_model, train_stats




def apply_lora_to_multimodal_model(
        model: AutoModelForCausalLM,
        tok: AutoProcessor,
        requests: List[Dict],
        hparams: LoRAMultimodalHyperParams,
        copy=False,
        return_orig_weights=False,
        keep_original_weight=False,
        **kwargs: Any,
) -> Tuple[AutoModelForCausalLM, Dict[str, Any]]:
    """
    Returns a model with the desired changes.
    :param copy: If true, will preserve the original model while creating a new one to edit.
        Note that you are responsible for deallocating the new model's memory to avoid leaks.
    :return: (1) the updated model, (2) the weights that changed
    """
    weights_copy = {}
    device = f'cuda:{hparams.device}'
    if copy:
        model = deepcopy(model)
        model.to(device)

    edited_model = execute_multimodal_lora(model, tok, requests, hparams, keep_original_weight)

    return edited_model, weights_copy

# import deepspeed

def execute_multimodal_lora(
        model: AutoModelForCausalLM,
        processor: AutoProcessor,
        requests: List[Dict],
        hparams: LoRAMultimodalHyperParams,
        keep_original_weight=False,
        **kwargs: Any,
) -> Dict[str, Tuple[torch.Tensor]]:
    """
    Executes the Lora update algorithm for the specified update at the specified layer
    Invariant: model at beginning of function == model at end of function
    """
    model.config.use_cache = False
    model.supports_gradient_checkpointing = True  #
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    
    if hparams.lora_type == "lora":
        Config = LoraConfig
    elif hparams.lora_type == "adalora":
        Config = AdaLoraConfig
    else:
        raise NotImplementedError
    if not keep_original_weight and hasattr(model,'peft_config'):
        peft_model = model
    else:
        peft_config = Config(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=hparams.rank,
            lora_alpha=hparams.lora_alpha, lora_dropout=hparams.lora_dropout,
            target_modules=hparams.target_modules
        )
        peft_model = get_peft_model(model, peft_config)

    peft_model.to(dtype=torch.float32)
    peft_model.is_parallelizable = True
    peft_model.model_parallel = True
    from torch.optim.lr_scheduler import ExponentialLR
    opt = torch.optim.SGD(
        peft_model.parameters(),
        lr=hparams.lr,
        weight_decay=hparams.weight_decay,
    )
    sheduler = ExponentialLR(opt, gamma=hparams.sh_lr)    
    if hasattr(peft_model, 'print_trainable_parameters'):
        peft_model.print_trainable_parameters()
    requests = deepcopy(requests)
    for request in requests:
        print(
            f"Executing LoRA algo for: "
            f"[{request['prompt']}] -> [{request['target']}]"
        )
    device = torch.device(f'cuda:{hparams.device}')
    # Define inputs
    prompts = [r["prompt"] for r in requests]
    labels = [r["target"] for r in requests]
    file_type = requests[0]['file_type']
    input_images = [r['image'] for r in requests]
    loss_meter = AverageMeter()
    prompt_batches = list(chunks(prompts, hparams.batch_size))
    label_batches = list(chunks(labels, hparams.batch_size))
    
    for it in range(hparams.num_steps):
        loss_meter.reset()
        progress = tqdm(
            zip(prompt_batches, label_batches),
            total=len(prompt_batches),
            desc=f"MM-LoRA Epoch {it + 1}/{hparams.num_steps}",
            leave=False,
        )
        for txt, tgt in progress:
            mask_token = -100
            opt.zero_grad()
            
            if hasattr(hparams, 'use_chat_template') and hparams.use_chat_template:
                if file_type == "video":
                    temp_prompt = [processor.apply_chat_template([
                                            {

                                                "role": "user",
                                                "content": [
                                                    {"type": "video"},
                                                    {"type": "text", "text": p},
                                                    ],
                                            },
                                        ],
                                                        add_generation_prompt=True,
                                                        tokenize=False) + l
                                    for p, l in zip(prompts, labels)]
                    
                elif file_type in ["image", "single-image", "multi-image"]:
                    if file_type == "multi-image":
                        num_images = len(input_images[0])
                    else:
                        num_images = 1
                    
                    temp_prompt = [processor.apply_chat_template([
                                            {

                                                "role": "user",
                                                "content": [{"type": "image"}] * num_images + [{"type": "text", "text": p}],
                                            },
                                        ],
                                                        add_generation_prompt=True,
                                                        tokenize=False)  + l
                                    for p, l in zip(prompts, labels)]              
                else:
                    raise AssertionError("Not support file type: {}".format(file_type))
                
                full_prompt = temp_prompt
                if file_type in ["image", "single-image", "multi-image"]:
                    multimodal_inputs = processor(images=input_images, text=full_prompt, return_tensors="pt", padding=True).to(device, dtype=torch.float32)
                elif file_type == "video":
                    multimodal_inputs = processor(videos=input_images[0], text=full_prompt, return_tensors="pt", padding=True).to(device, dtype=torch.float32)
                    
                tokens = multimodal_inputs
                            
            targets = processor.tokenizer(labels[0], add_special_tokens=False,
                     return_tensors="pt", padding=True, max_length=multimodal_inputs["input_ids"].size(1))["input_ids"]
    
            labels_ids = torch.full_like(multimodal_inputs["input_ids"], -100)
            labels_ids[:, -targets.size(1):] = targets
            tokens["labels"] = labels_ids
            
            tokens = tokens.to(device)
            pred = peft_model(**tokens)
            loss = pred.loss
            if not torch.isfinite(loss):
                raise RuntimeError(
                    f"Multimodal LoRA training encountered non-finite loss: {loss.item()}."
                )
            progress.set_postfix(loss=f"{loss.item():.4f}", avg=f"{loss_meter.avg:.4f}")
            # loss_meter.update(loss.item(), n=bs)
            loss_meter.update(loss.item(), n=1)

            # if loss.item() >= 1e-3:
            loss.backward()
            opt.step()
            sheduler.step()
        progress.close()
        print(f"MM-LoRA Epoch {it + 1}/{hparams.num_steps} avg_loss={loss_meter.avg:.6f}")

        # if loss_meter.avg < 1e-3:
        #     break
    return peft_model







class AverageMeter:
    """Computes and stores the average and current value"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


class TokenizedRequestDataset(Dataset):
    def __init__(self, samples: List[Dict[str, torch.Tensor]]):
        self.samples = samples
        self.lengths = [int(sample["input_ids"].shape[0]) for sample in samples]

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> Dict[str, torch.Tensor]:
        return self.samples[index]


class LengthBucketBatchSampler(Sampler[List[int]]):
    def __init__(self, lengths: List[int], batch_size: int, shuffle: bool = True, seed: int = 42):
        self.lengths = lengths
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.seed = seed

    def __iter__(self):
        rng = random.Random(self.seed)
        indices = list(range(len(self.lengths)))
        if self.shuffle:
            rng.shuffle(indices)
        indices.sort(key=lambda idx: self.lengths[idx])
        batches = [indices[start:start + self.batch_size] for start in range(0, len(indices), self.batch_size)]
        if self.shuffle:
            rng.shuffle(batches)
        for batch in batches:
            yield batch

    def __len__(self) -> int:
        return (len(self.lengths) + self.batch_size - 1) // self.batch_size


def resolve_autocast_dtype(model) -> torch.dtype | None:
    try:
        param_dtype = next(model.parameters()).dtype
    except StopIteration:
        return None
    if param_dtype in (torch.float16, torch.bfloat16):
        return param_dtype
    return None


def tokenize_requests_once(
    requests: List[Dict[str, Any]],
    tok: AutoTokenizer,
    max_length: int,
) -> tuple[List[Dict[str, torch.Tensor]], Dict[str, Any]]:
    texts = [r["prompt"] for r in requests]
    targets = [r["target_new"] for r in requests]
    full_texts = [f"{prompt} {target}" for prompt, target in zip(texts, targets)]

    prompt_encodings = tok(
        texts,
        add_special_tokens=True,
        truncation=True,
        max_length=max_length,
        padding=False,
    )
    full_encodings = tok(
        full_texts,
        add_special_tokens=True,
        truncation=True,
        max_length=max_length,
        padding=False,
    )

    samples: List[Dict[str, torch.Tensor]] = []
    total_input_tokens = 0
    total_target_tokens = 0
    for prompt_ids, full_ids in zip(prompt_encodings["input_ids"], full_encodings["input_ids"]):
        prompt_len = min(len(prompt_ids), len(full_ids))
        labels = list(full_ids)
        for idx in range(prompt_len):
            labels[idx] = -100
        input_tensor = torch.tensor(full_ids, dtype=torch.long)
        label_tensor = torch.tensor(labels, dtype=torch.long)
        samples.append(
            {
                "input_ids": input_tensor,
                "labels": label_tensor,
            }
        )
        total_input_tokens += len(full_ids)
        total_target_tokens += int((label_tensor != -100).sum().item())

    lengths = [sample["input_ids"].shape[0] for sample in samples]
    stats = {
        "num_samples": len(samples),
        "avg_sequence_length": (sum(lengths) / len(lengths)) if lengths else 0.0,
        "max_sequence_length_observed": max(lengths) if lengths else 0,
        "avg_target_tokens": (total_target_tokens / len(samples)) if samples else 0.0,
        "total_input_tokens": total_input_tokens,
        "total_target_tokens": total_target_tokens,
    }
    return samples, stats


def collate_tokenized_batch(batch: List[Dict[str, torch.Tensor]], pad_token_id: int) -> Dict[str, torch.Tensor]:
    max_len = max(int(item["input_ids"].shape[0]) for item in batch)
    batch_size = len(batch)
    input_ids = torch.full((batch_size, max_len), pad_token_id, dtype=torch.long)
    attention_mask = torch.zeros((batch_size, max_len), dtype=torch.long)
    labels = torch.full((batch_size, max_len), -100, dtype=torch.long)
    for idx, item in enumerate(batch):
        seq_len = int(item["input_ids"].shape[0])
        input_ids[idx, :seq_len] = item["input_ids"]
        attention_mask[idx, :seq_len] = 1
        labels[idx, :seq_len] = item["labels"]
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
    }


def build_lora_dataloader(
    requests: List[Dict[str, Any]],
    tok: AutoTokenizer,
    hparams: LoRAHyperParams,
) -> tuple[DataLoader, Dict[str, Any]]:
    max_length = int(getattr(hparams, "max_length", 128))
    samples, token_stats = tokenize_requests_once(requests, tok, max_length)
    dataset = TokenizedRequestDataset(samples)
    num_workers = max(0, int(getattr(hparams, "dataloader_num_workers", 0)))
    prefetch_factor = max(2, int(getattr(hparams, "prefetch_factor", 2)))
    pin_memory = bool(getattr(hparams, "pin_memory", True))
    persistent_workers = bool(getattr(hparams, "persistent_workers", True)) and num_workers > 0
    group_by_length = bool(getattr(hparams, "group_by_length", False))
    seed = int(getattr(hparams, "seed", 42))

    loader_kwargs: Dict[str, Any] = {
        "num_workers": num_workers,
        "pin_memory": pin_memory,
        "persistent_workers": persistent_workers,
        "collate_fn": partial(collate_tokenized_batch, pad_token_id=tok.pad_token_id),
    }
    if num_workers > 0:
        loader_kwargs["prefetch_factor"] = prefetch_factor

    if group_by_length:
        batch_sampler = LengthBucketBatchSampler(dataset.lengths, hparams.batch_size, shuffle=True, seed=seed)
        loader = DataLoader(dataset, batch_sampler=batch_sampler, **loader_kwargs)
    else:
        loader = DataLoader(dataset, batch_size=hparams.batch_size, shuffle=True, **loader_kwargs)

    token_stats.update(
        {
            "pad_token_id": tok.pad_token_id,
            "group_by_length": group_by_length,
            "dataloader_num_workers": num_workers,
            "pin_memory": pin_memory,
            "persistent_workers": persistent_workers,
            "prefetch_factor": prefetch_factor if num_workers > 0 else None,
            "num_batches_per_epoch": len(loader),
        }
    )
    return loader, token_stats


def chunks(arr, n):
    """Yield successive n-sized chunks from arr."""
    chunk = []
    for a in arr:
        chunk.append(a)
        if len(chunk) == n:
            yield chunk
            chunk = []
    if len(chunk) > 0:
        yield chunk
