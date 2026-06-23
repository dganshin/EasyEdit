# Model Availability Report

- created_at: `2026-06-23T00:12:33`
- download_gptj: `False`
- hf_endpoint: `https://hf-mirror.com`

## GPT-J-6B

- `/root/autodl-tmp/models/gpt-j-6B` exists=True files=1
- `/root/autodl-tmp/models/GPT-J-6B` exists=False files=None

- HF cache candidates: `['/root/autodl-tmp/hf_cache/hub/models--EleutherAI--gpt-j-6b']`
- download result: `None`
- config/tokenizer check: `{'checked': True, 'ok': False, 'reason': "ValueError('Unrecognized model in /root/autodl-tmp/models/gpt-j-6B. Should have a `model_type` key in its config.json, or contain one of the following strings in its name: albert, align, altclip, audio-spectrogram-transformer, autoformer, bark, bart, beit, bert, bert-generation, big_bird, bigbird_pegasus, biogpt, bit, blenderbot, blenderbot-small, blip, blip-2, bloom, bridgetower, bros, camembert, canine, chameleon, chinese_clip, chinese_clip_vision_model, clap, clip, clip_text_model, clip_vision_model, clipseg, clvp, code_llama, codegen, cohere, conditional_detr, convbert, convnext, convnextv2, cpmant, ctrl, cvt, dac, data2vec-audio, data2vec-text, data2vec-vision, dbrx, deberta, deberta-v2, decision_transformer, deformable_detr, deit, depth_anything, deta, detr, dinat, dinov2, distilbert, donut-swin, dpr, dpt, efficientformer, efficientnet, electra, encodec, encoder-decoder, ernie, ernie_m, esm, falcon, falcon_mamba, fastspeech2_conformer, flaubert, flava, fnet, focalnet, fsmt, funnel, fuyu, gemma, gemma2, git, glm, glpn, gpt-sw3, gpt2, gpt_bigcode, gpt_neo, gpt_neox, gpt_neox_japanese, gptj, gptsan-japanese, granite, granitemoe, graphormer, grounding-dino, groupvit, hiera, hubert, ibert, idefics, idefics2, idefics3, imagegpt, informer, instructblip, instructblipvideo, jamba, jetmoe, jukebox, kosmos-2, layoutlm, layoutlmv2, layoutlmv3, led, levit, lilt, llama, llava, llava_next, llava_next_video, llava_onevision, longformer, longt5, luke, lxmert, m2m_100, mamba, mamba2, marian, markuplm, mask2former, maskformer, maskformer-swin, mbart, mctct, mega, megatron-bert, mgp-str, mimi, mistral, mixtral, mllama, mobilebert, mobilenet_v1, mobilenet_v2, mobilevit, mobilevitv2, moshi, mpnet, mpt, mra, mt5, musicgen, musicgen_melody, mvp, nat, nemotron, nezha, nllb-moe, nougat, nystromformer, olmo, olmoe, omdet-turbo, oneformer, open-llama, openai-gpt, opt, owlv2, owlvit, paligemma, patchtsmixer, patchtst, pegasus, pegasus_x, perceiver, persimmon, phi, phi3, phimoe, pix2struct, pixtral, plbart, poolformer, pop2piano, prophetnet, pvt, pvt_v2, qdqbert, qwen2, qwen2_audio, qwen2_audio_encoder, qwen2_moe, qwen2_vl, rag, realm, recurrent_gemma, reformer, regnet, rembert, resnet, retribert, roberta, roberta-prelayernorm, roc_bert, roformer, rt_detr, rt_detr_resnet, rwkv, sam, seamless_m4t, seamless_m4t_v2, segformer, seggpt, sew, sew-d, siglip, siglip_vision_model, speech-encoder-decoder, speech_to_text, speech_to_text_2, speecht5, splinter, squeezebert, stablelm, starcoder2, superpoint, swiftformer, swin, swin2sr, swinv2, switch_transformers, t5, table-transformer, tapas, time_series_transformer, timesformer, timm_backbone, trajectory_transformer, transfo-xl, trocr, tvlt, tvp, udop, umt5, unispeech, unispeech-sat, univnet, upernet, van, video_llava, videomae, vilt, vipllava, vision-encoder-decoder, vision-text-dual-encoder, visual_bert, vit, vit_hybrid, vit_mae, vit_msn, vitdet, vitmatte, vits, vivit, wav2vec2, wav2vec2-bert, wav2vec2-conformer, wavlm, whisper, xclip, xglm, xlm, xlm-prophetnet, xlm-roberta, xlm-roberta-xl, xlnet, xmod, yolos, yoso, zamba, zoedepth')"}`

## LLaMA-2 Backup

- backup repo: `NousResearch/Llama-2-7b-hf`
- download result: `{'downloaded': False, 'repo_id': 'NousResearch/Llama-2-7b-hf', 'target': '/root/autodl-tmp/models/Llama-2-7b-hf-nousresearch', 'error': "LocalEntryNotFoundError('An error happened while trying to locate the file on the Hub and we cannot find the requested files in the local cache. Please check your connection and try again or make sure your Internet connection is on.')", 'traceback_tail': 'Traceback (most recent call last):\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/huggingface_hub/file_download.py", line 1572, in _get_metadata_or_catch_error\n    raise FileMetadataError(\nhuggingface_hub.errors.FileMetadataError: Distant resource does not seem to be on huggingface.co. It is possible that a configuration issue prevents you from downloading resources from https://huggingface.co. Please check your firewall and proxy settings and make sure your SSL certificates are updated.\n\nThe above exception was the direct cause of the following exception:\n\nTraceback (most recent call last):\n  File "/root/autodl-tmp/projects/EasyEdit/scripts/check_public_model_availability.py", line 82, in safe_snapshot\n    return snapshot_to_dir(repo_id, target)\n  File "/root/autodl-tmp/projects/EasyEdit/scripts/check_public_model_availability.py", line 71, in snapshot_to_dir\n    local_dir = snapshot_download(\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/huggingface_hub/utils/_validators.py", line 114, in _inner_fn\n    return fn(*args, **kwargs)\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/huggingface_hub/_snapshot_download.py", line 332, in snapshot_download\n    thread_map(\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/tqdm/contrib/concurrent.py", line 69, in thread_map\n    return _executor_map(ThreadPoolExecutor, fn, *iterables, **tqdm_kwargs)\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/tqdm/contrib/concurrent.py", line 51, in _executor_map\n    return list(tqdm_class(ex.map(fn, *iterables, chunksize=chunksize), **kwargs))\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/tqdm/std.py", line 1181, in __iter__\n    for obj in iterable:\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/concurrent/futures/_base.py", line 621, in result_iterator\n    yield _result_or_cancel(fs.pop())\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/concurrent/futures/_base.py", line 319, in _result_or_cancel\n    return fut.result(timeout)\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/concurrent/futures/_base.py", line 458, in result\n    return self.__get_result()\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/concurrent/futures/_base.py", line 403, in __get_result\n    raise self._exception\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/concurrent/futures/thread.py", line 58, in run\n    result = self.fn(*self.args, **self.kwargs)\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/huggingface_hub/_snapshot_download.py", line 306, in _inner_hf_hub_download\n    return hf_hub_download(\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/huggingface_hub/utils/_validators.py", line 114, in _inner_fn\n    return fn(*args, **kwargs)\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/huggingface_hub/file_download.py", line 994, in hf_hub_download\n    return _hf_hub_download_to_local_dir(\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/huggingface_hub/file_download.py", line 1257, in _hf_hub_download_to_local_dir\n    _raise_on_head_call_error(head_call_error, force_download, local_files_only)\n  File "/root/miniconda3/envs/easyedit/lib/python3.10/site-packages/huggingface_hub/file_download.py", line 1665, in _raise_on_head_call_error\n    raise LocalEntryNotFoundError(\nhuggingface_hub.errors.LocalEntryNotFoundError: An error happened while trying to locate the file on the Hub and we cannot find the requested files in the local cache. Please check your connection and try again or make sure your Internet connection is on.\n'}`

## Qwen2.5-7B

- `/root/autodl-tmp/models/Qwen2.5-7B` exists=True files=20

## LLaMA-2-7B Probe Only

- `/root/autodl-tmp/models/Llama-2-7b-hf` exists=False files=None
- `/root/autodl-tmp/models/llama-2-7b` exists=False files=None
- `/root/autodl-tmp/models/LLaMA-2-7B` exists=False files=None
- `/root/autodl-tmp/models/Llama-2-7b-hf-nousresearch` exists=True files=1

## Server Download Command

```bash
cd /root/autodl-tmp/projects/EasyEdit
bash /root/start_mihomo.sh || true
conda activate easyedit
export HF_HOME=/root/autodl-tmp/hf_cache/hf
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf_cache/transformers
export HF_DATASETS_CACHE=/root/autodl-tmp/hf_cache/datasets
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export HF_ENDPOINT=https://hf-mirror.com
python3 scripts/check_public_model_availability.py --download_gptj --hf_endpoint https://hf-mirror.com
```
