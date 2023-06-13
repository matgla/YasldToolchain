#!/bin/bash 
#
# Usage: ./build.sh 
# Based on: https://stackoverflow.com/a/72448410
#         : https://archlinux.org/packages/extra/x86_64/arm-none-eabi-gcc/

export TARGET=arm-none-eabi
export PREFIX=/opt/arm-none-eabi-with-pic
export PATH=$PATH:$PREFIX/bin

export GCC_VERSION=13.1.0
export BINUTILS_VERSION=2.40
export NEWLIB_VERSION=4.3.0.20230120

mkdir build 
cd build

if [[ ! -f binutils-$BINUTILS_VERSION.tar.gz ]]
then
  wget https://ftp.gnu.org/gnu/binutils/binutils-$BINUTILS_VERSION.tar.gz 
  if [[ $? -ne 0 ]] ; then
    exit 1
  fi
fi

if [[ ! -f gcc-$GCC_VERSION.tar.xz ]]
then
  wget https://ftp.gnu.org/gnu/gcc/gcc-$GCC_VERSION/gcc-$GCC_VERSION.tar.xz
  if [[ $? -ne 0 ]] ; then
    exit 1
  fi
fi 

if [[ ! -f newlib-$NEWLIB_VERSION.tar.gz ]]
then
  wget https://sourceware.org/pub/newlib/newlib-$NEWLIB_VERSION.tar.gz 
  if [[ $? -ne 0 ]] ; then
    exit 1
  fi
fi

tar -xf binutils-$BINUTILS_VERSION.tar.gz
if [[ $? -ne 0 ]] ; then
    exit 1
fi
tar -xf gcc-$GCC_VERSION.tar.xz
if [[ $? -ne 0 ]] ; then
    exit 1
fi
tar -xf newlib-$NEWLIB_VERSION.tar.gz
if [[ $? -ne 0 ]] ; then
    exit 1
fi
 
 mkdir build-binutils
 cd binutils-$BINUTILS_VERSION 
 sed -i "/ac_cpp=/s/\$CPPFLAGS/\$CPPFLAGS -O2/"
 cd ..
 cd build-binutils
 ../binutils-$BINUTILS_VERSION/configure --target=$TARGET \
   --prefix=$PREFIX \
   --with-sysroot=$PREFIX/$TARGET \
   --enable-multilib \
   --enable-interwork \
   --with-gnu-as \
   --with-gnu-ld \
   --disable-nls \
   --enable-ld=default \
   --enable-gold \
   --enable-plugins \
   --enable-deterministic-archives
 if [[ $? -ne 0 ]] ; then
     exit 1
 fi 
 
 make -j$(nproc)
 if [[ $? -ne 0 ]] ; then
     exit 1
 fi
 
sudo make install
if [[ $? -ne 0 ]] ; then
    exit 1
fi

export CFLAGS_FOR_TARGET="-g -Os -ffunction-sections -fdata-sections -fno-exceptions -msingle-pic-base -mno-pic-data-is-text-relative -fPIC"
export CXXFLAGS_FOR_TARGET=$CFLAGS_FOR_TARGET

cd ..
mkdir build-newlib
cd build-newlib 
../newlib-$NEWLIB_VERSION/configure --target=$TARGET \
  --prefix=$PREFIX \
  --with-pic \
  --disable-newlib-supplied-syscalls \
  --enable-newlib-reent-small \
  --enable-newlib-retargetable-locking \
  --disable-newlib-fvwrite-in-streamio \
  --disable-newlib-fseek-optimization \
  --disable-newlib-wide-orient \
  --enable-newlib-nano-malloc \
  --disable-newlib-unbuf-stream-opt \
  --enable-lite-exit \
  --enable-newlib-global-atexit \
  --enable-newlib-nano-formatted-io \
  --disable-nls
if [[ $? -ne 0 ]] ; then
    exit 1
fi

make -j$(nproc)
if [[ $? -ne 0 ]] ; then
    exit 1
fi

sudo make install 
if [[ $? -ne 0 ]] ; then
    exit 1
fi


cd ../gcc-$GCC_VERSION
mkdir -p build 
cd build
../configure --target=$TARGET \
  --prefix=$PREFIX \
  --with-pic \
  --with-sysroot=$PREFIX/$TARGET \
  --libexecdir=$PREFIX/${TARGET}/lib \
  --with-native-system-header-dir=/include \
  --enable-languages=c,c++ \
  --enable-plugins \
  --disable-decimal-float \
  --disable-libffi \
  --disable-libstdcxx-pch \
  --disable-libgomp \
  --disable-libmudflap \
  --disable-libquadmath \
  --disable-libssp \
  --disable-nls \
  --enable-shared=libgcc \
  --disable-threads \
  --disable-tls \
  --with-gnu-ld \
  --with-gnu-as \
  --with-system-zlib \
  --with-newlib \
  --with-headers=${PREFIX}/${TARGET}/include \
  --with-python-dir=share/gcc-arm-none-eabi \
  --with-gmp \
  --with-mpfr \
  --with-isl \
  --with-mpc \
  --with-libelf \
  --enable-gnu-indirect-function \
  --with-pkgversion='Yasld Toolchain' \
  --with-multilib-list=rmprofile

if [[ $? -ne 0 ]] ; then
    exit 1
fi

make -j$(nproc) INHIBIT_LIBC_CFLAGS='-DUSE_TM_CLONE_REGISTRY=0'
if [[ $? -ne 0 ]] ; then
    exit 1
fi

sudo make install 
if [[ $? -ne 0 ]] ; then
    exit 1
fi

