python3 generate_two_tht.py --output-dir generated/my_lib.pretty --name Test_THT_2Pad
rm /workspaces/kicad_linux/generated/svg/Test_THT_2Pad.svg;/usr/bin/kicad-cli fp export svg --layers F.Cu,F.SilkS,Edge.Cuts -o "/workspaces/kicad_linux/generated/svg" "/workspaces/kicad_linux/generated/my_lib.pretty"

git clone --depth=1 https://github.com/qgb/qpsu qgb

./git.py

python3 -c 'import kicad,Q;print(Q)'