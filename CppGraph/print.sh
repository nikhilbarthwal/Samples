a2ps -o library.ps --font-size=10 -R --columns=1 Library/*.h Library/*.cpp
a2ps -o examples.ps --font-size=10 -R --columns=1 Examples/*.cpp
ps2pdf library.ps
ps2pdf examples.ps
rm library.ps examples.ps
cp ../format.py .
python3 format.py Library/*.h Library/*.cpp Examples/*.cpp
rm format.py

