from setuptools import setup, find_packages

setup(name='python-juicenet',
      version='0.1.7',
      description='Read and control Juicenet/Juicepoint/Juicebox based EVSE devices',
      url='http://github.com/jesserockz/python-juicenet',
      author='Jesse Hills',
      license='MIT',
      install_requires=['requests'],
      packages=find_packages(exclude=["dist"]),
      zip_safe=True)
