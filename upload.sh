#!/bin/bash
set -e

# 压缩包名称
file="Qwen3-14b-finetuned-merged-$(date "+%Y%m%d-%H%M%S").zip"
# 把 Qwen3-14b-finetuned-merged 目录做成 zip 压缩包
zip -q -r "${file}" Qwen3-14b-finetuned-merged
# 通过 oss 上传到个人数据中的 backup 文件夹中
oss cp "${file}" oss://backup/