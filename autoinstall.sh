
#install osmo-fl2k
git clone git://git.osmocom.org/osmo-fl2k.git
mkdir osmo-fl2k/build
cd osmo-fl2k/build
cmake ../ -DINSTALL_UDEV_RULES=ON
make -j 3
sudo make install
sudo ldconfig
cd ../..

#install csdr
git clone https://github.com/simonyiszk/csdr.git
cd csdr
make
sudo make install
cd ..

#include liquid dsp
git clone https://github.com/jgaeddert/liquid-dsp.git
cd liquid-dsp
./bootstrap.sh     # <- only if you cloned the Git repo
./configure
make
sudo make install
cd ..

#build fl2k_iq
cd src
gcc fl2k_iq.c -o fl2k_iq -losmo-fl2k -O2 -lliquid -pthread -lm
cd ..
