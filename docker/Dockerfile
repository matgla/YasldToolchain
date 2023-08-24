FROM archlinux:base-20230723.0.166908 

RUN pacman --noconfirm -Syu
RUN pacman --noconfirm -Sy gcc clang cmake
RUN pacman --noconfirm -S git base-devel
RUN mkdir -p /tmp/yay-build
RUN useradd -m -G wheel builder && passwd -d builder && chown -R builder:builder /tmp/yay-build
RUN echo "builder ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN su - builder -c "git clone https://aur.archlinux.org/yay.git /tmp/yay-build/yay"
RUN su - builder -c "cd /tmp/yay-build/yay && makepkg -si --noconfirm"
RUN rm -rf /tmp/yay-build
RUN su - builder -c "yay --noconfirm -Syu && yay --noconfirm -Sy arm-none-eabi-gcc\
  arm-none-eabi-gdb arm-none-eabi-newlib arm-none-eabi-binutils"
RUN su - builder -c "yay --noconfirm -Syu && yay --noconfirm -Sy renode"
RUN pacman -Sy --noconfirm python-virtualenv
RUN pacman -Sy --noconfirm wget
RUN cd /opt && wget https://github.com/matgla/YasldToolchain/releases/download/release_0.2/yasld-toolchain-0.2.tar.xz
RUN cd /opt && tar -xJvf yasld-toolchain-0.2.tar.xz && rm -rf yasld-toolchain-0.2.tar.xz
ENV YASLD_TOOLCHAIN_PATH=/opt/yasld-toolchain
RUN pip install --break-system-packages -r /opt/renode/tests/requirements.txt
