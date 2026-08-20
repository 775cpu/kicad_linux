#!/usr/bin/env bash
set -Eeuo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
output_dir=${OUTPUT_DIR:-"$script_dir/generated"}
library_dir="$output_dir/my_lib.pretty"
footprint_name=${FOOTPRINT_NAME:-Test_THT_2Pad}

install_packages() {
    local apt_runner=(apt-get)
    if [[ ${EUID} -ne 0 ]]; then
        command -v sudo >/dev/null 2>&1 || {
            echo "需要 root 权限或 sudo 才能安装 KiCad。" >&2
            exit 1
        }
        apt_runner=(sudo apt-get)
    fi

    "${apt_runner[@]}" update
    "${apt_runner[@]}" install -y kicad python3-pip python3-venv
}

if ! command -v kicad-cli >/dev/null 2>&1; then
    echo "未找到 kicad-cli，开始安装 KiCad 和 Python 依赖..."
    install_packages
fi

kicad_cli=$(command -v kicad-cli)
python_bin=${KICAD_PYTHON:-}
if [[ -z "$python_bin" ]]; then
    for candidate in python3 /usr/lib/kicad/bin/python3 /usr/bin/python3; do
        if [[ -x "$candidate" ]]; then
            python_bin=$candidate
            break
        fi
    done
fi
[[ -n "$python_bin" ]] || { echo "找不到可用的 Python 解释器。" >&2; exit 1; }

if ! "$python_bin" -c 'import KicadModTree' >/dev/null 2>&1; then
    echo "使用 $python_bin 安装 KicadModTree..."
    "$python_bin" -m pip install --user --break-system-packages KicadModTree
fi

mkdir -p "$library_dir"
"$python_bin" "$script_dir/generate_two_tht.py" --output-dir "$library_dir" --name "$footprint_name"

svg_dir="$output_dir/svg"
rm -rf "$svg_dir"
mkdir -p "$svg_dir"
"$kicad_cli" fp export svg \
    --layers F.Cu,F.SilkS,Edge.Cuts \
    -o "$svg_dir" \
    "$library_dir"

svg_path="$svg_dir/${footprint_name}.svg"
[[ -s "$svg_path" ]] || { echo "SVG 为空或没有生成: $svg_path" >&2; exit 1; }
grep -Eq '<(svg|path|circle|rect|line|polygon|use)([ >])' "$svg_path" || {
    echo "SVG 没有可绘制内容: $svg_path" >&2
    exit 1
}

echo "完成。"
echo "封装: $library_dir/${footprint_name}.kicad_mod"
echo "SVG:  $svg_path ($(wc -c < "$svg_path") bytes)"