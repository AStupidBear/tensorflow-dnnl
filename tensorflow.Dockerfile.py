#!/usr/bin/env python
try:
    from pydocker import DockerFile
except ImportError:
    try:
        from urllib.request import urlopen
    except ImportError:
        from urllib import urlopen
    exec(urlopen('https://raw.githubusercontent.com/AStupidBear/pydocker/master/pydocker.py').read())

import logging
import os
import sys
import tempfile

import psutil

logging.getLogger('').setLevel(logging.INFO)
logging.root.addHandler(logging.StreamHandler(sys.stdout))

tf_compat = os.getenv('TF_COMPAT', '0') == '1'

if tf_compat:
    img = 'registry.cn-hangzhou.aliyuncs.com/astupidbear/tensorflow-compat:latest'
else:
    img = 'registry.cn-hangzhou.aliyuncs.com/astupidbear/tensorflow:latest'
d = DockerFile(base_img='tensorflow/tensorflow:devel-gpu-py3', name=img)

d.WORKDIR = '/tensorflow_src'
d.RUN = 'cd "/usr/local/lib/bazel/bin" && curl -LO https://releases.bazel.build/0.29.1/release/bazel-0.29.1-linux-x86_64 && chmod +x bazel-0.29.1-linux-x86_64'
d.RUN = 'git pull && git checkout r2.2 && yes "" | TF_CUDA_COMPUTE_CAPABILITIES="6.0,6.1,7.0,7.5" ./configure'
if tf_compat:
    d.RUN = 'bazel build --noincompatible_do_not_split_linking_cmdline -c opt --copt=-march=x86-64 --config=mkl --config=cuda --cxxopt="-D_GLIBCXX_USE_CXX11_ABI=0" --config=monolithic -k //tensorflow/tools/pip_package:build_pip_package'
else:
    d.RUN = 'bazel build --noincompatible_do_not_split_linking_cmdline -c opt --copt=-march=x86-64 --copt=-mavx --copt=-mavx2 --copt=-mfma --copt=-mfpmath=both --copt=-msse4.2 --config=mkl --config=cuda -k //tensorflow/tools/pip_package:build_pip_package'
d.RUN = './bazel-bin/tensorflow/tools/pip_package/build_pip_package /opt'

os.chdir(tempfile.mkdtemp())
d.build_img(extra_args='--network host --cpuset-cpus 0-%d' % (psutil.cpu_count() / 2))
os.system('docker run --name tensorflow %s /bin/true' % img)
os.makedirs('/tmp/tensorflow/', exist_ok=True)
os.system('docker cp tensorflow:/opt /tmp/tensorflow/')
os.system('docker rm tensorflow')
