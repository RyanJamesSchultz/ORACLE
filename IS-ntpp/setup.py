from setuptools import find_packages, setup

setup(
    name='eq',
    version='1.0',
    description='ORCALE: induced seismicity forecasting with a neural temporal point process',
    packages=find_packages('.'),
    zip_safe=False,
)
